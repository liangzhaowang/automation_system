#!/usr/bin/env python
# coding=utf-8
import os
import time
import re
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


class Daimler:
    def __init__(self, tr):
        self.app_name = tr.case_name
        self.app_path = tr.case_info["apk"]
        self.item_text = tr.case_info["itemtext"]
        self.result_item = tr.case_info["resultitem"]
        self.result = ''
        self.result_dir = tr.result_dir
        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        self.app = [self.app_name, self.app_path]
        self.tr_name = tr.case_name
        self.daimler = apptest([self.result_dir, tr.loop_index], self.app)
        for i in range(3):
            if self.main():
                break
            utiliy.hard_reboot()
        self.daimler.logout(self.daimler.my_func_name(), self.app_name + " test complate! " + ("<success>" if i < 2 else "<failed>"))
        self.returncode = 0 if i < 2 else 1

    def clean_app(self):
        self.daimler.kill_app()
        self.daimler.clear_app_data()
        #kill_adb_uiautomator_block_old()

    def run_test(self):
        self.clean_app()
        self.daimler.logout(self.daimler.my_func_name(), '...')
        self.daimler.launch_app()
        self.daimler.ui_operation.wait_for_root_page("tvDaimler")
        self.daimler.logout(self.daimler.my_func_name(), 'Begin testing......')
        time.sleep(1)

        if not self.daimler.ui_operation.click_ui_button_by_text(self.item_text):
            return False
        if not self.daimler.ui_operation.wait_for_complete_by_text("AutoBots"):
            return False
        time.sleep(2)
        #kill_adb_uiautomator_block_old()
        result = self.collect_result()

        self.daimler.device.screenshot("%s/result.png" % self.result_dir)
        self.daimler.logout(self.daimler.my_func_name(), "%s test finshed..." % self.daimler.app_name)
        time.sleep(5)
        #kill_adb_uiautomator_block_old()

        if not result:
            self.daimler.logout(self.daimler.my_func_name(), "Error, NO result found......")
            return False
        else:
            return result

    def collect_result(self):
        self.daimler.logout(self.daimler.my_func_name(), '...')
        time.sleep(1)

        fps_score = self.daimler.ui_operation.get_score_info_data(self.result_item, "text", "1")
        result = re.sub("[\xc2\xa0fps]", "", fps_score)

        if result == "":
            return False
        return result

    def main(self):
        self.daimler.logout(self.daimler.my_func_name(), '...')
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
        except Exception, e:
            self.daimler.logout(self.daimler.my_func_name(), "Setup Failure. %s" % e)
            return False
        result = self.run_test()
        if not result:
            result = self.run_test()
        if not result:
            self.clean_app()
            return False

        self.daimler.logout(self.daimler.my_func_name(), "Test result is : " + result)
        self.result = result
        return True


if __name__ == "__main__":
    tr = TestResult()
    daimler = Daimler(tr)
    tr.result(daimler.result)
    tr.save()
    exit(daimler.returncode)
