#!/usr/bin/env python
# coding=utf-8
import os
import time
import re
import json
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


testlist_dict = {
    "\"test13\"": "\"DROP TABLE\"",
    "\"test12\"": "\"DELETE with an index\"",
    "\"test11\"": "\"DELETE without an index\"",
    "\"test10\"": "\"INSERTs from a SELECT\"",
    "\"test1\"": "\"1000 INSERTs\"",
    "\"test4\"": "\"100 SELECTs without an index\"",
    "\"test5\"": "\"100 SELECTs on a string comparison\"",
    "\"test2\"": "\"25000 INSERTs in a transaction\"",
    "\"test3\"": "\"25000 INSERTs into an indexed table in a transaction\"",
    "\"test8\"": "\"1000 UPDATEs without an index\"",
    "\"test9\"": "\"25000 UPDATEs with an index\"",
    "\"test6\"": "\"Creating an index\"",
    "\"test7\"": "\"5000 SELECTs with an index\"",
}


def clean_app(rl):
    rl.kill_app()
    rl.clear_app_data()
    kill_adb_uiautomator_block_old()


def run_test(log_dir, rl):
    build_info = os.popen('adb shell getprop |grep system.build.fingerprint').read()
    build_version = re.findall('gordon_peak:([A-Za-z])/',build_info)
    clean_app(rl)
    rl.logout(rl.my_func_name(), '...')
    rl.launch_app()
    time.sleep(2)
    rl.ui_operation.click_ui_button_by_text("OK", skip_utiliy=True)
    time.sleep(1)
    
    if rl.ui_operation.wait_for_open_spacial_function('RL Benchmark: SQLite', timeout=10):
        rl.ui_operation.click(852, 606)
        # rl.ui_operation.click_ui_button_by_resourceIdMatches("button1")

    rl.ui_operation.wait_for_root_page("app_title")
    rl.logout(rl.my_func_name(), 'Begin testing......')
    time.sleep(1)
    if not rl.ui_operation.click_ui_button_by_text('Start'):
        return False
    if not rl.ui_operation.wait_for_complete("time", timeout=60):
        return False
    time.sleep(2)
    kill_adb_uiautomator_block_old()
    result = collect_result(log_dir, rl)

    rl.device.screenshot("%s/result.png" % log_dir)
    rl.logout(rl.my_func_name(), "%s test finshed..." % rl.app_name)
    clean_app(rl)
    time.sleep(5)
    kill_adb_uiautomator_block()

    if not result:
        rl.logout(rl.my_func_name(), "Error, NO result found......")
        return False
    else:
        return result


def rewrite_rlbenchmark(rl, file_path):
    line = ''
    try:
        with open(file_path) as fp:
            line = fp.read()
            for key,item in testlist_dict.items():
                if key in line:
                    line = line.replace(key, item)
            fp.close()
        with open(file_path, 'w+') as fpw:
            fpw.write(line)
            fpw.close()
    except Exception,e:
        rl.logout(rl.my_func_name(), "open %s is failed" % e)
        return False


def get_raw_data_list(rl, filepath):
    lines = []
    try:
        with open(filepath) as fpr:
            lines_raw = fpr.readlines()
            for line in lines_raw:
                if "name=" in line and "value=" in line and not "finish_time" in line:
                    line = line.replace("overall", "total Result")
                    lines.append(line)
    except Exception,e:
        rl.logout(rl.my_func_name(), "open error: %s"%e)
    return lines


def get_data_from_list(lines):
    dict_result = {}
    for line in lines:
        sobj = re.search(r'name=\"(?P<key>.+)\".+value=\"(?P<value>.+)\"', line, re.I)
        if sobj:
            dict_result[sobj.group("key")] = sobj.group("value")
    return dict_result


def collect_result(log_dir, rl):
    rl.logout(rl.my_func_name(), '...')
    os.system("adb root")
    time.sleep(1)
    rlbenchmark_file = os.path.join(log_dir, 'rlbenchmark.txt')
    alltext = 'adb shell cat /data/user/10/com.redlicense.benchmark.sqlite/shared_prefs/rlbenchmark.xml >'+rlbenchmark_file
    os.system(alltext)
    rewrite_rlbenchmark(rl, rlbenchmark_file)
    lines = get_raw_data_list(rl, rlbenchmark_file)
    if lines.__len__()>0:
        result_dic = get_data_from_list(lines)
    if len(result_dic) > 0:
        for key, value in result_dic.items():
            result_dic[key] = float(value)/1000
        rl.logout(rl.my_func_name(), "Result dict: "+str(result_dic))
        return result_dic
    else:
        return False


def main(rl, tr):

    rl.logout(rl.my_func_name(), '...')
    kill_adb_uiautomator_block()

    try:
        system_operation.turn_bluetooth('0')
        system_operation.turn_wifi('0')
    except Exception, e:
        rl.logout(rl.my_func_name(), "Setup Failure. %s" % e)
        return False
    result = run_test(log_dir, rl)
    if not result:
        clean_app(rl)
        return False
    else:
        rj = open("%s/result.json" % log_dir, 'w+')
        rj.write(json.dumps(result))
        rj.close()
    for key, value in result.items():
        tr.sub_score(key, value)
    tr.result(result['total Result'])
    tr.add_attachment(os.path.join(tr.result_dir, "result.json"))
    tr.save()
    return True


if __name__ == "__main__":
    tr = TestResult()
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    args = [log_dir, tr.loop_index]
    app = [tr.case_name, tr.case_info["apk"]]
    rl = apptest(args, app)
    for i in range(3):
        if main(rl, tr):
            break
        utiliy.hard_reboot()
    rl.logout(rl.my_func_name(), tr.case_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))
    exit(0 if i < 2 else 1)
