import os
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.exception_operation import kill_uiautomator
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.fps import test_fps
from runner.operation_lib.apptest import apptest
from atf import TestResult


def push_html():
    lodir = "./src/browser"
    panning_test.ui_operation.push_data(lodir)


def clean_app(panning_test):
    panning_test.clear_app_data()
    panning_test.ui_operation.click_by_event("HOME")


def down_up(panning_test,times):
    kill_uiautomator()
    for i in range(times):
        panning_test.swiping.up()
        panning_test.swiping.up()
        panning_test.swiping.up()
        panning_test.swiping.down()
        panning_test.swiping.down()
        panning_test.swiping.down()


def run_test(panning_fps_test, panning_test, log):
    push_html()
    clean_app(panning_test)
    panning_test.skip_chrome_wizard()
    panning_test.launch_chrome_with_page("permission_allow_button")
    time.sleep(3)
    kill_adb_uiautomator_block_old()
    kill_uiautomator()
    panning_fps_test.doInThread(down_up, panning_test, 50)
    time.sleep(2)
    panning_fps_test.doInThread(panning_fps_test.run_fpstool_ext, log)
    if not panning_test.ui_operation.wait_for_compelet_for_fps(timeout=60):
        return False
    avg_fps = panning_fps_test.collect_result(log)
    panning_fps_test.kill_fps_tools()
    panning_test.kill_app()
    panning_test.logout(panning_test.my_func_name(), "Frame rate while panning web page in Browser- average:%s"%avg_fps)
    return avg_fps


def main(tr, panning_fps_test, panning_test):
    
    kill_adb_uiautomator_block()
    try:
        system_operation.turn_airplane('1')
        system_operation.turn_bluetooth_p('0')
        system_operation.turn_wifi('1')
        system_operation.turn_gps('0')
        system_operation.set_display_time()
    except Exception,e:
        panning_test.log.error("exception error :%s !!!!"%e)
        return False
    time.sleep(2)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log = log_dir + "/result.txt"
    result = run_test(panning_fps_test, panning_test, log)
    if not result:
        clean_app(panning_test)
        return False
    tr.result('Frame_rate_while_panning_web_page_in_Browser', result, 'fps')
    tr.save()


if __name__ == '__main__':
    tr = TestResult()
    args = [tr.result_dir, tr.loop_index]
    panning_fps_test = test_fps("pannig_web", 'com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity')
    panning_test = apptest(args, tr.case_info["app_package"], tr.case_info["app_activity"], tr.case_info["url"], tr.case_name)
    panning_fps_test.kill_fps_tools()
    main(tr, panning_fps_test, panning_test)
