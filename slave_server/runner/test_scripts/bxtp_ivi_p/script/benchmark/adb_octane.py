#!/usr/bin/env python
# coding=utf-8
import os
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from atf import TestResult

# from browser import browsers


def run_test(test_mode,tr):
    test_mode.clear_app_data()
    test_mode.skip_chrome_wizard()
    time.sleep(3)
    test_mode.launch_chrome_with_page()
    time.sleep(3)
    test_mode.ui_operation.click_ui_button_by_text_or_resid(resid='run-octane')
    # tr.start_watt()
    if test_mode.ui_operation.wait_for_complete_by_text('Always show') == False:
        return False

def clean_app(test_mode):
    test_mode.clear_app_data()
    test_mode.ui_operation.click_by_event("HOME")


def main(test_mode):
    kill_adb_uiautomator_block_old()
    test_mode.device.watcher("google_accept").when(text="Accept").click()
    test_mode.ui_operation.click_by_event("MENU")
    kill_adb_uiautomator_block_old()
    time.sleep(1)
    test_mode.ui_operation.click_by_event("HOME")
    kill_adb_uiautomator_block_old()
    system_operation.connect_wifi(test_mode.log)

    if not run_test(test_mode, tr):
        clean_app(test_mode)
        return False
    test_mode.ui_operation.click_ui_button_by_text_or_resid('Always show')
    try :
        result=test_mode.device(resourceId="com.android.chrome:id/url_bar").text.split("/")[1]
    except Exception,e:
        test_mode.logout(test_mode.my_func_name(),"get result error%s"%e)
        clean_app(test_mode)
        return False
    if result == "":
        clean_app(test_mode)
        return False
    clean_app(test_mode)
    test_mode.logout(test_mode.my_func_name(),'The Result is: %s'%result)
    tr.result(result)
    tr.save()
    return True


if __name__ == "__main__":
    tr = TestResult(__file__)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    args = [log_dir, tr.loop_index]
    test_mode = apptest(args,
                        app_package="com.android.chrome",
                        app_activity = "com.android.chrome/com.google.android.apps.chrome.Main",
                        url="http://192.168.1.101/octane_v2",
                        case_name="adb_octane")
    icount = 0
    ilimite = 2
    while not main(test_mode):
        if icount > ilimite:
            break
        icount += 1
