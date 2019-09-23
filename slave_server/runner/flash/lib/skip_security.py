import os
import re
import subprocess
import time


def isBoot(wait_count=60):
    print 'check the device boot status'
    time.sleep(1)
    waitcount = 0
    while waitcount <= wait_count:
        if os.popen('adb shell getprop dev.bootcomplete').read().strip() == '1':
            print 'boot complete,start skip google security'
            return True
        else:
            print 'device offline,wait for boot'
            time.sleep(1)
            waitcount += 1
        return False

def installApk():
    print 'start install apk for device'
    time.sleep(1)
    subprocess.Popen('adb install ./runner/flash/lib/JIO.apk', shell=True)


def checkLog(timeout=60):
    print 'start ckeck logcat for vending window'
    time.sleep(1)
    timeinit = 0
    while timeinit <= timeout:
        if re.search('{com\.android\.vending/com\.google\.android\.finsky\.verifier\.impl\.ConsentDialog}*', os.popen('adb shell logcat -d |grep activity').read()):
            print 'find the google vending window,start click'
            time.sleep(1)
            for i in range(10):
                os.system('adb shell input tap 1176 593')
                time.sleep(1)
            print 'skip succuess'
            break
        print 'not find the window,waiting....'
        timeinit += 5
        time.sleep(5)

def startSkip():
    if isBoot():
        installApk()
        checkLog()
    else:
        print 'skip failed, no devices boot'

