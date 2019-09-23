#!/usr/bin/env python
# coding=utf-8
import os
import time
import json
import xml
import re
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult
import sys
import os
reload(sys)
sys.setdefaultencoding('utf8')

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


def run_test(antutu, antutu3d, tr):
    build_info = os.popen('adb shell getprop |grep system.build.fingerprint').read()
    build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)
    antutu.logout(antutu.my_func_name(), '...')
    antutu.app_install()
    antutu3d.app_install()
    antutu3d.kill_app()
    antutu.kill_app()
    antutu3d.clear_app_data()
    antutu.clear_app_data()
    time.sleep(1)
    antutu.launch_app()
    if build_version and build_version[0] == '10':
        antutu.ui_operation.click_ui_button_by_text("ALLOW", skip_utiliy=True)
        time.sleep(2)
        print " 1____....."
        antutu.ui_operation.click_ui_button_by_text("ALLOW", skip_utiliy=True)
        time.sleep(2)
        print "111"
        antutu.ui_operation.click_ui_button_by_text("ALLOW ALL THE TIME", skip_utiliy=True)
        time.sleep(2)
        print "2......."
        antutu.ui_operation.click_ui_button_by_text("ALLOW", skip_utiliy=True)
        time.sleep(2)
        print "3...."
   # antutu.ui_operation.wait_for_root_page('fl_bg')
    time.sleep(3)
    os.system("adb shell input tap 957.5 309")
    time.sleep(2)
    print "click test....."
   # kill_adb_uiautomator_block()
   # antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text')
   # time.sleep(3)
   # antutu.ui_operation.click_ui_button_by_text("CONTINUE", skip_utiliy=True)
    time.sleep(2)
   # antutu.ui_operation.click_ui_button_by_text("OK", skip_utiliy=True)
    run_watcher(antutu)
    time.sleep(3)
    if antutu.device.watcher('permissions').triggered:
        enable_permissions(antutu, antutu3d)
       # antutu.ui_operation.wait_for_root_page('fl_bg')
        os.system("adb shell input tap 957.5 309")
       # kill_adb_uiautomator_block()
       # antutu.ui_operation.click_ui_button_by_resourceIdMatches('start_test_text')
    if antutu3d.ui_operation.wait_for_complete('tv_score') or antutu.ui_operation.wait_for_complete('tv_score'):
        time.sleep(2)
        try:
            lines = antutu.device.dump()
            with open("score_antutu.xml", 'wb+') as fp:
                fp.write(lines)
        except Exception, e:
            antutu.logout(antutu.my_func_name(), "test error %s" % e)
            return False
        time.sleep(2)
        antutu.device.screenshot("%s/result.png" % tr.result_dir)
        result_dict = parse_xml_data("score_antutu.xml", antutu)
        for key, velue in result_dict.items():
            tr.sub_score(key, velue)
        antutu.kill_app()
        antutu.logout(antutu.my_func_name(), "%s test finished..." % app[0])
        time.sleep(5)
        if result_dict["total_score"] == "":
            antutu.logout(antutu.my_func_name(), "Error, NO result found......")
            return False
        else:
            return result_dict
    else:
        antutu.logout(antutu.my_func_name(), antutu.app_name+" Exception error: can't complete, Please check !!!!!!!")
        return False


def parse_xml_data(file_path, antutu):
    root = xml.dom.minidom.parse(file_path).documentElement
    if root.hasAttribute("rotation"):
        antutu.logout(antutu.my_func_name(), "Root element : %s" % root.getAttribute("rotation"))
    score = {}
    nodes = root.getElementsByTagName("node")
    for node in nodes:
        if node.getAttribute("text") == "AOSP on Intel Platform":
            total_score = nodes[nodes.index(node)+1].getAttribute("text")
            if total_score != "":
                antutu.logout(antutu.my_func_name(), "Total Score is:" + total_score)
                score["total_score"] = total_score
            continue

        if node.getAttribute("text") == "AOSP on broxton Platform":
            total_score = nodes[nodes.index(node)+1].getAttribute("text")
            if total_score != "":
                antutu.logout(antutu.my_func_name(), "Total Score is:" + total_score)
                score["total_score"] = total_score
            continue

        if node.getAttribute("text") == "3D":
            print node.getAttribute("text")
            d_score = nodes[nodes.index(node)+2].getAttribute("text")
            if d_score != "":
                antutu.logout(antutu.my_func_name(), "3D Score is:" + d_score)
                score["d_score"] = d_score
            continue

        if node.getAttribute("text") == "UX":
            ux_score = nodes[nodes.index(node)+2].getAttribute("text")
            if ux_score != "":
                antutu.logout(antutu.my_func_name(), "UX Score is:" + ux_score)
                score["ux_score"] = ux_score
            continue

        if node.getAttribute("text") == "CPU":
            cpu_score = nodes[nodes.index(node)+2].getAttribute("text")
            if cpu_score != "":
                antutu.logout(antutu.my_func_name(), "CPU Score is:" + cpu_score)
                score["cpu_score"] = cpu_score
            continue

        if node.getAttribute("text") == "RAM":
            ram_score = nodes[nodes.index(node)+2].getAttribute("text")
            if ram_score != "":
                antutu.logout(antutu.my_func_name(), "RAM Score is:" + ram_score)
                score["ram_score"] = ram_score
            continue
    return score


def main(antutu, antutu3d, tr):
    kill_adb_uiautomator_block()
    if antutu.command_timeout("adb wait-for-device", timeout=10):
        os.system("adb root")
        antutu.check_system_app_package("com.antutu.ABenchMark")
        system_operation.screen_on()
        time.sleep(1)
        system_operation.turn_bluetooth('0')
        system_operation.turn_wifi('0')
        time.sleep(2)

        results = run_test(antutu, antutu3d, tr)
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
        return False

    tr.result(results["total_score"])
    tr.add_attachment(tr.result_dir+"/result.json")
    tr.add_attachment(tr.result_dir+"/result.png")
    tr.save()
    clean_app(antutu, antutu3d)
    return True


if __name__ == "__main__":
    tr = TestResult()
    app1 = ["Antutu3D", "./test_src/antutu_benchmark_v7_3d.apk"]
    app = ["Antutu", "./test_src/antutu-benchmark-v731.apk"]
    if not os.path.exists(tr.result_dir):
        os.mkdir(tr.result_dir)
    args = [tr.result_dir, tr.loop_index]
    antutu3d = apptest(args, app1)
    antutu = apptest(args, app)
    for i in range(3):
        if main(antutu, antutu3d, tr):
            break
        utiliy.hard_reboot()
    antutu.logout(antutu.my_func_name(), "antutu_7_3 test complate! " + ("<success>" if i < 2 else "<failed>"))
    exit(0 if i < 2 else 1)
