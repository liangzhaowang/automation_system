#!/usr/bin/env python
# coding=utf-8
import os
import re
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


class Jio_random:
    def __init__(self, tr):
        self.app_name = tr.case_name
        self.app_path = tr.case_info["apk"]
        self.app = [self.app_name, self.app_path]
        self.tr_name = tr.case_name
        self.data = ''
        self.mobile_test = apptest([tr.result_dir, tr.loop_index], self.app)
        self.main(tr)

    def clear_data(self):
        self.mobile_test.kill_app()
        time.sleep(1)
        self.mobile_test.clear_app_data()
        time.sleep(2)

    def test_jio(self, log_dir):
        self.clear_data()
        time.sleep(1)
        self.mobile_test.launch_app()
        self.mobile_test.ui_operation.wait_for_root_page("main_list_view")
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text("Performance Tests")
        time.sleep(2)
        if self.tr_name == "JIO_Random_Write":
            self.mobile_test.ui_operation.click_ui_button_by_text("Random Write")
        if self.tr_name == "JIO_Random_Read":
            self.mobile_test.ui_operation.click_ui_button_by_text("Random Read")
        time.sleep(5)
        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Select the test item...')
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text("Run")

        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Begin testing...')
        # time.sleep(150)
        if self.mobile_test.ui_operation.wait_for_complete("testReportTitle", timeout=300) == False:
            return False
        time.sleep(1)
        result = self.collect_result()
        self.mobile_test.device.screenshot("%s/result.png" % log_dir)
        time.sleep(2)
        self.clear_data()
        self.mobile_test.logout(self.mobile_test.my_func_name(), "%s test finshed..." % self.tr_name)
        if result == False:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Error, NO result found......")
            return False
        else:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "%s (in IOPS): %s" % (self.tr_name, result))
        return result

    def get_search_obj(self, key_code, resource):
        sobj_m = re.findall('.+%s:\t(\d+,\d+)' % key_code, resource)
        sobj_s = re.findall('.+%s:\t\d+' % key_code, resource)
        if len(sobj_m) > 0:
            return sobj_m[0]
        elif len(sobj_s) > 0:
            return sobj_s[0]

    def collect_result(self):
        rr_score = ""
        rs = self.mobile_test.ui_operation.get_score_info_data("textViewLogContent", "text")
        if rs == "":
            return False
        if self.tr_name == "JIO_Random_Write":
            rr_score = self.get_search_obj('Random Write', rs)  # re.findall(r'.+Random Write:\t(\d+,\d+)',rs)[0]
        if self.tr_name == "JIO_Random_Read":
            rr_score = self.get_search_obj('Random Read', rs)  # re.findall(r'.+Random Read:\t(\d+,\d+)',rs)[0]
        if rr_score == "":
            return False
        rr_score = rr_score.replace(",", "")
        return rr_score

    def main(self, tr):
        kill_adb_uiautomator_block()
        try:
            system_operation.screen_on()
            time.sleep(1)
            system_operation.turn_airplane('1')
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
            system_operation.turn_gps('0')
            system_operation.set_display_time()
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Error setup load......")
            return False
        time.sleep(2)
        log_dir = tr.result_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        result = self.test_jio(log_dir)
        if not result:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Error,get result fail......")
            return False

        tr.result(self.tr_name, result, 'IOPS')
        tr.add_attachment(log_dir + "/result.png")
        tr.save()

if __name__ == "__main__":
    tr = TestResult()
    Jio_random(tr)
