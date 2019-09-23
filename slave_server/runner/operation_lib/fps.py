#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import re
import inspect
from runner.operation_lib.base_lib.thread_ctrl import FuncThread
from atf import TestLogger
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
logger = TestLogger().get_logger("process")


class test_fps:
    def __init__(self,case_name, activity_name):
        self.case_name = case_name
        self.tools_path = CUR_DIR + '/../test_src/fpstool2/FPStool2.py'
        self.activity_name = activity_name
        self.case_mode = ['MPEG4', 'VP9', 'H264', 'H265']
    def run_fpstool(self, log_out):
        if self.case_name.split("_")[0] in self.case_mode:
            self.activity_name = "com.android.gallery3d/com.android.gallery3d.app.MovieActivity#0"
        command = "python " + self.tools_path + " -c --debug=1 --legacy 'SurfaceView - "+self.activity_name+"' -n 1 > " +log_out
        logger.info(command)
        os.system(command)
    
    def run_fpstool_for_opera(self, log_out):
        if self.case_name.split("_")[0] in self.case_mode:
            self.activity_name = "com.opera.browser/com.opera.android.BrowserActivity#0"
        command = "python " + self.tools_path + " -c --debug=1 --legacy 'SurfaceView - "+self.activity_name+"' -n 1 > " +log_out
        logger.info(command)
        os.system(command)
    
    def run_fpstool_ext(self, log_out):
        if self.case_name.split("_")[0] == "H264" or self.case_name.split("_")[0] == "H265":
            self.activity_name="com.android.gallery3d/com.android.gallery3d.app.MovieActivity#0"
        command="python "+ self.tools_path + " -c --debug=1 --legacy " + self.activity_name+ "-n 1 "+" > " + log_out
        logger.info(command)
        os.system(command)
        
    #get function name
    def my_func_name(self):
        return inspect.stack()[1][3]

    #logout
    def logout(self, function_name, log_message):
        logger.info(">>>%s:" % function_name+log_message)

    def doInThread(self, func, *params, **paramMap):
        ft = FuncThread(func, *params, **paramMap)
        ft.setDaemon(True)
        ft.start()
        return ft

    def collect_result(self,log):
        s = os.popen("cat "+log+" |grep -a arithmetic").read()
        p = re.compile(r'\(arithmetic\):(.+)')
        results = re.findall(p, s)
        num = len(results)
        result_sum = 0
        for result in results:
            if result.strip() == '0.0':
                num -= 1
            result_sum = result_sum + float(result)
        if num == 0:
            self.logout(self.my_func_name(), "num == 0,exception error")
            return 0.0
        avg_result = float(result_sum) / int(num)
        return round(avg_result, 2)

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
