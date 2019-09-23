#!/usr/bin/env python
# coding=utf-8
import os
import time
import zipfile
from atf import TestResult
from runner.operation_lib.fps import test_fps
from runner.operation_lib.apptest import apptest
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.eventHunter import eventHunter
from runner.operation_lib.base_lib import system_operation


class gallery_fling_test:
    def __init__(self, tr):
        self.result = ''
        self.attfile = ''
        self.test_case = tr.case_name
        self.app_package = tr.case_info["app_package"]
        self.app_activity = tr.case_info["app_activity"]
        self.loop_index = tr.loop_index
        self.log_dir = tr.result_dir
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.args = [self.log_dir, self.loop_index]
        self.app = [self.test_case, '']
        self.gallery_fps_test = test_fps(self.test_case, self.app_package + '/' + self.app_activity + "#0")
        self.gallery_test = apptest(self.args, self.app, self.app_package, self.app_activity)
        self.main(self.log_dir)

    def set_settings(self):
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
            return True
        except Exception, e:
            self.gallery_test.logout(self.gallery_test.my_func_name(), "preload setup failed :%s" % e)
            return False

    def clear_test_app_data(self):
        self.gallery_test.logout(self.gallery_test.my_func_name(), ">>>>>>>>Clear app data<<<<<<<<")
        time.sleep(2)
        self.gallery_test.clear_app_data()

    def Prepare_data(self):
        self.clear_test_app_data()
        self.push_data()
        self.gallery_test.logout(self.gallery_test.my_func_name(), ">>>>>>>> Start Photo test <<<<<<<< ")
        time.sleep(1)
        self.gallery_test.launch_app()
        time.sleep(2)
        self.gallery_test.ui_operation.click_ui_button_by_text('NO THANKS')
        time.sleep(2)
        if not self.gallery_test.run_google_set():
            return False
        time.sleep(2)
        self.gallery_test.ui_operation.click_ui_button_by_resourceIdMatches("overflow_count")
        time.sleep(1)


    def push_data(self):
        if len(os.popen("adb shell ls /sdcard/browser").readlines()) > 1:
            os.system("adb shell rm -r /sdcard/browser")
            time.sleep(2)
            system_operation.reboot_system()
        lines = os.popen("adb shell ls /sdcard/wallpaper").readlines()
        copy_reboot = True
        if len(lines) > 20:
            copy_reboot = False
        self.gallery_test.logout(self.gallery_test.my_func_name(), "-------------------copy_reboot="+str(copy_reboot))
        os.system("adb shell rm /sdcard/*.mp4")
        if copy_reboot:
            os.system("adb shell rm -r /sdcard/wallpaper")
            self.gallery_test.logout(self.gallery_test.my_func_name(), ">>>>>>>> Push wallpaper to DUT <<<<<<<< ")
            time.sleep(2)
            self.gallery_test.ui_operation.push_data("./runner/test_src/wallpaper")
            time.sleep(2)
            system_operation.reboot_system()


    def set_gallery(self):
        os.system("adb shell am force-stop  com.android.gallery3d")
        os.system("adb shell am start -t image/* file:///mnt/sdcard/wallpaper/")
        dev = self.gallery_test.device(resourceId="com.android.gallery3d:id/gl_root_view")
        if dev.exists:
            dev.click()
        self.gallery_test.swiping.right()
        self.gallery_test.swiping.right()
        self.gallery_test.swiping.right()


    def swiping_action(self):
        kill_adb_uiautomator_block_old()
        os.system("adb root")
        time.sleep(1)
        leftright = eventHunter(self.gallery_test.device)
        leftright.center_left(repeat_swipes=3, cltimes=30, clstep=0)


    def run_test(self, log):
        self.Prepare_data()
        self.set_gallery()
        time.sleep(1)
        self.gallery_fps_test.doInThread(self.swiping_action)
        time.sleep(3)
        self.gallery_fps_test.doInThread(self.gallery_fps_test.run_fpstool, log)
        self.gallery_test.ui_operation.wait_for_compelet_for_fps(timeout=80)
        avg_fps = self.gallery_fps_test.collect_result(log)
        self.gallery_fps_test.kill_fps_tools()
        print avg_fps
        if avg_fps < 1.0:
            return False
        time.sleep(2)
        kill_adb_uiautomator_block_old()
        self.gallery_test.ui_operation.click_by_event("HOME")
        self.gallery_test.kill_app()
        self.gallery_test.logout(self.gallery_test.my_func_name(), "Flinging_image_list_in_gallery result is:%s" % avg_fps)
        return avg_fps


    def main(self, log_dir):
        if not self.set_settings():
            return False

        log = log_dir + "/result.txt"
        result = self.run_test(log)
        if not result:
            result = self.run_test(log)
        if not result:
            self.clear_test_app_data()
            return False
        self.result = result
        self.attfile = log
        return True


if __name__ == '__main__':
    tr = TestResult()
    gallery_fps_test = gallery_fling_test(tr)
    for f in os.listdir(gallery_fps_test.log_dir):
        if not f.endswith('.zip'):
            target_file = f + '.zip'
            zipf = zipfile.ZipFile(os.path.join(tr.result_dir, target_file), 'w', zipfile.ZIP_DEFLATED)
            zipf.write(os.path.join(tr.result_dir, f), f)
            zipf.close()
            tr.add_attachment(os.path.join(tr.result_dir, target_file))
    tr.result(gallery_fps_test.result)
    tr.add_attachment(gallery_fps_test.attfile)
    tr.save()

