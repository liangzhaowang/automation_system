import os
import json
import time
import re
from thread_ctrl import FuncThread
from makelog import makelog
from makelog import log_info

class watt_operate:
	def __init__(self,output_path,current_loop):
		self.output_path = output_path
		self.current_loop = current_loop
		self.log = log_info.logger
		self.get_watt_flags_time()

	def get_watt_flags_time(self):
		if os.path.exists(os.path.join(self.output_path, 'watt_' + str(self.current_loop) + '_flags')):
			with open(os.path.join(self.output_path, 'watt_' + str(self.current_loop) + '_flags'),"r") as wfp:
				line = wfp.read().strip().split("|")
				self.log.info( "line is %s !!!"%line)
			if len(line) == 2 and line[0] == "True":
				self.watt_flags = True
				self.watt_time = line[1]
			else:
				self.watt_flags = False
				self.watt_time = 5
		else:
			self.watt_flags = False
			self.watt_time = 5

	def start_cmd(self):
		os.system("adb root")
		os.system("adb shell /data/watt "+self.watt_time)

	def start_watt(self):
		self.kill_watt_runtime()
		os.system("adb shell rm /data/watt.txt")
		fthread = FuncThread(self.start_cmd)
		fthread.start()

	def kill_watt_runtime(self):
		kfp = os.popen("adb shell ps | grep watt")
		fklines = kfp.readlines()
		if len(fklines) > 0:
		    killid = fklines[0].split()[1]
		    try:
		        os.system("adb shell kill "+killid)
		    except expression as identifier:
		        print "kill %s error!!!"%killid

	def stop_watt(self):
		self.kill_watt_runtime()

	def rewrite_watt_result(self,path,watttime_nodefined = True):
		watt_lines = []
		sum1 = 0.0
		sum2 = 0.0
		sum3 = 0.0
		sum4 = 0.0
		try:
			with open(path,'r') as rwfp:
				self.log.info( "read %s !!!"%path)
				wattlines = rwfp.readlines()
				i = 0
				count = 0
				for line in wattlines:
					if i > 0:
						tmp = line.split()
						sum1 += int(tmp[0])
						sum2 += int(tmp[1])
						sum3 += int(tmp[2]) 
						sum4 += int(tmp[3])
						count += 1
					watt_lines.append(line)
					i += 1
				watt_lines.append("===========total power is ==========================\n")
				watt_lines.append("===========%s ==========================\n"%(sum2*5))
				watt_lines.append("===========test average value======================\n")
				watt_lines.append("%+10s%+10s%+10s%+10s\n"%(round(sum1/count,3),round(sum2/count,3),round(sum3/count,3),round(sum4/count,3)))
			with open(path,'w') as wwfp:
				self.log.info( "rewrite %s !!!"%path)
				wwfp.writelines(watt_lines)
			return True
		except Exception,e:
			self.log.error( "watt text open %s error!!!"%path)
			self.log.error( e)


	def compare_item(self,x,y,ABS):
		#print x,y
		abs_sub = abs(abs(x-y)-ABS)
		if abs_sub >= 0 and abs_sub <= ABS:
			return True
		else:
			return False

	def get_average(self,lists,i):
		s = sum(lists[:i])
		ave = s/i
		return ave	

	def get_effictive_data(self,lists,ABS=30):
		break_nu = 0
		for i in range(len(lists)):
			if lists[i] > 1000:
				break_nu = i
				break
			if not self.compare_item(lists[i],lists[i+1],ABS) or not self.compare_item(lists[i+1],self.get_average(lists,i+1),ABS):
				break_nu = i+1
				break
		return break_nu

	def parse_watt_file(self,watt_path,ABS=30):
		watt_clu = []
		with open(watt_path,"r") as fpr:	
			lines = fpr.readlines()
		if len(lines)<10:
			return False
		for line in lines[1:]:
			if len(line.strip()) > 0:
				watt_clu.append(int(line.split()[1]))
		watt_clu.reverse()
		end_index = len(lines) - self.get_effictive_data(watt_clu,ABS)
		with open(watt_path,"w+") as fpr:	
			fpr.writelines(lines[:end_index])
	
	def rewrite_watt_file(self,watt_path):
		llines = []
		with open(watt_path) as fpr:
			linerd = fpr.read()
		with open(watt_path) as fpl:
			lines = fpl.readlines()
		p = re.compile(r'\s+\d+\s+\d+\s+\d+')
		sobj = p.search(linerd,re.I|re.M)
		if sobj:
			for i in range(len(lines)):
				if not i == 1:
					llines.append(lines[i])
		with open(watt_path,"w+") as fpr:	
			fpr.writelines(llines)

	def watt_result_treat(self,ABS=30):
		os.system("adb root")
		time.sleep(1)
		self.out_put_filename = self.output_path+"/"+str(self.output_path).split('/')[-1]+"_"+str(self.current_loop)+"_watt"+".txt"
		os.system("adb pull /data/watt.txt "+self.out_put_filename)
		self.log.info( "copy /data/watt.txt is ok")
		self.rewrite_watt_file(self.out_put_filename)
		if not ABS == 30:
			self.parse_watt_file(self.out_put_filename,ABS)
		os.system("adb shell 'echo "+self.output_path+str(self.current_loop)+" >> /data/watt.txt'")
		self.rewrite_watt_result(self.out_put_filename)
		os.system("echo "+self.output_path+str(self.current_loop)+" >> "+self.out_put_filename)
		os.system("adb shell rm /data/watt.txt")
	
	def get_watt_average(self):
		index_nu = 0
		if self.watt_flags == False:
			return False
		try:
			with open(self.out_put_filename) as outfp:
				lines = outfp.readlines()
		except Exception,e:
			self.log.info("open %s error :%s"%(self.out_put_filename,e))
			return False
		for line in lines:
			if "test average value" in line:
				index_nu = lines.index(line)
		if index_nu > 0:
			vals = lines[index_nu+1]
			cpu_watt_val = vals.split()[1]
			self.log.info( "cpu_watt_val is %s !!!"%cpu_watt_val)
			return cpu_watt_val
		return False
    