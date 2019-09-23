#!/usr/bin/env python
# coding=utf-8
import os,sys
import time

sys.path.append('../../lib')
sys.path.append('lib')

from kill_uiautomator import kill_adb_uiautomator_block
import adbcmds
from apptest import apptest
from ATF import TestResult

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')

class glbench:
	def __init__(self,app_name,app_path,test_text):
		self.app_name = app_name
		self.app_path = app_path
		self.app = [self.app_name,self.app_path]
		self.data = ''
		self.test_text = test_text
		self.mobile_test = apptest(self.app)
		self.main()
		
	def ckeck_corporate(self):
		kill_adb_uiautomator_block()
		time.sleep(2)
		os.system("adb root")
		time.sleep(2)
		get_packes=os.popen("adb shell pm list packages -3").readlines()
		for i in get_packes:
			if i.count('package:com.glbenchmark.glbenchmark27.corporate\n')==1:
				package_corporate=i.strip().split(":")[1]
				os.system("adb uninstall %s"%package_corporate)
				print "com.glbenchmark.glbenchmark27.corporate is uninstalled"
			else:
				print "DUT have no corporate packages"

	def clear_data(self):
		self.mobile_test.kill_app()
		time.sleep(1)
		self.mobile_test.clear_app_data()
		time.sleep(2)

	def run_test(self,log_dir):
		self.clear_data()
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		time.sleep(1)
		self.mobile_test.launch_app()
		time.sleep(2)
		self.mobile_test.wait_for_root_page("listView1")
		time.sleep(2)
		kill_adb_uiautomator_block()
		self.mobile_test.click_ui_button_by_text("Performance Tests") #device(text="Performance Tests").click.wait()
		time.sleep(1)
		self.mobile_test.logout(self.mobile_test.my_func_name(),'Select test item...')
		kill_adb_uiautomator_block()
		time.sleep(1)
		try:
			self.mobile_test.device(scrollable=True).scroll.to(text=self.test_text)
			kill_adb_uiautomator_block()
			self.mobile_test.device(text=self.test_text).right(className="android.widget.CheckBox").click.wait()
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"scroll click error: %s "%e)
			return False
		self.mobile_test.logout(self.mobile_test.my_func_name(),'Begin testing......')
		time.sleep(1)
		kill_adb_uiautomator_block()
		self.mobile_test.click_ui_button_by_text("Start")
		self.tr.start_watt() #start watt
		time.sleep(10)
		self.mobile_test.wait_for_complete("listViewResults")
		time.sleep(1)
		result = self.collect_result()
		if result == False:
			self.clear_data()
			return False
		kill_adb_uiautomator_block()
		self.mobile_test.device.screenshot("%sresult.png"%log_dir)
		time.sleep(1)
		self.clear_data()
		self.mobile_test.logout(self.mobile_test.my_func_name(),"%s test finshed..."%self.app_name)
		time.sleep(5)
		return result

	def collect_result(self):
		try:
			kill_adb_uiautomator_block()
			fps_score = self.mobile_test.device(text=self.test_text).right(resourceIdMatches=".+/textViewFps$").info['text']
			if fps_score == "":
				return False
			return fps_score
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"get collect result is error: %s "%e)
			return False

	def main(self):
		self.tr = TestResult(sys.argv)
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		self.ckeck_corporate()
		time.sleep(2)
		kill_adb_uiautomator_block()
		time.sleep(1)
		self.mobile_test.screen_on()
		time.sleep(1)
		try:
			adbcmds.turn_airplane('1')
			adbcmds.turn_bluetooth('0')
			adbcmds.turn_wifi('0')
			adbcmds.turn_gps('0')
			adbcmds.set_display_time()
		except Exception, e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"preload setup is error %s"%e)
			return False
		time.sleep(2)
		print CUR_DIR
		log_dir = os.path.join(CUR_DIR,'../'+out_dir+'/')
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)
		result = self.run_test(log_dir)
		if result == False:
			return False
		result = result.replace("fps","").strip()
		self.mobile_test.logout(self.mobile_test.my_func_name(),"Test result is : %s"%result)
		self.tr.result(self.app_name, result,'fps')
		self.tr.save()

