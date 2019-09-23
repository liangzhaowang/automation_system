#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


class Glbench:
    def __init__(self, tr, app_name, app_path, test_text):
        self.app_name = app_name
        self.app_path = app_path
        self.app = [self.app_name, self.app_path]
        self.data = ''
        self.test_text = test_text
        self.mobile_test = apptest(sys.argv, self.app)

        for i in range(3):
            if self.main(tr):
                break
            utiliy.hard_reboot()
        self.mobile_test.logout(self.mobile_test.my_func_name(), self.app_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))
        exit(0 if i < 2 else 1)

    def check_corporate(self):
        kill_adb_uiautomator_block()
        time.sleep(2)
        os.system("adb root")
        time.sleep(2)
        self.mobile_test.check_system_app_package("glbenchmark27.corporate")

    def clear_data(self):
        self.mobile_test.kill_app()
        time.sleep(1)
        self.mobile_test.clear_app_data()
        time.sleep(2)

    def run_test(self, log_dir):
        self.clear_data()
        self.mobile_test.logout(self.mobile_test.my_func_name(), '...')
        time.sleep(1)
        self.mobile_test.launch_app()
        time.sleep(2)
        self.mobile_test.ui_operation.wait_for_root_page("listView1")
        time.sleep(2)
        kill_adb_uiautomator_block()
        self.mobile_test.ui_operation.click_ui_button_by_text("Performance Tests")
        time.sleep(1)
        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Select test item...')
        kill_adb_uiautomator_block()
        time.sleep(1)
        try:
            self.mobile_test.device(scrollable=True).scroll.to(text=self.test_text)
            kill_adb_uiautomator_block()
            self.mobile_test.device(text=self.test_text).right(className="android.widget.CheckBox").click.wait()
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "scroll click error: %s " % e)
            return False
        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Begin testing......')
        time.sleep(1)
        kill_adb_uiautomator_block()
        self.mobile_test.ui_operation.click_ui_button_by_text("Start")
        # self.tr.start_watt() #start watt
        time.sleep(10)
        self.mobile_test.ui_operation.wait_for_complete("listViewResults")
        time.sleep(1)
        result = self.collect_result()
        if result:
            self.clear_data()
            return False
        kill_adb_uiautomator_block()
        self.mobile_test.device.screenshot("%s/result.png" % log_dir)
        time.sleep(1)
        self.clear_data()
        self.mobile_test.logout(self.mobile_test.my_func_name(), "%s test finshed..." % self.app_name)
        time.sleep(5)
        return result

    def collect_result(self):
        try:
            kill_adb_uiautomator_block()
            fps_score = self.mobile_test.device(text=self.test_text).right(resourceIdMatches=".+/textViewFps$").info[
                'text']
            if fps_score == "":
                return False
            return fps_score
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "get collect result is error: %s " % e)
            return False

    def main(self, tr):
        self.mobile_test.logout(self.mobile_test.my_func_name(), '...')
        self.check_corporate()
        time.sleep(2)
        kill_adb_uiautomator_block()
        time.sleep(1)
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "preload setup is error %s" % e)
            return False
        time.sleep(2)
        log_dir = tr.result_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        result = self.run_test(log_dir)
        if result:
            return False
        result = result.replace("fps", "").strip()
        self.mobile_test.logout(self.mobile_test.my_func_name(), "Test result is : %s" % result)
        tr.result(self.app_name, result, 'fps')
        tr.save()


if __name__ == "__main__":
    tr = TestResult()
    Glbench(tr, tr.case_name, tr.case_info["apk"], tr.case_info["arg"])
