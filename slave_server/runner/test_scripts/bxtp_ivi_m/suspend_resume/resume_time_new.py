#!/usr/bin/python
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
CUR_DIR = os.path.abspath(__file__).strip(
	os.path.abspath(__file__).split('/')[-1])
lib_dir = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])+"/lib/"
result_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),"result")
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
		with open(os.path.join(result_dir,out_dir,'dmesg.txt'),"r") as fread:
			line = fread.readlines()
			if line:

				llist = open(os.path.join(result_dir,out_dir,'dmesg.txt')).readlines()
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

def get_suspend_resume_time_stamp(out_dir):
	global count_time
	global waittime
	count_time +=1
	if wait_for_dev():
		os.system('adb root')
		time.sleep(2)
		os.system('adb push '+os.path.join(CUR_DIR,'lib','abl_dumper_app') +' /data')
		time.sleep(10)
		cmd_thread = cmd_port_thread(
			"echo 123456|sudo -s python " + CUR_DIR + "/lib/relay08_ctrl_button.py -p 1", 1)
		cmd_thread.start()
		while wait_for_dev():
			if not wait_for_dev():
				print "into suspend"
				break
			time.sleep(1)
		time.sleep(10)
	os.system("echo 123456|sudo -s python " + CUR_DIR +
			  "/lib/relay08_ctrl_button.py -p 1")
	#time.sleep(2)
	
	if(wait_for_complete()):

		os.system('adb shell cat /d/suspend_stats >'+os.path.join(result_dir, out_dir) +'/suspend_stats.txt')
		f = open(os.path.join(result_dir, out_dir, 'suspend_stats.txt'))
		line = f.readlines()
		print line
		for i in line:
			if i.count('success:') ==1:
				try:
					item = re.search(r"\d+",i).group(0)
					#print item
					os.system('adb root')
					time.sleep(1)
					os.system('adb shell <'+ os.path.join(CUR_DIR,'abl_dump.txt'))
					time.sleep(2)
					os.system('adb pull /data/abl_dump.txt ' +os.path.join(result_dir,out_dir,'abl_dump.txt'))
					time.sleep(2)

					cmd = 'adb shell dmesg >' + os.path.join(result_dir,out_dir,'dmesg.txt')
					os.popen(cmd)
					get_abl_data(out_dir)
					return True
					if item == 0:
						os.system("echo 123456|sudo -s python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
						return False
			
				except Exception, e:
					print e
			

	else:
		os.system("echo 123456|sudo -s python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
		time.sleep(1)

		return False
	


	
def get_abl_data(out_dir):
	
	try:
		with open(os.path.join(result_dir, out_dir, 'abl_dump.txt'),"r") as fread:
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
						
	except Exception, e:
		print e

def get_ioc_data(out_dir):
	global item_start
	global item_end
	try:
		with open(os.path.join(result_dir,out_dir,'outttylog.txt'),"r") as fread:
			line = fread.readlines()
			if line:

				llist = open(os.path.join(result_dir,out_dir,'outttylog.txt')).readlines()
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
								
	except Exception, e:
		print e	

def renew_ttylog(out_dir):
	os.system('python '+CUR_DIR+'/lib/rwfile.py ' + "../"+'./result/out_dir')
	time.sleep(1)
	get_ioc_data(out_dir)

def run_case():
	lists=[]
	os.system('python '+CUR_DIR+'/lib/adb_rlbench.py')
	os.system('adb shell input keyevent 4')
	for i in range(1):
		lists.append(rlbench_main())
	print lists	
		
def main():
	
	out_dir = time.strftime('%Y%m%d_%H%M%S')
	if not os.path.exists(os.path.join(result_dir, '/' + out_dir + '/')):
		os.mkdir(os.path.join(result_dir, '/' + out_dir + '/'))
	serial_thread_state = os.path.join(result_dir,'/'+out_dir+'/serial_sate')
	with open(serial_thread_state,'w+') as fp:
		fp.write("0\n")
	cmd_thread = cmd_port_thread("echo 123456|sudo -s python " +CUR_DIR+"/lib/serial_log.py -p /dev/ttyUSB2 -o "+result_dir+out_dir, 1)
	cmd_thread.start()
	
	while (not get_suspend_resume_time_stamp(out_dir)):
		os.system("echo 123456|sudo -s python " +CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
		time.sleep(20)
		if get_suspend_resume_time_stamp(out_dir):
			break
	serial_port_check(usb_name='ttyUSB2')
	renew_ttylog(out_dir)
	abl = get_abl_data(out_dir)
	ioc = get_ioc_data(out_dir)
	kernel = parse_dmesg_resume_time(out_dir)
	if abl or ioc or kernel:
		result = 'ioc_time : %s msecs abl_time : %s msecs kernel_time : %s msecs' % (round(float(ioc),3), abl, kernel)
		try:
			with open(os.path.join(result_dir,out_dir,'raw_data.txt'),"w") as fread:
				fread.write(str(result))
				fread.close()
		except Exception, e:
			print e
		resume_time =get_abl_data(out_dir)+get_ioc_data(out_dir)+parse_dmesg_resume_time(out_dir)
		print round(float(resume_time),3)
	run_case()
	os.system('adb shell input keyevent 4')
	serial_thread_state = os.path.join(result_dir,'/'+out_dir+'/serial_sate')
	with open(serial_thread_state,'w+') as fp:
		fp.write("1\n")	
	#os.system("cp -r "+out_dir+" "+tmp_dir)
	#os.system("sudo echo 123456| sudo -S rm -r "+out_dir)
	os.system("mv "+os.path.join(lib_dir,out_dir,"rlbenchmark.txt") +" "+os.path.join(result_dir,out_dir))
	#os.system("rm "+serial_thread_state)
	print ""	
	tr.result('Resume_time',resume_time,'msecs')
	tr.add_attachment(os.path.join(result_dir,out_dir,'raw_data.txt'))
	tr.add_attachment(os.path.join(result_dir,out_dir,'dmesg.txt'))
	tr.add_attachment(os.path.join(result_dir,out_dir,'outttylog.txt'))
	tr.add_attachment(os.path.join(result_dir,out_dir,'abl_dump.txt'))
	tr.add_attachment(os.path.join(lib_dir,out_dir,'rlbenchmark.txt'))
	tr.save()
	

if __name__ == "__main__":
	main()


	

