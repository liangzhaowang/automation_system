import os
import time
from runner.operation_lib.base_lib.ctrl_relay08_threading import create_relay08_cmd
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.ctrl_relay08_threading import control_relay08_port_thread
from uiautomator import Device


def replug_usb3():
    try:
        USBthread = control_relay08_port_thread(0, "replug_ttyUBS3", 2, 3)
        USBthread.start()
    except Exception, e:
        print e


class Turn_Seting():
    def __init__(self, state):
        self.device = Device()
        self.state = state

    def get_state(self, key):
        time.sleep(3)
        text = os.popen('adb shell settings get global '+key).readlines()
        former_state = 'Error'
        if len(text) > 0:
            former_state = text[0].strip()
            print(key+' current state is : %s' % former_state)
        return former_state

    def turn_airplane(self):
        if self.state == self.get_state('airplane_mode_on'):
            print('airplane already turned ' + self.state)
            return True

        for i in range(4):
            os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
            kill_adb_uiautomator_block_old()
            self.device(text="Airplane mode").click.wait()
            time.sleep(1)
            os.system('adb shell am force-stop com.android.settings')
            if self.state == self.get_state('airplane_mode_on'):
                return True
        return False


class Auto_Realy08():
    def __init__(self, line):
        self.line = line

    def create_relaycmd(self):
        create_relay08_cmd(self.line)
