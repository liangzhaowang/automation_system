#! /usr/bin/env python
# coding=utf-8
import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.UI_interface_operation import ui_operation
from ATF import TestResult, TestLogger


def prepare_data(ui_operat, log):
    kill_adb_uiautomator_block()
    log.info(">>>>>>>>Push data to DUT<<<<<<<<")
    try:
        time.sleep(2)
        os.system("adb root")
        time.sleep(2)
        src_file1="./src/cpufreq-bench"
        src_file2="./src/perf"
        src_file3="./src/sysbench"
 
        ui_operat.push_data(src_file1,'/data/')
        ui_operat.push_data(src_file2,'/data/')
        ui_operat.push_data(src_file3,'/data/')

        os.system("adb shell chmod 777 /data/cpufreq-bench")
        os.system("adb shell chmod 777 /data/perf")
        os.system("adb shell chmod 777 /data/sysbench")
    except Exception, e:
        log.info("prepare_data error: " + e.message)
        return False


def run_test(log, ui_operat, logs):
    kill_adb_uiautomator_block()
    logs.info( ">>>>>>>>Begin_test<<<<<<<<")
    try:
        time.sleep(2)
        command="adb shell /data/perf bench sched messaging -g 64 >"
        kill_adb_uiautomator_block()
        os.system(command+log)
        logs.info(command+log)
        if ui_operat.watt_operate.watt_flags:
            ui_operat.watt_operate.start_watt()
        time.sleep(5)
        result = collect_result(log,logs)
        if ui_operat.watt_operate.watt_flags:
            ui_operat.watt_operate.stop_watt()
            try:
                ui_operat.watt_operate.watt_result_treat()
            except Exception,e:
                logs.error("watt_operate error %s."%e)
                return False
        if not result:
            logs.error("No result data,test failed!!!!!!")
            return False
        else:
            return result
    except Exception, e:
        logs.error("run_test error :%s !!!!!!" % e)
        return False


def collect_result(log, logs):
    kill_adb_uiautomator_block()
    logs.info(">>>>>>>>Collect_result<<<<<<<<")
    time.sleep(2)
    with open(log) as tfp:
        total_time = tfp.readlines()
    try:
        result=total_time[4].strip().split()[2]
        result=round(float(result), 2)
    except Exception, e:
        logs.error("result file open error %s" % e)
        return False
    if result == '':
        logs.error("collect_result error")
        return False
    else:
        return result


def main():
    tr = TestResult(sys.argv)
    ui_operat = ui_operation(tr.result_dir, tr.current_loop)
    logs = TestLogger().get_logger("process")
    prepare_data(ui_operat, logs)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log = log_dir + '/result.txt'
    result = run_test(log, ui_operat, logs)
    if not result:
        logs.error("test_result have no data!!!!")
        return False
    logs.info("sched messaging -g 64: %s" % result)
    time.sleep(2)
    tr.result('Perf_sched_messaging_64', result, 'sec')
    tr.save()
    time.sleep(2)
    os.system("adb root")
    time.sleep(2)
    os.system("adb shell rm /data/cpufreq-bench")
    os.system("adb shell rm /data/perf")
    os.system("adb shell rm /data/sysbench")
    kill_adb_uiautomator_block()


if __name__ == '__main__':
    main()





