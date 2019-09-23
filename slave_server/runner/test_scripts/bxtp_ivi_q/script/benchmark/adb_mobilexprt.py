#!/usr/bin/env python
# coding=utf-8
import os
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.exception_operation import kill_uiautomator
from runner.operation_lib.base_lib.exception_operation import app_exception_kill_case
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


class Mobilexpor:

    def __init__(self, tr):
        self.app_name = tr.case_name
        self.app_path = tr.case_info["apk"]
        self.app_use_name = "com.mobilexprt"
        self.app = [self.app_name, self.app_path]
        self.tr_name = tr.case_name
        self.data = ''
        self.mobile_test = apptest([tr.result_dir, tr.loop_index], self.app)
        self.main(tr)

    def clear_data(self):
        self.mobile_test.kill_app(self.app_use_name)
        self.mobile_test.clear_app_data(self.app_use_name)
        time.sleep(1)
        self.mobile_test.ui_operation.click_by_event('HOME')
        time.sleep(3)

    def run_test(self, timeout=100):
        # self.clear_data()
        self.mobile_test.launch_app()
        # time.sleep(30)
        self.mobile_test.ui_operation.wait_for_root_page("ok_button")
        kill_adb_uiautomator_block_old()
        self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('ok_button')
        self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('launch_button', timeout=timeout)
        while "Extracting content" in self.mobile_test.device.dump():
            time.sleep(10)
            kill_adb_uiautomator_block_old()
            time.sleep(2)
        # 	time.sleep
        # time.sleep(60)
        if self.tr_name == "MobileXPRT_perf":
            self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('cancel_button', timeout=timeout)
            # self.mobile_test.wait_for_root_page('button_media_tests')
            if not self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('button_media_tests',
                                                                                      timeout=120):
                return False
        if self.tr_name == "MobileXPRT_ux":
            self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('ok_button', timeout=timeout)
            self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('done_button', timeout=timeout)
            # self.mobile_test.wait_for_root_page('button_ux_tests')
            if not self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('button_ux_tests', timeout=120):
                return False
        kill_adb_uiautomator_block()
        kill_uiautomator()
        time.sleep(5)
        # time.sleep(400)
        if self.mobile_test.ui_operation.wait_for_complete("group_score", splittime=400, timeout=500) == False:
            return False
        time.sleep(2)
        # self.tr.kill_watt_runtime()
        kill_adb_uiautomator_block()
        if not app_exception_kill_case(self.mobile_test.app_package):
            return False
        app_device = self.mobile_test.device(resourceIdMatches=".+/group_name")

        if (app_device.exists):
            right_dev = app_device.right(resourceIdMatches=".+/group_score")
            if right_dev.exists:
                self.data = str(right_dev.info['text'])
        kill_adb_uiautomator_block()

        if self.data != "" and self.data.isdigit():
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Test data is %s" % self.data)
            return self.data
        return False

    def main(self, tr):
        os.system("adb root")
        self.clear_data()
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "failed %s" % e)
            return False
        time.sleep(2)
        log_dir = tr.result_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        result = self.run_test()
        if result == False:
            self.clear_data()
            return False
        self.mobile_test.device.screenshot("%s/result.png" % log_dir)
        self.clear_data()

        tr.result(self.tr_name, result, 'score')
        tr.add_attachment(log_dir + "/result.png")
        tr.save()


if __name__ == "__main__":
    tr = TestResult()
    Mobilexpor(tr)
