#!/usr/bin/env python
# coding=utf-8
import os,sys
import time
import re

sys.path.append('../../lib')
sys.path.append('lib')

import adbcmds
from apptest import apptest
from ATF import TestResult
from kill_uiautomator import kill_adb_uiautomator_block
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')


class jio_random:
	def __init__(self,app_name,app_path,tr_name):
		self.app_name = app_name
		self.app_path = app_path
		self.app = [self.app_name,self.app_path]
		self.tr_name = tr_name
		self.data = ''
		self.mobile_test = apptest(self.app)
		self.main()
	
	def clear_data(self):
		self.mobile_test.kill_app()
		time.sleep(1)
		self.mobile_test.clear_app_data()
		time.sleep(2)

	def test_jio(self,log_dir):
		self.clear_data()
		time.sleep(1)
		self.mobile_test.launch_app()
		self.mobile_test.wait_for_root_page("main_list_view")
		time.sleep(2)
		self.mobile_test.click_ui_button_by_text("Performance Tests")
		time.sleep(2)
		if self.tr_name == "JIO_Random_Write":
			self.mobile_test.click_ui_button_by_text("Random Write")
		if self.tr_name == "JIO_Random_Read":
			self.mobile_test.click_ui_button_by_text("Random Read")
		time.sleep(5)
		self.tr.start_watt()
		self.mobile_test.logout(self.mobile_test.my_func_name(),'Select the test item...')
		time.sleep(2)
		self.mobile_test.click_ui_button_by_text("Run")

		self.mobile_test.logout(self.mobile_test.my_func_name(),'Begin testing...')
		#time.sleep(150)
		if self.mobile_test.wait_for_complete("testReportTitle",timeout=60) == False:
			return False
		time.sleep(1)
		self.mobile_test.device.screenshot("%sresult.png"%log_dir)
		result = self.collect_result()
		time.sleep(2)
		self.clear_data()
		self.mobile_test.logout(self.mobile_test.my_func_name(),"%s test finshed..."%self.tr_name)
		if result == False:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"Error, NO result found......")
			return False
		else:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"%s (in IOPS): %s"%(self.tr_name,result))
		return result
	
	def collect_result(self):
		rr_score = ""
		rs = self.mobile_test.get_score_info_data("textViewLogContent","text")
		if rs == "":
			return False
		if self.tr_name == "JIO_Random_Write":
			rr_score = re.findall(r'.+Random Write:\t(\d+,\d+)',rs)[0]
		if self.tr_name == "JIO_Random_Read":
			rr_score = re.findall(r'.+Random Read:\t(\d+,\d+)',rs)[0]
		if rr_score == "":
			return False
		rr_score = rr_score.replace(",","")
		return rr_score

	def main(self):
		self.tr = TestResult(sys.argv)
		kill_adb_uiautomator_block()
		try:
			self.mobile_test.screen_on()
			time.sleep(1)
			adbcmds.turn_airplane('1')
			adbcmds.turn_bluetooth('0')
			adbcmds.turn_wifi('0')
			adbcmds.turn_gps('0')
			adbcmds.set_display_time()
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"Error setup load......")
			return False
		time.sleep(2)
		print CUR_DIR
		log_dir = os.path.join(CUR_DIR,'../'+out_dir+'/')
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)
		result = self.test_jio(log_dir)
		if result == False:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"Error,get result fail......")
			return False

		self.tr.result(self.tr_name, result, 'IOPS')
		self.tr.add_attachment(log_dir+"result.png")
		self.tr.save()

