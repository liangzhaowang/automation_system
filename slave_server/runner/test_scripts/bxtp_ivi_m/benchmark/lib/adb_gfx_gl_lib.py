#!/usr/bin/env python
# coding=utf-8
import os,sys
import time
import re

sys.path.append('./lib')
sys.path.append('lib')
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib'))
# from kill_uiautomator import kill_adb_uiautomator_block
import adbcmds
from apptest_new import apptest
from atf import *

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')
apk_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'gfxbench_gl-4.0.1+corporate.x86_64.x86.apk')
tr = TestResult(__file__)

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

	def click_test_selection(self):
		time.sleep(10)
		try:
			self.mobile_test.click_ui_button_by_text("OK")
			time.sleep(2)
		except Exception,e:
			self.mobile_test.click_ui_button_by_text("OK")
			os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
			time.sleep(10)
			result =self.run_test(log_dir)
		try:
			self.mobile_test.wait_for_root_page("main_circleControl")
		except Exception,e:
			os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
			time.sleep(10)
			result =self.run_test(log_dir)
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		display_h = self.mobile_test.device.info['displayHeight']
		display_w = self.mobile_test.device.info['displayWidth']
		icon_x = display_w * 58 / 100
		icon_y = display_h * 70 / 100
		self.mobile_test.device.click(icon_x,icon_y)

	def swipe_item_down(self):
		
		display_h = self.mobile_test.device.info['displayHeight']
		display_w = self.mobile_test.device.info['displayWidth']
		icon_sx = display_w * 58 / 100
		icon_sy = display_h * 70 / 100
		icon_ex = display_w * 58 / 100
		icon_ey = display_h * 30 / 100

		self.mobile_test.device.swipe(icon_sx,icon_sy,icon_ex,icon_ey)

	def swipe_item_up(self):
		
		display_h = self.mobile_test.device.info['displayHeight']
		display_w = self.mobile_test.device.info['displayWidth']
		icon_sx = display_w * 58 / 100
		icon_sy = display_h * 50 / 100
		icon_ex = display_w * 58 / 100
		icon_ey = display_h * 80 / 100

		self.mobile_test.device.swipe(icon_sx,icon_sy,icon_ex,icon_ey)
	
	def prepare_for_selection(self,timeout=5):
		icount = 0
		# kill_adb_uiautomator_block()
		while icount < timeout:
			app_dev = self.mobile_test.device(text='High-Level Tests')
			if app_dev.exists:
				right_dev=app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
				if right_dev.exists:
					d =right_dev.checked
					if d:
						right_dev.click()
						icount = 0
						self.swipe_item_down()
			
			app_dev =self.mobile_test.device(text='Low-Level Tests')
			if app_dev.exists:
				right_dev=app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
				if right_dev.exists:
					d =right_dev.checked
					if d:
						right_dev.click()
						icount = 0
						self.swipe_item_down()
			else:
				self.swipe_item_down()
			
			app_dev =self.mobile_test.device(text='Special Tests')
			if app_dev.exists:
				right_dev=app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
				if right_dev.exists:
					d =right_dev.checked
					if d:
						right_dev.click()
						icount = 0
						self.swipe_item_down()
			else:
				self.swipe_item_down()
			app_dev =self.mobile_test.device(text='Battery Test')
			if app_dev.exists:
				right_dev=app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
				if right_dev.exists:
					d =right_dev.checked
					if d:
						right_dev.click()
						icount = 0
						self.swipe_item_down()
			else:
				self.swipe_item_down()
			app_dev =self.mobile_test.device(text='Fixed Time Test')
			if app_dev.exists:
				right_dev=app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
				if right_dev.exists:
					d =right_dev.checked
					if d:
						right_dev.click()
						icount = 0
			time.sleep(1)
			icount += 1
			# kill_adb_uiautomator_block()
		if icount > 0:
			return False
		else:
			return True

	def select_item(self,timeout = 10):
		self.mobile_test.logout(self.mobile_test.my_func_name(),'...')
		# kill_adb_uiautomator_block()
		icount = 0
		print '1111'
		# app_dev =''
		app_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text='Manhattan').sibling(textContains='ES 3.0')
		view_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text='1080p Manhattan Offscreen').sibling(textContains='ES 3.0')
		# man_dev = self.mobile_test.device(textMatches="This is the original Manhattan test, first introduced in GFXBench 3.0")
		while icount < timeout:
			
			if "Manhattan" in self.tr_name:
				app_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text='Manhattan').sibling(textContains='ES 3.0')
				view_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text='1080p Manhattan Offscreen').sibling(textContains='ES 3.0')
				
			if "T-Rex" in self.tr_name:
				app_dev = self.mobile_test.device(text="T-Rex")	
				view_dev = self.mobile_test.device(text="1080p T-Rex Offscreen")
			# app_dev = self.mobile_test.device(text="T-Rex")
			if app_dev.exists:
				if "onscreen" in self.tr_name:
					app_dev.click()
					# kill_adb_uiautomator_block()
					icount = 0
					break
			
			# view_dev = self.mobile_test.device(text="1080p T-Rex Offscreen")
				if "offscreen" in self.tr_name:
					while icount < timeout:
						if view_dev.exists:
							view_dev.click()
							icount = 0
							break
						else:
							self.swipe_item_down()
							time.sleep(1)
							icount += 1
					icount = 0
					break
					# kill_adb_uiautomator_block()
				
			time.sleep(1)
			icount += 1
			# kill_adb_uiautomator_block()	
				
		if icount > 0:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"select_item failed.....")
			return False
		else:
			return True

	def run_test(self,log_dir,timeout=10):
		os.system('adb shell input keyevent 82')
		time.sleep(2)
		self.mobile_test.launch_app()
		time.sleep(5)
		try:
			self.click_test_selection()
			time.sleep(1)
		except Exception,e:
			os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
			time.sleep(10)
			result =self.run_test(log_dir)
		self.prepare_for_selection()
		time.sleep(1)
		for i in range(10):
			self.swipe_item_up()
		time.sleep(2)
		if not self.select_item():
			self.mobile_test.logout(self.mobile_test.my_func_name(),"start Run test is failed.....")
			# kill_adb_uiautomator_block()
			os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
			time.sleep(10)
			result =self.run_test(log_dir)
			return False
		time.sleep(2)
		self.mobile_test.logout(self.mobile_test.my_func_name(),"Run test.....")
		# kill_adb_uiautomator_block()
		self.mobile_test.click_ui_button_by_text("Start")
		time.sleep(2)
		try:
			self.mobile_test.wait_for_complete("results_testList",timeout=600)
			time.sleep(2)
			# kill_adb_uiautomator_block()
			self.mobile_test.device.screenshot("%sresult.png"%log_dir)
		except Exception,e:
			os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
			time.sleep(10)
			result =self.run_test(log_dir)
		result = self.collect_result()
		if result == False:
			return False
		self.mobile_test.logout(self.mobile_test.my_func_name(),"%s test finshed..."%self.app_name)
		# kill_adb_uiautomator_block()
		time.sleep(2)
		self.clear_data()
		return result

	def collect_result(self):
		try:
			result = ""
			# kill_adb_uiautomator_block()
			fps_score = self.mobile_test.get_score_info_data("updated_result_item_subresult",'text')
			print fps_score
			# kill_adb_uiautomator_block()
			#result = re.sub("[()\xa0Fps]","",fps_score)
			result =re.search(r"(?P<rlfps_score>\d+)\S*.+",fps_score).group('rlfps_score')
			if result == "":
				return False
			return result
		except Exception,e:
			self.mobile_test.logout(self.mobile_test.my_func_name(),"get updated_result_item_subresult score failed")
			return False

	def main(self):
		self.tr = TestResult(__file__)
		# kill_adb_uiautomator_block()
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
		self.result = result
		return True


