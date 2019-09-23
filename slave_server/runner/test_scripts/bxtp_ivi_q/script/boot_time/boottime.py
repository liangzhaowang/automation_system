import os
import sys
import time
import serial
import argparse


def logPrint(msg):
    print msg

class SimpleTest:
    def __init__(self, autoFlag, hostPassword):
        self.startTime = 0
        self.endTime = 0
        self.resultTime = 0
        self.flag = autoFlag
        self.pwd = hostPassword
        self.serialPort = serial.Serial('/dev/ttyUSB3', '115200', 8)


    def checkPower(self, mode=0):
        if mode:
            if not os.popen("adb wait-for-device").read() and os.popen('adb shell getprop dev.bootcomplete').read().strip() == '1':
                return True
            else:
                return False
        else:
            time.sleep(1)
            if os.popen("adb devices").read().split('\n')[1] == '':
                logs("DUT is power off and please press inition button")
            else:
                logs("DUT is power on,system will exit!")
                sys.exit()

    def achiveResult(self):
        if self.flag:
            logs("Automation Test Begin shutdown DUT")
            Auto_Realy08(3).create_relaycmd()
            time.sleep(30)
            if os.popen("adb devices").read().split('\n')[1] == '':
                logs("Shutdown complete Begin power on...")
                time.sleep(1)
                Auto_Realy08(1).create_relaycmd()
                self.startTime = time.time()
                logs("Automation start time is:{}".format(self.startTime))
        else:
            logs("Manual Test Begin check serial status")
            self.checkPower()
            while True:
                serLog = self.serialPort.readline()
                if serLog.find('ABL:') != -1:
                    self.startTime = time.time()
                    self.serialPort.close()
                    logs("Manual start time is:{}".format(self.startTime))
                    break
        while True:
            if self.checkPower(1) and os.popen("adb logcat --regex 'Starting\ phase\ 1000' --max-count 1").readline():
                self.endTime = time.time()
                break

        self.resultTime = float("%.3f"%(self.endTime - self.startTime))
        if self.flag:
            tr.result(self.resultTime)
            tr.save()
        return self.resultTime

def usage():
    parser = argparse.ArgumentParser(description="simple tool for boot time")
    parser.add_argument('-a', '--automation', dest='automation', action='store_true', help='automation execute script')
    parser.add_argument('-p', '--pwd', dest='linux_password', type=str, default='', help='password for linux host')
    return parser.parse_args()

if __name__ == "__main__":
    linux_pwd = ''
    auto_flag = False
    logs = logPrint
    args = usage()
    if args.automation:
        from atf import TestResult, TestLogger
        from src.AutoTest import *
        tr = TestResult(__file__)
        logs = TestLogger().get_logger("process").info
        logs("Automation test mode")
        auto_flag = True
    else:
        logs("Manual test mode")
    if args.linux_password:
        linux_pwd = args.linux_password
    else:
        logs("Must input linux host passwd,useage: '-p inux_pwd'")
        sys.exit()
    os.system("echo %s|sudo -S chmod 777 /dev/ttyUSB3" % linux_pwd)
    logs("Boot time is {} second".format(SimpleTest(auto_flag, linux_pwd).achiveResult()))