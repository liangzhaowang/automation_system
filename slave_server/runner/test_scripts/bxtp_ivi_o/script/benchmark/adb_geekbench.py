#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from xml.dom.minidom import parse
import xml.dom.minidom
from runner.operation_lib.base_lib.exception_operation import kill_uiautomator
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult

result = []
result_str = ''
app = []


def clear_all(geek):
    geek.logout(">>>>>>>>Clear recent apps......")
    time.sleep(1)
    geek.kill_app()
    geek.clear_app_data()


def parse_xml_data(file_path, geek):
    DOMTree = xml.dom.minidom.parse(file_path)
    all_file = DOMTree.documentElement
    if all_file.hasAttribute("rotation"):
        geek.logout("Root element : %s" % all_file.getAttribute("rotation"))
    score = {}
    nodes = all_file.getElementsByTagName("node")
    for node in nodes:
        if "Single-Core Score" in node.getAttribute("content-desc"):
            sindex = nodes.index(node)-1
            sscore = nodes[sindex].getAttribute("content-desc")
            if sscore != "":
                geek.logout("Single-Core Score is:", sscore)
                score["Single-Core"] = sscore

        if "Multi-Core Score" in node.getAttribute("content-desc"):
            mindex = nodes.index(node)-1
            mscore = nodes[mindex].getAttribute("content-desc")
            if mscore != "":
                geek.logout("Multi-Core Score is:", mscore)
                score["Multi-Core"] = mscore
    return score


def set_up(geek):
    try:
        system_operation.turn_gps('0')
        system_operation.turn_wifi('0')
        system_operation.turn_bluetooth('0')
        system_operation.turn_airplane('1')
        system_operation.set_display_time()
    except Exception, e:
        geek.logout(geek.my_func_name(), "set up error %s" % e)
        return False


def run_test(log_dir, geek):
    clear_all(geek)
    time.sleep(1)
    geek.launch_app()
    time.sleep(5)
    geek.ui_operation.click_ui_button_by_text('Run Benchmarks')
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
    except Exception,e:
        geek.logout(geek.my_func_name(), "test error %s" % e)
        return False
    time.sleep(2)
    geek.device.screenshot("%s/result.png" % log_dir)
    result = parse_xml_data("./score.xml", geek)
    if len(result) == 0:
        os.system("rm ./score.xml")
        return False
    os.system("rm ./score.xml")
    geek.logout(geek.my_func_name(), "Result is: %s" % result["Single-Core"])
    return result


def main(geek, tr):
    set_up(geek)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    result = run_test(log_dir, geek)
    if not result:
        return False
    geek.logout( geek.my_func_name(), "Geekbench value is %s" % result["Single-Core"])
    for key,val in result.items():
        tr.sub_score(key, val)
    tr.result(result["Single-Core"])
    tr.add_attachment(log_dir+"/result.png")
    tr.save() 
    clear_all(geek)
    return True


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    tr = TestResult()
    app=["Geekbench", "./test_src/Geekbench-3.3.1-Android.apk"]
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    args = [log_dir, tr.loop_index]
    geek = apptest(args, app)
    icount = 0
    ilimite = 2
    while not main(geek, tr):
        if icount > ilimite:
            break
        icount += 1
