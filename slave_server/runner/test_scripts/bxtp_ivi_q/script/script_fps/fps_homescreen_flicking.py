#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.apptest import apptest
from runner.operation_lib.fps import test_fps
from atf import TestResult


def long_click(homescreen_test,app_no):
    kill_adb_uiautomator_block()
    bounds = homescreen_test.device(resourceIdMatches='.+/icon',index=app_no).info['bounds']
    x = int(bounds['left'])/2 + int(bounds['right'])/2
    y = int(bounds['top'])/2 + int(bounds['bottom'])/2
    kill_adb_uiautomator_block()
    homescreen_test.device.swipe(x,y,x-20,y-20)
    # homescreen_test.swiping.swipe_by_position(x,y,x-20,y-20)


def add_icon(homescreen_test):
    kill_adb_uiautomator_block()
    homescreen_test.ui_operation.click_by_event("HOME")
    time.sleep(1)
    icon_count = int(homescreen_test.device(className='android.widget.TextView').count)
    app_no = 2
    while icon_count < 28:
        kill_adb_uiautomator_block()
        homescreen_test.device(description='Apps list').click()
        long_click(homescreen_test,app_no)
        time.sleep(1)
        kill_adb_uiautomator_block()
        homescreen_test.ui_operation.click_by_event("HOME")
        icon_count = int(homescreen_test.device(className='android.widget.TextView').count)


def open_widgets(homescreen_test):
    kill_adb_uiautomator_block()
    homescreen_test.ui_operation.click_by_event("HOME")
    bounds = homescreen_test.device(description='Apps list').info['bounds']
    x = int(bounds['left']) - 5
    y = int(bounds['top']) + 5
    kill_adb_uiautomator_block()
    homescreen_test.device.long_click(x,y)
    kill_adb_uiautomator_block()
    homescreen_test.device(text='WIDGETS').click()


def drag_widgets(homescreen_test):
    kill_adb_uiautomator_block()
    bounds = homescreen_test.device(textContains='Month').info['bounds']
    x = int(bounds['left'])/2 + int(bounds['right'])/2
    y = int(bounds['top'])/2 + int(bounds['bottom'])/2
    kill_adb_uiautomator_block_old()
    homescreen_test.device.drag(x,y,x+x,y)
    time.sleep(3)


def add_widgets(homescreen_test):
    kill_adb_uiautomator_block_old()
    homescreen_test.ui_operation.click_by_event("HOME")
    time.sleep(2)
    kill_adb_uiautomator_block_old()
    homescreen_test.swiping.left()
    time.sleep(3)
    wid_num = int(homescreen_test.device(className='com.android.launcher3.LauncherAppWidgetHostView').count)
    if wid_num == 6:
        pass
    else:
        while True:
            if wid_num != 6:
                homescreen_test.log.info("begin test>>>>>>>>>>>>>>>>>>>>>>")
                open_widgets(homescreen_test)
                time.sleep(1)
                drag_widgets(homescreen_test)
                time.sleep(2)
                wid_num+=1
                homescreen_test.log.info(wid_num)
                time.sleep(1)
            else:
                return False


def left_right(homescreen_test):
    for i in range(30):
        homescreen_test.swiping.right()
        time.sleep(1.5)
        homescreen_test.swiping.left()
        time.sleep(1.5)


def run_test(homescreen_fpstest, homescreen_test,log):
    kill_adb_uiautomator_block()
    add_icon(homescreen_test)
    add_widgets(homescreen_test)
    time.sleep(3)
    homescreen_fpstest.doInThread(left_right,homescreen_test)
    time.sleep(3)
    homescreen_fpstest.doInThread(homescreen_fpstest.run_fpstool_ext,log)

    if not homescreen_test.ui_operation.wait_for_compelet_for_fps(timeout=60):
        return False
    avg_fps=homescreen_fpstest.collect_result(log)
    homescreen_fpstest.kill_fps_tools()
    if avg_fps < 1.0:
        return False
    homescreen_fpstest.logout( homescreen_fpstest.my_func_name(), "Frame rate of Home screen flicking result is:%s" % avg_fps)
    return avg_fps


def main(homescreen_fpstest, homescreen_test):
    tr = TestResult()
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log = log_dir+"result.txt"
    result = run_test(homescreen_fpstest,homescreen_test,log)
    if result == False:
        return False
    tr.result('Frame_rate_of_Home_screen_flicking', result, 'fps')
    tr.save()


if __name__ == '__main__':
    homescreen_fpstest = test_fps("homescreen_fpstest", 'com.android.launcher3/com.android.launcher3.Launcher')
    homescreen_test = apptest(sys.argv,app_package="com.android.launcher3", app_activity="com.android.launcher3.Launcher", case_name="homescreen_fpstest")
    homescreen_fpstest.kill_fps_tools()
    main(homescreen_fpstest, homescreen_test)
