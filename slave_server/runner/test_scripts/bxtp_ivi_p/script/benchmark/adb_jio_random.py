#!/usr/bin/env python
# coding=utf-8
import os
import re
import time
from runner.operation_lib import utiliy
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
        for i in range(3):
            if self.main(tr):
                break
            utiliy.hard_reboot()
        self.mobile_test.logout(self.mobile_test.my_func_name(), self.app_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))

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
        self.mobile_test.ui_operation.app_package = "android"
        self.mobile_test.ui_operation.click_ui_button_by_text("OK")
        self.mobile_test.ui_operation.app_package = self.mobile_test.app_package
        time.sleep(1)
        self.mobile_test.ui_operation.click_ui_button_by_text("Performance Tests")
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text("Random Read")
        self.mobile_test.ui_operation.click_ui_button_by_text("Random Write")
        self.mobile_test.ui_operation.click_ui_button_by_text("Sequential Read")
        self.mobile_test.ui_operation.click_ui_button_by_text("Sequential Write")
        time.sleep(5)
        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Select the test item...')
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text("Run")

        self.mobile_test.logout(self.mobile_test.my_func_name(), 'Begin testing...')
        if not self.mobile_test.ui_operation.wait_for_complete("testReportTitle", timeout=600):
            return False
        time.sleep(1)
        result = self.collect_result()
        self.mobile_test.device.screenshot("%s/result.png" % log_dir)
        time.sleep(2)
        self.clear_data()
        self.mobile_test.logout(self.mobile_test.my_func_name(), "%s test finshed..." % self.tr_name)
        if not result:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Error, NO result found......")
            return False
        else:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "%s (in IOPS): %s" % (self.tr_name, result))
        return result

    def get_search_obj(self, key_code, resource):
        obj = re.findall('.+%s:\t(\d+,*\d*\.*\d+|[1-9])' % key_code, resource.replace("0.00", "0"))
        if len(obj) > 0:
            return obj[0]
        else:
            return 0

    def collect_result(self):
        result_dict = {}
        rs = self.mobile_test.ui_operation.get_score_info_data("textViewLogContent", "text")
        if rs == "":
            return False
        rr_score = self.get_search_obj('Random Read', rs)
        rw_score = self.get_search_obj('Random Write', rs)
        sr_score = self.get_search_obj('Sequential Read', rs)
        sw_score = self.get_search_obj('Sequential Write', rs)

        if rr_score == "":
            return False
        result_dict["rr_score"] = rr_score.replace(",", "")
        result_dict["rw_score"] = rw_score.replace(",", "")
        result_dict["sr_score"] = sr_score.replace(",", "")
        result_dict["sw_score"] = sw_score.replace(",", "")
        return result_dict

    def main(self, tr):
        kill_adb_uiautomator_block()
        try:
            system_operation.screen_on()
            time.sleep(1)
            system_operation.turn_airplane('1')
            system_operation.turn_bluetooth_p('0')
            system_operation.turn_wifi('0')
            system_operation.turn_gps('0')
            system_operation.set_display_time()
        except Exception:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Error setup load......")
            return False
        time.sleep(2)
        log_dir = tr.result_dir
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        result = self.test_jio(log_dir)
        if not result:
            return False
        else:
            for key, velue in result.items():
                tr.sub_score(key, velue)

        tr.result(result["rr_score"])
        tr.add_attachment(log_dir + "/result.png")
        tr.save()


if __name__ == "__main__":
    tr = TestResult()
    Jio_random(tr)
