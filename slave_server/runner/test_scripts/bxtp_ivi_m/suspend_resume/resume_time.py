#!/usr/bin/python
import serial
import time,sys
import traceback
import random, tempfile
import os,re
import commands,threading
import subprocess
sys.path.append('./lib')
sys.path.append('lib')
# from lib.adb_rlbench import rlbench_main
from atf import *

tr = TestResult(__file__)

CUR_DIR = os.path.abspath(__file__).strip(
	os.path.abspath(__file__).split('/')[-1])
lib_dir = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])+"/lib/"
count_time = 0
lines = 0
lists_all = []
result_time = 0
waittime = 0
item_start = 0
item_end = 0
resume_complete = False
class cmd_port_thread (threading.Thread):
	"""
	class control_ignition_thread
	"""

	def __init__(self, cmd, time):
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
		os.system(str(self.cmd))
		print ""
def adb(cmd):

	adb_command = 'adb ' + cmd
	return os.popen(adb_command).read()

def wait_for_complete(timeout=70):
	global waittime
	# print 'waiting for boot complete'
	for i in range(timeout):
		#		print i
		time.sleep(1)
		if adb('shell getprop dev.bootcomplete').lstrip().strip() == '1':
			waittime = i
			return True
	
	return False


def kill_fork_server():
	fgrep = os.popen('ps -aux | grep adb').readlines()
	for lines in fgrep:
		if lines.count('fork-server') == 1:
			# print lines
			item = lines.split()
			# print item[1]
			os.system('kill ' + item[1])


def wait_for_dev():
	if os.popen('adb devices').readlines()[1] == '\n':
		return False
	else:
		return True

def serial_port_check(usb_name='ttyUSB2'):
    id = ''
    find_line = os.popen("ps -aux | grep " + usb_name +
                         " | grep 'sudo minicom'").readline()
    if not "ps -aux" in find_line:
        # print find_line.strip()
        id = find_line.split()[1]
    if id == '':
        # print "not id"
        return True
    else:
        # print "id is %s"%id
        if os.system("echo 123456|sudo kill " + id) == 0:
            # print "killing %s ...."%id
            return True
        else:
            # print "kill %s is failed!!!"%id
            return False

def parse_dmesg_resume_time(out_dir):
	try:
		with open(os.path.join(CUR_DIR,out_dir,'dmesg.txt'),"r") as fread:
			line = fread.readlines()
			if line:

				llist = open(os.path.join(CUR_DIR,out_dir,'dmesg.txt')).readlines()
				llist.reverse()
				line = ''
				for index in llist:
					if index.count('PM: resume of devices complete after') == 1:
						line = index
						break	
			#print 'line =',line
			result_time = re.search(r'.(?P<time>\d+\.\d+).msec',line,re.M|re.I).group('time')
			dmesg_time = float(result_time)
			return dmesg_time
	except Exception, e:
		print e
		return 0
def get_suspend_resume_time_stamp(out_dir):
	global count_time
	global waittime
	count_time +=1
	if wait_for_complete():
		os.system('adb root')
		time.sleep(2)
		os.system('adb push '+os.path.join(CUR_DIR,'lib','abl_dumper_app') +' /data')
		time.sleep(10)
		os.system('adb push '+os.path.join(CUR_DIR,'lib','android.sh') +' /sdcard/')
		time.sleep(5)
		os.system('adb shell <'+ os.path.join(CUR_DIR,'capture-start.txt'))
		time.sleep(2)
		cmd_thread = cmd_port_thread(
			"echo 123456|sudo -S python " + CUR_DIR + "/lib/relay08_ctrl_button.py -p 1", 1)
		cmd_thread.start()
		for i in range(500):
			time.sleep(1)
			if wait_for_dev():
				continue
			else:
				print 'into suspend'
				break
		else:	
			print 'TIME OUT'
		time.sleep(10)
	os.system("echo 123456|sudo -S python " + CUR_DIR +
			  "/lib/relay08_ctrl_button.py -p 1")
	#time.sleep(2)
	
	if wait_for_complete():
		time.sleep(1)
		os.system('adb root')
		time.sleep(5)
		os.system('adb shell cat /d/suspend_stats >'+os.path.join(CUR_DIR, './' + out_dir) +'/suspend_stats.txt')
		time.sleep(5)
		f = open(os.path.join(CUR_DIR, out_dir, 'suspend_stats.txt'))
		line = f.readlines()
		print line
		if len(line) ==0:
			os.system('adb root')
			time.sleep(5)
			os.system('adb shell cat /d/suspend_stats >'+os.path.join(CUR_DIR, './' + out_dir) +'/suspend_stats.txt')
			time.sleep(5)
			f = open(os.path.join(CUR_DIR, out_dir, 'suspend_stats.txt'))
			line = f.readlines()
			print line
		else:
			pass
		for i in line:
			if i.count('success:') ==1:
				try:
					item = re.search(r"\d+",i).group(0)
					#print item
					os.system('adb root')
					time.sleep(1)
					os.system('adb shell <'+ os.path.join(CUR_DIR,'abl_dump.txt'))
					time.sleep(2)
					os.system('adb shell <'+ os.path.join(CUR_DIR,'capture-end.txt'))
					time.sleep(2)
					os.system('adb pull /data/abl_dump.txt ' +os.path.join(CUR_DIR,out_dir,'abl_dump.txt'))
					time.sleep(2)
					os.system('adb pull /sdcard/ftrace.txt ' +os.path.join(CUR_DIR,out_dir,'ftrace.txt'))
					time.sleep(1)
					os.system('adb pull /sdcard/dmesg.txt ' +os.path.join(CUR_DIR,out_dir,'dmesg.txt'))
					time.sleep(1)
					os.system('adb pull /sdcard/log.txt ' +os.path.join(CUR_DIR,out_dir,'log.txt'))
					time.sleep(1)
					p=subprocess.Popen('python '+os.path.join(CUR_DIR+'/lib/analyze_suspend.py')+' -ftrace '+os.path.join(CUR_DIR,out_dir,'ftrace.txt'),shell=True, cwd=os.path.join(CUR_DIR,out_dir))
					time.sleep(1)
					os.rename(os.path.join(CUR_DIR,out_dir,'output.html'),os.path.join(CUR_DIR,out_dir,'output.h5'))
					time.sleep(2)
					get_abl_data(out_dir)
					return True
					if item == 0:
						os.system("echo 123456|sudo -S python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
						return 0
			
				except Exception, e:
					print e
			

	else:
		os.system("echo 123456|sudo -S python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
		time.sleep(1)

		return 0
	
def get_kernel_resume_time(out_dir):
	try:
		with open(os.path.join(CUR_DIR,out_dir,'output.h5'),"r") as fread:
			line = fread.readlines()
			if line:
				llist = open(os.path.join(CUR_DIR,out_dir,'output.h5')).readlines()	
				line = ''
				for index in llist:
					if index.count('Kernel Resume Time') == 1:
						line = index
						try:
							t = re.search(r'Kernel Resume Time: <b>(.+) ms<', line).group(1)
						except Exception,e:
							return 0
			kernel_resume_time =float(t)
			print kernel_resume_time
			if kernel_resume_time == "":
				return 0
			else:
				return kernel_resume_time

	except Exception, e:
		return 0

	
def get_abl_data(out_dir):
	
	try:
		with open(os.path.join(CUR_DIR, out_dir, 'abl_dump.txt'),"r") as fread:
			lines = fread.readlines() 
			flag = False
			llines = []
			for i in lines:
				if i.count("Index") == 1:
					flag = True
				if flag:
					llines.append(i)
					i=i.split('\n')
					for item in i:
						item =item.split('\t')
						if item[0] =='55':
							item[1] = float(item[1])
							jti= round(float(item[1]),3)
							return jti
		return 0				
	except Exception, e:
		print e
		return 0
def get_ioc_data(out_dir):
	global item_start
	global item_end
	try:
		with open(os.path.join(CUR_DIR,out_dir,'outttylog.txt'),"r") as fread:
			line = fread.readlines()
			if line:

				llist = open(os.path.join(CUR_DIR,out_dir,'outttylog.txt')).readlines()
				llist.reverse()
				line = ''
				line_end =''
				for index in llist:
					if index.count('Wakeup button state (Normal Boot) = 1') == 1:
						line = index
						#print 'line =',line
						r =re.compile(r'^(\d+):(\d+)\s(\d+)s(\d+)')
						item = r.findall(line)[0]
						item_start = float(item[0])*3600+float(item[1])*60+float(item[2])+float(item[3])/1000
						#print item_start
				for index in llist:	
					if index.count('SoC startup started!') == 1:
						line_end = index
						#print 'line_end =',line_end
						t = re.compile(r'^(\d+):(\d+)\s(\d+)s(\d+)')
						item = t.findall(line_end)[0]
						item_end = float(item[0])*3600+float(item[1])*60+float(item[2])+float(item[3])/1000
						#print item_end
			delta = round(float((item_end - item_start)*1000),3)
			return delta
		return 0						
	except Exception, e:
		print e	
		return 0
def renew_ttylog(out_dir):
	os.system('python '+CUR_DIR+'/lib/rwfile.py ' + "../"+out_dir)
	time.sleep(1)
	get_ioc_data(out_dir)

def run_case():
	lists=[]
	os.system('python '+CUR_DIR+'/lib/adb_rlbench.py')
	os.system('adb shell input keyevent 4')
	lists.append(rlbench_main())
	print lists	
		
def main():
	result={}
	out_dir = time.strftime('%Y%m%d_%H%M%S')
	if not os.path.exists(os.path.join(CUR_DIR, './' + out_dir + '/')):
		os.mkdir(os.path.join(CUR_DIR, './' + out_dir + '/'))
	serial_thread_state = os.path.join(CUR_DIR,'./'+out_dir+'/serial_sate')
	with open(serial_thread_state,'w+') as fp:
		fp.write("0\n")
	cmd_thread = cmd_port_thread("echo 123456|sudo -S python " +CUR_DIR+"/lib/serial_log.py -p /dev/ttyUSB2 -o "+CUR_DIR+'./'+out_dir, 1)
	cmd_thread.start()
	
	while (not get_suspend_resume_time_stamp(out_dir)):
		os.system("echo 123456|sudo -S python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
		time.sleep(20)
		if get_suspend_resume_time_stamp(out_dir):
			break
	serial_port_check(usb_name='ttyUSB2')
	renew_ttylog(out_dir)
	result['abl_time'] = get_abl_data(out_dir)
	print result['abl_time']
	ioc = get_ioc_data(out_dir)
	result['ioc_time'] = round(float(ioc),3)
	print result['ioc_time']
	result['kernel_time'] = get_kernel_resume_time(out_dir)
	print result['kernel_time']
	try:
		with open(os.path.join(CUR_DIR,out_dir,'raw_data.txt'),"w") as fread:
			fread.write(str(result))
			fread.close()
	except Exception, e:
		print e
	resume_time =result['abl_time']+result['ioc_time']+result['kernel_time']
	# kernel_time =kernel
	print round(float(resume_time),3)
		# print round(float(kernel_time),3)
	# run_case()
	os.system('adb shell input keyevent 4')
	serial_thread_state = os.path.join(CUR_DIR,'./'+out_dir+'/serial_sate')
	with open(serial_thread_state,'w+') as fp:
		fp.write("1\n")	
	print ""	
	tr.result(resume_time)
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'raw_data.txt'),'raw_data.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'dmesg.txt'),'dmesg.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'ftrace.txt'),'ftrace.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'log.txt'),'log.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'output.h5'),'output.h5')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'outttylog.txt'),'outttylog.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'abl_dump.txt'),'abl_dump.txt')
	for key,val in result.items():
		tr.sub_score(key,str(val))
	tr.save()
	

if __name__ == "__main__":
	main()


	

