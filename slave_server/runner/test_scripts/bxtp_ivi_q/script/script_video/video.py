#!/usr/bin/env python
# coding=utf-8
import os
import time
import zipfile
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib import system_operation
from runner.operation_lib.apptest import apptest
from runner.operation_lib.fps import test_fps
from atf import TestResult
result = []


class video_playback_test:
    def __init__(self, test_case, app_package, app_activity, result_dir, loop_index):
        self.src_dic = {

            "H265_4k60fps": "http://10.239.93.52/workloads/H265_4k60fps.html"

        }
        self.result = ''
        self.attfile = ''
        self.test_case = test_case
        self.app_package = app_package
        self.app_activity = app_activity
        self.loop_index = loop_index
        self.video_fps_test = test_fps(self.test_case, self.app_package + '/' + self.app_activity)
        self.result_dir = result_dir
        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        self.args = [self.result_dir, self.loop_index]
        self.app = [self.test_case, '']
        self.video_test = apptest(self.args, self.app, self.app_package, self.app_activity)
        for i in range(3):
            if self.main():
                break
            #utiliy.hard_reboot()
        self.returncode = 0 if i < 2 else 1
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), self.test_case + " test complate! " + ("<success>" if i < 2 else "<failed>"))
    def set_settings(self):
        try:
            system_operation.turn_bluetooth('0')
        except Exception, e:
            self.video_fps_test.logout(self.video_fps_test.my_func_name(), "preload setting error: %s" % e)
            return False
    def install_opera_apk(self):
            a=os.popen('adb shell pm list packages -3 | grep opera')
            b=a.read().split()
            if "com.opera.browser" in b:
                os.system('adb uninstall com.opera.browser')
            os.system(" adb install ./runner/test_src/opera.apk")
            print "install...."
            time.sleep(3)
    def run_test(self, log,timeout=30):
        self.video_test.logout(self.video_test.my_func_name(), ">>>>>>>> Start video test <<<<<<<< ")
        self.video_test.clear_app_data()
        os.system("adb shell am start -n com.opera.browser/com.opera.android.MainLauncherActivity -d http://10.239.93.52/workloads/H265_4k60fps.html")
        time.sleep(30)
        print "123..."
        os.system("adb shell input tap 967.5 978")
        print "click accept..."
        # icount = 0
        # while icount < timeout:
        #     kill_adb_uiautomator_block_old()
        #     time.sleep(2)
        # kill_adb_uiautomator_block_old()
        # dev = self.video_test.device(test='ACCEPT & CONTINUE')
        # kill_adb_uiautomator_block_old()
        # if dev.exists:
        #     print "==click=="
        #     kill_adb_uiautomator_block_old()
        #     time.sleep(2)
        #     self.video_test.device(test='ACCEPT & CONTINUE').click()
        #     kill_adb_uiautomator_block_old()
        #     # dev.click()
        #     time.sleep(2)
        time.sleep(3)
        os.system("adb shell input tap 63 442")
        print "fullscreen..."
        time.sleep(2)
        os.system("adb shell input tap 968 528")
        print "play video..."
        time.sleep(25)
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "sssssssssssssssssssssssssssss")

        self.video_fps_test.doInThread(self.video_fps_test.run_fpstool_for_opera, log)
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "sssss")
        duration = 20
        while duration > 0:
            if utiliy.is_app_runing(self.app_package):
                self.video_test.logout(self.video_test.my_func_name(), "\r>>>Please wait for test complete ... %s(s)" % duration)
                duration -=10
                time.sleep(10)
            else:
                print "nnnnnnnnnnnnot run"
            #else:
             #   self.video_fps_test.kill_fps_tools()
              #  return 0

        avg_fps = self.video_fps_test.collect_result(log)
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "%s result is:%s" % (self.test_case, avg_fps))
        self.video_fps_test.kill_fps_tools()
        #kill_adb_uiautomator_block()
        return avg_fps
        # else:
        #     print "..............."
    def main(self):
        #self.set_settings()
        self.attfile = self.result_dir + "/result.txt"
        self.video_fps_test.kill_fps_tools()
        self.install_opera_apk()
        self.result = self.run_test(self.attfile)
    #    self.video_test.clear_app_data()
        self.video_fps_test.kill_fps_tools()
        self.video_fps_test.logout(self.video_fps_test.my_func_name(),
                                   "%s: test complete, result is:%s" % (self.test_case, self.result))
        return False if self.result < 20 else True


if __name__ == '__main__':
    tr = TestResult()
    video_fps_test = video_playback_test(tr.case_name, tr.case_info["app_package"], tr.case_info["app_activity"],
                                         tr.result_dir, tr.loop_index)
    for f in os.listdir(video_fps_test.result_dir):
        if not f.endswith('.zip'):
            target_file = f + '.zip'
            zipf = zipfile.ZipFile(os.path.join(video_fps_test.result_dir, target_file), 'w', zipfile.ZIP_DEFLATED)
            zipf.write(os.path.join(video_fps_test.result_dir, f), f)
            zipf.close()
            tr.add_attachment(os.path.join(video_fps_test.result_dir, target_file))
    tr.result(video_fps_test.result)
    tr.add_attachment(video_fps_test.attfile)
    tr.save()
    exit(video_fps_test.returncode)

