#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import json
import re
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult, TestLogger

logger = TestLogger().get_logger("process")
result = []
result_str = ''
app = []

def push_data():
    dmark.logout(dmark.my_func_name(), '...')
    os.system("adb shell rm -rf /sdcard/3DMark/packages")
    time.sleep(1)
    logger.debug('mkdir -p /sdcard/3DMark/packages')
    os.system("adb shell mkdir -p /sdcard/3DMark/packages")
    time.sleep(1)
    logger.debug('Push data...')
    os.system("adb push ./test_src/is-android-data-42_0_0.dlc /sdcard/3DMark/packages")
    time.sleep(2)


def run_test(log_dir, tr, timeout = 10):
    dmark.logout(dmark.my_func_name(), '...')
    dmark.launch_app()
    time.sleep(1)
    push_data()
    kill_adb_uiautomator_block()
    if dmark.ui_operation.wait_for_root_page(decription_text="Welcome") == False:
        return False
    time.sleep(5)
    kill_adb_uiautomator_block()

    dmark.ui_operation.click_ui_button_by_resourceIdMatches("explanationButton", not_id=True)
    dmark.ui_operation.click_ui_button_by_description("Retry")
    dmark.ui_operation.click_ui_button_by_description("Installed", timeout=300)
    dmark.ui_operation.click_ui_button_by_description("javascript:void(0)", timeout=20)
    time.sleep(5)
    dmark.ui_operation.click_ui_button_by_description(descriptioncon='Run', index_nu="1", timeout=20)

    ######### tr.start_watt()

    if dmark.ui_operation.wait_for_complete("devicelistdetailsview",timeout=1800) == False:
        return False
    time.sleep(2)
    kill_adb_uiautomator_block()
    dmark.device.screenshot("%sresult.png"%log_dir)
    try:
        ts, pt, ps, gs, gt1, gt2 = collect_result()
    except Exception,e:
        dmark.logout(dmark.my_func_name(), 'get data failse %s' % e)
        return False
    dmark.kill_app()
    dmark.logout(dmark.my_func_name(), "%s test finshed..." % app[0])
    time.sleep(5)
    if ts == '':
        dmark.logout(dmark.my_func_name(), "Error, NO result found......")
        return False
    else:
        dmark.logout(dmark.my_func_name(), '3DMark total_score is %s' % ts)
        dmark.logout(dmark.my_func_name(), '3DMark physics_test is %s' % pt)
        dmark.logout(dmark.my_func_name(), '3DMark physics_score is %s' % ps)
        dmark.logout(dmark.my_func_name(), '3DMark graphics_score is %s' % gs)
        dmark.logout(dmark.my_func_name(), '3DMark graphics_test1 is %s' % gt1)
        dmark.logout(dmark.my_func_name(), '3DMark graphics_test2 is %s' % gt2)
        return ts, pt, ps, gs, gt1, gt2

def collect_result():
    try:
        dmark.logout(dmark.my_func_name(), '...')
        kill_adb_uiautomator_block()
        total_score = dmark.device(description="Score").right(className="android.view.View").info['contentDescription']
        kill_adb_uiautomator_block()
        physics_test = dmark.device(index="11").info['contentDescription']
        kill_adb_uiautomator_block()
        physics_score = dmark.device(index="5", instance=0).info['contentDescription']
        kill_adb_uiautomator_block()
        graphics_score = dmark.device(index="3", instance=3).info['contentDescription']
        kill_adb_uiautomator_block()
        graphics_test1 = dmark.device(index="7", instance=0).info['contentDescription']
        kill_adb_uiautomator_block()
        graphics_test2 = dmark.device(index="9").info['contentDescription']
        ts = re.sub("[(\-) ]", "", total_score)
        pt = re.sub("[(\-) FPS]", "", physics_test)
        ps = re.sub("[(\-) ]", "", physics_score)
        gs = re.sub("[(\-) ]", "", graphics_score)
        gt1 = re.sub("[(\-) FPS]", "", graphics_test1)
        gt2 = re.sub("[(\-) FPS]", "", graphics_test2)
        return ts, pt, ps, gs, gt1, gt2
    except Exception, e:
        dmark.logout(dmark.my_func_name(), 'get data failse %s' % e)
        return False


def main(tr):
    kill_adb_uiautomator_block_old()
    if dmark.command_timeout("adb wait-for-device",timeout=10):
        os.system("adb root")
        time.sleep(1)
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_airplane('1')
            system_operation.turn_bluetooth_p('0')
            system_operation.turn_wifi('0')
            system_operation.turn_gps('0')
            system_operation.set_display_time()
        except Exception, e:
            dmark.logout(dmark.my_func_name(), 'preload failse %s'%e)
            return False
        time.sleep(2)

        log_dir = os.path.join(tr.result_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        results = run_test(log_dir, tr)
        if not results:
            return False


        d_result = {
            'total_score': results[0],
            'physics_test': results[1],
            'physics_score': results[2],
            'graphics_score': results[3],
            'graphics_test1': results[4],
            'g raphics_test2': results[5]
        }
        rj = open("%sresult.json" % log_dir, 'w+')
        cpu_watt = dmark.ui_operation.watt_operate.get_watt_average()
        if not cpu_watt == False:
            d_result['cpu_watt'] = cpu_watt
        rj.write(json.dumps(d_result))
        rj.close()
    else:
        dmark.logout(dmark.my_func_name(), "Timeout to wait for device,device is disconnect.")
        raise Exception("Device is  disconnect...")
    for key, velue in results.items():
        tr.sub_score(key, velue)
    tr.result(results[0])
    tr.add_attachment(log_dir+"result.json")
    tr.add_attachment(log_dir+"result.png")
    tr.save()
    return True


if __name__ == "__main__":
    tr = TestResult()
    if not os.path.exists(tr.result_dir):
        os.mkdir(tr.result_dir)
    app = ["futuremark", "./test_src/3dmarkandroid-v1.3.1375.apk"]
    args = [tr.result_dir, tr.loop_index]
    dmark = apptest(args, app)
    icount = 0
    ilimite = 2
    while not main(tr):
        if icount > ilimite:
            break
        icount += 1
