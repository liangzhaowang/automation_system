#!/usr/bin/env python

import os
import zipfile
import time
from conf import conf
from base_lib.ctrl_relay08_threading import create_relay08_cmd


def zip_file(startdir, file_news):
    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(startdir):
        fpath = dirpath.replace(startdir, '')
        fpath = fpath and fpath + os.sep or ''
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath+filename)
    z.close()


def reconnect_power():
    create_relay08_cmd(3, 2)


def reconnect_usb():
    create_relay08_cmd(2, 2)


def press_power_key():
    create_relay08_cmd(1)


def hard_reboot():
    print "===============> hard reboot <================"
    reconnect_power()
    time.sleep(10)
    press_power_key()
    for i in range(3):
        if wait_device_bootcomplete():
            return True
        else:
            hard_reboot()
    return False
 

def enter_fastboot_mode():
    cmd_reset = "echo '" + conf.host.PASSWD + "' | sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c r"
    os.system(cmd_reset)
    time.sleep(2)
    cmd_fastboot = "echo '" + conf.host.PASSWD + "' | sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n4#"
    os.system(cmd_fastboot)
    time.sleep(5)


def startup_by_usb():
    cmd_startup = "echo '" + conf.host.PASSWD + "' | sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"  # modify by yuwei@20170224
    os.system(cmd_startup)


def is_app_runing(app_name):
    ret = os.popen("adb shell ps | grep " + app_name).readlines()
    if len(ret) > 0:
        return True
    else:
        False

def wait_device_bootcomplete(timeout=90):
    for i in range(timeout):
        if os.popen('adb shell getprop dev.bootcomplete').read().strip() == '1':
            return True
        else:
            time.sleep(1)
    return False
        
