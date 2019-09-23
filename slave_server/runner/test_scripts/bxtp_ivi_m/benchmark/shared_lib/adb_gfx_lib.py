#!/usr/bin/env python
# coding=utf-8
import os,sys
import time
import re

sys.path.append('../../lib')
sys.path.append('lib')
from kill_uiautomator import kill_adb_uiautomator_block
import adbcmds
from apptest import apptest
from ATF import TestResult

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')

class gfx:

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

	def click_test_selection(self,):
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		display_h = self.mobile_test.device.info['displayHeight']
		display_w = self.mobile_test.device.info['displayWidth']
		icon_x = display_w * 58 / 100
		icon_y = display_h * 70 / 100
		self.mobile_test.device.click(icon_x,icon_y)

	def select_item(self,timeout = 5):
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		kill_adb_uiautomator_block()
		icount = 0
		app_dev = self.mobile_test.device(text="Manhattan")
		while icount < timeout:
			if "Manhattan" in self.tr_name:
				app_dev = self.mobile_test.device(text="Manhattan")
			if "T-Rex" in self.tr_name:
				app_dev = self.mobile_test.device(text="T-Rex")
			if app_dev.exists:
				view_dev=app_dev.right(className="android.widget.ImageView")
				if "offscreen" in self.tr_name :
					view_dev.right(className="android.widget.ImageView").click()
				if  "onscreen" in self.tr_name:
					view_dev.click()
				kill_adb_uiautomator_block()
				icount = 0
				break
			time.sleep(1)
			icount += 1
			kill_adb_uiautomator_block()
		if icount > 0:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"select_item fialed.....")
			return False
		else:
			return True

	def run_test(self,log_dir,timeout=10):
		self.mobile_test.launch_app()
		time.sleep(5)
		self.mobile_test.wait_for_root_page("main_circleControl")
		self.click_test_selection()
		time.sleep(1)
		if not self.select_item():
			self.mobile_test.logout(self.mobile_test.my_func_name(),"start Run test is failed.....")
			kill_adb_uiautomator_block()
			return False
		time.sleep(2)
		self.mobile_test.logout(self.mobile_test.my_func_name(),"Run test.....")
		kill_adb_uiautomator_block()
		self.mobile_test.click_ui_button_by_text("Start")
		self.tr.start_watt()
		time.sleep(2)
		self.mobile_test.wait_for_complete("results_testList",timeout=600)
		time.sleep(2)
		kill_adb_uiautomator_block()
		self.mobile_test.device.screenshot("%sresult.png"%log_dir)
		result = self.collect_result()
		if result == False:
			return False
		self.mobile_test.logout(self.mobile_test.my_func_name(),"%s test finshed..."%self.app_name)
		kill_adb_uiautomator_block()
		time.sleep(2)
		self.clear_data()
		return result

	def collect_result(self):
		try:
			result = ""
			kill_adb_uiautomator_block()
			fps_score = self.mobile_test.get_score_info_data("cell_result_unit",'text',"1")
			kill_adb_uiautomator_block()
			result = re.sub("[() fps]","",fps_score)
			if result == "":
				return False
			return result
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"get cell_result_unit score failed")
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
			return False 
		time.sleep(2)
		print CUR_DIR
		log_dir = os.path.join(CUR_DIR,'../'+out_dir+'/')
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)
		result = self.run_test(log_dir)
		if result == False:
			return False

		self.mobile_test.logout(self.mobile_test.my_func_name(),"Test result is : %s"%result)
		self.tr.result(self.tr_name, result, 'fps')
		self.tr.save()


