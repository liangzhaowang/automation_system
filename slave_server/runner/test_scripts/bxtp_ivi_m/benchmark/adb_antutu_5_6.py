#!/usr/bin/env python
# coding=utf-8
import os,sys
import time
import json
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])

from atf import TestResult
sys.path.append(CUR_DIR+'../operation_lib')
#sys.path.append('operation_lib')
from base_lib.exception_operation import kill_adb_uiautomator_block
from base_lib.exception_operation import kill_adb_uiautomator_block_old
from base_lib.exception_operation import kill_uiautomator
from base_lib.exception_operation import app_exception_kill_case
from base_lib import system_operation
from apptest import apptest
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')


def clean_app(antutu):
	kill_adb_uiautomator_block_old()
	antutu.clear_app_data()

def enable_permissions(antutu):
	kill_adb_uiautomator_block_old()
	antutu.logout(antutu.my_func_name(),'...')
	back_times = 0
	time.sleep(3)
	if antutu.ui_operation.wait_for_open_spacial_function('Enable 64-bit',timeout=10):
		time.sleep(1)
		antutu.ui_operation.click_ui_button_by_resourceIdMatches("btn_ok")
		back_times += 1
		time.sleep(3)
	if antutu.ui_operation.wait_for_open_spacial_function('AnTuTu Benchmark 64-bit',timeout=10):
		time.sleep(2)
		antutu.ui_operation.click_ui_button_by_resourceIdMatches("ok_button",package='antutu')
		back_times -= 1
		time.sleep(3)

	if antutu.ui_operation.wait_for_open_spacial_function('App installed.',timeout=10):
		time.sleep(2)
		antutu.ui_operation.click_ui_button_by_resourceIdMatches("done_button",package='antutu')	
		time.sleep(3)
	kill_adb_uiautomator_block_old()
	for i in range(back_times):
		antutu.ui_operation.click_by_event("BACK")
		# kill_adb_uiautomator_block_old()


def run_test(tr,log_dir,antutu):
	antutu.logout(antutu.my_func_name(),'...')
	result_dict = {}
	antutu.app_install()
	antutu.kill_app()
	antutu.clear_app_data()
	time.sleep(1)
	antutu.launch_app()
	time.sleep(5)
	enable_permissions(antutu)
	if antutu.ui_operation.wait_for_root_page('start_test_region') == False:
		return False
	# kill_adb_uiautomator_block_old()

	if antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text',timeout=10,package='antutu') == False:
		return False
	time.sleep(3)

	if antutu.ui_operation.wait_for_complete('detail_btn',timeout=1800,skipstep=30,package='antutu'):
		try:
			# result_text = antutu.device(resourceIdMatches=".+/device_name$",textContains="Non-verified").info['text']
			# ts = result_text.lstrip().strip().split(":")[-1]
			# result_dict["total_score"] = ts
			result_dict_ex = collect_result_ex(antutu)
			antutu.ui_operation.log.info(result_dict_ex)
			for key,velue in result_dict_ex.items():
				tr.sub_score(key, velue)
			result_dict.update(result_dict_ex)
			print log_dir
			antutu.device.screenshot("%sresult.png"%log_dir)
		except Exception,e:
			antutu.ui_operation.log.error('get result total is fail,error :%s'%e)
			return False
		time.sleep(2)
		antutu.ui_operation.click_ui_button_by_resourceIdMatches("detail_btn",package='antutu')
		if antutu.ui_operation.wait_for_open_spacial_function('Details - v5.6',timeout=100):
			# time.sleep(2)
			# kill_adb_uiautomator_block_old()
			antutu.device.screenshot("%sresult.png"%log_dir)
			# result_dict.update(collect_result(antutu))

		antutu.kill_app()
		antutu.logout(antutu.my_func_name(),"%s test finshed..."%app[0])
		time.sleep(5)
		if result_dict["total_score"] == "":
			antutu.logout(antutu.my_func_name(),"Error, NO result found......")
			return False
		else:
			antutu.logout(antutu.my_func_name(),'Antutu total_score is %s'%result_dict["total_score"])
			for item in result_dict.keys():
				if not "total_score" == item:
					antutu.logout(antutu.my_func_name(),'Antutu %s is %s'%(item,result_dict[item]))
			return result_dict

	else:
		antutu.logout(antutu.my_func_name(), antutu.app_name+" Exception error: can't complete, Please check !!!!!!!")
		return False
def collect_result_ex(antutu):
	result_dict = {}
	output_log = os.path.join(CUR_DIR,out_dir+'/antutu.txt')
	allresult = 'adb logcat -d | grep -i antutubenchmarkscore >'+output_log
	os.system(allresult)
	try:
		with open(output_log) as fpout:
			result = fpout.readlines()
		if(len(result)>2):
			for line in result:
				for key,item in logcat_score_id_dict.items():
					if item in line:
						value = line.strip().split(":")[-1]
						if len(value) > 0:
							result_dict[key] = value
		antutu.logout(antutu.my_func_name(),'antutu result is :%s'%result_dict.items())
	except Exception,e:
		antutu.log.error('get antutu test result error :%s'%e)
	return result_dict

# def collect_result(antutu,timeout = 5):
# 	result_dict = {}
# 	antutu.logout(antutu.my_func_name(),'...')
# 	for item in score_id_dict.keys():
# 		# kill_adb_uiautomator_block_old()
# 		item_score = antutu.ui_operation.get_score_info_data(score_id_dict[item],'text',timeout=timeout)
# 		if len(item_score)>0:
# 			result_dict[item]=item_score
# 	return result_dict

def main(antutu,tr):

	# kill_adb_uiautomator_block()
	if antutu.command_timeout("adb wait-for-device",timeout=10):
		# run_watcher()
		antutu.check_system_app_package("antutu")
		time.sleep(3)
		os.system("adb root")
		system_operation.screen_on(antutu.log)
		# time.sleep(1)
		# system_operation.turn_airplane('1', antutu.log)
		# system_operation.turn_bluetooth('0', antutu.log)
		# system_operation.turn_wifi('0', antutu.log)
		# system_operation.turn_gps('0', antutu.log)
		# system_operation.set_display_time(antutu.log)
		time.sleep(2)
		antutu.log.info(CUR_DIR)

		results = run_test(tr,log_dir,antutu)
		if  results == False:
			antutu.logout(antutu.my_func_name(),"Error, run test result get error......")
			return False
		if len(results['total_score']) == 0:
			antutu.logout(antutu.my_func_name(),"Error, run test result get total score error......")
			return False
		rj = open("%sresult.json"%log_dir,'w+')
		rj.write(json.dumps(results))
		rj.close()

		#antutu.app_uninstall()
	else:
		antutu.logout(antutu.my_func_name(),"Timeout to wait for device,device is disconnect.")
		raise Exception("Device is disconnect...")
		return False

	tr.result(results['total_score'])
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/antutu.txt'),'antutu.txt')
	tr.add_attachment(log_dir+"result.png")
	tr.save()
	#clean_app(antutu)
	return True

if __name__ == "__main__":
	# score_id_dict = {
	# 		"Multitask":"ue_multitask_text",
	# 		"Runtime":"ue_dalvik_text",
	# 		"CPU integer":"cpu_int_text",
	# 		"CPU float-point":"cpu_float_text",
	# 		"Single-thread integer":"cpu_int_text2",
	# 		"Single-thread float-point":"cpu_float_text2",
	# 		"RAM Operation":"mem_text",
	# 		"RAM Speed":"ram_text",
	# 		"2D graphics":"gpu_2d_text",
	# 		"3D graphics":"gpu_3d_text",
	# 		"Storage I/O":"io_sdw_text",
	# 		"Database I/O":"io_db_text"
	# }

	logcat_score_id_dict = {
			"Multitask":"multitask :",
			"Runtime":"ue_dalvik_text :",
			"CPU integer":"integer :",
			"CPU float-point":"float :",
			"Single-thread integer":"integersingle :",
			"Single-thread float-point":"floatsingle :",
			"RAM Operation":"memory :",
			"RAM Speed":"ram :",
			"2D graphics":"2d :",
			"3D graphics":"3d :",
			"Storage I/O":"storage :",
			"Database I/O":"database :",
			"total_score":"score :"
	}
	tr = TestResult(__file__)
	app = ["Antutu","./src/AnTuTu_v5.6.apk"]
	log_dir = os.path.join(CUR_DIR,'./'+out_dir+'/')
	if not os.path.exists(log_dir):
		os.mkdir(log_dir)
	args = [log_dir,tr.loop_index]
	antutu = apptest(args,app)
	icount = 0
	ilimite = 2
	while not main(antutu,tr):
		if icount > ilimite:
			break
		icount +=1
