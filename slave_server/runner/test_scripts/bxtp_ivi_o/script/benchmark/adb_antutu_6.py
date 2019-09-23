#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import json
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


def clean_app(antutu, antutu3d):
    antutu3d.clear_app_data()
    antutu.clear_app_data()


def run_watcher(antutu):
    antutu.logout(antutu.my_func_name(), '...')
    kill_adb_uiautomator_block_old()
    antutu.device.watcher('permissions').when(resourceIdMatches='.+/alertTitle$', text='No Permissions').click(resourceIdMatches='.+/button1$',text='OK')
    antutu.device.watchers.run()


def enable_permissions(antutu, antutu3d):
    antutu.logout(antutu.my_func_name(), '...')
    kill_adb_uiautomator_block()
    antutu.ui_operation.click_ui_button_by_text('Permissions')
    if antutu.device(resourceId='com.antutu.ABenchMark:id/info').exists:
        antutu.device(resourceId="com.antutu.ABenchMark:id/btn_close").click()
    list_text = ['Camera', 'Location', 'Phone', 'Storage']
    time.sleep(3)
    for item in list_text:
        kill_adb_uiautomator_block()
        if antutu.device(text=item).right(text='OFF').exists:
            kill_adb_uiautomator_block()
            antutu.device(text=item).right(text='OFF').click()
    kill_adb_uiautomator_block_old()
    antutu.ui_operation.click_by_event("BACK")
    kill_adb_uiautomator_block_old()
    antutu.ui_operation.click_by_event("BACK")


def run_test(log_dir, antutu, antutu3d):
    antutu.logout(antutu.my_func_name(),'...')
    antutu.app_install()
    antutu3d.app_install()
    antutu3d.kill_app()
    antutu.kill_app()
    antutu3d.clear_app_data()
    antutu.clear_app_data()
    time.sleep(1)
    antutu.launch_app()
    antutu.ui_operation.wait_for_root_page('fl_bg')
    kill_adb_uiautomator_block()
    antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text')
    time.sleep(3)
    run_watcher(antutu)
    time.sleep(3)
    if antutu.device.watcher('permissions').triggered:
        enable_permissions(antutu, antutu3d)
        antutu.ui_operation.wait_for_root_page('fl_bg')
        kill_adb_uiautomator_block()
        antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text')
    if antutu.ui_operation.wait_for_complete('lv_testedlist'):
        time.sleep(2)
        kill_adb_uiautomator_block()
        antutu.device.screenshot("%s/result.png" % log_dir)
        ts,ms,gs = collect_result(antutu)
        antutu.kill_app()
        antutu.logout(antutu.my_func_name(), "%s test finished..." % app[0])
        time.sleep(5)
        if ts == "":
            antutu.logout(antutu.my_func_name(), "Error, NO result found......")
            return False
        else:
            antutu.logout(antutu.my_func_name(), 'Antutu total_score is %s' % ts)
            antutu.logout(antutu.my_func_name(), 'Antutu marooned_score is %s' % ms)
            antutu.logout(antutu.my_func_name(), 'Antutu garden_score is %s' % gs)
            return ts, ms, gs
    else:
        antutu.logout(antutu.my_func_name(), antutu.app_name+" Exception error: can't complete, Please check !!!!!!!")
        return False


def collect_result(antutu,timeout = 5):
    antutu.logout(antutu.my_func_name(),'...')
    ts = antutu.ui_operation.get_score_info_data('tv_score', 'text', timeout=timeout)
    ms = antutu.ui_operation.get_score_info_data('tv_marooned_score', 'text', timeout=timeout)
    gs = antutu.ui_operation.get_score_info_data('tv_garden_score', 'text', timeout=timeout)
    return ts, ms, gs


def main(antutu, antutu3d):
    tr = TestResult(sys.argv)
    kill_adb_uiautomator_block()
    if antutu.command_timeout("adb wait-for-device", timeout=10):
        os.system("adb root")
        antutu.check_system_app_package("antutu.ABenchMark")
        system_operation.screen_on()
        time.sleep(1)
        system_operation.turn_airplane('1')
        system_operation.turn_bluetooth('0')
        system_operation.turn_wifi('0')
        system_operation.turn_gps('0')
        time.sleep(2)
        log_dir = tr.result_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        results = run_test(log_dir, antutu, antutu3d)
        if not results:
            return False
        if len(results[0]) == 0:
            return False
        else :
            d_result = {'total_score': results[0]}
            if len(results[1]) > 0:
                d_result['marooned_score'] = results[1]
            if len(results[2]) > 0:
                d_result['garden_score'] = results[2]
        rj = open("%sresult.json" % log_dir, 'w+')
        rj.write(json.dumps(d_result))
        rj.close()
    else:
        antutu.logout(antutu.my_func_name(), "Timeout to wait for device,device is disconnect.")
        raise Exception("Device is disconnect...")

    tr.result('Antutu_6_1_4_total_result', results[0], 'score')
    tr.add_attachment(log_dir+"/result.json")
    tr.add_attachment(log_dir+"/result.png")
    tr.save()
    clean_app(antutu, antutu3d)


if __name__ == "__main__":
    app1 = ["Antutu3D", "./src/Antutu3DBenchMark_6.1.1.apk"]
    app = ["Antutu", "./src/AntutuBenchMark_6.1.4.apk"]
    antutu3d = apptest(sys.argv, app1)
    antutu = apptest(sys.argv, app)
    main(antutu, antutu3d)

