#!/usr/bin/env python3

import sys
import os
import re
import getopt
import configparser
import json
from subprocess import check_call
from collections import defaultdict

def usage():
	"""Main program of SARS-CoV-2 panel analysis pipeline.
	Usage: Main_SARS-CoV-2.py -i <config>
	-i	Config json file
	-h	Help information
	-s	Submit model [local/qsubsge]
	"""
	print(usage.__doc__)
	return

def create_dirs(*dirname):
	for each in dirname:
		if not os.path.exists(each):
			os.system("mkdir -p %s" % each)
	return

def fqtype_error():
	print('FqType is not valid,use SE/PE.')
	sys.exit(1)
	return

def GenerateData(script,sample_dict,fqtype):
	for key, value in sample_dict.items():
		sample = key
		barcode_dir = result_dir + '/' + sample
		Clean_dir = barcode_dir + '/01.Clean'
		create_dirs(Clean_dir)
		if len(value) == 1:
			for k, v in value.items():
				barcode = k
				raw_path = v
				if fqtype == 'SE':
					rawfq = 'Raw_' + sample + '.fq.gz'
					if os.path.exists('%s/%s'%(Clean_dir,rawfq)):
						os.system('rm %s/%s'%(Clean_dir,rawfq))
					script.write("ln -s %(raw_path)s/*%(barcode)s.fq.gz %(Clean_dir)s/%(rawfq)s\n"%{'raw_path':raw_path,'barcode':barcode,'Clean_dir':Clean_dir,'rawfq':rawfq})
				elif fqtype == 'PE':
					rawfq1 = 'Raw_' + sample + '_1.fq.gz'
					rawfq2 = 'Raw_' + sample + '_2.fq.gz'
					if os.path.exists('%s/%s'%(Clean_dir,rawfq1)):
						os.system('rm %s/%s'%(Clean_dir,rawfq1))
					if os.path.exists('%s/%s'%(Clean_dir,rawfq2)):
						os.system('rm %s/%s'%(Clean_dir,rawfq2))
					script.write("ln -s %(raw_path)s/*%(barcode)s_1.fq.gz %(Clean_dir)s/%(rawfq1)s\nln -s %(raw_path)s/*%(barcode)s_2.fq.gz %(Clean_dir)s/%(rawfq2)s\n"%{'raw_path':raw_path,'barcode':barcode,'Clean_dir':Clean_dir,'rawfq1':rawfq1,'rawfq2':rawfq2})
				else:
					fqtype_error()
		else:
			if fqtype == 'SE':
				rawfq = 'Raw_' + sample + '.fq.gz'
				cmd = 'cat '
				for k, v in value.items():
					barcode = k
					raw_path = v
					cmd += '%s/*%s.fq.gz '%(raw_path,barcode)
				cmd += '> %s/%s\n'%(Clean_dir,rawfq)
				script.write(cmd)
			elif fqtype == 'PE':
				rawfq1 = 'Raw_' + sample + '_1.fq.gz'
				rawfq2 = 'Raw_' + sample + '_2.fq.gz'
				cmd1 = 'cat '
				cmd2 = 'cat '
				for k, v in value.items():
					barcode = k
					raw_path = v
					cmd1 += '%s/*%s_1.fq.gz '%(raw_path,barcode)
					cmd2 += '%s/*%s_2.fq.gz '%(raw_path,barcode)
				cmd1 += '> %s/%s\n'%(Clean_dir,rawfq1)
				cmd2 += '> %s/%s\n'%(Clean_dir,rawfq2)
				script.write(cmd1)
				script.write(cmd2)
			else:
				fqtype_error()
	return

def CleanData(script,sample,fqtype,SplitData,qualsys):
	barcode_dir = result_dir + '/' + sample
	Clean_dir = barcode_dir + '/01.Clean'
	conf = '%s/soapnuke_conf.txt'%(Clean_dir)
	create_dirs(Clean_dir)
	with open(conf,'w') as fs:
		fs.write('qualSys=%s\n'%(qualsys))
	if fqtype == 'SE':
		#rawfq = raw_data_path + '/*' + barcode + '.fq.gz'
		rawfq = Clean_dir + '/Raw_' + sample + '.fq.gz'
		#cleanfq = Clean_dir + '/Clean_' + sample + '.fq.gz'
		cleanfq = 'Clean_' + sample + '.fq.gz'

		if SplitData:
			t_dict = {'G':10**9,'M':10**6,'K':10**3}
			SplitData_n = int(SplitData.strip()[0:-1])*t_dict[SplitData.strip()[-1]]
			with open(conf,'a') as fs:
				fs.write('totalReadsNum=%s\n'%(SplitData_n))
			script.write("%(SOAPnuke)s filter %(SOAPnuke_param)s -1 %(rawfq)s -C %(cleanfq)s -o %(Clean_dir)s -c %(conf)s\n"\
				%{'SOAPnuke':SOAPnuke,'SOAPnuke_param':SOAPnuke_param,'rawfq':rawfq,'cleanfq':cleanfq,'Clean_dir':Clean_dir,'conf':conf})
		else:
			script.write("%(SOAPnuke)s filter %(SOAPnuke_param)s -1 %(rawfq)s -C %(cleanfq)s -o %(Clean_dir)s -c %(conf)s\n"\
				%{'SOAPnuke':SOAPnuke,'SOAPnuke_param':SOAPnuke_param,'rawfq':rawfq,'cleanfq':cleanfq,'Clean_dir':Clean_dir,'conf':conf})
	elif fqtype == 'PE':
		#rawfq1 = raw_data_path + '/*' + barcode + '_1.fq.gz'
		#rawfq2 = raw_data_path + '/*' + barcode + '_2.fq.gz'
		rawfq1 = Clean_dir + '/Raw_' + sample + '_1.fq.gz'
		rawfq2 = Clean_dir + '/Raw_' + sample + '_2.fq.gz'
		#cleanfq1 = Clean_dir + '/Clean_' + sample + '_1.fq.gz'
		#cleanfq2 = Clean_dir + '/Clean_' + sample + '_2.fq.gz'
		cleanfq1 = 'Clean_' + sample + '_1.fq.gz'
		cleanfq2 = 'Clean_' + sample + '_2.fq.gz'

		if SplitData:
			t_dict = {'G':10**9,'M':10**6,'K':10**3}
			SplitData_n = int(SplitData.strip()[0:-1])*t_dict[SplitData.strip()[-1]]
			with open(conf,'a') as fs:
				fs.write('totalReadsNum=%s\n'%(SplitData_n))
			script.write("%(SOAPnuke)s filter %(SOAPnuke_param)s -1 %(rawfq1)s -2 %(rawfq2)s -C %(cleanfq1)s -D %(cleanfq2)s -o %(Clean_dir)s -c %(conf)s\n"\
				%{'SOAPnuke':SOAPnuke,'SOAPnuke_param':SOAPnuke_param,'rawfq1':rawfq1,'rawfq2':rawfq2,'cleanfq1':cleanfq1,'cleanfq2':cleanfq2,'Clean_dir':Clean_dir,'conf':conf})
		else:
			script.write("%(SOAPnuke)s filter %(SOAPnuke_param)s -1 %(rawfq1)s -2 %(rawfq2)s -C %(cleanfq1)s -D %(cleanfq2)s -o %(Clean_dir)s -c %(conf)s\n"\
			%{'SOAPnuke':SOAPnuke,'SOAPnuke_param':SOAPnuke_param,'rawfq1':rawfq1,'rawfq2':rawfq2,'cleanfq1':cleanfq1,'cleanfq2':cleanfq2,'Clean_dir':Clean_dir,'conf':conf})
	else:
		fqtype_error()
	return

def bwaaln(script,barcode,fqtype,read_len):
	barcode_dir = result_dir + '/' + barcode
	Clean_dir = barcode_dir + '/01.Clean'
	Align_dir = barcode_dir + '/02.Align'
	create_dirs(Align_dir)
	seed_len = str(int(int(read_len)*0.9))
	max_diff_seed = int(int(seed_len)/16)
	if fqtype == 'SE':
		cleanfq = Clean_dir + '/Clean_' + barcode + '.fq.gz'
		script.write("%(bwa)s aln -l %(seed_len)s -k %(max_diff_seed)s -t 3 -f %(Align_dir)s/%(barcode)s.sai %(database)s/%(reftag)s.fa %(cleanfq)s && %(bwa)s samse -r \"@RG\\tID:PE100\\tPL:MGISEQ\\tPU:PE100\\tLB:mutPCR\\tSM:%(barcode)s\\tCN:BGI\" %(database)s/%(reftag)s.fa %(Align_dir)s/%(barcode)s.sai %(cleanfq)s | %(samtools)s view -b - | %(samtools)s sort -T %(Align_dir)s/%(barcode)s.sort -o %(Align_dir)s/%(barcode)s.sort.bam - && rm %(Align_dir)s/%(barcode)s.sai\n" \
			%{'bwa':bwa,'samtools':samtools,'database':database,'cleanfq':cleanfq,'Align_dir':Align_dir,'barcode':barcode,'seed_len':seed_len,'max_diff_seed':max_diff_seed})
		script.write("%(samtools)s index %(Align_dir)s/%(barcode)s.sort.bam \n" %{'samtools':samtools,'Align_dir':Align_dir,'barcode':barcode})
	elif fqtype == 'PE':
		cleanfq1 = Clean_dir + '/Clean_' + barcode + '_1.fq.gz'
		cleanfq2 = Clean_dir + '/Clean_' + barcode + '_2.fq.gz'
		script.write("%(bwa)s aln -l %(seed_len)s -k %(max_diff_seed)s -t 3 -f %(Align_dir)s/%(barcode)s_1.sai %(database)s/%(reftag)s.fa %(cleanfq1)s && %(bwa)s aln -l %(seed_len)s -k %(max_diff_seed)s -t 3 -f %(Align_dir)s/%(barcode)s_2.sai %(database)s/%(reftag)s.fa %(cleanfq2)s && %(bwa)s sampe -a 1000 -r \"@RG\\tID:PE100\\tPL:MGISEQ\\tPU:PE100\\tLB:mutPCR\\tSM:%(barcode)s\\tCN:BGI\" %(database)s/%(reftag)s.fa %(Align_dir)s/%(barcode)s_1.sai %(Align_dir)s/%(barcode)s_2.sai %(cleanfq1)s %(cleanfq2)s | %(samtools)s view -b - | %(samtools)s sort -T %(Align_dir)s/%(barcode)s.sort -o %(Align_dir)s/%(barcode)s.sort.bam - && rm %(Align_dir)s/%(barcode)s_1.sai %(Align_dir)s/%(barcode)s_2.sai\n" \
			%{'bwa':bwa,'samtools':samtools,'database':database,'cleanfq1':cleanfq1,'cleanfq2':cleanfq2,'Align_dir':Align_dir,'barcode':barcode,'seed_len':seed_len,'max_diff_seed':max_diff_seed})
		script.write("%(samtools)s index %(Align_dir)s/%(barcode)s.sort.bam \n" %{'samtools':samtools,'Align_dir':Align_dir,'barcode':barcode})
	return

def bwamem(script,barcode,fqtype):
	barcode_dir = result_dir + '/' + barcode
	Clean_dir = barcode_dir + '/01.Clean'
	Align_dir = barcode_dir + '/02.Align'
	create_dirs(Align_dir)
	if fqtype == 'SE':
		cleanfq = Clean_dir + '/Clean_' + barcode + '.fq.gz'
		script.write("%(bwa)s mem -M -R \"@RG\\tID:%(barcode)s\\tPL:MGISEQ\\tLB:mutPCR\\tSM:%(barcode)s\" -t 1 %(database)s/%(reftag)s.fa %(cleanfq)s | %(samtools)s view -b - | %(samtools)s sort -T %(Align_dir)s/%(barcode)s.sort -o %(Align_dir)s/%(barcode)s.sort.bam -\n"\
			%{'reftag':reftag,'bwa':bwa,'samtools':samtools,'database':database,'cleanfq':cleanfq,'Align_dir':Align_dir,'barcode':barcode})
		script.write("%(samtools)s index %(Align_dir)s/%(barcode)s.sort.bam \n" %{'samtools':samtools,'Align_dir':Align_dir,'barcode':barcode})
	elif fqtype == 'PE':
		cleanfq1 = Clean_dir + '/Clean_' + barcode + '_1.fq.gz'
		cleanfq2 = Clean_dir + '/Clean_' + barcode + '_2.fq.gz'
		script.write("%(bwa)s mem -M -R \"@RG\\tID:%(barcode)s\\tPL:MGISEQ\\tLB:mutPCR\\tSM:%(barcode)s\" -t 1 %(database)s/%(reftag)s.fa %(cleanfq1)s %(cleanfq2)s | %(samtools)s view -b - | %(samtools)s sort -T %(Align_dir)s/%(barcode)s.sort -o %(Align_dir)s/%(barcode)s.sort.bam -\n"\
			%{'reftag':reftag,'bwa':bwa,'samtools':samtools,'database':database,'cleanfq1':cleanfq1,'cleanfq2':cleanfq2,'Align_dir':Align_dir,'barcode':barcode})
		script.write("%(samtools)s index %(Align_dir)s/%(barcode)s.sort.bam \n" %{'samtools':samtools,'Align_dir':Align_dir,'barcode':barcode})
	else:
		fqtype_error()
	return

def CovDep(script,barcode):
	barcode_dir = result_dir + '/' + barcode
	Align_dir = barcode_dir + '/02.Align'
	covdep_dir = barcode_dir + '/03.covdep'
	lambda_covdep_dir = covdep_dir + '/lambda_cov'
	GAPDH_covdep_dir = covdep_dir + '/GAPDH_cov'
	create_dirs(covdep_dir,lambda_covdep_dir,GAPDH_covdep_dir)
	## bamqc with all map bam
	script.write("%(bamdst)s --cutoffdepth 1 --maxdepth 1000000 -q 1 -p %(virusbed)s -o %(covdep_dir)s %(Align_dir)s/%(barcode)s.sort.bam \n"\
		%{'bamdst':bamdst,'virusbed':virusbed,'covdep_dir':covdep_dir,'Align_dir':Align_dir,'barcode':barcode})
	script.write("%(bamdst)s --cutoffdepth 1 --maxdepth 1000000 -q 1 -p %(lambdabed)s -o %(covdep_dir)s/lambda_cov %(Align_dir)s/%(barcode)s.sort.bam \n"\
		%{'bamdst':bamdst,'lambdabed':lambdabed,'covdep_dir':covdep_dir,'Align_dir':Align_dir,'barcode':barcode})
	script.write("%(bamdst)s --cutoffdepth 1 --maxdepth 1000000 -q 1 -p %(GAPDH_bed)s -o %(covdep_dir)s/GAPDH_cov %(Align_dir)s/%(barcode)s.sort.bam \n"\
		%{'bamdst':bamdst,'GAPDH_bed':GAPDH_bed,'covdep_dir':covdep_dir,'Align_dir':Align_dir,'barcode':barcode})
	return

def Statistics(script,fqtype):
	if fqtype == 'PE':
		script.write("export PYTHONPATH=%(python3_lib)s:$PYTHONPATH && %(python3)s %(bin)s/CoV_stat.py -t PE -d %(result_dir)s -l %(barcode_file)s\n"\
			%{'bin':bin,'result_dir':result_dir,'barcode_file':barcode_file,'python3':python3,'python3_lib':python3_lib})
	elif fqtype == 'SE':
		script.write("export PYTHONPATH=%(python3_lib)s:$PYTHONPATH && %(python3)s %(bin)s/CoV_stat.py -t SE -d %(result_dir)s -l %(barcode_file)s\n"\
			%{'bin':bin,'result_dir':result_dir,'barcode_file':barcode_file,'python3':python3,'python3_lib':python3_lib})
	return

def CutPrimer(script,fqtype_p,sample):
	sample_dir = result_dir + '/' + sample
	Align_dir = sample_dir + '/02.Align'
	CutPrimer_dir = sample_dir + '/04.CutPrimer'
	create_dirs(CutPrimer_dir)
	#script.write("export PYTHONPATH=%(python3_lib)s:$PYTHONPATH && %(python3)s %(bin)s/Cut_Multi_Primer.py -p %(primer_list)s -b %(Align_dir)s/%(sample)s.sort.bam -s %(sample)s -o %(CutPrimer_dir)s && %(samtools)s index %(CutPrimer_dir)s/%(sample)s.bam\n"\
	#	%{'bin':bin,'primer_list':primer_list,'Align_dir':Align_dir,'sample':sample,'CutPrimer_dir':CutPrimer_dir,'lib':lib,'python3':python3,'fqtype_p':fqtype_p,'python3_lib':python3_lib,'samtools':samtools})
	script.write("export PYTHONPATH=%(python3_lib)s:$PYTHONPATH && %(python3)s %(bin)s/Cut_Multi_Primer.OutputFq.py -p %(primer_list)s -b %(Align_dir)s/%(sample)s.sort.bam -s %(sample)s -o %(CutPrimer_dir)s -t %(fqtype_p)s\n"\
		%{'bin':bin,'primer_list':primer_list,'Align_dir':Align_dir,'sample':sample,'CutPrimer_dir':CutPrimer_dir,'lib':lib,'python3':python3,'fqtype_p':fqtype_p,'python3_lib':python3_lib})
	return

def AlignVariant(script,fqtype,cutprimer_list,consensus_depth):
	with open(cutprimer_list,'r') as fi:
		for line in fi:
			i = line.split()
			sample = i[0]
			if fqtype == 'PE':
				fq1 = i[1]
				fq2 = i[2]
			elif fqtype == 'SE':
				fq = i[1]
			sample_dir = result_dir + '/' + sample
			Align_dir = sample_dir + '/02.Align'
			CutPrimer_dir = sample_dir + '/04.CutPrimer'
			Stat_dir = sample_dir + '/05.Stat'
			create_dirs(Stat_dir)
			if fqtype == 'PE':
				script.write("%(flash)s %(flash_param)s %(fq1)s %(fq2)s -o %(sample)s -d %(CutPrimer_dir)s && %(bwa)s mem -Y -M -R \"@RG\\tID:%(sample)s\\tSM:%(sample)s\" -t 1 %(ref)s %(CutPrimer_dir)s/%(sample)s.notCombined_1.fastq %(CutPrimer_dir)s/%(sample)s.notCombined_2.fastq | %(samtools)s view -b - | %(samtools)s sort -T %(Stat_dir)s/%(sample)s -o %(Stat_dir)s/%(sample)s.notCombined.bam - && %(bwa)s mem -Y -M -R \"@RG\\tID:%(sample)s\\tSM:%(sample)s\" -t 1 %(ref)s %(CutPrimer_dir)s/%(sample)s.extendedFrags.fastq | %(samtools)s view -b - | %(samtools)s sort -T %(Stat_dir)s/%(sample)s -o %(Stat_dir)s/%(sample)s.extendedFrags.bam - && %(samtools)s merge -f %(Stat_dir)s/%(sample)s.bam %(Stat_dir)s/%(sample)s.notCombined.bam %(Stat_dir)s/%(sample)s.extendedFrags.bam && rm %(Stat_dir)s/%(sample)s.notCombined.bam %(Stat_dir)s/%(sample)s.extendedFrags.bam\n"\
					%{'bwa':bwa,'samtools':samtools,'sample':sample,'ref':ref,'fq1':fq1,'fq2':fq2,'Stat_dir':Stat_dir,'flash':flash,'flash_param':flash_param,'CutPrimer_dir':CutPrimer_dir})
			elif fqtype == 'SE':
				script.write("%(bwa)s mem -Y -M -R \"@RG\\tID:%(sample)s\\tSM:%(sample)s\" -t 3 %(ref)s %(fq)s | %(samtools)s view -b - | %(samtools)s sort -T %(Stat_dir)s/%(sample)s -o %(Stat_dir)s/%(sample)s.bam -\n"\
					%{'bwa':bwa,'samtools':samtools,'sample':sample,'ref':ref,'fq':fq,'Stat_dir':Stat_dir})
			script.write("%(samtools)s index %(Stat_dir)s/%(sample)s.bam\n"%{'samtools':samtools,'Stat_dir':Stat_dir,'sample':sample})
			script.write("%(mosdepth)s -n --fast-mode -c MN908947.3 --by 100 %(Stat_dir)s/depth %(Stat_dir)s/%(sample)s.bam\n"%{'mosdepth':mosdepth,'Stat_dir':Stat_dir,'sample':sample,'CutPrimer_dir':CutPrimer_dir})
			script.write("zcat %(Stat_dir)s/depth.regions.bed.gz|awk  '{print NR\"\\t\"log($4+1)/log(10)}' > %(Stat_dir)s/%(sample)s.draw.depth\n"%{'Stat_dir':Stat_dir,'sample':sample})
			script.write("%(samtools)s depth -d 100000000 -a -b %(variantbed)s %(Stat_dir)s/%(sample)s.bam > %(Stat_dir)s/%(sample)s.depth\n"%{'samtools':samtools,'variantbed':variantbed,'sample':sample,'Stat_dir':Stat_dir,'CutPrimer_dir':CutPrimer_dir})
			script.write("export R_LIBS=%(R_lib)s:$R_LIBS && %(Rscript)s %(bin)s/line.depth.R %(Stat_dir)s/%(sample)s.draw.depth %(Stat_dir)s/Windows.Depth.svg\n"%{'Rscript':Rscript,'bin':bin,'Stat_dir':Stat_dir,'R_lib':R_lib,'sample':sample})
			script.write("%(freebayes)s -t %(virusbed)s %(freebayes_param)s -f %(ref)s %(Stat_dir)s/%(sample)s.bam > %(Stat_dir)s/%(sample)s.raw.vcf && %(bcftools)s norm -f %(ref)s %(Stat_dir)s/%(sample)s.raw.vcf -o %(Stat_dir)s/%(sample)s.vcf\n%(bgzip)s -f %(Stat_dir)s/%(sample)s.vcf\n%(tabix)s %(Stat_dir)s/%(sample)s.vcf.gz\n%(java)s -jar %(bin)s/snpEff/snpEff.jar MN908947.3 %(Stat_dir)s/%(sample)s.vcf.gz > %(Stat_dir)s/%(sample)s.snpEff.vcf -stats %(Stat_dir)s/%(sample)s.snpEff.html \nexport PYTHONPATH=%(python3_lib)s:$PYTHONPATH && %(python3)s %(bin)s/get_anno_table.py %(Stat_dir)s/%(sample)s.snpEff.vcf %(Stat_dir)s %(sample)s\n"%{'freebayes':freebayes,'virusbed':virusbed,'Stat_dir':Stat_dir,'sample':sample,'ref':ref,'bgzip':bgzip,'tabix':tabix,'bcftools':bcftools,'freebayes_param':freebayes_param,'java':java,'bin':bin,'python3':python3,'python3_lib':python3_lib,'CutPrimer_dir':CutPrimer_dir})
			script.write("%(bin)s/Consensus.pl %(Stat_dir)s/%(sample)s.depth %(ref)s %(consensus_depth)s %(Stat_dir)s/%(sample)s.reference1.fa %(Stat_dir)s/%(sample)s.vcf.gz\n"%{'bin':bin,'Stat_dir':Stat_dir,'sample':sample,'ref':ref,'consensus_depth':consensus_depth})
			script.write("%(bcftools)s consensus -f %(Stat_dir)s/%(sample)s.reference1.fa -o %(Stat_dir)s/%(sample)s.Consensus.fa %(Stat_dir)s/%(sample)s.vcf.gz\n"%{'bcftools':bcftools,'Stat_dir':Stat_dir,'sample':sample})
			script.write("sed -i \"s/MN908947.3 MARV, complete genome/%(sample)s/g\" %(Stat_dir)s/%(sample)s.Consensus.fa\n"%{'Stat_dir':Stat_dir,'sample':sample})
			script.write("zcat %(Stat_dir)s/%(sample)s.vcf.gz | grep -v '^#'|awk '{print $1\"\\t\"$2-1\"\\t\"$2\"\\t\"$4\"\\t\"$5}'| %(bedtools)s intersect -a - -b %(bed2)s -loj |cut -f 1,3-5,9 > %(Stat_dir)s/%(sample)s.vcf.anno\n"%{'Stat_dir':Stat_dir,'sample':sample,'bedtools':bedtools,'bed2':bed2})
			#script.write("rm %(Stat_dir)s/%(sample)s.draw.depth %(Stat_dir)s/%(sample)s.reference1.fa\n"%{'Stat_dir':Stat_dir,'sample':sample})
	return

def GetReport(script,sample):
	sample_dir = result_dir + '/' + sample
	Stat_dir = sample_dir + '/05.Stat'
	script.write("%(python3)s %(bin)s/etiology/generate_rem_report.py %(Stat_dir)s %(sample)s \n"\
		%{'bin':bin,'Stat_dir':Stat_dir,'sample':sample,'python3':python3})
	return

def MainShell(script_file,step0shell,step1shell,step2shell,step3shell,step4shell,step5shell,step6shell,step7shell):
	script = open(script_file,'w')
	script.write('''echo "start step0  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step0 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step0shell})
	script.write('''echo "start step1  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step1 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step1shell})
	script.write('''echo "start step2  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 6G --lines 2 --maxjob 300 %(stepshell)s && echo "finish step2 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step2shell})
	script.write('''echo "start step3  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step3 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step3shell})
	script.write('''echo "start step4  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step4 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step4shell})
	script.write('''echo "start step5  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step5 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step5shell})
	script.write('''echo "start step6  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 6G --lines 15 --maxjob 300 %(stepshell)s && echo "finish step6 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step6shell})
	script.write('''echo "start step7  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(watchdog)s --mem 1G --lines 1 --maxjob 300 %(stepshell)s && echo "finish step7 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'watchdog':watchdog,'stepshell':step7shell})
	script.write('%(python3)s %(bin)s/Result_summary.py -l %(barcode_file)s -r %(result_dir)s -o %(sum_dir)s\n'%{'python3':python3,'bin':bin,'barcode_file':barcode_file,'result_dir':result_dir,'sum_dir':sum_dir})
	script.close()
	return

def MainShell_qsubsge(script_file,step0shell,step1shell,step2shell,step3shell,step4shell,step5shell,step6shell,step7shell):
	script = open(script_file,'w')
	script.write('''echo "start step0  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step1 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step0 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step0shell})
	script.write('''echo "start step1  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step1 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step1 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step1shell})
	script.write('''echo "start step2  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step2 --lines 2 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step2 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step2shell})
	script.write('''echo "start step3  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step3 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step3 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step3shell})
	script.write('''echo "start step4  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G,p=2 -binding linear:2 -P %(subproject)s"  --jobprefix step4 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step4 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step4shell})
	script.write('''echo "start step5  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step5 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step5 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step5shell})
	script.write('''echo "start step6  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=6G -P %(subproject)s -l num_proc=1"  --jobprefix step6 --lines 15 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step6 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step6shell})
	script.write('''echo "start step7  at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`" && perl %(qsubsge)s --queue %(queue)s --resource="vf=1G -P %(subproject)s -l num_proc=1"  --jobprefix step7 --lines 1 --reqsub --interval 5 --convert no -maxjob 500 %(stepshell)s && echo "finish step7 at `date +'%%Y-%%m-%%d %%H:%%M:%%S %%z'`"\n'''\
		%{'qsubsge':qsubsge,'queue':queue,'subproject':subproject,'stepshell':step7shell})
	script.write('%(python3)s %(bin)s/Result_summary.py -l %(barcode_file)s -r %(result_dir)s -o %(sum_dir)s\n'%{'python3':python3,'bin':bin,'barcode_file':barcode_file,'result_dir':result_dir,'sum_dir':sum_dir})
	script.close()
	return

if __name__ == '__main__':
	if len(sys.argv) < 2:
		usage()
		sys.exit(1)

	try:
		opts,args = getopt.getopt(sys.argv[1:],"hi:s:")
	except getopt.GetoptError:
		print("ERROR: Param error")
		sys.exit(1)

	subprj = 'local'

	for key, value in opts:
		if key == '-h':
			usage()
			sys.exit()
		if key == '-i':
			jsonfile = value
		if key == '-s':
			subprj = value
	file_json = open(jsonfile,'r')
	jsonobj = json.load(file_json)
	rootpath = os.path.dirname(sys.path[0])
	bin = rootpath + '/bin'
	lib = rootpath + '/lib'
	database = rootpath + '/database'
	tools = rootpath + '/tools'

	fqtype_p = jsonobj["FqType"]
	fqtype = fqtype_p[0:2]
 
	reftag = jsonobj["RefTag"]

	# tools
	try:
		SOAPnuke_param = jsonobj["SOAPnuke_param"]
	except:
		if fqtype == 'PE':
			SOAPnuke_param = '-l 10 -q 0.2 -n 0.05 -f AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA  -r AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG'
		elif fqtype == 'SE':
			SOAPnuke_param = '-l 10 -q 0.2 -n 0.05 -f AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA'
		else:
			print('ERROR: Invalid FqType in json file.')
			sys.exit(1)
	try:
		freebayes_param = jsonobj["freebayes_param"]
	except:
		freebayes_param = '-H -p 1 -q 20 -m 60 --min-coverage 20 -F 0.6'
	try:
		consensus_depth = jsonobj["consensus_depth"]
	except:
		consensus_depth = 10
	try:
		qualsys = jsonobj["qualsys"]
	except:
		qualsys = 2

	if '--min-coverage' not in freebayes_param:
		print("ERROR: The <--min-coverage> parameter must be set via <freebayes_param> in the input.json.")
		sys.exit(1)

	min_coverage = freebayes_param.split('--min-coverage')[1].split()[0].strip()
	try:
		float(min_coverage)
	except:
		print('ERROR: Invalid value of <--min-coverage> in <freebayes_param>')
		sys.exit(1)
	if float(min_coverage) < float(consensus_depth):
		print('ERROR: The value of <--min-coverage> in <freebayes_param> must exceed the <consensus_depth>.')
		sys.exit(1)

	flash_param = '-m 7'
	java = jsonobj["java"]
	python3 = jsonobj["python3"]
	python3_lib = jsonobj["python3_lib"]
	Rscript = jsonobj["Rscript"]
	R_lib = jsonobj["R_lib"]
	seqtk = jsonobj["seqtk"]
	bwa = jsonobj["bwa"]
	samtools = jsonobj["samtools"]
	freebayes = jsonobj["freebayes"]
	bcftools = jsonobj["bcftools"]
	bgzip = jsonobj["bgzip"]
	tabix = jsonobj["tabix"]
	bedtools = jsonobj["bedtools"]
	mosdepth = jsonobj["mosdepth"]
	bamdst = jsonobj["bamdst"]
	SOAPnuke = jsonobj["SOAPnuke"]
	flash = jsonobj["flash"]

	#read_len = fqtype_p[2:]
	barcode_file = jsonobj["sample_list"]
	virusbed = database + '/' + reftag + '.virus.bed'
	virusbed_cutprimer = database + '/' + reftag + '.virus.cutprimer.bed'
	lambdabed = database + '/lambda.bed'
	GAPDH_bed = database + '/GAPDH.bed'
	variantbed = database + '/' + reftag + '.variant.bed'
	bed2 = database + '/MARV.bed'
	ref = database + '/MARV.fasta'
	watchdog = bin+'/localsubmit/bin/watchDog_v1.0.pl'
	qsubsge = rootpath+'/bin/qsub-sge.pl'
	try:
		queue = jsonobj["queue"]
		subproject = jsonobj["project"]
	except:
		queue = 'mgi.q'
		subproject = 'P18Z18000N0394'
	work_dir = jsonobj["workdir"]
	try:
		primer_version = jsonobj["primer_version"]
	except:
		primer_version = '2.0'
	primer_list = database + '/' + reftag + '.primer.xls'
	#primer_list = '%s/nCoV.primer.%s.xls'%(database,primer_version)
	try:
		SplitData = jsonobj["SplitData"]
	except:
		SplitData = ''
	result_dir = os.path.abspath(work_dir)+"/result"
	shell_dir = os.path.abspath(work_dir)+"/shell"
	sum_dir = os.path.abspath(work_dir)+"/summary"
	create_dirs(work_dir,result_dir,shell_dir,sum_dir)

	step0shell = open(shell_dir+ '/step0.GenerateData.sh','w')
	step1shell = open(shell_dir+ '/step1.filter.sh','w')
	step2shell = open(shell_dir+ '/step2.bwa.sh','w')
	step3shell = open(shell_dir+ '/step3.bamdst.sh','w')
	step4shell = open(shell_dir+ '/step4.CutPrimer.sh','w')
	step5shell = open(shell_dir+ '/step5.statistic.sh','w')
	step6shell = open(shell_dir+ '/step6.AlignVariant.sh','w')
	step7shell = open(shell_dir+ '/step7.GetReport.sh','w')

	file_cut_primer_list = open('%s/CutPrimer.list'%(work_dir),'w')

	sample_dict = defaultdict(dict)

	with open(barcode_file,'r') as fb:
		for line in fb:
			sample, barcode, raw_data_path = line.split()
			if sample not in sample_dict:
				if fqtype == 'PE':
					file_cut_primer_list.write('%s\t%s/%s/04.CutPrimer/%s_1.cutprimer.fq.gz\t%s/%s/04.CutPrimer/%s_2.cutprimer.fq.gz\n'%(sample,result_dir,sample,sample,result_dir,sample,sample))
				elif fqtype == 'SE':
					file_cut_primer_list.write('%s\t%s/%s/04.CutPrimer/%s.cutprimer.fq.gz\n'%(sample,result_dir,sample,sample))
			sample_dict[sample][barcode] = raw_data_path
	file_cut_primer_list.close()

	for key, value in sample_dict.items():
		sample = key
		CleanData(step1shell,sample,fqtype,SplitData,qualsys)
		#bwaaln(step2shell,sample,fqtype,read_len)
		bwamem(step2shell,sample,fqtype)
		CovDep(step3shell,sample)
		CutPrimer(step4shell,fqtype_p,sample)
		GetReport(step7shell,sample)

	GenerateData(step0shell,sample_dict,fqtype)
	Statistics(step5shell,fqtype)
	AlignVariant(step6shell,fqtype,'%s/CutPrimer.list'%(work_dir),consensus_depth)
	step0shell.close()
	step1shell.close()
	step2shell.close()
	step3shell.close()
	step4shell.close()
	step5shell.close()
	step6shell.close()
	step7shell.close()

	finalshell = work_dir + "/main.sh"
	if subprj == 'local':
		MainShell(finalshell,shell_dir+ '/step0.GenerateData.sh',shell_dir+ '/step1.filter.sh',shell_dir+ '/step2.bwa.sh',shell_dir+ '/step3.bamdst.sh',shell_dir+ '/step4.CutPrimer.sh',shell_dir+ '/step5.statistic.sh',shell_dir+ '/step6.AlignVariant.sh',shell_dir+ '/step7.GetReport.sh')
	elif subprj == 'qsubsge':
		MainShell_qsubsge(finalshell,shell_dir+ '/step0.GenerateData.sh',shell_dir+ '/step1.filter.sh',shell_dir+ '/step2.bwa.sh',shell_dir+ '/step3.bamdst.sh',shell_dir+ '/step4.CutPrimer.sh',shell_dir+ '/step5.statistic.sh',shell_dir+ '/step6.AlignVariant.sh',shell_dir+ '/step7.GetReport.sh')
	else:
		print('ERROR: invalid -s param,use local/qsubsge')
		sys.exit(1)
