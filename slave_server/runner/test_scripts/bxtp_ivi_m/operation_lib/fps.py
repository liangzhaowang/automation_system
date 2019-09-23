#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import threading
import time
import sys
import re
import inspect
sys.path.append('../../operation_lib')
sys.path.append('operation_lib')
from base_lib.exception_operation import kill_adb_uiautomator_block
from base_lib.exception_operation import kill_adb_uiautomator_block_old
from base_lib import system_operation
from base_lib.exception_operation import wait_for_device_reboot
from base_lib.exception_operation import app_exception_kill_case
from base_lib.thread_ctrl import FuncThread
from base_lib.makelog import makelog
from base_lib.makelog import log_info
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])


class test_fps:
    def __init__(self,case_name,activity_name):
        self.case_name = case_name
        self.tools_path =CUR_DIR+'/../'+'./src/fpstool2/FPStool2.py'
        self.activity_name = activity_name
        self.log_mes = log_info.logger


    def run_fpstool(self,log_out):
        command="python "+ self.tools_path +" -c --debug=1 --legacy 'SurfaceView - "+self.activity_name+"' > " +log_out
        self.log_mes.info(command)
        os.system(command)
    
    def run_fpstool_ext(self,log_out):
        command="python "+ self.tools_path +" -c --debug=1 --legacy "+self.activity_name+" > " +log_out
        self.log_mes.info(command)
        os.system(command)
        
    #get function name
    def my_func_name(self):
        return inspect.stack()[1][3]
    #logout
    def logout(self,function_name,log_message):
        self.log_mes.info( ">>>%s:"%function_name+log_message)

    def doInThread(self,func, *params, **paramMap):
        ft = FuncThread(func, *params, **paramMap)
        ft.setDaemon(True)
        ft.start()
        return ft

    def collect_result(self,log):
        s = os.popen("cat "+log+" |grep -a arithmetic").read()
        p = re.compile(r'\(arithmetic\):(.+)')
        results = re.findall(p,s)
        num = len(results)
        result_sum = 0
        for result in results:
            if result.strip() == '0.0':
                num -= 1
            result_sum = result_sum + float(result)
        if num == 0:
            self.logout( self.my_func_name(),"num == 0,exception error")
            return 0.0
        avg_result = float(result_sum) / int(num)
        return round(avg_result,2)

    
    def kill_fps_tools(self):
        cmdfp = os.popen("ps -aux | grep '"+self.tools_path+"'")
        lines = cmdfp.readlines()
        kill_fps_list = []
        for item in lines:
            if "grep" not in item:
                # print item
                kill_fps_list.append(item.split()[1])
        if len(kill_fps_list) > 0:
            for item in kill_fps_list:
                os.system("kill -9 "+item)	


if __name__ == '__main__':
    pass
