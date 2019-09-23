#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from xml.dom.minidom import parse
import xml.dom.minidom
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_uiautomator
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult

result = []
result_str = ''
app = []


def clear_all(geek):
    geek.logout(geek.my_func_name(), ">>>>>>>>Clear recent apps......")
    time.sleep(1)
    geek.kill_app()
    geek.clear_app_data()


def parse_xml_data(file_path, geek):
    DOMTree = xml.dom.minidom.parse(file_path)
    all_file = DOMTree.documentElement
    if all_file.hasAttribute("rotation"):
        geek.logout(geek.my_func_name(), "Root element : %s" % all_file.getAttribute("rotation"))
    score = {}
    nodes = all_file.getElementsByTagName("node")
    for node in nodes:
        if node.getAttribute("text") == "Geekbench Score" and node.getAttribute("class") == "android.view.View":
            sscore = nodes[nodes.index(node)+1].getAttribute("text")
            if sscore != "":
                geek.logout(geek.my_func_name(), "Single-Core Score is:" + sscore)
                score["Single-Core"] = sscore

            mscore = nodes[nodes.index(node)+3].getAttribute("text")
            if mscore != "":
                geek.logout(geek.my_func_name(), "Multi-Core Score is:" + mscore)
                score["Multi-Core"] = mscore
    return score


def set_up(geek):
    try:
        system_operation.turn_wifi('0')
        system_operation.turn_bluetooth('0')
    except Exception, e:
        geek.logout(geek.my_func_name(), "set up error %s" % e)
        return False


def run_test(geek, tr):
    clear_all(geek)
    time.sleep(1)
    geek.clear_caches()

    if tr.case_info["arg"] == "version_3":
        geek.launch_app()
        geek.ui_operation.wait_for_root_page("runBenchmarks")
        geek.ui_operation.app_package = "android"
        geek.ui_operation.click_ui_button_by_text("OK")
        geek.ui_operation.app_package = geek.app_package
        time.sleep(1)
        geek.ui_operation.click_ui_button_by_text('Run Benchmarks')
    else:
        system_operation.connect_wifi_manual("shz13f-otcandroidlab-ap01-aosp", "cdexswzaq")
        time.sleep(3)
        geek.launch_app()
        geek.ui_operation.wait_for_root_page("home")
        geek.ui_operation.click_ui_button_by_text("ACCEPT")
        time.sleep(1)
        geek.ui_operation.click_ui_button_by_text("RUN CPU BENCHMARK")
        time.sleep(2)
        geek.ui_operation.click_ui_button_by_text("OK")
    kill_uiautomator()
    ver = os.popen('adb shell getprop ro.build.version.release').read()
    if ver:
        ver = ver.strip()
    if ver == '6.0.1':
        result = geek.ui_operation.wait_for_complete_by_text("Result", timeout=500)
    else:
        result = geek.ui_operation.wait_for_complete_by_text("RESULT", timeout=500)
    time.sleep(5)
    if not result:
        return False
    try:
        lines = geek.device.dump()
        with open("score.xml", 'wb+') as fp:
            fp.write(lines)
    except Exception, e:
        geek.logout(geek.my_func_name(), "test error %s" % e)
        return False
    time.sleep(2)
    geek.device.screenshot("%s/result.png" % tr.result_dir)
    result = parse_xml_data("./score.xml", geek)
    if len(result) == 0:
        os.system("rm ./score.xml")
        return False
    os.system("rm ./score.xml")
    geek.app_uninstall()
    set_up(geek)
    geek.logout(geek.my_func_name(), "Result is: %s" % result["Multi-Core"])
    return result


def main(geek, tr):
    set_up(geek)
    if not os.path.exists(tr.result_dir):
        os.mkdir(tr.result_dir)
    result = run_test(geek, tr)
    if not result:
        return False
    geek.logout(geek.my_func_name(), "Geekbench value is %s" % result["Multi-Core"])
    for key, val in result.items():
        tr.sub_score(key, val)
    tr.result(result["Multi-Core"])
    tr.add_attachment(tr.result_dir+"/result.png")
    tr.save() 
    clear_all(geek)
    return True


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    tr = TestResult()
    app = [tr.case_name, tr.case_info["apk"]]
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    args = [log_dir, tr.loop_index]
    geek = apptest(args, app)
    for i in range(3):
        if main(geek, tr):
            break
        utiliy.hard_reboot()
    geek.logout(geek.my_func_name(), tr.case_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))
    exit(0 if i < 2 else 1)
