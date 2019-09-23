#!/usr/bin/env python
# coding=utf-8
import os
import time
import json
import zipfile
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


def clean_app(antutu):
    kill_adb_uiautomator_block_old()


def enable_permissions(antutu):
    kill_adb_uiautomator_block_old()
    antutu.logout(antutu.my_func_name(), '...')
    back_times = 0
    if antutu.ui_operation.wait_for_open_spacial_function('Enable 64-bit', timeout=10):
        time.sleep(1)
        antutu.ui_operation.click_ui_button_by_resourceIdMatches("btn_ok")
        back_times += 1
    if antutu.ui_operation.wait_for_open_spacial_function('AnTuTu Benchmark', timeout=10):
        time.sleep(1)
        antutu.ui_operation.click_ui_button_by_resourceIdMatches("button1", package='antutu')
    if antutu.ui_operation.wait_for_open_spacial_function('Install unknown apps', timeout=10):
        back_times += 1
        time.sleep(1)
        antutu.ui_operation.click_ui_button_by_resourceIdMatches("switch_widget", package='antutu')
        time.sleep(2)
        antutu.ui_operation.click_by_event("BACK")
        back_times -= 1
    if antutu.ui_operation.wait_for_open_spacial_function('AnTuTu Benchmark 64-bit', timeout=10):
        print "find -- AnTuTu Benchmark 64-bit"
        time.sleep(2)
        antutu.ui_operation.click(1872, 933)  # click(ok_button)
        time.sleep(3)
    if antutu.ui_operation.wait_for_open_spacial_function('App insttalled', timeout=10):
        print "find -- App insttalled"
        time.sleep(2)
        antutu.ui_operation.click(1816, 933)  # click(done_button)
        time.sleep(3)

    kill_adb_uiautomator_block_old()
    for i in range(back_times):
        antutu.ui_operation.click_by_event("BACK")
        kill_adb_uiautomator_block_old()


def run_test(antutu, tr):
    antutu.logout(antutu.my_func_name(), '...')
    result_dict = {}
    antutu.app_install()
    antutu.kill_app()
    time.sleep(1)
    antutu.launch_app()
    enable_permissions(antutu)
    if not antutu.ui_operation.wait_for_root_page('start_test_text'):
        return False
    kill_adb_uiautomator_block_old()

    if not antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text', timeout=10, package='antutu'):
        return False
    time.sleep(3)

    if antutu.ui_operation.wait_for_complete('detail_btn', timeout=1800, package='antutu'):
        try:
            result_dict_ex = collect_result_ex(antutu, tr)
            antutu.logout(antutu.my_func_name(), str(result_dict_ex))
            for key, velue in result_dict_ex.items():
                tr.sub_score(key, velue)
            result_dict.update(result_dict_ex)
            antutu.device.screenshot("%s/result.png" % tr.result_dir)
        except Exception, e:
            antutu.logout('ERROR', 'get result total is fail,error :%s' % e)
            return False
        time.sleep(2)
        antutu.ui_operation.click_ui_button_by_resourceIdMatches("detail_btn", package='antutu')
        if antutu.ui_operation.wait_for_open_spacial_function('Details - v5.6', timeout=100):
            kill_adb_uiautomator_block_old()
            antutu.device.screenshot("%s/result.png" % tr.result_dir)

        antutu.kill_app()
        antutu.logout(antutu.my_func_name(), "%s test finished..." % app[0])
        time.sleep(5)
        if result_dict["total_score"] == "":
            antutu.logout(antutu.my_func_name(), "Error, NO result found......")
            return False
        else:
            antutu.logout(antutu.my_func_name(), 'Antutu total_score is %s' % result_dict["total_score"])
            for item in result_dict.keys():
                if not "total_score" == item:
                    antutu.logout(antutu.my_func_name(), 'Antutu %s is %s' % (item, result_dict[item]))
            return result_dict

    else:
        antutu.logout(antutu.my_func_name(), antutu.app_name+" Exception error: can't complete, Please check !!!!!!!")
        return False


def collect_result_ex(antutu, tr):
    result_dict = {}
    output_log = os.path.join(tr.result_dir, 'antutu.txt')
    allresult = 'adb logcat -d | grep -i antutubenchmarkscore >'+output_log
    os.system(allresult)

    try:
        with open(output_log) as fpout:
            result = fpout.readlines()
        if len(result) > 2:
            for line in result:
                for key, item in logcat_score_id_dict.items():
                    if item in line:
                        value = line.strip().split(":")[-1]
                        if len(value) > 0:
                            result_dict[key] = value
        antutu.logout(antutu.my_func_name(), 'antutu result is :%s' % result_dict.items())
    except Exception, e:
        antutu.logout(antutu.my_func_name(), 'get antutu test result error :%s' % e)
    return result_dict


def main(antutu, tr):
    kill_adb_uiautomator_block()
    if antutu.command_timeout("adb wait-for-device", timeout=10):
        antutu.check_system_app_package("antutu")
        time.sleep(3)
        os.system("adb root")
        system_operation.screen_on()
        time.sleep(2)

        results = run_test(antutu, tr)
        if not results:
            antutu.logout(antutu.my_func_name(), "Error, run test result get error......")
            return False
        if len(results['total_score']) == 0:
            antutu.logout(antutu.my_func_name(), "Error, run test result get total score error......")
            return False
        rj = open("%s/result.json" % tr.result_dir, 'w+')
        rj.write(json.dumps(results))
        rj.close()

    else:
        antutu.logout(antutu.my_func_name(), "Timeout to wait for device,device is disconnect.")
        raise Exception("Device is disconnect...")
        return False

    tr.result(results['total_score'])
    tr.add_attachment(os.path.join(tr.result_dir, 'antutu.txt'), 'antutu.txt')
    tr.add_attachment(os.path.join(tr.result_dir, "result.png"))
    for file in os.listdir(tr.result_dir):
        if not file.endswith('.zip'):
            target_file = file+'.zip'
            f = zipfile.ZipFile(os.path.join(tr.result_dir, target_file), 'w', zipfile.ZIP_DEFLATED)
            f.write(os.path.join(tr.result_dir, file), file)
            f.close()
            tr.add_attachment(os.path.join(tr.result_dir, target_file))
    tr.save()
    return True


if __name__ == "__main__":
    logcat_score_id_dict = {
        "Multitask": "multitask :",
        "Runtime": "ue_dalvik_text :",
        "CPU integer": "integer :",
        "CPU float-point": "float :",
        "Single-thread integer": "integersingle :",
        "Single-thread float-point": "floatsingle :",
        "RAM Operation": "memory :",
        "RAM Speed": "ram :",
        "2D graphics": "2d :",
        "3D graphics": "3d :",
        "Storage I/O": "storage :",
        "Database I/O": "database :",
        "total_score": "score :"
    }
    tr = TestResult()
    app = [tr.case_name, tr.case_info["apk"]]
    if not os.path.exists(tr.result_dir):
        os.mkdir(tr.result_dir)
    args = [tr.result_dir, tr.loop_index]
    antutu = apptest(args, app)
    for i in range(3):
        if main(antutu, tr):
            break
        utiliy.hard_reboot()
    antutu.logout(antutu.my_func_name(), "antutu5.6 test complate! " + ("<success>" if i < 2 else "<failed>"))
    exit(0 if i < 2 else 1)