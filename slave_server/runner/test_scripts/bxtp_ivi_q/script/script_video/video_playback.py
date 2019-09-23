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
            "H264_720P_30FPS": "ToS_720p_29.97fps_H264_4000kbps_8bits_noHDR_v1511090000.mp4",
            "H264_1080P_60FPS": "ToS_1080p_59.94fps_H264_25000kbps_8bits_noHDR_v1511090000_barcode.mp4",
            "H264_4kx2k_60FPS": "ToS_2160p_59.94fps_H264_35000kbps_8bits_noHDR_v1511090000_code_new.mp4",
            "H265_1080P_8bit": "ToS_1080p_59.94fps_H265_12000kbps_8bits_noHDR_v1511090000_code_new.mp4",
            "H265_4kx2k_10bit": "ToS_2160p_59.94fps_H265_35000kbps_10bits_noHDR_v1511090000_code_new.mp4",
            "MPEG4_1920x1080_60FPS": "ToS_1080p_59.94fps_H264_25000kbps_8bits_noHDR_v1511090000_code_new.mp4",
            "VP9_3840X2460_30FPS": "ToS_2160p_29.97fps_VP9_35000kbps_8bits_noHDR_v2014_code_new.webm"
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
            time.sleep(10)
            utiliy.hard_reboot()
        self.returncode = 0 if i < 2 else 1
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), self.test_case + " test complate! " + ("<success>" if i < 2 else "<failed>"))

    def choose_video(self, timeout=10):
        icount = 0
        #kill_adb_uiautomator_block_old()
        while icount < timeout:
            try:
                dev = self.video_test.device(resourceId="com.android.gallery3d:id/gl_root_view")
                print "+++start click+++++"
                #kill_adb_uiautomator_block_old()
                if dev.exists:
                    print "====click ======="
                    #kill_adb_uiautomator_block_old()
                    dev.click()
                else:
                    break
                time.sleep(2)
                #kill_adb_uiautomator_block_old()
                self.video_test.device(resourceId="com.android.gallery3d:id/gl_root_view").click()
                return True
            except Exception, e:
                self.video_fps_test.logout(self.video_fps_test.my_func_name(), "choose video is error:%s" % e)
                return False
            icount += 1
            time.sleep(1)
        if icount >= timeout:
            return False
        else:
            return True

    def set_settings(self):
        try:
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
        except Exception, e:
            self.video_fps_test.logout(self.video_fps_test.my_func_name(), "preload setting error: %s" % e)
            return False

    def run_test(self, log):
        self.video_test.logout(self.video_test.my_func_name(), ">>>>>>>> Start video test <<<<<<<< ")
        self.video_test.clear_app_data()
        self.video_test.launch_app()
        time.sleep(2)
        print "lunch......"
        time.sleep(2)
        if not self.choose_video():
            return 0
        time.sleep(25)
        self.video_fps_test.doInThread(self.video_fps_test.run_fpstool, log)
        duration = 20
        while duration > 0:
            if utiliy.is_app_runing(self.app_package):
                self.video_test.logout(self.video_test.my_func_name(), "\r>>>Please wait for test complete ... %s(s)" % duration)
                duration -= 10
                time.sleep(10)
            else:
                self.video_fps_test.kill_fps_tools()
                return 0

        avg_fps = self.video_fps_test.collect_result(log)
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "%s result is:%s" % (self.test_case, avg_fps))
        self.video_fps_test.kill_fps_tools()
        #kill_adb_uiautomator_block()
        return avg_fps

    def main(self):
        os.system('adb root')
        time.sleep(2)
	os.system('adb shell rm /storage/emulated/10/*.png')
        line = os.popen("adb shell ls /sdcard/" + self.src_dic[self.test_case]).read()
        push_file = False if "No such file or directory" not in line and self.src_dic[self.test_case] in line else True
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "-------------------push_file=" + str(push_file))
        if push_file:
            os.system("adb shell rm /storage/emulated/10/*.mp4")
            self.video_test.ui_operation.push_data("./runner/test_src/%s" % (self.src_dic[self.test_case]))
            time.sleep(2)
            system_operation.reboot_system()
        else:
            time.sleep(5)
        self.set_settings()
        self.attfile = self.result_dir + "/result.txt"
        self.video_fps_test.kill_fps_tools()
        self.result = self.run_test(self.attfile)
        self.video_test.kill_app()
        self.video_test.clear_app_data()
        self.video_fps_test.kill_fps_tools()
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "%s: test complete, result is:%s" % (self.test_case, self.result))
        return False if self.result < 20 else True


if __name__ == '__main__':
    tr = TestResult()
    video_fps_test = video_playback_test(tr.case_name, tr.case_info["app_package"], tr.case_info["app_activity"], tr.result_dir, tr.loop_index)
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
