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
sys.path.append('../../lib')
sys.path.append('lib')
from ATF import TestResult


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

def kernel_in_grabserial(grabserial_path):
	try:
		with open(grabserial_path) as grab_str:
			grabserial_str = grab_str.read()
			match1 = re.search(r'Starting Kernel' ,grabserial_str)
			match2 = re.search(r'Timekeeping Ready' ,grabserial_str)
	except Exception, e:
		print e

	if match1 and match2:
		return True
	else:
		return False

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

	if kernel_in_grabserial(grabserial_path):
		i = len(lines)
		cused = 0
		for j in range(i):
			if cused > 1:
				break

			if re.match(r'(.*)Starting Kernel(.*)',lines[j]):
				tmplist.append(listtime(lines[j]))
				cused +=1

			if re.match(r'(.*)Timekeeping Ready(.*)',lines[j]):
				tmplist.append(int(listtime(lines[j])) - int(listtime(lines[j-1])))
				cused +=1

		if len(tmplist) < 3:
			print "***************************************"
			print "ERROR: !!!THE grabserial.txt or dmesg.txt is broken\n Cannot output offset.txt \nThanks!!!!"
			print "***************************************"
			time.sleep(1)
			return

		offsetlist.append(tmplist[1])
		offsetlist.append(tmplist[2])
		offsetlist.append(tmplist[0]-jti)
		new_offset(os.path.join(CUR_DIR,out_dir+'/offset.txt'),offsetlist)

	else:
		timeoffset=out_dmesg_timestamp(grabserial_path)
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

def serial_port_check(usb_name='ttyUSB3'):
	id = ''
	find_line = os.popen("ps -aux | grep "+usb_name+" | grep 'sudo minicom'").readline()
	if not "ps -aux" in find_line:
		print find_line
		id = find_line.split()[1]
	if id == '':
		print "not id"
		return True
	else:
		print "id is %s"%id
		if os.system("echo 123456|sudo kill "+ id) == 0:
			print "killing %s ...."%id
			return True
		else:
			print "kill %s is failed!!!"%id
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
		else:
			pass

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
		cmd = "python %s -o %s"%(os.path.join(CUR_DIR,'./src/btm_gather.py'),out_dir)
	print cmd
	os.system(cmd)
	try:
		with open(os.path.join(CUR_DIR,out_dir+'/report.csv')) as freport:
			line = 	freport.readlines()[-1]
			total_time = line.split()[0]
			print "boot_time = %s"%total_time
			tr.result('fullboot', total_time,'sec')		
	except Exception, e:
		print "con't open report.csv"
		print e

	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/boot_progress.csv'), 'fullboot')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/report.csv'), 'stackbar')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/abl_dump.txt'))
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/grabserial.txt'))
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/dmesg.txt'))
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/logcat.log'))
	if os.path.exists(os.path.join(CUR_DIR,out_dir+'/bootgraph.html')):
		tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/bootgraph.html'))
	tr.save()


if __name__ == "__main__":
    tr = TestResult(sys.argv)
    print "======================================================="
    print "Notes:please make sure the DUT USB is connection \nand replug USB of debug board"
    print "======================================================="
    main(sys.argv[1:])





