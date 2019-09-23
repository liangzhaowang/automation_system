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
from browser import browsers
from apptest import app_excetion_kill_case
from ATF import TestResult

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')

class vellamo:

	def __init__(self,app_name,app_path,tr_name):
		self.app_name = app_name
		self.app_path = app_path
		# self.app_use_name = "com.quicinc.vellamo"
		self.app = [self.app_name,self.app_path]
		self.tr_name = tr_name
		self.data = ''
		self.mobile_test = apptest(self.app)
		self.chrome_test = browsers("chrome")
		self.main()
		

	def clear_data(self):
		self.mobile_test.logout(self.mobile_test.my_func_name(),"......Clear app data......")
		time.sleep(1)
		self.mobile_test.clear_app_data()


	def push_data(self):
		os.system("adb root")
		os.system("adb shell setenforce 0")
		self.mobile_test.app_install()
		os.system("adb push ./src/app_assets3 /data/data/com.quicinc.vellamo/app_assets3")
		os.system("adb shell 'cd /data/data/com.quicinc.vellamo/; chmod -R 0777 ./app_assets3'")
	
	def run_test(self,timeout=100):
		self.clear_data()
		self.chrome_test.skip_chrome_wizard()
		self.push_data()
		time.sleep(5)
		self.mobile_test.launch_app()
		time.sleep(5)
		if not self.mobile_test.click_ui_button_by_text("Accept") :
			return False
		# if self.mobile_test.device(text="Vellamo EULA").exists:
		# 	kill_adb_uiautomator_block()
		# 	self.mobile_test.device(text="ACCEPT").click.wait()
		time.sleep(5)
		self.mobile_test.wait_for_root_page("main_root_vslider")
		if self.mobile_test.device(text="LET'S ROLL" ).exists:
			self.mobile_test.device(text="LET'S ROLL" ).click()
		# self.mobile_test.wait_for_root_page("button1")
		# kill_adb_uiautomator_block()
		# self.mobile_test.click_ui_button_by_resourceIdMatches('android:id/button1')
		if self.tr_name == "Vellamo_chrome_browser":
			kill_adb_uiautomator_block()
			self.mobile_test.click_ui_button_by_text_to_right_resourceIdMatches("Browser","card_launcher_run_button")
			time.sleep(2)
			score_text = "Chrome Browser"
		if self.tr_name == "Vellamo_webview_browser":
			kill_adb_uiautomator_block()
			# self.mobile_test.device(resourceId='com.quicinc.vellamo:id/card_browser_button').click()
			self.mobile_test.click_ui_button_by_resourceIdMatches('card_browser_button')
			time.sleep(2)
			kill_adb_uiautomator_block()
			self.mobile_test.device(resourceId='com.quicinc.vellamo:id/card_browser_button').right(resourceId='com.quicinc.vellamo:id/card_browser_button').click()
			time.sleep(2)
			kill_adb_uiautomator_block()
			self.mobile_test.click_ui_button_by_text_to_right_resourceIdMatches("Browser","card_launcher_run_button")
			score_text = "Android WebView Browser"
		if self.tr_name == "Vellamo_Metal":
			kill_adb_uiautomator_block()
			self.mobile_test.click_ui_button_by_text_to_right_resourceIdMatches("Metal","card_launcher_run_button")
			score_text = "Metal"
		
		if self.tr_name == "Vellamo_Multicore":
			kill_adb_uiautomator_block()
			self.mobile_test.click_ui_button_by_text_to_right_resourceIdMatches("Multicore","card_launcher_run_button")
			score_text = "Multicore"
		
		self.mobile_test.click_ui_button_by_text("Got it")
		time.sleep(5)
		self.tr.start_watt()
		time.sleep(5)
		self.mobile_test.logout(self.mobile_test.my_func_name(),"Begin testing......")	
		time.sleep(2)
		if self.tr_name == "Vellamo_chrome_browser" or self.tr_name == "Vellamo_webview_browser":
			time.sleep(140)
		elif self.tr_name == "Vellamo_Multicore":
			time.sleep(70)
		else:
			time.sleep(30)	
		self.mobile_test.wait_for_complete("card_score_score")
		time.sleep(2)
		self.tr.kill_watt_runtime()
		if not self.mobile_test.click_ui_button_by_text("No"):
			return False
		# self.mobile_test.device(text='NO').click()
		time.sleep(2)
		self.mobile_test.click_ui_button_by_text('Compare Scores')
		# if self.mobile_test.device(text='Compare Scores').exists:
		# 	kill_adb_uiautomator_block()
		# 	self.mobile_test.device(text="Compare Scores").click()
		if self.mobile_test.device(className="android.widget.ImageView",instance=0).exists:
			kill_adb_uiautomator_block()
			self.mobile_test.click_ui_button_by_resourceIdMatches('score_pane_topbar_button')
			# self.mobile_test.device(resourceId='com.quicinc.vellamo:id/score_pane_topbar_button').click.wait()		
		if not app_excetion_kill_case(self.mobile_test.app_package):
			return False
		# app_device = self.mobile_test.device(text = score_text)
		# if(app_device.exists):
		# 	right_dev = app_device.right(resourceIdMatches = ".+/card_score_score$")
		# 	if right_dev.exists:
		# 		self.data = str(right_dev.info['text'])
		self.data = self.mobile_test.get_score_info_data('card_score_score','text')
		kill_adb_uiautomator_block()
		if self.data != ""and self.data.isdigit():
			self.mobile_test.logout(self.mobile_test.my_func_name(),"Test data is %s"%self.data)
			return self.data
		return False
		

	def main(self):
		self.tr = TestResult(sys.argv)
		kill_adb_uiautomator_block()
		self.mobile_test.screen_on()
		time.sleep(1)
		try:
			adbcmds.turn_airplane('1')
			adbcmds.turn_bluetooth('0')
			adbcmds.turn_wifi('0')
			adbcmds.turn_gps('0')
			adbcmds.set_display_time()
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"preload setup is error %s"%e)
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

