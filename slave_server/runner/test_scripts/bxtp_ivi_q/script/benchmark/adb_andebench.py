#!/usr/bin/env python
# coding=utf-8
import os
import sys
import re
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.exception_operation import app_exception_kill_case
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult, TestLogger

logger = TestLogger().get_logger("process")
result = ""
app_pakage_name = "com.eembc.coremark"


def button_operation(andebench, tr):
    try:
        andebench.ui_operation.click_by_event("MENU")
        kill_adb_uiautomator_block()
        andebench.ui_operation.click_ui_button_by_text('Settings')
        kill_adb_uiautomator_block()
        andebench.ui_operation.click_by_event("BACK")
        kill_adb_uiautomator_block()
        andebench.ui_operation.click_ui_button_by_text('Reset')
        kill_adb_uiautomator_block()
        andebench.ui_operation.click_by_event("BACK")
        kill_adb_uiautomator_block()
        andebench.ui_operation.click_ui_button_by_resourceIdMatches('btn_start_on')
    except Exception, e:
        andebench.logout(andebench.my_func_name(),"button operation is error,error code is %s"%e)
        return False

  
def main(andebench, timeout=80):
    tr = TestResult(sys.argv)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    try:
        system_operation.turn_wifi('0')
        system_operation.turn_bluetooth('0')
        clear_all(andebench)
    except Exception, e:
        andebench.logout(andebench.my_func_name(), "Setup Failure. %s" % e)
        return False
    andebench.launch_app()
    if button_operation(andebench, tr) == False:
        return False
    time.sleep(5)
    if andebench.ui_operation.watt_operate.watt_flags:
        andebench.ui_operation.watt_operate.start_watt()
    iconut = 0
    while iconut < timeout:
        if not app_exception_kill_case(andebench.app_package):
            if andebench.ui_operation.watt_operate.watt_flags:
                andebench.ui_operation.watt_operate.stop_watt()
            return False
        app_device = andebench.device(resourceIdMatches='.+/cid$')
        if app_device.exists and (re.search(r'.+\n.+: \d+\n.+: \d+\n',app_device.info['text'],re.I|re.M)):
            kill_adb_uiautomator_block_old()
            iconut = 0
            if andebench.ui_operation.watt_operate.watt_flags:
                andebench.ui_operation.watt_operate.stop_watt()
                try:
                    andebench.ui_operation.watt_operate.watt_result_treat(ABS=30)
                except Exception, e:
                    andebench.logout(andebench.my_func_name(), "watt_operate error %s."%e)
                    return False
            break
        iconut += 1
        time.sleep(5)
        kill_adb_uiautomator_block()
    if not iconut == 0:
        andebench.logout(andebench.my_func_name(), "complete is error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if andebench.ui_operation.watt_operate.watt_flags:
            andebench.ui_operation.watt_operate.stop_watt()
        return False

    time.sleep(2)
    andebench.device.screenshot("%s/result.png" % log_dir)
    kill_adb_uiautomator_block()
    app_device = andebench.device(resourceIdMatches='.+/cid$')
    if app_device.exists:
        result = app_device.info
    else:
        return False

    Text = result['text']
    Native = Text.split('\n')

    time.sleep(3)
    AndEMark_Native_result = Native[1].split(':')[-1]
    AndEMark_Java_result = Native[2].split(':')[-1]
    andebench.logout(andebench.my_func_name(), 'AndEMark_Native ='+AndEMark_Native_result)
    andebench.logout(andebench.my_func_name(), 'AndEMark_Java ='+AndEMark_Java_result)

    andebench.ui_operation.click_by_event("HOME")
    kill_adb_uiautomator_block_old()
    system_operation.set_display_orientaion("natural", andebench.log)
    kill_adb_uiautomator_block_old()
    tr.result('AndEBench_Native_result', AndEMark_Native_result, 'score')
    tr.add_attachment(log_dir+"/result.png")
    tr.save()


def clear_all(andebench):
    andebench.kill_app()
    andebench.clear_app_data()
    andebench.ui_operation.click_by_event("HOME")


if __name__ == '__main__':
    app = ["AndEBench", "./test_src/AndEBench.apk"]
    andebench = apptest(sys.argv, app)
    main(andebench)

