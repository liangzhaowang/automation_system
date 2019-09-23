#!/usr/bin/env python
# coding=utf-8
import os
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import app_exception_kill_case
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult


class Vellamo:
    def __init__(self, tr):
        self.app_name = tr.case_name
        self.app_path = tr.case_info["apk"]
        self.log_dir = tr.result_dir
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.app = [self.app_name, self.app_path]
        self.tr_name = tr.case_name
        self.data = ''
        self.args = [self.log_dir, tr.loop_index]
        self.mobile_test = apptest(self.args, self.app)
        self.chrome_test = apptest(self.args, app_package="com.android.chrome", app_activity="com.android.chrome/com.google.android.apps.chrome.Main", case_name="chrome")
        icount = 0
        ilimite = 2
        while not self.main(tr):
            if icount > ilimite:
                break
            icount += 1

    def clear_data(self):
        self.mobile_test.logout(self.mobile_test.my_func_name(), "......Clear app data......")
        time.sleep(1)
        self.mobile_test.clear_app_data()
        self.mobile_test.kill_app()

    def push_data(self):
        os.system("adb root")
        os.system("adb shell setenforce 0")
        self.mobile_test.app_install(3)
        os.system("adb push ./src/app_assets3 /data/data/com.quicinc.vellamo/app_assets3")
        os.system("adb shell 'cd /data/data/com.quicinc.vellamo/; chmod -R 0777 ./app_assets3'")

    def run_test(self, timeout=100):
        self.clear_data()
        self.chrome_test.skip_chrome_wizard()
        self.push_data()
        self.mobile_test.launch_app()
        if not self.mobile_test.ui_operation.click_ui_button_by_text("Accept"):
            self.mobile_test.logout(self.mobile_test.my_func_name(), "preoperation failed")
            return False
        time.sleep(5)
        self.mobile_test.ui_operation.wait_for_root_page("main_root_vslider")
        self.mobile_test.ui_operation.click_ui_button_by_text("LET'S ROLL")
        if self.tr_name == "Vellamo_chrome_browser":
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_text_to_right_resourceIdMatches("Browser",
                                                                                             "card_launcher_run_button")
            score_text = "Chrome Browser"
        if self.tr_name == "Vellamo_webview_browser":
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('card_browser_button')
            time.sleep(2)
            kill_adb_uiautomator_block()
            self.mobile_test.device(resourceId='com.quicinc.vellamo:id/card_browser_button').right(resourceId='com.quicinc.vellamo:id/card_browser_button').click()
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_text_to_right_resourceIdMatches("Browser", "card_launcher_run_button")
            score_text = "Android WebView Browser"
        if self.tr_name == "Vellamo_Metal":
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_text_to_right_resourceIdMatches("Metal", "card_launcher_run_button")
            score_text = "Metal"
        if self.tr_name == "Vellamo_Multicore":
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_text_to_right_resourceIdMatches("Multicore", "card_launcher_run_button")
            score_text = "Multicore"

        self.mobile_test.ui_operation.click_ui_button_by_text("Got it")
        time.sleep(2)
        self.mobile_test.logout(self.mobile_test.my_func_name(), "Begin testing......")
        time.sleep(2)
        self.mobile_test.ui_operation.wait_for_complete("card_score_score", ABS=120)
        time.sleep(2)

        if not self.mobile_test.ui_operation.click_ui_button_by_text("No"):
            self.mobile_test.logout(self.mobile_test.my_func_name(), "preoperation failed")
            return False
        time.sleep(2)
        self.mobile_test.ui_operation.click_ui_button_by_text('Compare Scores')
        if self.mobile_test.device(className="android.widget.ImageView", instance=0).exists:
            kill_adb_uiautomator_block()
            self.mobile_test.ui_operation.click_ui_button_by_resourceIdMatches('score_pane_topbar_button')
        if not app_exception_kill_case(self.mobile_test.app_package):
            return False
        self.data = self.mobile_test.ui_operation.get_score_info_data('card_score_score', 'text')
        kill_adb_uiautomator_block()
        if self.data != "" and self.data.isdigit():
            self.mobile_test.logout(self.mobile_test.my_func_name(), "Test data is %s" % self.data)
            return self.data
        return False

    def main(self, tr):
        kill_adb_uiautomator_block()
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_airplane('1')
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
            system_operation.turn_gps('0')
            system_operation.set_display_time()
        except Exception, e:
            self.mobile_test.logout(self.mobile_test.my_func_name(), "preload setup is error %s" % e)
            return False
        time.sleep(2)
        result = self.run_test()
        if not result:
            self.clear_data()
            return False
        self.mobile_test.device.screenshot("%s/result.png" % self.log_dir)
        self.clear_data()
        tr.result(result)
        tr.add_attachment(self.log_dir + "/result.png")
        tr.save()
        return True


if __name__ == "__main__":
    tr = TestResult()
    Vellamo(tr)
