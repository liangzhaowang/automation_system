#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
from runner.operation_lib.base_lib.UI_interface_operation import ui_operation
from runner.operation_lib.base_lib import system_operation
from atf import TestResult, TestLogger


def set_up(log_mes):
    log_mes.info(">>>>>>>>>>Set_up<<<<<<<<<<")
    time.sleep(2)
    try:
        system_operation.turn_wifi(0)
        system_operation.turn_bluetooth(0)
        system_operation.turn_gps(0)
        system_operation.turn_airplane(1)
        system_operation.set_display_time()
    except Exception, e:
        log_mes.error("excption error :%s"%e)
        return False


def run_test(log_dir, log_mes, ui_operat):
    log_mes.info(">>>>>>>>>>>Begin_test<<<<<<<<")
    time.sleep(2)
    ui_operat.clear_recent()
    time.sleep(30)
    try:
        dev_test = ui_operat.device(resourceIdMatches='.+/search_plate_padding_frame$')
        if dev_test.exists:
            log_mes.info("Homescreen enable Success")
        else:
            log_mes.info("Homescreen enable Failed")
            return False
    except Exception,e:
        return False
    time.sleep(2)
    log_mes.info(">>>>>>>>>>Start watt<<<<<<<<<<")
    if ui_operat.watt_operate.watt_flags:
        ui_operat.watt_operate.start_watt()
    for i in range(90):
        i+=1
        time.sleep(1)
        sys.stdout.write("\r>>>>>>>>>Please wait for test:%s(sec)"%i)
        sys.stdout.flush()
    print
    time.sleep(2)
    fs_watt=os.popen("adb shell ls /data/").readlines()
    i='watt.txt\n'
    if fs_watt.count(i) != 0:
        log_mes.info('watt log exists')
        os.system("adb pull /data/watt.txt %s"%log_dir)
        result = 1
    else:
        log_mes.info('watt log not found')
        result = 0
    if ui_operat.watt_operate.watt_flags:
        ui_operat.watt_operate.stop_watt() 
        try:
            ui_operat.watt_operate.watt_result_treat()
        except Exception,e:
            log_mes.error("watt_operate error %s."%e)
            return False
    return result


def main():
    tr = TestResult(sys.argv)
    ui_operat = ui_operation(tr.output_path, tr.current_loop)
    log_mes = TestLogger().get_logger("process")
    set_up(log_mes)
    time.sleep(2)
    log_dir = tr.result_dir
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    if not ui_operat.watt_operate.watt_flags:
        log_mes.error("please open watt_flag in config.xml!")
        return False
    result = run_test(log_dir, log_mes, ui_operat)
    if not result:
        return False
    log_mes.info("Homescreen Static watt is: %s" % result)
    tr.result('Homescreen_Static', result, 'bool')
    tr.save()


if __name__ == '__main__':
    main()
