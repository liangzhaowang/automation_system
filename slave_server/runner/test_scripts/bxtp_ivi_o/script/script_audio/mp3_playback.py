#!/usr/bin/env python
# coding=utf-8
from uiautomator import device as d
import os,sys,thread
import time,re
sys.path.append('../../lib')
sys.path.append('lib')
from atf import TestResult
sys.path.append('../../operation_lib')
sys.path.append('operation_lib')
from base_lib.exception_operation import kill_adb_uiautomator_block
from base_lib.exception_operation import kill_adb_uiautomator_block_old
from base_lib import system_operation
from apptest import apptest
from fps import test_fps 
CUR_DIR=os.path.dirname(os.path.abspath(__file__))
out_dir=time.strftime('%Y%m%d_%H%M%S')
result = []
# def run_google_set():
#     if d(text="Back up & sync").exists:
#         d(resourceId="com.google.android.apps.photos:id/auto_backup_switch").click()
#         d.press.back()
#     kill_adb_uiautomator_block()
#     time.sleep(3)
#     # d.press.back()
#     kill_adb_uiautomator_block()
#     time.sleep(3)
#     if d(text="Keep backup off?").exists:
#         d(text="KEEP OFF").click()
#         kill_adb_uiautomator_block()
def choose_audio(mobile_test):
    # d(text='Rum Boogie').click()
    mobile_test.ui_operation.click_ui_button_by_text("Rum Boogie")
    time.sleep(2)
    mobile_test.ui_operation.click_ui_button_by_resourceIdMatches("fab_play",timeout=10)
    # if d(resourceIdMatches='.+/fab_play$').exists:
    #     d(resourceIdMatches='.+/fab_play$').click()
    mobile_test.ui_operation.click_ui_button_by_resourceIdMatches("pause")
    # d(resourceIdMatches='.+/pause$').click()
    time.sleep(2)
# def get_screen_off_time():
#     time.sleep(3)
#     text = os.popen('adb shell settings get system screen_off_timeout').readlines()
#     current_state = 'Error'
#     if len(text) > 0:
#         current_state = text[0].strip()
#         print 'current screen off time is {t}'.format(t=current_state)
# def set_15_secs():
#     if get_screen_off_time() == '15000':
#         print 'screen off time is already 15 secs'
#     else:
#         os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
#         d(text="Sleep").click()
#         d(text="15 seconds").click()
#         time.sleep(1)
#         os.system("adb shell am force-stop com.android.settings")

def get_volume():
    time.sleep(3)
    text = os.popen('adb shell settings get system volume_music').readlines()
    current_state = 'Error'
    if len(text) > 0:
        current_state = text[0].strip()
        print 'current screen off time is {t}'.format(t=current_state)
    
def set_volume():
    if get_volume() == '4':
        print 'volume is already 25%'
    else:
        os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
        d(text="Sound").click()  
        os.system('adb shell service call audio 3 i32 3 i32 4 i32 1')
        time.sleep(1)
        os.system("adb shell am force-stop com.android.settings")

def set_settings(log_mes):
    os.system('adb shell input keyevent 82')
    time.sleep(2)
    system_operation.turn_airplane('1')
    system_operation.turn_bluetooth('0')
    system_operation.turn_wifi('0')
    system_operation.turn_gps('0')
    
def Prepare_data(mobile_test):

    line = os.popen("adb shell ls /sdcard/music/music_gsma_44100_128k.mp3").read()
    print line
    copy_reboot = True
    if not "No such file or directory" in line:
        copy_reboot = False
    mobile_test.logout(mobile_test.my_func_name(), "-------------------copy_reboot="+str(copy_reboot))
    if copy_reboot:
        os.system("adb shell rm /sdcard/music/*.mp3")
        mobile_test.log.info(">>>>>>>> Push video to DUT <<<<<<<< ")
        time.sleep(2)
        mobile_test.ui_operation.push_data("./test_src/music_gsma_44100_128k.mp3","/sdcard/music/")
        time.sleep(2)
        system_operation.reboot_system()
    # os.system('adb push ./src/music_gsma_44100_128k.mp3 /sdcard/music')
    # time.sleep(2)
    # os.system("adb reboot")
    # os.system("adb wait-for-device")
    # time.sleep(30)
    # os.system('adb shell input keyevent 82')
    # time.sleep(1)
    # os.system("adb root")
    # time.sleep(2)
    # os.system("adb wait-for-device")
    print ">>>>>>>> Clear recent apps <<<<<<<<"
    kill_adb_uiautomator_block_old()
    mobile_test.ui_operation.clear_recent()
    # d.press.recent()
    # time.sleep(5)
    # kill_adb_uiautomator_block()
    # while d(resourceId='com.android.systemui:id/dismiss_task').exists:
    #     kill_adb_uiautomator_block()
    #     d(resourceId='com.android.systemui:id/dismiss_task').click()
    #     time.sleep(1)
    #     kill_adb_uiautomator_block()
    # kill_adb_uiautomator_block()
    # d.press.home()
    # time.sleep(1)
    print ">>>>>>>> Start Music test <<<<<<<< "
    os.system("adb shell stop media")
    os.system("adb shell setprop audio.offload.disable 1")
    os.system("adb shell start media")
    time.sleep(1)
    mobile_test.launch_app()
    # os.system('adb shell am start -n com.google.android.music/com.android.music.activitymanagement.TopLevelActivity')
    time.sleep(2)
    mobile_test.ui_operation.click_ui_button_by_text("SKIP")
    # if d(text='SKIP').exists:
    #     d(text='SKIP').click()

    # run_google_set()

def run_test(mobile_test,log):
    Prepare_data(mobile_test)
    choose_audio(mobile_test)
    # for i in range(180):
    #     i+=1
    #     time.sleep(1)
    #     sys.stdout.write("\r>>>Please wait for test complete ... %s(s)"%i)
    #     sys.stdout.flush()
    flag = False
    if mobile_test.ui_operation.wait_for_compelet_for_fps(timeout=180):
        flag = True
    os.system("adb shell stop media")
    time.sleep(2)
    return flag
    
def main():
    mobile_test = apptest(sys.argv,app_package = "com.google.android.music",app_activity="com.android.music.activitymanagement.TopLevelActivity",case_name = 'mp3_playback')
    set_settings(mobile_test.log)
    system_operation.set_display_time(mobile_test.log,displaytime=15000) #set_15_secs()
    log_dir=os.path.join(CUR_DIR,'./'+out_dir+'/')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log=log_dir+"result.txt"
    result = run_test(mobile_test,log)
    if result == False:
        return False
    tr = TestResult()
    tr.result(result)
    tr.save()
if __name__ == '__main__':
    main()
