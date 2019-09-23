import os
import time
import re
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from atf import TestResult


CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class FIO:
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
        os.system('adb push ' + os.path.join(CUR_DIR, 'sh', 'fio') + ' /data')
        os.system('adb push ' + os.path.join(CUR_DIR, 'sh', 'WD_drive_Prepare_script.sh') + ' /data')
        os.system("adb shell chmod a+x /data/fio")
        os.system("adb shell chmod a+x /data/WD_drive_Prepare_script.sh")
        os.system('adb shell <' + os.path.join(CUR_DIR,'prepare.txt'))

    def run_test(self):
        self.prepare()
        time.sleep(1)
        if self.pre_cmd:
            os.system("adb root")
            if self.pre_cmd == 'read.txt':
                os.system('adb push ' + os.path.join(CUR_DIR, 'sh', 'fio_rand_read-sh') + ' /data')
                os.system('adb shell < ' + os.path.join(CUR_DIR, self.pre_cmd))
                time.sleep(5)
                os.system('adb pull /data/FIO_Rand_RD_Run2.txt ' + os.path.join(self.result_dir, 'FIO_Rand_RD_Run.txt'))
            else:
                os.system('adb push ' + os.path.join(CUR_DIR, 'sh', 'fio_rand_write-sh') + ' /data')
                os.system('adb shell < ' + os.path.join(CUR_DIR, self.pre_cmd))
                time.sleep(5)
                os.system('adb pull /data/FIO-Random-Write-Run2.txt ' + os.path.join(self.result_dir, 'FIO-Random-Write-Run.txt'))
        result = self.collect_result()
        if not result:
            return False
        time.sleep(2)
        return result

    def collect_result(self):
        try:
            result = ""
            if self.pre_cmd == 'read.txt':
                with open(os.path.join(self.result_dir, 'FIO_Rand_RD_Run.txt'), "r") as fread:
                    line = fread.readlines()
                    if line:
                        for index in line:
                            if index.count('READ: bw=') == 1 or index.count('WRITE: bw=') == 1:
                                try:
                                    result = index.split(',')[0].split('=')[1].split('MiB/s')[0]
                                except Exception, e:
                                    print e
                                    return 0
            else:
                with open(os.path.join(self.result_dir, 'FIO-Random-Write-Run.txt'), "r") as fread:
                    line = fread.readlines()
                    if line:
                        for index in line:
                            if index.count('READ: bw=') == 1 or index.count('WRITE: bw=') == 1:
                                try:
                                    result = index.split(',')[0].split('=')[1].split('MiB/s')[0]
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
       kill_adb_uiautomator_block()
       time.sleep(1)
       try:
           system_operation.turn_bluetooth('0')
           system_operation.turn_wifi('0')
       except Exception:
           return False
        time.sleep(2)

        result = self.run_test()
        if not result:
            return False

        print result
        self.result = result
        return True

if __name__ == "__main__":
    tr = TestResult()
    fio = FIO(tr)
    tr.result(fio.result)
    tr.add_attachment(tr.result_dir + "/FIO_Rand_RD_Run.txt")
    tr.save()
    exit(fio.returncode)


