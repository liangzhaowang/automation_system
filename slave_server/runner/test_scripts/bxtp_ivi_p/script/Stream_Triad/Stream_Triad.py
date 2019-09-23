#! /usr/bin/env python
# coding=utf-8
import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block
from runner.operation_lib.base_lib.exception_operation import kill_adb_uiautomator_block_old
from runner.operation_lib.base_lib.exception_operation import get_define_urlt_usb
from runner.operation_lib.base_lib.watt_opteration import watt_operate
from runner.operation_lib.base_lib import system_operation
from ATF import TestResult, TestLogger

logger = TestLogger().get_logger("process")


def set_settings():
    logger.info(">>>>>>Setup settings<<<<<<")
    time.sleep(2)
    kill_adb_uiautomator_block()
    try:
        os.system("adb root")
        system_operation.turn_airplane('1')
        system_operation.turn_wifi('0')
        system_operation.turn_bluetooth_p('0')
        system_operation.turn_gps('0')
        time.sleep(1)
        os.system("adb root")
        time.sleep(2)
    except Exception, e:
        logger.error("set_settings error")
        return False


def prepare_data():
    logger.info(">>>>>>Push Data to DUT<<<<<<")
    try:
        os.system("adb root")
        time.sleep(2)
        kill_adb_uiautomator_block()
        os.system("adb shell 'sync && echo 3 > /proc/sys/vm/drop_caches'")
        time.sleep(2)
        kill_adb_uiautomator_block()
        os.system("adb push ./src/stream_icc_openmp_static_xSSSE3 /data/")
        time.sleep(2)
        kill_adb_uiautomator_block()
        os.system("adb shell chmod 777 /data/stream_icc_openmp_static_xSSSE3")
        time.sleep(2)
        logger.info(">>>>>>Poweroff the screen<<<<<<")
        time.sleep(2)
        with open(os.path.join("runner/operation_lib/host_passwd")) as pwdfp:
            host_passwd = pwdfp.read()
        os.system("echo '"+host_passwd+"' | sudo -S python ./operation_lib/base_lib/relay08_ctrl_button.py -p 1 -c "+get_define_urlt_usb())
        time.sleep(1)
        os.system("adb root")
    except Exception, e:
        logger.error("prepare_data error %s" % e)
        return False

def run_test(log,watt_operat):
    logger.info(">>>>>>Begin Testing<<<<<<")
    try:
        count = 0
        while count < 60:
            cline=os.popen("adb root").read().strip()
            if "is already running as root" in cline:
                if watt_operat.watt_flags:
                    watt_operat.start_watt()
                # time.sleep()
                command='adb shell /data/stream_icc_openmp_static_xSSSE3 >'
                os.system(command+log)
                logger.info(command+log)
                time.sleep(2)
                result = collect_result(log)
                break
            logger.info("Devices is offline now,please retry after 2 seconds")
            time.sleep(2)
            count+=1
        if count >= 60:
            if watt_operat.watt_flags:
                watt_operat.stop_watt()               
            return False
        if watt_operat.watt_flags:
            watt_operat.stop_watt() 
            try:
                watt_operat.watt_result_treat()
            except Exception, e:
                logger.error("watt_operate error %s." % e)
                return False
        return result

    except Exception, e:
        logger.error("run_test error:%s" % e)
        return False


def collect_result(log):
    Triad = open(log).readlines()
    f=Triad[29].split()
    fps_result=f[1]
    if fps_result == '':
        logger.info("fps_result has no data....")
        return False
    else:
        return fps_result

def main():
    tr = TestResult(sys.argv)
    watt_operat = watt_operate(tr.output_path, tr.current_loop)
    set_settings()
    prepare_data()
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log = log_dir+"/result.txt"
    result=run_test(log, watt_operat)
    if result == '':
        logger.error("stream_Triad value not found")
        return False
    logger.info("Stream_Triad value is:"+str(result))
    time.sleep(5)
    kill_adb_uiautomator_block_old()
    time.sleep(1)
    tr.result('Stream_Triad_Rate', result, 'MB/s')
    tr.save()
    time.sleep(10)


if __name__ == '__main__':
    main()
