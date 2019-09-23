#!/usr/bin/env python
# coding=utf-8
import os
import re
import json
import time
import zipfile
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult, Device


class Gfx:
    def __init__(self, tr):
        self.app_name = tr.case_name
        self.app_path = tr.case_info["apk"]
        self.item_text = tr.case_info["itemtext"]
        self.pre_cmd = tr.case_info["pre_cmd"] if 'pre_cmd' in tr.case_info else ''
        self.result = ''
        self.result_dir = tr.result_dir
        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        self.app = [self.app_name, self.app_path]
        self.tr_name = tr.case_name
        self.data = ''
        self.mobile_test = apptest([self.result_dir, tr.loop_index], self.app)
        for i in range(3):
            if self.main():
                break
            utiliy.hard_reboot()
        self.mobile_test.logout(self.mobile_test.my_func_name(), self.app_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))
        self.returncode = 0 if i < 2 else 1

    def clear_data(self):
        self.mobile_test.kill_app()
        time.sleep(1)
        self.mobile_test.clear_app_data()
        time.sleep(2)

    def click_test_selection(self):
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text("OK")
        time.sleep(2)
        self.mobile_test.ui_operation.wait_for_root_page("main_circleControl")
        self.mobile_test.logout(self.mobile_test.my_func_name(), '...')
        self.mobile_test.device.click(1047, 673)

    def swipe_item_down(self):
        display_h = self.mobile_test.device.info['displayHeight']
        display_w = self.mobile_test.device.info['displayWidth']
        icon_sx = display_w * 58 / 100
        icon_sy = display_h * 70 / 100
        icon_ex = display_w * 58 / 100
        icon_ey = display_h * 30 / 100
        self.mobile_test.device.swipe(icon_sx, icon_sy, icon_ex, icon_ey)

    def swipe_item_up(self):
        display_h = self.mobile_test.device.info['displayHeight']
        display_w = self.mobile_test.device.info['displayWidth']
        icon_sx = display_w * 58 / 100
        icon_sy = display_h * 50 / 100
        icon_ex = display_w * 58 / 100
        icon_ey = display_h * 80 / 100
        self.mobile_test.device.swipe(icon_sx, icon_sy, icon_ex, icon_ey)

    def prepare_for_selection(self, timeout=5):
        icount = 0
        kill_adb_uiautomator_block()
        while icount < timeout:
            app_dev = self.mobile_test.device(text='High-Level Tests')
            if app_dev.exists:
                right_dev = app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
                if right_dev.exists:
                    d = right_dev.checked
                    if d:
                        right_dev.click()
                        icount = 0
                        self.swipe_item_down()

            app_dev = self.mobile_test.device(text='Low-Level Tests')
            if app_dev.exists:
                right_dev = app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
                if right_dev.exists:
                    d = right_dev.checked
                    if d:
                        right_dev.click()
                        icount = 0
                        self.swipe_item_down()
            else:
                self.swipe_item_down()

            app_dev = self.mobile_test.device(text='Special Tests')
            if app_dev.exists:
                right_dev = app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
                if right_dev.exists:
                    d = right_dev.checked
                    if d:
                        right_dev.click()
                        icount = 0
                        self.swipe_item_down()
            else:
                self.swipe_item_down()
            app_dev = self.mobile_test.device(text='Battery Test')
            if app_dev.exists:
                right_dev = app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
                if right_dev.exists:
                    d = right_dev.checked
                    if d:
                        right_dev.click()
                        icount = 0
                        self.swipe_item_down()
            else:
                self.swipe_item_down()
            app_dev = self.mobile_test.device(text='Fixed Time Test')
            if app_dev.exists:
                right_dev = app_dev.right(resourceIdMatches='.+/updated_test_select_item_group_checkbox')
                if right_dev.exists:
                    d = right_dev.checked
                    if d:
                        right_dev.click()
                        icount = 0
            time.sleep(1)
            icount += 1

            kill_adb_uiautomator_block()
        if icount > 0:
            return False
        else:
            return True

    def select_item(self, timeout=5):
        self.mobile_test.logout(self.mobile_test.my_func_name(), '...')
        kill_adb_uiautomator_block()
        texts = self.item_text.split('#')
        if len(texts) > 1:
            item_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text=texts[0]).sibling(textContains=texts[1])
        else:
            item_dev = self.mobile_test.device(className="android.widget.LinearLayout").child(text=texts[0])

        if item_dev.exists:
            item_dev.click()
            return True
        else:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "select_item failed.....")
            return False

    def run_test(self):
        build_info = os.popen('adb shell getprop |grep system.build.fingerprint').read()
        build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)
#        self.mobile_test.launch_app()
#        time.sleep(3)
#        kill_adb_uiautomator_block()
#        time.sleep(2)
#        if build_version and build_version[0] == '10':
#            self.mobile_test.ui_operation.click_ui_button_by_text("CONTINUE", skip_utiliy=True)
#            time.sleep(2)
#            self.mobile_test.ui_operation.click_ui_button_by_text("OK", skip_utiliy=True)
#            time.sleep(2)
#        self.mobile_test.ui_operation.click_ui_button_by_text("OK")
#        time.sleep(2)
#        self.mobile_test.kill_app()
#        #self.mobile_test.device.click(1110, 730)
#        time.sleep(3)
#        print " clear data........."

        if self.pre_cmd:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "execute the pre cmd: " + self.pre_cmd)
            os.system(os.path.join(os.path.dirname(__file__), "util", self.pre_cmd))
        self.mobile_test.kill_app()
        time.sleep(3)
        self.mobile_test.launch_app()
        time.sleep(3)
        kill_adb_uiautomator_block()
        time.sleep(5)
        if build_version and build_version[0] == '10':
            self.mobile_test.ui_operation.click_ui_button_by_text("CONTINUE", skip_utiliy=True)
            time.sleep(2)
            kill_adb_uiautomator_block()
            print " continue......."
            self.mobile_test.ui_operation.click_ui_button_by_text("OK", skip_utiliy=True)
            time.sleep(3)
            print "11111111okokok......"
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_text("OK")
            time.sleep(3)
            print "2222222222okokokok....."
            self.mobile_test.ui_operation.wait_for_root_page("main_circleControl")
            time.sleep(5)
            self.mobile_test.device.click(1110, 730)
        else:
            self.click_test_selection()
            kill_adb_uiautomator_block()
        time.sleep(1)
        self.prepare_for_selection()
        time.sleep(1)
        for i in range(10):
            self.swipe_item_up()
        time.sleep(2)
        if not self.select_item():
            self.mobile_test.logout(self.mobile_test.my_func_name(), "start Run test is failed.....")
            kill_adb_uiautomator_block()
            return False
        time.sleep(2)
        self.mobile_test.logout(self.mobile_test.my_func_name(), "Run test.....")
        kill_adb_uiautomator_block()
        # self.mobile_test.ui_operation.click_ui_button_by_text("Start")  # p can find 'Start', but can't click
        self.mobile_test.ui_operation.click(300, 525)
        time.sleep(2)
        try:
            self.mobile_test.ui_operation.wait_for_complete("results_testList", timeout=600)
            time.sleep(2)
            kill_adb_uiautomator_block()
            self.mobile_test.device.screenshot("%s/result.png" % self.result_dir)
        except Exception:
            time.sleep(10)
            self.run_test()
        result = self.collect_result()
        if not result:
            return False
        self.mobile_test.logout(self.mobile_test.my_func_name(), "%s test finished..." % self.app_name)
        kill_adb_uiautomator_block()
        time.sleep(2)
        self.clear_data()
        return result

    def collect_result(self):
        try:
            result = ""
            kill_adb_uiautomator_block()
            fps_score = self.mobile_test.ui_operation.get_score_info_data("updated_result_item_subresult", 'text', "1")
            kill_adb_uiautomator_block()
            result = re.sub("[()\xc2\xa0Fps]", "", fps_score)
           # result_basepath = "/storage/self/primary/Android/data/{pkg_name}/files/results/".format(pkg_name=self.mobile_test.app_package)
            #result_path = os.popen("adb shell ls {dir}".format(dir=result_basepath)).readlines()
           # if len(result_path) > 0:
            #    result_file = os.popen("adb shell ls {path}".format(path=os.path.join(result_basepath, result_path[-1]))).readlines()
            #    if len(result_file) > 0:
             #       result_str = os.popen("adb shell cat {file}".format(file=os.path.join(result_basepath, result_path[-1].strip(), result_file[-1]))).read()
              #      result_obj = json.loads(result_str)
              #      result = "%.2f" % result_obj["results"][0]["gfx_result"]["fps"] if result_obj["results"][0]["gfx_result"]["fps"] > 1 else ""
            if result == "":
                return False
            return result
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "get result failed: " + e.message)
            return False

    def main(self):
        kill_adb_uiautomator_block()
        self.mobile_test.check_system_app_package("glbenchmark27.corporate")
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
        except Exception:
            return False
        time.sleep(2)

        result = self.run_test()
        if not result:
            return False

        self.mobile_test.logout(self.mobile_test.my_func_name(), "Test result is : %s" % result)
        self.result = result
        self.mobile_test.app_uninstall()
        return True


if __name__ == "__main__":
    tr = TestResult()
    gfx_Man = Gfx(tr)

    for f in os.listdir(gfx_Man.result_dir):
        if not f.endswith('.zip'):
            target_file = f + '.zip'
            zipf = zipfile.ZipFile(os.path.join(gfx_Man.result_dir, target_file), 'w', zipfile.ZIP_DEFLATED)
            zipf.write(os.path.join(gfx_Man.result_dir, f), f)
            zipf.close()
            tr.add_attachment(os.path.join(gfx_Man.result_dir, target_file))
    tr.result(gfx_Man.result)
    tr.save()
    exit(gfx_Man.returncode)
