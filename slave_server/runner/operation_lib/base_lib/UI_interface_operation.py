#!/usr/bin/python

import os
import re
import sys
import time
import inspect
from uiautomator import Device
from runner.operation_lib import utiliy
from exception_operation import kill_adb_uiautomator_block
from exception_operation import kill_adb_uiautomator_block_old
from exception_operation import kill_uiautomator
from exception_operation import unclock_android_o_screen
from atf import TestLogger

logger = TestLogger().get_logger("process")


class Swiping(object):
    def __init__(self, device, dspx=1920, dspy=1080):
        self.device = device
        line = os.popen("adb shell dumpsys window displays |head -n 3").read()
        p = re.compile(r"cur=(?P<dspx>\d+)[xX]+(?P<dspy>\d+)")
        sobj = p.search(line, re.I)
        if sobj:
            dspx = int(sobj.group('dspx'))
            dspy = int(sobj.group('dspy'))
        try:
            self.dev_x = self.device.info['displayWidth']
            self.dev_y = self.device.info['displayHeight']
        except Exception:
            self.dev_x = dspx
            self.dev_y = dspy
        self.uy = int(self.dev_y * 40 / 100)
        self.dy = int(self.dev_y * 60 / 100)
        self.udx = int(self.dev_x * 1 / 2)
        self.lry = int(self.dev_y * 1 / 2)
        self.lx = int(self.dev_y * 40 / 100)
        self.rx = int(self.dev_y * 60 / 100)
        self.x1 = self.dev_x * 1 / 3
        self.y1 = self.dev_y * 1 / 3
        self.x3 = self.dev_x * 2 / 3
        self.y3 = self.dev_y * 2 / 3

    def swipe_by_position(self, x, y, dx, dy):
        os.system("adb shell input swipe %s %s %s %s" % (x, y, dx, dy))

    def up(self, num=0):
        if num == 0:
            os.system("adb shell input swipe %s %s %s %s" % (self.udx, self.dy, self.udx, self.uy))
        else:
            self.device.swipe(self.udx, self.dy, self.udx, self.uy, steps=num)

    def down(self, num=0):
        if num == 0:
            os.system("adb shell input swipe %s %s %s %s" % (self.udx, self.uy, self.udx, self.dy))
        else:
            self.device.swipe(self.udx, self.uy, self.udx, self.dy, steps=num)

    def left(self, num=0):
        if num == 0:
            os.system("adb shell input swipe %s %s %s %s" % (self.rx, self.lry, self.lx, self.lry))
        else:
            self.device.swipe(self.rx, self.lry, self.lx, self.lry, steps=num)

    def right(self, num=0):
        if num == 0:
            os.system("adb shell input swipe %s %s %s %s" % (self.lx, self.lry, self.rx, self.lry))
        else:
            self.device.swipe(self.lx, self.lry, self.rx, self.lry, steps=num)

    def zoomin(self):
        self.device().gesture((self.x1, self.y1), (self.x3, self.y3)).to((self.udx, self.lry), (self.udx, self.lry))

    def zoomout(self):
        self.device().gesture((self.udx, self.lry), (self.udx, self.lry)).to((self.x1, self.y1), (self.x3, self.y3))


class ui_operation(object):
    def __init__(self, output_path, current_loop, running_app_package="", app_name=""):
        self.app_package = running_app_package
        self.output_path = output_path
        self.current_loop = current_loop
        self.device = Device()
        self.app_name = app_name
        self.swiping = Swiping(self.device)

    # get function name
    def my_func_name(self):
        return inspect.stack()[1][3]

    # logout
    def logout(self, function_name, log_message):
        logger.info(">>>%s:" % function_name+log_message)

    def clear_recent(self):
        kill_adb_uiautomator_block_old()
        y = int(self.device.info['displaySizeDpY'])
        kill_adb_uiautomator_block_old()
        cy = y/2
        x = int(self.device.info['displaySizeDpX'])
        kill_adb_uiautomator_block_old()
        cx = x/2
        self.click_by_event("HOME")
        time.sleep(2)
        self.click_by_event("KEYCODE_APP_SWITCH")
        time.sleep(5)
        kill_adb_uiautomator_block_old()
        if not self.device.info['currentPackageName'] == "com.android.systemui":
            self.logout(self.my_func_name(), "recent key click is failed...")
            return False
        icount = 0
        if not self.device(text="Your recent screens appear here").exists:
            kill_adb_uiautomator_block_old()
            while not self.device(resourceIdMatches=".+/dismiss_task$").exists:
                if not self.device.info['currentPackageName'] == "com.android.systemui":
                    self.logout(self.my_func_name(), "recent key click is failed...")
                    return False
                if icount > 50:
                    return False
                icount += 1
                self.device.swipe(cx, cy, cx, y, steps=5)
                self.device(resourceIdMatches=".+/dismiss_task$").click()
                time.sleep(1)
                kill_adb_uiautomator_block_old()
            kill_adb_uiautomator_block_old()
            self.device(resourceIdMatches=".+/dismiss_task$").click()
        time.sleep(2)
        self.click_by_event("BACK")

    def wait_for_complete(self, complete_text, timeout=600, splittime=5, package=''):
        i = 0
        failed_time = 0
        if not splittime == 5:
            time.sleep(splittime)        
        kill_adb_uiautomator_block_old()

        while i < timeout:
            unclock_android_o_screen()
            kill_adb_uiautomator_block()
            if package == '' and not utiliy.is_app_runing(self.app_package):
                if failed_time > 2:
                    return False
                failed_time += 1
                continue
            app_dev = self.device(resourceIdMatches=".+/%s$" % complete_text)
            if app_dev:
                if app_dev.exists:
                    self.logout(self.my_func_name(), "%s test finshed..." % self.app_name)
                    return True
            else:
                i += 5
                time.sleep(5)
                self.logout(self.my_func_name(), "\r>>>Please wait for test complete. %s (s)" % i)
                failed_time = 0
        else:
            self.logout(self.my_func_name(), "Timeout for %s test" % self.app_package)
            return False

    def wait_for_compelet_for_fps(self, timeout=100):
        kill_uiautomator()
        while timeout > 0:
            if not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            timeout -= 10
            time.sleep(10)
            self.logout(self.my_func_name(), "\r>>>Please wait for test complete ... %s(s)" % timeout)

        return True

    def wait_for_complete_by_text(self, complete_text, timeout=1800):
        i = 0
        failed_time = 0
        self.logout(self.my_func_name(), "%s test waiting..." % self.app_package)
        kill_adb_uiautomator_block()
        while i < timeout:
            unclock_android_o_screen()
            if self.device(text=complete_text).exists:
                self.logout(self.my_func_name(), "%s test finshed..." % self.app_package)
                return True
            else:
                i += 5
                kill_adb_uiautomator_block()
                time.sleep(5)
                if not utiliy.is_app_runing(self.app_package):
                    if failed_time > 2:
                        self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                        return False
                    failed_time += 1
                    continue
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)" % i)
                sys.stdout.flush()
                failed_time = 0
        else:
            self.logout(self.my_func_name(), "Timeout for %s test" % self.app_name)
            return False

    def wait_for_complete_ex(self, complete_text, timeout=1800):
        i = 0
        failed_time = 0
        self.logout(self.my_func_name(), "%s test waiting..." % self.app_package)
        kill_adb_uiautomator_block()
        while i < timeout:
            unclock_android_o_screen()
            if self.device(resourceId="%s" % complete_text).exists:
                return True
            else:
                i += 5
                kill_adb_uiautomator_block()
                time.sleep(5)
                if not utiliy.is_app_runing(self.app_package):
                    if failed_time > 2:
                            self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                            return False
                    failed_time += 1
                    continue
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)" % i)
                sys.stdout.flush()
                failed_time = 0
        else:
            self.logout(self.my_func_name(), "Timeout for %s test" % self.app_name)
            return False

    def wait_for_root_page(self, root_text="", decription_text="", timeout=300):
        failed_time = 0
        self.logout(self.my_func_name(), "Wait for %s root page" % self.app_name)
        for i in range(timeout):
            unclock_android_o_screen()
            if i % 5 == 0:
                kill_adb_uiautomator_block_old()
                kill_uiautomator()
            if decription_text == "":
                if self.device(resourceIdMatches=".+/%s$" % root_text).exists:
                    print
                    break
            else:
                if self.device(description="%s" % decription_text).exists:
                    print
                    break
            i += 1
            time.sleep(1)
            if not utiliy.is_app_runing(self.app_package):
                if failed_time > 6:
                        self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                        return False
                failed_time += 1
                continue
            sys.stdout.write("\r>>>Please wait for %s root page. %s (s)" % (self.app_name, i))
            sys.stdout.flush()
            failed_time = 0
        if i >= timeout:
            return False
        else:
            return True

    def get_score_info_data(self, key_code='', info_code='', index="", timeout=10):
        icount = 0
        score = ""
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            unclock_android_o_screen()
            if len(index) == 0:
                app_dev = self.device(resourceIdMatches=".+/%s$" % key_code)
            else:
                app_dev = self.device(resourceIdMatches=".+/%s$" % key_code, index=index)
            if app_dev.exists:
                try:
                    score = app_dev.info[info_code]
                except Exception:
                        self.logout(self.my_func_name(), "get score is failed")
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        return score

    def get_info_data(self, key_code='', info_code='', index="", timeout=10):
        icount = 0
        raw_data = ""
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            unclock_android_o_screen()
            if len(index) == 0:
                app_dev = self.device(resourceIdMatches=".+/%s$" % key_code)
            else:
                app_dev = self.device(resourceIdMatches=".+/%s$" % key_code, index=index)
            if app_dev.exists:
                try:
                    raw_data = app_dev.info[info_code]
                except Exception, e:
                        self.logout(self.my_func_name(), "get raw_data is failed")
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        return raw_data

    def click_ui_button_by_resourceIdMatches(self, key_code, not_id=False, timeout=10, package=''):
        icount = 0
        kill_adb_uiautomator_block_old()
        self.logout(self.my_func_name(), "%s click..." % key_code)
        while icount < timeout:
            unclock_android_o_screen()
            if package == '' and not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            if not_id:
                app_dev = self.device(resourceIdMatches="%s" % key_code)
            else:
                app_dev = self.device(resourceIdMatches=".+/%s$" % key_code)
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        if icount > 0:
            return False
        else:
            return True

    def click_ui_button_by_description(self, key_code='', descriptioncon='', index_nu='', timeout=10):
        icount = 0
        kill_adb_uiautomator_block_old()
        self.logout(self.my_func_name(), "%s click..." % key_code)
        while icount < timeout:
            unclock_android_o_screen()
            if not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            if not "" == index_nu:
                if not "" == key_code:
                    app_dev = self.device(index=index_nu, description=key_code)
                if not "" == descriptioncon:
                    app_dev = self.device(index=index_nu, descriptionContains=descriptioncon)
            else:
                if not "" == key_code:
                    app_dev = self.device(description=key_code)
                if not "" == descriptioncon:
                    app_dev = self.device(descriptionContains=descriptioncon)      
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        if icount > 0:
            return False
        else:
            return True

    def click_ui_button_by_text_to_right_resourceIdMatches(self, test_text, key_code, timeout=10):
        icount = 0
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            unclock_android_o_screen()
            if not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            app_dev = self.device(text=test_text)
            if app_dev.exists:
                right_bt = app_dev.right(resourceIdMatches=".+/%s$" % key_code)
                if right_bt.exists:
                    right_bt.click()
                    icount = 0
                    break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        if icount > 0:
            return False
        else:
            return True

    def click_ui_button_by_text_or_resid(self, key_code='', resid='', timeout=10):
        icount = 0
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            unclock_android_o_screen()
            if not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            if resid == "":
                app_dev = self.device(text=key_code)
            else:
                app_dev = self.device(resourceId=resid)
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        if icount > 0:
            return False
        else:
            return True

    def wait_for_open_spacial_function(self, sp_text="", resourceIdMatches_txt="", timeout=600):
        failed_time = 0

        self.logout(self.my_func_name(), "Wait for %s spacial function: %s" % (self.app_package, sp_text))
        for i in range(timeout):
            unclock_android_o_screen()
            if i % 5 == 0:
                kill_adb_uiautomator_block()
            if resourceIdMatches_txt == "":
                if self.device(text=sp_text).exists:
                    return True
            else:
                if self.device(resourceIdMatches=".+/%s$" % resourceIdMatches_txt).exists:
                    return True
            i += 1
            time.sleep(1)
            if not utiliy.is_app_runing(self.app_package):
                if failed_time > 6:
                        self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                        return False
                failed_time += 1
                continue
            failed_time = 0
        return False

    def click_ui_button_by_text(self, key_code="", textcont="", index_nu="", timeout=10, skip_utiliy=False):
        icount = 0
        kill_adb_uiautomator_block_old()
        while icount < timeout:
            unclock_android_o_screen()
            if not skip_utiliy and not utiliy.is_app_runing(self.app_package):
                self.logout(self.my_func_name(), "%s test is failed..." % self.app_package)
                return False
            if not "" == index_nu:
                if not "" == key_code:
                    app_dev = self.device(index=index_nu, text=key_code)
                if not "" == textcont:
                    app_dev = self.device(index=index_nu, textContains=textcont)
            else:
                if not "" == key_code:
                    app_dev = self.device(text=key_code)
                if not "" == textcont:
                    app_dev = self.device(textContains=textcont)              
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block_old()
        if icount > 0:
            return False
        else:
            return True

    def push_data(self, lodir, redir="/sdcard/"):
        build_info = os.popen('adb shell getprop |grep system.build.fingerprint').read()
        build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)
	if build_version and build_version[0] == '10':
           redir = "/storage/emulated/10/"
        os.system("adb push %s %s" % (lodir, redir))
        os.system("adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://%s%s" % (redir, os.path.basename(lodir)))
        
    def click(self, x, y):
        os.system("adb shell input tap %d %d" % (x, y))
        time.sleep(1)

    def click_by_event(self, keyevent):
        os.system("adb shell input keyevent %s" % keyevent)
        time.sleep(1)

    def killapp(self):
        self.click_by_event("KEYCODE_APP_SWITCH")
        self.dpad_down()
        self.dpad_down()
        self.click_by_event("DEL")
        self.click_by_event("HOME")

    def dpad_center(self):
        os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')

    def dpad_up(self):
        os.system('adb shell input keyevent KEYCODE_DPAD_UP')

    def dpad_down(self):
        os.system('adb shell input keyevent KEYCODE_DPAD_DOWN')

    def system_setup(self, tog_airplane=False, tog_wifi=False, tog_bt=False, tog_gps=False, tog_display=True):
        '''
        initial state
        airplane    off
        wifi        on
        bt          on
        gps         on
        display     15sec
        '''

        # toggle airplane state
        if tog_airplane:
            os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
            self.dpad_up()
            self.dpad_up()
            self.dpad_center()
            self.killapp()

        # toggle wifi
        if tog_wifi:
            os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
            self.dpad_up()
            self.dpad_up()
            self.dpad_up()
            self.dpad_center()
            self.killapp()

        # toggle gps
        if tog_gps:
            os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
            self.dpad_up()
            self.dpad_up()
            self.dpad_center()
            self.killapp()

        # toogle bluetooth
        if tog_bt:
            os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
            self.dpad_up()
            self.dpad_up()
            self.dpad_up()
            self.dpad_center()
            self.killapp()

        if tog_display:
            os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
            self.dpad_up()
            self.dpad_up()
            for i in range(3):
                self.dpad_down()
            self.dpad_center()
            for i in range(8):
                self.dpad_down()
            self.dpad_up()
            self.dpad_center()
            self.killapp()

        os.system('adb shell am force-stop com.android.settings')
