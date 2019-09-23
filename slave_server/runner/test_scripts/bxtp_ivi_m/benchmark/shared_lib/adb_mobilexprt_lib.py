#!/usr/bin/env python
# coding=utf-8
import os,sys
sys.path.append('../../lib')
sys.path.append('./lib')

import time
import re
import commands,threading
from kill_uiautomator import kill_adb_uiautomator_block
import adbcmds
from apptest import apptest
from apptest import app_excetion_kill_case
from ATF import TestResult

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')

class mobilexpor:

	def __init__(self,app_name,app_path,tr_name):
		self.app_name = app_name
		self.app_path = app_path
		self.app_use_name = "com.mobilexprt"
		self.app = [self.app_name,self.app_path]
		self.tr_name = tr_name
		self.data = ''
		self.mobile_test = apptest(self.app)
		self.main()

	def clear_data(self):
		self.mobile_test.kill_app(self.app_use_name)
		self.mobile_test.clear_app_data(self.app_use_name)
		time.sleep(1)
		self.mobile_test.device.press.home()
		time.sleep(3)


	def run_test(self,timeout=50):
		#self.clear_data()
		self.mobile_test.launch_app()
		#time.sleep(30)
		self.mobile_test.wait_for_root_page("ok_button")
		kill_adb_uiautomator_block()
		self.mobile_test.click_ui_button_by_resourceIdMatches('ok_button')
		self.mobile_test.click_ui_button_by_resourceIdMatches('launch_button',timeout)
		while "Extracting content" in self.mobile_test.device.dump():
			time.sleep(10)
			kill_adb_uiautomator_block()
			time.sleep(2)
    	# 	time.sleep
		#time.sleep(60)
		if self.tr_name == "MobileXPRT_perf":
			self.mobile_test.click_ui_button_by_resourceIdMatches('cancel_button',timeout)
			# self.mobile_test.wait_for_root_page('button_media_tests')
			if not self.mobile_test.click_ui_button_by_resourceIdMatches('button_media_tests',120):
				return False
		if self.tr_name == "MobileXPRT_ux":
			self.mobile_test.click_ui_button_by_resourceIdMatches('ok_button',timeout)
			self.mobile_test.click_ui_button_by_resourceIdMatches('done_button',timeout)
			# self.mobile_test.wait_for_root_page('button_ux_tests')
			if not self.mobile_test.click_ui_button_by_resourceIdMatches('button_ux_tests',120):
				return False
		kill_adb_uiautomator_block()
		time.sleep(10)
		self.tr.start_watt()
		time.sleep(400)	
		if self.mobile_test.wait_for_complete("group_score",timeout=500) == False:
			return False
		time.sleep(2)
		self.tr.kill_watt_runtime()
		kill_adb_uiautomator_block()
		if not app_excetion_kill_case(self.mobile_test.app_package):
			return False
		app_device = self.mobile_test.device(resourceIdMatches = ".+/group_name")

		if(app_device.exists):
			right_dev = app_device.right(resourceIdMatches = ".+/group_score")
			if right_dev.exists:
				self.data = str(right_dev.info['text'])
		kill_adb_uiautomator_block()

		# if self.data != ""and self.data.isdigit():
		if self.data != "":
			self.mobile_test.logout(self.mobile_test.my_func_name(),"Test data is %s"%self.data)
			return self.data
		return False
		

	def main(self):
		os.system("adb root")
		self.mobile_test.screen_on()
		time.sleep(1)
		self.tr = TestResult(sys.argv)
		try:
			adbcmds.turn_airplane('1')
			adbcmds.turn_bluetooth('0')
			adbcmds.turn_wifi('0')
			adbcmds.turn_gps('0')
			adbcmds.set_display_time()
		except Exception,e:
			return False
		time.sleep(2)
		print CUR_DIR
		log_dir = os.path.join(CUR_DIR,'../'+out_dir+'/')
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)
		result = self.run_test()
		if result == False:
			self.clear_data()
			return False
		self.mobile_test.device.screenshot("%sresult.png"%log_dir)
		self.clear_data()
	
		self.tr.result(self.tr_name, result, 'score')
		self.tr.add_attachment(log_dir+"result.png")
		self.tr.save()

