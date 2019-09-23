import os
import time
import re
from runner.operation_lib import utiliy
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib import system_operation
from atf import TestResult

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

def wait_for_dev():
    for i in range(100):
        time.sleep(1)
        if os.popen('adb devices').readlines()[1] == '\n':
            continue
        else:
            print "123456"

        return True
    else:
        return False

def run_test(result_dir):
    if wait_for_dev():
        os.system("adb root")
        time.sleep(3)
        os.chdir("runner/test_scripts/bxtp_ivi_q/script/benchmark/multiway-media-test-transcode/")
        os.system("./run_transcode.sh 3 1")
        time.sleep(20)
        os.system("./run_decode.sh 3 33 1")
        time.sleep(20)
        os.system("./exec_case.sh 1 32 > " + os.path.join(result_dir, 'decodelog.txt'))
        time.sleep(20)
        os.chdir(os.path.abspath(os.path.join(os.getcwd(),"../../../../../..")))
    else:
        print " ...."
    result = collect_result(result_dir)
    if not result:
        return False
    time.sleep(2)
    return result

def collect_result(result_dir):
    try:
        result = 0.0
        with open(os.path.join(result_dir, 'decodelog.txt'), "r") as fread:
            for line in fread:
                if 'fps: ' in line:
                    i = 0
                    if i <= len(line):
                        try:
                            data = re.search(r'899, fps: (.+), fread_fps:', line).group(1)
                            result = result + float(data)
                            i += 1
                        except Exception, e:
                            print e
                            return 0
                        result = result/(i+1)
        if result == 0.0:
            return False
        else:
            return result
    except Exception, e:
        print e
        return False

def main():
    tr = TestResult()
    result_dir = tr.result_dir
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)
    result = run_test(result_dir)
    tr.result(result)
    tr.add_attachment(tr.result_dir + "/decodelog.txt")
    tr.save()

if __name__ == "__main__":
    main()