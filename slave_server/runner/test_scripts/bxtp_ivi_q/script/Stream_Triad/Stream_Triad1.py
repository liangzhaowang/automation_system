import os
import time
import re
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from atf import TestResult


CUR_DIR = os.path.dirname(os.path.abspath(__file__))

class Stream:
    def __init__(self, tr):
        self.case_name = tr.case_name
        self.pre_cmd = tr.case_info["pre_cmd"] if 'pre_cmd' in tr.case_info else ''
        self.result = ''
        self.result_dir = tr.result_dir
        if not os.path.exists(self.result_dir):
            os.mkdir(self.result_dir)
        self.tr_name = tr.case_name
        self.data = ''
        for i in range(3):
            if self.main():
                break
        self.returncode = 0 if i < 2 else 1


    def prepare(self):
        os.system("adb root")
        os.system('adb push ' + "./runner/test_src/"+ 'stream_icc_openmp_static_xSSSE3' + ' /data')
        os.system("adb shell chmod 0777 /data/stream_icc_openmp_static_xSSSE3")


    def run_test(self):
        self.prepare()
        time.sleep(1)
        #if self.pre_cmd:
        os.system("adb root")
            # os.system('adb push ' + "./runner/test_src/"+ 'stream_icc_openmp_static_xSSSE3' + ' /data')
        print self.result_dir
        os.system('adb shell  < '+ os.path.join(CUR_DIR, 'prepare.txt')+'>' + os.path.join(self.result_dir, 'streamlog.txt'))
        #time.sleep(5)
        result = self.collect_result()
        if not result:
            return False

        return result

    def collect_result(self):
            try:
                result = ""
                with open(os.path.join(self.result_dir, 'streamlog.txt'), "r") as fread:
                    for line in fread:
                        if 'Total memory required =' in line:
                            try:
                                result = re.search(r'Total memory required = (.+) MiB', line).group(1)
                            except Exception, e:
                                print e
                                return 0
                if result == "":
                    return False
                return result
            except Exception, e:
                print e
                return False

    def main(self):
        system_operation.screen_on()
        time.sleep(1)
        try:
            system_operation.turn_bluetooth_p('0')
            system_operation.turn_wifi('0')
            os.system("adb shell input keyevent 26")
            time.sleep(3)
        except Exception:
            return False
        time.sleep(2)

        result = self.run_test()
        if not result:
            return False

        self.result = result
        return True

if __name__ == "__main__":
    tr = TestResult()
    stream=Stream(tr)
    tr.result(stream.result)
    tr.add_attachment(tr.result_dir + "/streamlog.txt")
    tr.save()
    exit(stream.returncode)
