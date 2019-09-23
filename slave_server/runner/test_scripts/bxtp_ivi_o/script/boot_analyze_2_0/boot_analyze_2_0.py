#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import csv
import sys
import argparse
import threading
from collections import OrderedDict
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
reload(sys)
sys.setdefaultencoding('utf8')

CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
host_pwd = '123456' #Passwd for ubuntu host
show_png = False
auto_flag = False


def logprinter(msg):
    print msg

class cmd_port_thread (threading.Thread):
    """
    class control_ignition_thread
    """
    def __init__(self, cmd, time=0.1):
        """
        control_ignition_thread __init__
        """
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.time = time

    def run(self):
        """
        threading run
        """
        logs(self.cmd)
        time.sleep(self.time)
        os.system(self.cmd)


class Get_Logs:
    def __init__(self, log_path, auto_flag, config):
        self.log_path = log_path
        self.boot_is_complete = False
        self.auto = auto_flag
        self.conf = config

    def print_process(self, times=31):
        """
        print_process
        """
        for i in range(1, times):
            sys.stdout.write('>>' + "\b")
            sys.stdout.flush()
            time.sleep(0.03)
        logs("")

    def calc_wait_processtime(self, i):
        if i % 10 == 0:
            sys.stdout.writelines(str(i) + "%.." + "\b")
            return True
        else:
            return False

    def print_wait_process(self, times=1.0):
        """
        print_wait_process
        """
        sys.stdout.write('waiting...')
        sys.stdout.flush()
        for i in range(1, 100):
            if not self.calc_wait_processtime(i):
                sys.stdout.write('....' + "\b")
            sys.stdout.flush()
            time.sleep(times / 100)
        logs("100%")

    def adb(self, cmd):
        adb_command = 'adb ' + cmd
        return os.popen(adb_command).read()

    def wait_for_boot(self, timeout=70):
        logs('waiting for boot complete')
        for i in range(timeout):
            time.sleep(1)
            if self.adb('shell getprop dev.bootcomplete').lstrip().strip() == '1':
                self.boot_is_complete = True
                return True
        return False

    def reset_list(self, ids):
        idlist = []
        for line in ids:
            if line not in idlist:
                idlist.append(line)
        return idlist

    def serial_port_check(self, usb_name='usb3'):
        ids = []
        exclude_lines = ["ps -aux", "grep", "--color=auto"]
        count = 0
        flag = True
        usb_name1 = "tty" + usb_name.upper()
        find_lines = os.popen("ps -aux | grep " + usb_name + " | grep minicom").readlines()
        find_lines += os.popen("ps -aux | grep " + usb_name1 + " | grep minicom").readlines()
        find_lines += os.popen("ps -aux | grep minicom -s").readlines()
        for find_line in find_lines:
            for line in exclude_lines:
                if line in find_line:
                    flag = False
                    break
                else:
                    flag = True
            if flag:
                ids.append(find_line.split()[1])
        ids = self.reset_list(ids)
        for item in ids:
            if os.system("echo " + host_pwd + " |sudo -S kill " + item) == 0:
                logs("killing %s ...." % item)
                count += 1
            else:
                logs("kill %s is failed!!!" % item)
        if count == len(ids):
            return True
        else:
            return False

    def auto_run(self, log_path, conf):

        lines = []
        try:
            lines = conf['commands']
        except Exception, e:
            logs(e)
        runsecuss = 0
        if self.auto:
            Auto_Realy08(3).create_relaycmd()
            Auto_Realy08(2).create_relaycmd()
        while True:
            if self.serial_port_check():
                break
        time.sleep(20)
        try:
            for i in lines["start_thread"]:
                i = i.replace(r'$(host_pwd)', host_pwd)
                i = i.replace(r'$(cwd)', log_path)
                i = i.replace(r'$(pwd)', CUR_DIR)
                cmd_thread = cmd_port_thread(i)
                cmd_thread.start()
            time.sleep(2)
        except Exception, e:
            logs(e)
        if self.auto:
            Auto_Realy08(1).create_relaycmd()
        if len(lines["commands"]) > 0:
            if self.wait_for_boot():
                for line in lines["commands"]:
                    if runsecuss != 0:
                        logs("fail:%s" % line)
                    if line.startswith('sleep'):
                        self.print_wait_process(int(line.lstrip("sleep ")) + 0.0)
                    else:
                        line = line.replace(r'$(cwd)', log_path)
                        line = line.replace(r'$(pwd)', CUR_DIR)
                        logs(line)
                    runsecuss = os.system(line)
                    self.print_process()
        else:
            logs("read prerun_commands fails")

    def usbisok(self):
        """
        usbisok to scan /dev/ttyUSB3 is ok
        """
        if self.auto:
            logs("=============================================================")
            logs("Begin set normal shutdown please wait")
            time.sleep(2)
            os.system('adb root')
            time.sleep(2)
            try:
                Turn_Seting('1').turn_airplane()
            except Exception, e:
                logs("set airplane error:%s" % e)
            time.sleep(2)
            os.system('adb shell setprop sys.powerctl shutdown')
            time.sleep(3)
            logs("Set normal shutdown success")
            logs("=============================================================")
            time.sleep(30)
        else:
            raw_input("====== PLEASE MAKE SURE THE DUT IS POWER OFF & PRESS THE 'ENTER KEY' TO CONTINUE... ======")
            DevIces = os.popen("adb devices").read().split('\n')[1]
            if DevIces:
                logs('====== THE DUT (%s) IS NOT POWER OFF, SYSTEM WILL EXIT ======'% (DevIces))
                time.sleep(3)
                sys.exit()
            else:
                time.sleep(5)
        flag = False
        cmd = 'ls /dev/ttyUSB3'
        if self.auto:
            replug_usb3()
        try_times = 0
        while True:
            time.sleep(0.1)
            if os.system(cmd) != 0:
                logs('please plug in debug board USB')
                flag = True
            elif flag and os.popen(cmd).readlines()[0].split('\n')[-2] == '/dev/ttyUSB3':
                logs("====================================================================================")
                logs("When you see the log print as 'echo host_password | sudo -S python xxx> xxx/xxx.log'")
                logs("You must press ignition, After a moment, you will see the amazing result............")
                logs("====================================================================================")
                time.sleep(1)
                return True
            elif try_times > 60:
                logs("plug USB timeout!")
                return False
            elif try_times % 10 == 0 and self.auto:
                try_times += 1
                replug_usb3()
            else:
                logs("please replug debug board's USB!")
                try_times += 1
                time.sleep(1)

    def run_case(self):
        while not self.boot_is_complete:
            if self.usbisok():
                self.auto_run(self.log_path, self.conf)
            else:
                return
        logs("======================================================")
        logs("Parse all logs for Result,Please wait for done........")
        logs("=======================================================")
        self.print_wait_process(6.0)


class Logs_Parse:
    def __init__(self, log_path, config):
        self.log_path = log_path
        self.config = config
        self.init_data = self.get_data()
        self.tmplist = []

    def get_data(self):
        time_log = OrderedDict()
        for key_name in self.config['log'].keys():
            time_list = []
            logconfig = self.config['log'][key_name]['config']
            log_file = os.path.join(self.log_path, logconfig['log_name'])
            log_doc = open(log_file).read()
            if os.path.exists(log_file) and os.path.getsize(log_file) != 0 and not re.match('Could not open memory file',log_doc):
                try:
                    lines = open(log_file).readlines()
                    for i in self.config['log'][key_name]['tag']:
                        for line in lines:
                            time_filter = -1
                            if re.search(i['filter'], line):
                                time_filter = self.LogTime(self.config['log'][key_name]['config']['time_pattern'], line, self.config['log'][key_name]['config']['time_index'])
                            if time_filter >= 0 and not filter(lambda x:x[1] == i['name'], time_list):
                                time_tuple = time_filter, i['name']
                                time_list.append(time_tuple)
                except Exception, e:
                    logs("Get %s data Error:%s" % (key_name, e.message))
                    return False
                if self.config['log'][key_name]['config'].has_key('insert_data'):
                    insert_data = self.config['log'][key_name]["config"]["insert_data"]
                    if not filter(lambda x: x[1] == insert_data[1], time_list):
                        time_list.append(tuple(insert_data))
                if self.config['log'][key_name]['config']['parent_axis'] == 'main':
                    time_list.append((0.000, u'init'))
                time_log[key_name] = time_list
            else:
                logs("No data :{0}".format(log_file))
        return time_log

    def LogTime(self, pattern, log, Timesplit = 0):
        logTime = 0
        if re.search(pattern, log):
            Timelog = re.findall(pattern, log)[Timesplit]
            if pattern == '(\d+\.\d+)':
                logTime = float(Timelog)*10**3
            if pattern == '(\d+:\d+:\d+\.\d+)':
                logTime = (float(Timelog.split(':')[0])*3600+float(Timelog.split(':')[1])*60+float(Timelog.split(':')[2]))*10**3
            if pattern == '\s+(\d+)\sms':
                logTime = float(Timelog)
            if pattern == '\s+(\d+)s(\d+)ms':
                logTime = float(Timelog[0])*10**3+float(Timelog[1])
            if pattern == '\s+(\d+\.\d+)':
                logTime = float(Timelog)
        return logTime

    def FuzzyMatch(self, x, y):
        stamp_time = 0
        LogFunc = lambda log:log[0] if log[0] else log[1]
        fuzzyPattern = ':\s([a-zA-Z_].+)|\s([a-zA-Z_].+)'
        log_x = open(os.path.join(self.log_path, self.config['log'][x]['config']['log_name'])).readlines()
        log_y = open(os.path.join(self.log_path, self.config['log'][y]['config']['log_name'])).readlines()
        for i in log_x:
            if re.findall(fuzzyPattern, i):
                Log_x = (LogFunc)(re.findall(fuzzyPattern, i)[0])
            for j in log_y:
                if re.findall(fuzzyPattern, j):
                    Log_y = (LogFunc)(re.findall(fuzzyPattern, j)[0])
                    if not stamp_time and Log_x and Log_y and Log_x == Log_y:
                        timePattern_x = self.config['log'][x]['config']['time_pattern']
                        timePattern_y = self.config['log'][y]['config']['time_pattern']
                        stamp_time = self.LogTime(timePattern_y, j) - self.LogTime(timePattern_x, i)
        logs("Fuzzy Match: {0} {1} {2}".format(x, y, stamp_time))
        return stamp_time

    def data_parse(self):
        total = []
        result = []
        datas = {}
        for j in self.config['log'].keys():
            if 'tag' in self.config['log'][j] and j in self.init_data:
                try:
                    stamp_time = 0
                    tmp_list = []
                    if self.config['log'][j]['config']['parent_axis'] != 'main':
                        parent_log = self.config['log'][j]['config']['parent_axis']
                        for k in self.init_data[j]:
                            for l in self.init_data[parent_log]:
                                if k[1] == l[1]:
                                    stamp_time = l[0] - k[0]
                        if stamp_time == 0:
                            stamp_time = self.FuzzyMatch(j, parent_log)
                        if stamp_time == 0:
                            logs("{0}&{1} have no same log".format(j, parent_log))
                            break
                        for i in self.init_data[j]:
                            tmp_list.append((i[0]+stamp_time, i[1]))
                        self.init_data[parent_log].extend(tmp_list)
                        total = sorted(set(self.init_data[parent_log]), key=lambda x: x[0])
                except Exception, e:
                    logs("Parse {0} data Error:{1}".format(j, e.message))
                    break
        try:
            for i in total:
                temp_tuple = float("%.3f" % (i[0]*0.001)), i[1]
                result.append(temp_tuple)
            result = sorted(set(result), key=lambda x: x[0])
            for j in self.config["stage"]:
                data = self.generate_list(result, j)
                datas[j] = data
        except Exception, e:
            logs("Set display data Error:%s" % e.message)
        logs("Total:")
        for time_tag in result:
            time.sleep(0.1)
            logs(time_tag)
        for key, value in datas.items():
            logs(key+":")
            for line in value["stage"]:
                time.sleep(0.1)
                logs(line)
        self.write_csv(self.log_path, result, datas)
        result_data = 0
        result_log = ''
        for key in datas.keys():
            result_data = datas[key]["display"][-1][0]
            result_log = datas[key]["display"][-1][1]
        logs("=============================================================")
        logs("Result is:%s sec (End tag:'%s')" % (result_data, result_log))
        logs("=============================================================")
        return datas, result, result_data

    def generate_list(self, result, data):
        display = []
        stage = []
        content = {}
        stage_list = self.config["stage"][data]
        try:
            for m in stage_list:
                for n in m["durations"]:
                    for q in result:
                        if n == q[1]:
                            display.append(q)
            display = sorted(set(display), key=lambda x: x[0])
        except Exception, e:
            logs("Generate display_{0} data Error:{1}".format(data, e.message))
        try:
            for lines in stage_list:
                stage_time = -1
                for line in display:
                    if lines["start"] == line[1]:
                        stage_time = line[0]
                    if stage_time > -1 and lines["end"] == line[1] and (("%.3f" % (line[0] - stage_time), lines["name"]) not in stage):
                        stage.append(("%.3f" % (line[0] - stage_time), lines["name"]))
            content["display"] = display
            content["stage"] = stage
            content["data"] = data
            return content
        except Exception, e:
            logs("Generate stages failed:%s" % e.message)

    def write_csv(self, log_path, result, datas):
        try:
            with open(os.path.join(log_path,"report.csv"), 'wb') as csvFile:
                writer = csv.writer(csvFile, 'excel-tab')
                writer.writerow(["Total:"])
                for entry in result:
                    writer.writerow(entry)
                for key,value in datas.items():
                    writer.writerow("")
                    writer.writerow(["%s:" % key])
                    for stages in value["stage"]:
                        writer.writerow(stages)
                    writer.writerow("")
                    writer.writerow(["%s:" % (key+"_display")])
                    for stages in value["display"]:
                        writer.writerow(stages)
        except Exception, e:
            logs(e)

class Data_Bar():
    def __init__(self, data, stage, key_tag, show_png, log_path):
        self.data = data
        self.stage = stage
        self.log_path = log_path
        self.start = []
        self.duration = []
        self.categories = []
        self.tag = key_tag
        self.show = show_png

    def data_dic(self):
        tempdata = []
        try:
            for i in range(len(self.data)):
                tempdata.append(self.data[i])
            for i in range(len(tempdata)):
                if i+1 < len(tempdata):
                    if float(tempdata[i+1][0]) - float(tempdata[i][0]) > 0:
                        self.start.append(float(tempdata[i][0]))
                        self.duration.append(float("%.3f" % (float(tempdata[i+1][0]) - float(tempdata[i][0]))))
                        self.categories.append(tempdata[i][1]+"->"+tempdata[i+1][1])
            self.start.append(float(tempdata[-1][0]))
            self.duration.append(0)
            self.categories.append("Total")
            self.start.reverse()
            self.duration.reverse()
            self.categories.reverse()
            return {"a_starts": self.start, "b_durations": self.duration, "categories": self.categories}, {"phase": self.stage}
        except Exception, e:
            logs("generate data dict Error:%s" % e.message)
            return False

    def generate_bar(self):
        phase_x = []
        bar_len = []
        categories_x = []
        data, stage = self.data_dic()
        for i in stage["phase"]:
            bar_len.append(float(i[0]))
            phase_x.append(float(i[0]))
            categories_x.append(i[1])
        for j in range(len(phase_x)):
            if j != 0:
                phase_x[j] = phase_x[j] + phase_x[j-1]
        categories_x.append("")
        df = pd.DataFrame(data)
        ax = df.plot.barh(stacked=True, color=["#F0F8FF", "#4F94FF"])
        ax.set_yticklabels(data["categories"], rotation=0, fontsize='small')
        ax.legend(loc=5)
        phase_x.append(ax.get_xlim()[1])
        for i, a_v in enumerate(data["a_starts"]):
            ax.text(a_v*0.2, i - 0.18, str(a_v), color='#36648B', fontweight='bold')
        for j, b_v in enumerate(data["b_durations"]):
            if data["b_durations"][j] == 0:
                dcolor = "#FFFFFF"
            else:
                dcolor = "#FFA07A"
            ax.text(data["a_starts"][j] + b_v * 0.2, j - 0.18, str(b_v), color=dcolor, fontweight='bold')
        ax2 = ax.twiny()
        ax2.set_xticks(phase_x)
        ax2.set_xticklabels(categories_x, rotation=30, ha='left')
        bottom = len(data["a_starts"])
        bar_b = [bottom] * len(phase_x)
        bar_height = [0.5] * len(phase_x)
        bar_left = [0] + phase_x[:-1]
        bar_len += [phase_x[-1] - bar_left[-1]]
        colors = ["#8B0000", "#87CEFF", "#8A2BE2", "#71C671", "#CD3333", "#FFFFFF", "#8B0000", "#87CEFF", "#8A2BE2", "#71C671", "#CD3333", "#FFFFFF"]

        ax2.barh(bar_b, bar_len, bar_height, bar_left, color=colors)
        for k, c_v in enumerate(phase_x):
            if k == 1:
                x_axi = phase_x[k] - 0.6
            else:
                x_axi = phase_x[k] - 0.1
            ax2.text(x_axi, len(data["a_starts"]) - 0.5, str(c_v), color=colors[k], fontweight='bold')
        if self.show:
            plt.show()
        else:
            fig = plt.gcf()
            fig.set_size_inches(25, 18)
            fig.savefig(os.path.join(self.log_path, '%s.png' % self.tag), dpi=100)

def init_arguments():
    parser = argparse.ArgumentParser(description='Measures boot time.')
    parser.add_argument('-p', '--pwd', dest='passwd', type=str, default='', help='host password for sudo')
    parser.add_argument('-a', '--automation', dest='automation', action='store_true', help='automation execute script')
    parser.add_argument('-m', '--manual', dest='manual', action='store_true', help='manual excute script')
    parser.add_argument('-s', '--show', dest='show', action='store_true', help='show the result png')
    parser.add_argument('-c', '--config', dest='config', type=str, help='config_file name in the config folder')
    return parser.parse_args()

def main():
    config = json.load(open(os.path.join(CUR_DIR, 'config', config_name), 'r'), object_pairs_hook=OrderedDict)
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    try:
        Get_Logs(log_path, auto_flag, config).run_case()
        content, result, result_data = Logs_Parse(log_path, config).data_parse()
    except IOError, e:
        logs("Test error: %s" % e.message)
        return False
    try:
        for key in content.keys():
            Data_Bar(content[key]["display"], content[key]["stage"], content[key]["data"], show_png, log_path).generate_bar()
    except Exception, e:
        logs("generate png error: {0}".format(e.message))
    if auto_flag:
        try:
            for key in content.keys():
                for score in content[key]["stage"]:
                    tr.sub_score(score[1], score[0])
            for file in os.listdir(log_path):
                tr.add_attachment(os.path.join(log_path, file))
            tr.add_attachment(os.path.join(CUR_DIR, 'config', config_name))
            tr.result(result_data)
            tr.save()
        except Exception, e:
            logs("Tr data error:%s" % e)
    return True

if __name__ == "__main__":
    out_dir = time.strftime('%Y%m%d_%H%M%S')
    log_path = ''
    args = init_arguments()
    logs = logprinter
    config_name = ''
    if args.passwd:
        host_pwd = args.passwd
    else:
        logs("Must input linux host passwd useage: '-p linux_pwd'")
        sys.exit()
    if args.manual:
        log_path = os.path.join(CUR_DIR, out_dir)
    if args.automation:
        from atf import TestResult, TestLogger
        from src.auto_test import *
        auto_flag = True
        tr = TestResult(__file__)
        logs = TestLogger().get_logger("process").info
        log_path = tr.result_dir
    if args.show:
        show_png = True
    if args.config:
        config_name = args.config
    else:
        logs("Must input config name in the config folder useage: '-c config_name'")
        sys.exit()
    icount = 0
    ilimite = 1
    print "log_path", log_path
    while not main():
        if icount > ilimite:
            break
        icount += 1
