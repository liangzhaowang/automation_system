#!/usr/bin/python
import argparse
import serial
import time,sys
import traceback
import random, tempfile
import os,re
import commands,threading
sys.path.append('../../lib')
sys.path.append('lib')
from lib.adb_rlbench import rlbench_main
from ATF import TestResult

tr = TestResult(sys.argv)
result_time = 0
waittime = 0
resume_complete = False
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])

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

def adb(cmd):
	adb_command = 'adb ' + cmd
	return os.popen(adb_command).read()

def wait_for_complete(timeout=70):
	global waittime
	print 'waiting for boot complete'
	for i in range(timeout):
	#	print i
		time.sleep(1)
		if adb('shell getprop dev.bootcomplete').lstrip().strip() == '1':
			waittime = i
			return True
	return False	


def kill_fork_server():
	fgrep = os.popen('ps -aux | grep adb').readlines()
	for lines in fgrep:
		if lines.count('fork-server') == 1:
			#print lines
			item = lines.split()
			#print item[1]
			os.system('kill '+item[1])

def wait_for_dev():
	if os.popen('adb devices').readlines()[1] == '\n':
		return False
	else:
		return True


def parse_dmesg_resume_time(dmesg_path):
	if os.path.exists(dmesg_path):
		message = 'the "%s" file exists.'
	else:
		message = 'Sorry, I cannot find the "%s" file.'
	print message % dmesg_path
	filedmesg = open(dmesg_path,'r')
	line = filedmesg.readlines()
	if line:

		llist = open(dmesg_path).readlines()
		llist.reverse()
		line = ''
		for index in llist:
			if index.count('PM: resume of devices complete after') == 1:
				line = index;
				break	
		print 'line =',line
		result_time = re.search(r'.(?P<time>\d+\.\d+).msec',line,re.M|re.I).group('time')
		print 'The result_time is',result_time,'msecs'
	else:
		print 'The file is empty!'
	
	tr.result('kernel_resume_time', str(result_time), 'msec')
	
	

def get_suspend_resume_time_stamp(out_dir):
	global waittime
	if wait_for_dev():
		cmd_thread = cmd_port_thread("echo 123456|sudo -s python "+CUR_DIR+"/lib/relay08_ctrl_button.py -p 1",2)
		cmd_thread.start()
		while wait_for_dev():
			if not wait_for_dev():
				print "into suspend"
				break
			time.sleep(1)
		time.sleep(20)
	os.system("echo 123456|sudo -s python "+CUR_DIR+"/lib/relay08_ctrl_button.py -p 1")
	if(wait_for_complete()):
		if waittime < 10:
			cmd = 'adb shell dmesg >'+os.path.join(CUR_DIR,'./'+out_dir)+'/dmesg.txt'
			print cmd
			os.popen(cmd)
			return True
		else:
			print "resume time is so long, more than %s secs."%waittime
			return False
	else:
		print "Device is shutdown,please check it,thanks!"
		return False
	

def print_wait_process_ex(times=1.0):
	sys.stdout.write('parsing')
	sys.stdout.flush()
	for i in range(1,50):
		if i%10 == 0:
			sys.stdout.write('\b'*9+' '*9+'\b'*9)
		else:
			sys.stdout.write('.')
		sys.stdout.flush()																						 
		time.sleep(times/100)
	print ""
def run_case():
	lists=[]
	os.system('python '+CUR_DIR+'/lib/adb_rlbench.py')
	os.system('adb shell input keyevent 4')
	for i in range(0,1):
		lists.append(rlbench_main())
	print lists

def main():
	
	out_dir=time.strftime('%Y%m%d_%H%M%S')
	
	print CUR_DIR
	if not os.path.exists(os.path.join(CUR_DIR,'./'+out_dir+'/')):
		os.mkdir(os.path.join(CUR_DIR,'./'+out_dir+'/'))
	
	

	while (not get_suspend_resume_time_stamp(out_dir)):
		os.system("echo 123456|sudo -s python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
		time.sleep(30)
		if get_suspend_resume_time_stamp(out_dir):
			break
		#pass
	print_wait_process_ex(3.0)
	parse_dmesg_resume_time(os.path.join(CUR_DIR,'./'+out_dir+'/dmesg.txt'))
	run_case()
	os.system('adb shell input keyevent 4')	
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/dmesg.txt'))
	tr.save()

if __name__ == "__main__":
	main()
