#!/usr/bin/env python3

import sys
import os
import pysam
import time
from subprocess import check_call
from optparse import OptionParser
from multiprocessing import Pool

def get_primer_info(file_primer):
	R_set = set()
	with open(file_primer,'r') as fa:
		for line in fa:
			chrn, primer1, start1, end1, primer2, start2, end2 = line.split()
			if int(start1) > int(start2):
				R1_start = start2
				R1_end = end2
				R2_start = start1
				R2_end = end1
			elif int(start1) < int(start2):
				R1_start = start1
				R1_end = end1
				R2_start = start2
				R2_end = end2
			R_set.add('%s\t%s\t%s\t%s\t%s'%(chrn,R1_start,R1_end,R2_start,R2_end))
	return R_set

def cut_primer(chrn,pos,pos_end,reverse,seq,qua,R_set):
	result = 'NA'
	for i in R_set:
		p_chrn, p_start1, p_end1, p_start2, p_end2 = i.split()
		if chrn == p_chrn and int(pos) - 10 <= int(p_start1) <= int(pos) + 10 and reverse == 'mate_reverse':
			result = 'PASS'
			#cut_seq = seq[(int(p_end1) - int(p_start1) + 1):]
			cut_seq = seq
			#cut_qua = qua[(int(p_end1) - int(p_start1) + 1):]
			cut_qua = '!'*(int(p_end1) - int(p_start1) + 1) + qua[(int(p_end1) - int(p_start1) + 1):]
			break
		elif chrn == p_chrn and int(pos_end) - 10 <= int(p_end2) <= int(pos_end) + 10 and reverse == 'read_reverse':
			result = 'PASS'
			#cut_seq = seq[0:(100 - int(p_end2) + int(p_start2) + 1)]
			cut_seq = seq
			#cut_qua = qua[0:(100 - int(p_end2) + int(p_start2) + 1)]
			cut_qua = qua[0:(len(seq) - int(p_end2) + int(p_start2) - 1)] + '!'*(int(p_end2) - int(p_start2) + 1)
			break
	if result == 'NA':
		cut_seq = seq
		cut_qua = qua
	return cut_seq, cut_qua, result

def revcom(seq):
	return seq.translate(str.maketrans('ACGT', 'TGCA'))[::-1]

def gzip_fq(fastq):
	check_call('gzip %s'%(fastq),shell=True)
	return

def usage():
	"""
Primer adapter processing program.
----------------------------------
Version: 1.2

Usage:
	Cut_Multi_Primer.py -p <STR> -b <STR> -s <STR> -o <STR>

Param list:
	-h		Help information
	-p		Primer position file.
	-b		Input bam file
	-s		Sample name
	-o		Output directory
	-t		Fastq type(PE/SE)
	"""
	print(usage.__doc__)
	sys.exit(1)
	return

if __name__ == '__main__':
	if len(sys.argv) < 2:
		usage()
	parser = OptionParser()
	parser.add_option('-p', dest = 'opt_p', help = 'Primer position file', type = 'string')
	parser.add_option('-b', dest = 'opt_b', help = 'Input bam file', type = 'string')
	parser.add_option('-s', dest = 'opt_s', help = 'Sample name', type = 'string')
	parser.add_option('-o', dest = 'opt_o', help = 'Output directory', type = 'string')
	parser.add_option('-t', dest = 'opt_t', help = 'Fastq type', type = 'string')
	optlist, args = parser.parse_args()

	file_primer = optlist.opt_p
	inbam = optlist.opt_b
	sample = optlist.opt_s
	outdir = optlist.opt_o
	FqType_p = optlist.opt_t
	FqType = FqType_p[0:2]

	print('[',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'] Started processing ')

	R_set = get_primer_info(file_primer)
	file_inbam = pysam.AlignmentFile(inbam,'rb',check_sq=False)
	outfq1 = '%s/%s_1.cutprimer.fq'%(outdir,sample)
	outfq2 = '%s/%s_2.cutprimer.fq'%(outdir,sample)
	outfq = '%s/%s.cutprimer.fq'%(outdir,sample)
	log = '%s/%s.cutprimer.log'%(outdir,sample)

	fq1_dict = {}
	fq2_dict = {}
	#abnormal_set = set()

	n = 0
	a = 0

	if FqType == 'PE':
		file_out1 = open(outfq1,'w')
		file_out2 = open(outfq2,'w')
	elif FqType == 'SE':
		file_out = open(outfq,'w')

	for r in file_inbam:
		readid = r.query_name
		seq = r.seq
		qua = r.qual
		try:
			chrn = r.reference_name
			pos = int(r.pos) + 1
			pos_end = pos
			cigar = r.cigartuples
			for key, value in cigar:
				if key == 0 or key == 1 or key == 2:
					pos_end += value
		except:
			continue

		if r.is_unmapped:
			continue
		if r.is_reverse:
			reverse = 'read_reverse'
		else:
			reverse = 'mate_reverse'

		if r.is_secondary:
			continue
		if chrn != 'NC_001608.3' and n > 1:
			continue
		else:
			n += 1
		cut_seq, cut_qua, result = cut_primer(chrn,pos,pos_end,reverse,seq,qua,R_set)
		if result == 'NA':
			a += 1
			continue
			#abnormal_set.add(readid)
		if r.is_reverse:
			cut_seq = revcom(cut_seq)
			cut_qua = cut_qua[::-1]
		if FqType == 'PE':
			if r.is_read1:
				fq1_dict[readid] = '@%s/1\n%s\n%s\n%s\n'%(readid,cut_seq,'+',cut_qua)
			else:
				fq2_dict[readid] = '@%s/2\n%s\n%s\n%s\n'%(readid,cut_seq,'+',cut_qua)
			if readid in fq1_dict and readid in fq2_dict:
				file_out1.write(fq1_dict[readid])
				file_out2.write(fq2_dict[readid])
				del fq1_dict[readid]
				del fq2_dict[readid]
		elif FqType == 'SE':
			file_out.write('@%s\n%s\n%s\n%s\n'%(readid,cut_seq,'+',cut_qua))

	file_inbam.close()
	file_log = open(log,'w')
	file_log.write('Fraction of invalid reads: ' + ('NA' if n == 0 else '%.3f' % (100 * a / n)) + '%\n')
	file_log.close()

	if FqType == 'PE':
		file_out1.close()
		file_out2.close()

		if os.path.exists(outfq1+'.gz'):
			check_call('rm %s.gz'%(outfq1),shell=True)
		if os.path.exists(outfq2+'.gz'):
			check_call('rm %s.gz'%(outfq2),shell=True)

		p = Pool(2)
		p.apply_async(gzip_fq,args=(outfq1,))
		p.apply_async(gzip_fq,args=(outfq2,))
		p.close()
		p.join()

		print('[',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'] Finished processing ')
	elif FqType == 'SE':
		file_out.close()
		file_log.close()

		if os.path.exists(outfq+'.gz'):
			check_call('rm %s.gz'%(outfq),shell=True)

		gzip_fq(outfq)
		print('[',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'] Finished processing ')
