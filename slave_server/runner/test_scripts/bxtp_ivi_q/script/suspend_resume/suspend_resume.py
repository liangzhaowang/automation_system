#!/usr/bin/python

import os
import time
from runner.operation_lib.base_lib.ctrl_relay08_threading import control_relay08_port_thread
from runner.operation_lib.base_lib.exception_operation import wait_for_boot
from atf import TestResult


def get_suspend_resume_time_stamp():
    control_relay08_port_thread(port_id=1).start()          # click button
    for i in range(1000):
        time.sleep(1)
        if os.popen('adb devices').readlines()[1] == '\n':
            break                                              # into suspend
        else:
            continue
    else:
        return False
    time.sleep(10)
    control_relay08_port_thread(port_id=1).start()
    time.sleep(2)
    for r_time in range(180):
        time.sleep(1)
        if wait_for_boot():
            if r_time < 10:
                return True                         # suspend is sucessful
            else:
                return False
        else:
            return False
    return False


def main():
    tr = TestResult(__file__)
    if get_suspend_resume_time_stamp():
        tr.result("pass")
        tr.save()
    else:
        tr.result("fail")
        tr.save()

if __name__ == "__main__":
    if wait_for_boot():
        main()
    else:
        print "can't find devices"

