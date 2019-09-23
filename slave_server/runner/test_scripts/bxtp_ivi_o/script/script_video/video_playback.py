#!/usr/bin/env python
# coding=utf-8
import os
import time
import zipfile
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
            "H264_2160P_60FPS": "ToS_2160p_59.94fps_H264_35000kbps_8bits_noHDR_v1511090000_code_new.mp4",
            "H265_2K_10bit": "ToS_2160p_59.94fps_H265_35000kbps_10bits_noHDR_v1511090000_code_new.mp4",
            "H265_2K_8bit": "ToS_2160p_59.94fps_H265_35000kbps_8bits_noHDR_v1511090000_code_new.mp4",
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
        self.main()

    def choose_video(self, timeout=10):
        icount = 0
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            try:
                dev = self.video_test.device(resourceId="com.android.gallery3d:id/gl_root_view")
                if dev.exists:
                    dev.click()
                else:
                    break
                time.sleep(2)
                kill_adb_uiautomator_block_old()
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
            system_operation.turn_airplane('1')
            system_operation.turn_bluetooth('0')
            system_operation.turn_wifi('0')
            system_operation.turn_gps('0')
            system_operation.set_display_time()
        except Exception, e:
            self.video_fps_test.logout(self.video_fps_test.my_func_name(), "preload setting error: %s" % e)
            return False

    def Prepare_data(self):
        self.video_test.clear_app_data()
        self.video_test.logout(self.video_test.my_func_name(), ">>>>>>>> Start Photo test <<<<<<<< ")
        time.sleep(2)
        self.video_test.launch_app()
        time.sleep(2)

    def run_test(self, log):
        self.Prepare_data()
        if not self.choose_video():
            return False
        time.sleep(2)
        self.video_fps_test.doInThread(self.video_fps_test.run_fpstool, log)
        if not self.video_test.ui_operation.wait_for_compelet_for_fps(40):
            return False
        avg_fps = self.video_fps_test.collect_result(log)
        self.video_fps_test.kill_fps_tools()
        if avg_fps < 20.0:
            return False
        time.sleep(2)
        kill_adb_uiautomator_block()
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "%s result is:%s" % (self.test_case, avg_fps))
        return avg_fps

    def main(self):
        line = os.popen("adb shell ls /sdcard/" + self.src_dic[self.test_case]).read()
        print line
        self.video_fps_test.kill_fps_tools()
        push_file = True
        if "No such file or directory" not in line and self.src_dic[self.test_case] in line:
            push_file = False
        self.video_fps_test.logout(self.video_fps_test.my_func_name(), "-------------------push_file=" + str(push_file))
        if push_file:
            os.system("adb shell rm /sdcard/*.mp4")
            self.video_test.ui_operation.push_data("./runner/test_src/%s" % (self.src_dic[self.test_case]))
            time.sleep(2)
            system_operation.reboot_system()

        if not push_file:
            time.sleep(20)
        self.set_settings()
        log = self.result_dir + "/result.txt"
        result = self.run_test(log)
        self.video_test.kill_app()
        self.video_test.clear_app_data()
        self.video_fps_test.kill_fps_tools()
        if result == False:
            return False
        self.result = result
        print "result ==", result
        self.attfile = log
        return True


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
