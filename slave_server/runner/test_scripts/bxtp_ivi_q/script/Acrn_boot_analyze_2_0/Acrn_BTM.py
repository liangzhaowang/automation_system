#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import json
import argparse
import csv
from threading import Thread
from collections import OrderedDict
reload(sys)
sys.setdefaultencoding("ISO-8859-1")


def logprint(msg):
    print msg

class Acrnboot:
    def __init__(self, config, dir):
        self.config = json.load(open(config, 'r'), object_pairs_hook=OrderedDict)
        self.devType = self.config['type']
        self.logdir = dir
        self.result = OrderedDict()
        self.passset = 0
        self.serline = 0
        self.boottime = 0

    def getaddrip(self):
        ipaddr = ''
        ttyusb3_log = os.path.join(self.logdir, 'ttyUSB3.log')
        if os.path.exists(ttyusb3_log):
            iptext = open(ttyusb3_log, 'r').read()
            ipaddrs = re.findall('inet\s+(\d+.\d+.\d+.\d+)/', iptext)
            for i in ipaddrs:
                if i != '127.0.0.1':
                    ipaddr = i
                    print 'ipaddr:'+ipaddr
        return 'root@'+ipaddr

    def getSerlog(self, sernum):
        for i in self.config["capture"]["thread"]:
            serialcmd = i% (REAL_DIR, sernum, acrn_pwd, acrn_user, os.path.join(self.logdir, "{0}.log".format(sernum.replace('/dev/', ''))))
            print "serialcmd", serialcmd
            os.system(serialcmd)

    def parseLog(self):
        logResult = {}
        for i in self.config["log"].keys():
            tmpResult = []
            for j in self.config["log"][i]["tag"]:
                log_name = os.path.join(self.logdir, self.config["log"][i]["config"]["log_name"])
                if os.path.exists(log_name) and os.path.getsize(log_name) != 0:
                    for k in open(log_name).readlines():
                        if k and re.search(j["filter"], k):
                            time_pattern_config = self.config["log"][i]["config"]['filter_time_pattern']
                            tmptime = re.findall(time_pattern_config, k)
                            if not filter(lambda x:x[1] == j["name"], tmpResult):
                                logtime = 0
                                if time_pattern_config.find('ms') != -1:
                                    tmptime = re.findall('\d+', tmptime[0])
                                    if len(tmptime) == 1:
                                        logtime = int(tmptime[0])
                                    if len(tmptime) == 2:
                                        logtime = int(tmptime[0])*10**3+int(tmptime[1])
                                else:
                                    if time_pattern_config == '\d+.\d+':
                                        logtime = float(tmptime[0])*10**3
                                    if time_pattern_config == '\d+:\d+:\d+.\d+':
                                        logtime = (float(tmptime[0].split(':')[0])*3600+float(tmptime[0].split(':')[1])*60+float(tmptime[0].split(':')[2]))*10**3
                                tmpResult.append((logtime, j["name"]))
            if self.config["log"][i]["config"]["parent_axis"] == "main":
                tmpResult.append((000, "init"))
            if self.config["log"][i]["config"].has_key("insert_data"):
                insert_data = self.config['log'][i]["config"]["insert_data"]
                if not filter(lambda x: x[1] == insert_data[1], tmpResult):
                    tmpResult.append(tuple(insert_data))
            logResult[i] = sorted(tmpResult, key=lambda x:x[0])
        return logResult

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
        fuzzyPattern = '\s\[\d+:\d+:\d+.\d+\]\s([a-zA-Z_].+)|:\s([a-zA-Z_].+)|\s([a-zA-Z_].+)'
        log_x = open(os.path.join(self.logdir, self.config['log'][x]['config']['log_name'])).readlines()
        log_y = open(os.path.join(self.logdir, self.config['log'][y]['config']['log_name'])).readlines()
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

    def raiseResult(self):
        total = []
        Result = []
        logResult = self.parseLog()
        for i in self.config["log"].keys():
            offsettime = 0
            tmpLoglist = []
            parent_axis = self.config["log"][i]["config"]["parent_axis"]
            if not parent_axis == "main":
                if logResult.has_key(i) and logResult.has_key(parent_axis):
                    for j in logResult[i]:
                        for k in logResult[parent_axis]:
                            if j[1] == k[1]:
                                offsettime = float(k[0] - j[0])
                    if offsettime == 0:
                        offsettime = self.FuzzyMatch(i, parent_axis)
                    if offsettime == 0:
                        logs("\033[1;31mWarning:'{0} & {1} have no same log' \033[0m".format(i, parent_axis))
                        continue
                    for line in logResult[i]:
                        logTime = float("%.3f" % (line[0] + offsettime))
                        tmpTuple = logTime, line[1]
                        tmpLoglist.append(tmpTuple)
                    logResult[parent_axis].extend(tmpLoglist)
                    total = logResult[parent_axis]
        try:
            for i in total:
                Result.append((float("%.3f" % (i[0]*(0.001))),i[1].encode('utf-8')))
            self.result["total"] = sorted(set(Result), key=lambda x:x[0])
            for j in self.config["stage"]:
                data = self.generate_list(Result, j)
                self.result[j.encode('utf-8')] = data
            logs("--*-- Total --*--")
            for resdata in self.result["total"]:
                time.sleep(0.1)
                logs(resdata)
            try:
                end_tag = self.result[self.result.keys()[-1]]["detail"][-1]
                self.boottime = end_tag[0]
                logs("Result:{0}s ({1})".format(self.boottime, end_tag[1]))
            except Exception, e:
                logs("\033[1;31mGenerate Result Error:%s' \033[0m"%e)
            time.sleep(1)
            self.writeCsv(self.result)
            if auto_flag:
                self.upload_attachment(self.boottime)
        except Exception, e:
            logs("append data error:%s" % e)

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
            logs("Generate display_{0} data Error:{1}".format(data, e))

        try:
            for lines in stage_list:
                stage_time = -1
                for line in display:
                    if lines["start"] == line[1]:
                        stage_time = line[0]
                    if stage_time > -1 and lines["end"] == line[1] and (
                        ("%.3f" % (line[0] - stage_time), lines["name"]) not in stage):
                        stage.append(("%.3f" % (line[0] - stage_time), lines["name"]))
            content["detail"] = display
            content["stage"] = stage
            content["data"] = data
            return content
        except Exception, e:
            logs("Generate stages failed:%s" % e)

    def writeCsv(self, datas):
        try:
            with open(os.path.join(self.logdir,"report.csv"), 'wb') as csvFile:
                writer = csv.writer(csvFile, 'excel-tab')
                writer.writerow(["Total:"])
                for key,value in datas.items():
                    if key == 'total':
                        for entry in datas["total"]:
                            writer.writerow(entry)
                    else:
                        writer.writerow("")
                        writer.writerow(["%s:" % key])
                        for stages in value["stage"]:
                            writer.writerow(stages)
                        writer.writerow("")
                        writer.writerow(["%s:" % (key+"_detail")])
                        for stages in value["detail"]:
                            writer.writerow(stages)
        except Exception, e:
            logs(e)

    def upload_attachment(self, bootTime):
        logfiles = os.listdir(self.logdir)
        for i in logfiles:
            logfile = os.path.join(self.logdir, i)
            if os.path.getsize(logfile) != 0:
                tr.add_attachment(logfile)
        for key, value in self.result.items():
            if isinstance(value, dict) and value.has_key('stage'):
                for i in value['stage']:
                    tr.sub_score(i[1], i[0])
	tr.add_attachment(config)
        tr.result(bootTime)
        tr.save()

    def parseMain(self):
        if auto_flag:
            logs("=============================================================")
            logs("Begin set normal shutdown please wait")
            os.system('adb root')
            time.sleep(2)
            Auto_Realy08(3).create_relaycmd()
            time.sleep(3)
            logs("Set normal shutdown success")
            logs("=============================================================")
            time.sleep(30)
        else:
            raw_input("************ PLEASE MAKE SURE THE DUT IS POWER OFF & PRESS THE 'ENTER KEY' TO CONTINUE... \
            ************")
        if os.popen("adb devices").read().split('\n')[1] == '':
            t1 = Thread(target=self.getSerlog, args=('/dev/ttyUSB2',))
            t1.start()
            t2 = Thread(target=self.getSerlog, args=('/dev/ttyUSB3',))
            t2.start()
            logs("************ \033[1;31m WAIT FOR DUT POWER ON('PLEASE PRESS THE IGNITION BUTTON')...\
            \033[0m ************")
            if auto_flag:
                logs("******Auto press inition button******")
                #time.sleep(5)
                Auto_Realy08(1).create_relaycmd()
            t1.join()
            t2.join()
            time.sleep(2)
            for i in range(60):
                if os.popen("adb devices").read().split('\n')[1] != '':
                    if len(self.config["capture"]["commands"]) > 0:
                        logs("************ CAPTURE ADB LOGS ************")
                        for i in self.config["capture"]["commands"]:
                            if i.find('adb') != -1:
                                if i.find('%s') != -1:
                                    i = i.replace('%s', self.logdir)
                                try:
                                    os.system(i)
                                except Exception, e:
                                    logs(e)
			    if i.find('rm') != -1:
                                os.system(i)
                            if i.find('sshpass') != -1:
                                i = i%(acrn_pwd, self.getaddrip(), self.logdir)
                                print "scp cmd:%s"%i
                                os.system(i)
				time.sleep(2)
                            if i.find('sleep') != -1:
                                i = int(i.replace('sleep ', ''))
                                time.sleep(i)
                    time.sleep(2)
                    logs("************ PARSE LOGS ************")
                    time.sleep(2)
                    self.raiseResult()
                    break
                else:
                    logs("****** wait for devices ******")
                    time.sleep(2)
        else:
            time.sleep(2)
            self.parseMain()
def usage():
    parser = argparse.ArgumentParser(description="Test boot time for acrn")
    parser.add_argument('-a', '--automation', dest='automation', action='store_true', help='automation execute script')
    parser.add_argument('-u', '--user', dest='acrn_username',type=str,default='',help='Username for acrn_sos')
    parser.add_argument('-p', '--pwd', dest='acrn_password',type=str,default='',help='password for acrn_sos')
    parser.add_argument('-P', '--Pwd', dest='linux_password',type=str,default='',help='Password for linux host')
    parser.add_argument('-c', '--config', dest='config_name', type=str, help='config name in the config folder')
    return parser.parse_args()

if __name__ == "__main__":
    REAL_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
    logdir = os.path.join(REAL_DIR, time.strftime("%Y%m%d_%H%M%S"))
    linux_pwd = ''
    acrn_user = ''
    acrn_pwd = ''
    config_name = ''
    logs = logprint
    auto_flag = False
    args = usage()
    if args.automation:
        from atf import TestResult, TestLogger
        from src.AutoTest import *
        tr = TestResult(__file__)
        logs = TestLogger().get_logger("process").info
        logdir = tr.result_dir
        auto_flag = True
    if args.linux_password:
        linux_pwd = args.linux_password
    else:
        logs("Must input linux host passwd,useage: '-P linux_pwd'")
        sys.exit()
    if args.acrn_password:
        acrn_pwd = args.acrn_password
    else:
        logs("Must input acrn_sos passwd,useage: '-p pwd'")
        sys.exit()
    if args.acrn_username:
        acrn_user = args.acrn_username
    else:
        logs("Must input acrn_sos username,useage: '-u user'")
        sys.exit()
    if args.config_name:
        config_name = args.config_name
    else:
        logs("Must input config name in the config folder,usage: '-c config_name'")
        sys.exit()
    os.system("echo %s|sudo -S chmod 777 /dev/ttyUSB3" % linux_pwd)
    os.system("echo %s|sudo -S chmod 777 /dev/ttyUSB2" % linux_pwd)
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logs("************ BREAKDOWN DATA PATH: %s ************"%logdir)
    config = os.path.join(REAL_DIR, 'config', config_name)
    Acrnboot(config, logdir).parseMain()








