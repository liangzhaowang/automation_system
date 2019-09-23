import os
import time
from runner.operation_lib.base_lib.ctrl_relay08_threading import create_relay08_cmd
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.ctrl_relay08_threading import control_relay08_port_thread
from runner.operation_lib.base_lib import system_operation
from uiautomator import Device

def replug_usb3():
    try:
        USBthread = control_relay08_port_thread(0, "replug_ttyUBS3", 2, 3)
        USBthread.start()
    except Exception, e:
        print e

def setsystem():
        system_operation.turn_wifi(0)
        system_operation.turn_bluetooth(0)

class Auto_Realy08():
    def __init__(self, line):
        self.line = line

    def create_relaycmd(self):
        create_relay08_cmd(self.line)
