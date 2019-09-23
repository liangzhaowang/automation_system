#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.eventHunter import eventHunter
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from runner.operation_lib.fps import test_fps
from atf import TestResult


def disable_google(zooming_test,str):
    if str == 'accept':
        if zooming_test.device(text='ACCEPT').exists:
            zooming_test.device(text='ACCEPT').click.wait(timeout=30)
        else:
            pass
    if str == 'ok':
        if zooming_test.device(text='OK').exists:
            zooming_test.device(text='OK').click.wait(timeout=30)
        else:
            pass


def set_settings(zooming_test):
    zooming_test.logout( zooming_test.my_func_name(),">>>>>>Set config<<<<<<")
    kill_adb_uiautomator_block_old()
    try:
        system_operation.turn_airplane('1')
        system_operation.modify_wifi()
        system_operation.turn_bluetooth('0')
        system_operation.turn_gps('1')
        system_operation.set_display_time()
        time.sleep(2)
        kill_adb_uiautomator_block_old()
        zooming_test.ui_operation.click_by_event("HOME")
        time.sleep(1)
    except Exception,e:
        zooming_test.logout( zooming_test.my_func_name(),"preload setup failed :%s"%e)
        return False
    kill_adb_uiautomator_block_old()
    zooming_test.ui_operation.click_by_event("HOME")
    time.sleep(10)


def run_test(zooming_fps_test,zooming_test,log,timeout=10):
    kill_adb_uiautomator_block_old()
    time.sleep(3)
    zooming_test.launch_app()
    time.sleep(3)
    kill_adb_uiautomator_block_old()
    zooming_test.ui_operation.click_ui_button_by_text("SKIP")
    time.sleep(2)
    kill_adb_uiautomator_block_old()
    disable_google(zooming_test,'ok')
    kill_adb_uiautomator_block_old()
    zooming_test.ui_operation.click_ui_button_by_text("GOT IT")
    time.sleep(5)
    kill_adb_uiautomator_block_old()
    try:
        zooming_test.device(className="android.widget.ImageView",instance=5).click.wait(timeout=50)
        time.sleep(3)
        kill_adb_uiautomator_block_old()
        disable_google(zooming_test,'ok')
        time.sleep(3)
        kill_adb_uiautomator_block_old()
        disable_google(zooming_test,'accept')
    except Exception,e:
        zooming_test.logout( zooming_test.my_func_name(),"click android.widget.ImageView error")
        return False
    try:
        time.sleep(5)
        icount = 0
        while icount < timeout:
            kill_adb_uiautomator_block_old()
            if zooming_test.device(text="Take the shortcut").exists:
                zooming_test.logout(zooming_test.my_func_name(),"---------------------------------back1")
                kill_adb_uiautomator_block_old()
                zooming_test.ui_operation.click_by_event("BACK")
                break
            time.sleep(1)
            icount += 1
        kill_adb_uiautomator_block_old()
        icount = 0
        while icount < timeout:
            kill_adb_uiautomator_block_old()
            if zooming_test.device(text="Calibrate your blue dot's compass anytime").exists:
                zooming_test.logout( zooming_test.my_func_name(),"---------------------------------back2")
                kill_adb_uiautomator_block_old()
                zooming_test.ui_operation.click_by_event("BACK")
                break
            time.sleep(1)
            icount += 1
    except Exception,e:
       zooming_test.logout(zooming_test.my_func_name(),"failed to go back")
       return False
    kill_adb_uiautomator_block_old()
    time.sleep(2)
    zooming_fps_test.doInThread(swiping_action)
    time.sleep(3)
    #tr.start_watt()
    zooming_fps_test.doInThread(zooming_fps_test.run_fpstool_ext,log)
    time.sleep(3)
    if zooming_test.ui_operation.wait_for_compelet_for_fps(timeout=50) == False:
        return False
    avg_fps=zooming_fps_test.collect_result(log)
    zooming_fps_test.kill_fps_tools()
    if avg_fps < 1.0:
        zooming_test.clear_app_data()
        zooming_test.kill_app()
        return False

    time.sleep(2)
    kill_adb_uiautomator_block_old()
    zooming_test.clear_app_data()
    zooming_test.kill_app()
    zooming_test.logout( zooming_test.my_func_name(),"Fps_while_zooming_in_map result is: %s"%avg_fps)
    return avg_fps


def swiping_action():
    kill_adb_uiautomator_block_old()
    os.system("adb root")
    time.sleep(1)
    event = eventHunter()
    event.test_zooming(repeat_zoom=5)


def main(zooming_fps_test,zooming_test):
    tr = TestResult(sys.argv)
    if not set_settings(zooming_test):
        return False
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log = log_dir + "result.txt"
    result=run_test(zooming_fps_test, zooming_test, log)
    if not result:
        zooming_fps_test.kill_fps_tools()
        return False
    tr.result('Fps_while_zooming_in_map', result, 'fps')
    tr.save()
    kill_adb_uiautomator_block()
    zooming_test.device.watchers.remove()


if __name__ == '__main__':
    zooming_fps_test = test_fps("zooming_map",'com.google.android.apps.maps/com.google.android.maps.MapsActivity')
    zooming_test = apptest(sys.argv,app_package = "com.google.android.apps.maps",app_activity="com.google.android.maps.MapsActivity",case_name = "zooming_map")
    zooming_fps_test.kill_fps_tools()
    main(zooming_fps_test,zooming_test)
