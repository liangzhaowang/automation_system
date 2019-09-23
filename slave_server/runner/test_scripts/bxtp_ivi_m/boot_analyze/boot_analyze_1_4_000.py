#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os, sys
import re,threading
import time, getopt
import subprocess
from src.ctrl_relay08_threading import control_relay08_port_thread as control_relay08_port_thread
from src.ctrl_relay08_threading import create_relay08_cmd
#CUR_DIR = os.path.dirname(__file__)
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
boot_is_complete = False
host_passwd = '123456'
sys.path.append('./lib')
sys.path.append('lib')
from atf import *
import matplotlib.pyplot as plt

class cmd_port_thread (threading.Thread):
	"""
	class control_ignition_thread
	"""
	def __init__(self,cmd,time):
		"""
		control_ignition_thread __init__
		"""
		threading.Thread.__init__(self)
		self.cmd = cmd
		self.time = time

	def run(self):
		"""
		threading run
		"""
		print self.cmd
		time.sleep(self.time)
		os.system(self.cmd)

def read_number(item):
    """
    read_number to remove point
    """
    jti =item.split('.')[0]+item.split('.')[1]
    return int(jti)

def new_offset(offset_path,offsetlist):
    """
    to create offset.txt
    """
    for i in range(0,len(offsetlist)):
        offsetlist[i] = str(offsetlist[i])
    
    try:
        with open(offset_path,"w+") as foffset:
            foffset.write(" ".join(offsetlist))
    except Exception,e:
        print e

def rewrite_abl_dump(dump_path):
    """
    rewrite abl_dump.txt 
    """
    try:
        with open(dump_path,"r") as fread:
            lines = fread.readlines() 
            flag = False
            llines = []
            jti = 0
            for i in lines:
                if i.count("Index") == 1:
                    flag = True

                if flag:
                    llines.append(i)
                    i=i.split('\n')
                    for item in i:
                        item =item.split('\t')
                        if item[0] =='55':
                            jti =read_number(item[1])
    except Exception, e:
        print e

    try:
        with open(dump_path,"w+") as fwrite:
            fwrite.writelines(llines)
        return jti
    except Exception, e:
        print e


def listtime(line):
    """
    get time from line in the list
    """
    nanoseconds = 0
    regex = re.compile("^\[(?P<time1>\d+\.\d+).(?P<time2>\d+\.\d+)\](?P<line>.*)$")
    match = regex.match(line)
    if match:
        try:
            nanoseconds = int(match.groupdict().get('time1', '').split('.')[0]) * 1000000 + int(match.groupdict().get('time1', '').split(' ')[0].split('.')[1])
        except Exception,e:
            print e
    return nanoseconds
def parser_dmesg_timestamp(line):
    """
    parser_dmesg_timestamp
    """
    argument1 = 0
    argument2 = 0
    regex = re.compile("^\[(?P<time1>\d+\.\d+) (?P<time2>\d+\.\d+)\].\[ *(?P<time3>\d+\.\d+)\](?P<line>.*)$")
    match = regex.match(line)
    if match:
        try:
            argument1 = int(match.groupdict().get('time1', '').split('.')[0]) * 1000000 + int(match.groupdict().get('time1', '').split(' ')[0].split('.')[1])
            argument2 = int(match.groupdict().get('time3', '').split('.')[0]) * 1000000 + int(match.groupdict().get('time3', '').split(' ')[0].split('.')[1])
        except IndexError:
            pass
    #print "argument1 %s"%argument1
    #print "argument2 %s"%argument2
    return (argument1-argument2)
	
def out_dmesg_timestamp(grabserial_path):
    """
    out_dmesg_timestamp
    """
    dmesg_first_timestamp = 0
    try:
        with open(grabserial_path) as fp:
            lines = fp.readlines()
            i = len(lines)-1
            if "shell@bxtp_abl" in lines[i]:
                dmesg_first_timestamp = parser_dmesg_timestamp(lines[i-1])
            else:
                dmesg_first_timestamp = parser_dmesg_timestamp(lines[i])
    except Exception, e:
        print e

    return dmesg_first_timestamp

def rewrite_dmwseg(dmesg_path):
	try:
		with open(dmesg_path,'r') as fmesg:
			lines = fmesg.readlines()
			lines.insert(0,"[    0.000000] Calibrating delay loop (skipped), value calculated using timer frequency..\n")
			lines.insert(0,"[    0.000000] Initializing cgroup subsys cpuset\n")   
	except Exception, e:
		print e
	try:
		with open(dmesg_path,'w+') as fmesg:
			fmesg.writelines(lines)
	except Exception, e:
		print e

def new_grabserial(grabserial_path,dmesg_path,jti,out_dir):
	"""
	new_grabserial
	"""

	lines = []
	try:
		with open(grabserial_path) as fp:
			lines = fp.readlines()
	except Exception, e:
		print e


	cused = 0
	tmplist = []
	timeoffset=out_dmesg_timestamp(grabserial_path)
	print "timeoffset %s"%timeoffset
	offsetlist = []
	for i in lines:
		if cused > 0:
			break

		if i.count('==> jump to image') == 1:
			tmplist.append(listtime(i))
			cused += 1
    
	tmplist.append(timeoffset)
	try:
		with open(dmesg_path) as fpd:
			lines = fpd.readlines()
			fpd.close()
	except Exception, e:
		print e

	cused = 0
    
	for i in lines:
		if cused > 0:
			break

		if i.count("Calibrating delay loop (skipped), value calculated using timer frequency.."):
			tmplist.append(listtime(i)+timeoffset)
			cused +=1
	if cused == 0:
		rewrite_dmwseg(dmesg_path)
		try:
			with open(dmesg_path) as fpd:
				lines = open(dmesg_path).readlines()
		except Exception, e:
			print e
		for i in lines:
			if cused > 0:
				break

			if i.count("Calibrating delay loop (skipped), value calculated using timer frequency.."):
				tmplist.append(listtime(i)+timeoffset)
				cused +=1
	if len(tmplist) < 3:
		print "***************************************"
		print "ERROR: !!!THE grabserial.txt or dmesg.txt is broken\n Cannot output offset.txt \nThanks!!!!"
		print "***************************************"
		time.sleep(1)
		return	
	offsetlist.append(tmplist[1])
	offsetlist.append(tmplist[2]-tmplist[1])
	offsetlist.append(tmplist[0]-jti)
	new_offset(os.path.join(CUR_DIR,out_dir+'/offset.txt'),offsetlist)

def print_process(times=31):
    """
    print_process
    """
    for i in range(1,times):
        sys.stdout.write('>>'+"\b")
        sys.stdout.flush()
        time.sleep(0.03)
    print ""

def calc_wait_processtime(i):
    if i % 10 == 0:
        sys.stdout.writelines(str(i)+"%.."+"\b")
        return True
    else:                                                                                                          
        return False

def print_wait_process(times=1.0):
    """
    print_wait_process
    """
    sys.stdout.write('waiting...')
    sys.stdout.flush()
    for i in range(1,100):
        if not calc_wait_processtime(i):
            sys.stdout.write('....'+"\b")
        sys.stdout.flush()
        time.sleep(times/100)
    print "100%"

def adb(cmd):

    adb_command = 'adb ' + cmd
    return os.popen(adb_command).read()

def wait_for_boot(timeout=70):
	global boot_is_complete
	print 'waiting for boot complete'
	for i in range(timeout):
	#	print i
		time.sleep(1)
		if adb('shell getprop dev.bootcomplete').lstrip().strip() == '1':
			boot_is_complete = True
			return True
	return False	

def reset_list(ids):
	idlist = []
	for line in ids:
		if not line in idlist:
			idlist.append(line)
	return idlist

def serial_port_check(usb_name='usb3'):
	#print "====="
	ids = []
	exclude_lines = ["ps -aux","grep","--color=auto"]
	count = 0
	flag = True
	usb_name1="tty"+usb_name.upper()
	#print "usb_name1="+usb_name1
	find_lines = os.popen("ps -aux | grep "+usb_name+" | grep minicom").readlines()
	find_lines += os.popen("ps -aux | grep "+usb_name1+" | grep minicom").readlines()
	find_lines += os.popen("ps -aux | grep minicom -s").readlines()
	#print find_lines
	for find_line in find_lines:
		#print find_line
		for line in exclude_lines:
			if line in find_line:
				flag = False
				break
			else:
				flag = True
		if flag:
			#print find_line
			ids.append(find_line.split()[1])
	ids = reset_list(ids)
	#print "ids are:"
	#print ids
	for item in ids:
		if os.system("echo chenxi|sudo -S kill "+ item) == 0:
			print "killing %s ...."%item
			count += 1
		else:
			print "kill %s is failed!!!"%item
		#print count,".....",len(ids)
	if count == len(ids):
		return True
	else:
		return False


def auto_run(out_dir):
	"""
	auto_run to run the commands from './src/prerun_commands'
	"""

	lines = []
	try:
		with open(os.path.join(CUR_DIR,'./src/prerun_commands'),'r') as fprerun:
			lines = fprerun.readlines()
	except Exception,e:
		print e
	runsecuss = 0
	create_relay08_cmd(3)
	create_relay08_cmd(2)
#	time.sleep(1)
#	os.system('sudo python ./src/serial_com.py -p /dev/ttyUSB2 -c n1#')
	while True:
		if serial_port_check():
			break
		if serial_port_check("usb3"):
			break

	time.sleep(20)
#	os.system('sudo python ./src/serial_com.py -p /dev/ttyUSB2')

	cmd_thread = cmd_port_thread("sudo python "+CUR_DIR+"/./src/grabserial -v -d '/dev/ttyUSB3' -b 115200 -w 8 -p N -s 1 -e 130 -t -m 'Initializing cgroup subsys cpu*' > "+CUR_DIR+"/./"+out_dir+"/grabserial.txt",1)
	cmd_thread.start()
	time.sleep(2)
	create_relay08_cmd(1)
#	powerthread = control_relay08_port_thread(1,"replug_ttyUBS3",1,2)#control_ignition_thread(1,"replug_ttyUBS3",1,2)
#	powerthread.start()
	if len(lines) > 0:
		if wait_for_boot():
			for line in lines:
				if runsecuss != 0:
					print "fail:%s"%line
				if line.startswith('sleep'):
					print_wait_process(int(line.lstrip("sleep "))+0.0)
				else: 
					line = line.replace('out',out_dir)
					line = line.replace(r'$(pwd)',CUR_DIR)
					print line
				runsecuss = os.system(line)
				print_process()
	else:
		print "read prerun_commands fails"

def usbisok():
    """
    usbisok to scan /dev/ttyUSB3 is ok
    """
    flag = False
    cmd = 'ls /dev/ttyUSB3'
    create_relay08_cmd(3)
    USBthread = control_relay08_port_thread(0,"replug_ttyUBS3",2,3)#control_ignition_thread(0,"replug_ttyUBS3",2,3)
    USBthread.start()
    while True:
        time.sleep(0.5)
        if os.system(cmd) != 0:
            print 'please plug in debug board USB'
            flag = True
        elif flag and  os.popen(cmd).readlines()[0].split('\n')[-2] == '/dev/ttyUSB3':
            #print 'The debug board usb plugin'
            print "======================================================================="
            print "after the next command is typed, and input password for 'sudo' command,"
            print "you can press ignition, After a moment, you may see amazing result....."
            print "======================================================================="
            time.sleep(1)
            break
        else:
            print "please replug debug board's USB!"
            continue
def genline(start, end):
	delta = (end - start)/1000.0
	r = range(1000)
	l = [start + i * delta for i in r]
	return l

def get_profile(csvfile,dir):
	try:
		with open(csvfile,"r") as files:
			csv_res = files.readlines()
			files.close()
	except Exception,e:
		print e



	lables = ["timeline", "pre-CSE", "CSE", "ABL", "Stage0", "Stage1", "Stage2", "pre kernel", "VMM", "Trusty/lk", "Decomp", "kernel", "RVC"]

	timeline = { "pre-CSE": [0, 0],
				"CSE": [0, 0],
				"ABL": [0, 0],
				"Stage0": [0, 0],
				"Stage1": [0, 0],
				"Stage2": [0, 0],
				"pre kernel": [0, 0],
				"VMM": [0, 0],
				"Trusty/lk": [0, 0],
				"Decomp": [0, 0],
				"kernel": [0, 0],
				"RVC": [0, 0]}

	timeline_color = { "pre-CSE": 'm',
				"CSE": 'c',
				"ABL": 'y',
				"Stage0": 'y',
				"Stage1": 'y',
				"Stage2": 'y',
				"pre kernel": 'g',
				"VMM": 'g',
				"Trusty/lk": 'g',
				"Decomp": 'g',
				"kernel": 'k',
				"RVC": 'b'}

	ylables = list(range(len(lables) + 1))
	ylables.reverse()

	"""
	get data
	"""


	for line in csv_res:
		l = line.decode("utf-8").strip().split()
		if "CSE" in line:
			if " start " in line:
				timeline["pre-CSE"][1] = int(float(l[0]) * 1000)
				timeline["CSE"][0] = int(float(l[0]) * 1000)
			elif " ready " in line:
				timeline["ABL"][0] = int(float(l[0]) * 1000)
				timeline["Stage0"][0] = int(float(l[0]) * 1000)
				timeline["CSE"][1] = int(float(l[0]) * 1000)
		elif "ABL" in line:
			if " mark " in line:
				if "stage-0 done" in line:
					timeline["Stage0"][1] = int(float(l[0]) * 1000)
				elif "stage-1 loaded" in line:
					timeline["Stage1"][0] = int(float(l[0]) * 1000)
				elif "stage-1 done" in line:
					timeline["Stage1"][1] = int(float(l[0]) * 1000)
				elif "stage-2 start" in line:
					timeline["Stage2"][0] = int(float(l[0]) * 1000)
			if " ready " in line:
				timeline["Stage2"][1] = int(float(l[0]) * 1000)
				timeline["ABL"][1] = int(float(l[0]) * 1000)
				timeline["pre kernel"][0] = int(float(l[0]) * 1000)
				timeline["VMM"][0] = int(float(l[0]) * 1000)
		elif "pre_kernel" in line:
			if " start " in line:
				timeline["Trusty/lk"][0] = int(float(l[0]) * 1000)
				timeline["VMM"][1] = int(float(l[0]) * 1000)
			elif " ready " in line:
				timeline["Trusty/lk"][1] = int(float(l[0]) * 1000)
				timeline["Decomp"][0] = int(float(l[0]) * 1000)
		elif "kernel" in line:
			if " start " in line:
				timeline["pre kernel"][1] = int(float(l[0]) * 1000)
				timeline["Decomp"][1] = int(float(l[0]) * 1000)
				timeline["kernel"][0] = int(float(l[0]) * 1000)
			elif " ready" in line:
				timeline["kernel"][1] = int(float(l[0]) * 1000)
		if "RVC" in line:
			if " start " in line:
				timeline["RVC"][0] = int(float(l[0]) * 1000)
			elif "ready" in line:
				timeline["RVC"][1] = int(float(l[0]) * 1000)




	"""
	now build plot
	"""

	for x in lables[1:]:
		xpoints = genline(timeline[x][0], timeline[x][1])
		ypoints = [ylables[0]] * len(xpoints)
		plt.plot(xpoints, ypoints, timeline_color[x], linewidth=7.0)

	for x, y, in zip(lables[1:], ylables[1:]):
		xpoints = genline(timeline[x][0], timeline[x][1])
		ypoints = [y] * len(xpoints)
		plt.plot(xpoints, ypoints,  timeline_color[x], linewidth=7.0)
		plt.text((timeline[x][0] + timeline[x][1])/2, y + 0.2, "{}".format(timeline[x][1] - timeline[x][0]))

	plt.yticks(ylables, lables)
	plt.grid(True)
	plt.savefig(dir+"/profile.png")

def main(argv):
	"""
	main
	"""
	inputfile = ''
	global boot_is_complete
	out_dir=time.strftime('%Y%m%d_%H%M%S')
#	if not os.path.exists(os.path.join(CUR_DIR,out_dir)):
#		os.mkdir(os.path.join(CUR_DIR,out_dir))

	try:
		opts, args = getopt.getopt(argv,"hi:o:e",["iconfig=",'outdir=',"exec"])
	except getopt.GetoptError:
		print 'get_report_csv.py [-e] [-i <configfile>][-o <out_dir>]'
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print 'get_report_csv.py [-e] [-o outdir][-i <configfile>]'
			sys.exit()
		elif opt in ("-i", "--iconfig"):
			if(arg.count('/')==0):
				inputfile = './config/'+arg
			else:
				inputfile = arg
			inputfile = os.path.join(CUR_DIR,inputfile)
#		elif opt in ("-o","--out_dir"):
#			out_dir = arg
		elif opt in ("-e", "--exec"):
			if not os.path.exists(os.path.join(CUR_DIR,out_dir)):
				os.mkdir(os.path.join(CUR_DIR,out_dir))
			while not boot_is_complete:
				usbisok()
				auto_run(out_dir)

	if not os.path.exists(os.path.join(CUR_DIR,out_dir)):
		os.mkdir(os.path.join(CUR_DIR,out_dir))

	if os.path.exists(os.path.join(CUR_DIR,out_dir+'/abl_dump.txt')):
		jti = rewrite_abl_dump(os.path.join(CUR_DIR,out_dir+'/abl_dump.txt'))
	else:
		print '======================<<<<<ERROR>>>>>====================='
		print CUR_DIR+'./'+out_dir+'/abl_dump.txt is not exist,\nplease run ./boot_analyz.py -e to create it \n Thanks'
		print '=========================================================='
		sys.exit()
	if os.path.exists(os.path.join(CUR_DIR,out_dir+'/grabserial.txt')) and os.path.exists(os.path.join(CUR_DIR,out_dir+'/dmesg.txt')):
		new_grabserial(os.path.join(CUR_DIR,out_dir+'/grabserial.txt'),os.path.join(CUR_DIR,out_dir+'/dmesg.txt'),jti,out_dir)
	else:
		print '========================<<<<<ERROR>>>>>===================='
		print CUR_DIR+'./'+out_dir+'/grabserial.txt or ./'+out_dir+'/dmesg.txt is not exist,\nplease run ./boot_analyz_1_1.py -e to create it \n Thanks'
		print '==========================================================='
		sys.exit()

	print "===================================================="

	if inputfile != '':
		cmd = "python %s -i %s -o %s"%(os.path.join(CUR_DIR,'./src/btm_gather.py'),inputfile,out_dir)
	else:
		cmd = "python %s -o %s"%(os.path.join(CUR_DIR,'./src/btm_gather.py',out_dir))
	print cmd
	os.system(cmd)
	try:
		with open(os.path.join(CUR_DIR,out_dir+'/report.csv')) as freport:
			line = 	freport.readlines()[-1]
			total_time = line.split()[0]
			print "boot_time = %s"%total_time
			tr.result(total_time)		
	except Exception, e:
		print "can't open report.csv"
		print e
		tr.result('can\'t open report.csv')	

	csvfile = os.path.join(CUR_DIR,out_dir+'/report.csv')
	dir = os.path.join(CUR_DIR,out_dir)
	get_profile(csvfile,dir)

	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/boot_progress.csv'), 'fullboot')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/report.csv'), 'stackbar')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'grabserial.txt'),'grabserial.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'dmesg.txt'),'dmesg.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'logcat.log'),'logcat.log')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'proc_cmdline.log'),'proc_cmdline.log')
	if os.path.exists(os.path.join(CUR_DIR,out_dir,'bootgraph.html')):
		tr.add_attachment(os.path.join(CUR_DIR,out_dir,'bootgraph.html'),'bootgraph.html')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'profile.png'),'profile.png')
	tr.save()


if __name__ == "__main__":
    tr = TestResult(__file__)
    print "======================================================="
    print "Notes:please make sure the DUT USB is connection \nand replug USB of debug board"
    print "======================================================="
    main(sys.argv[1:])





