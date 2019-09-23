#!/usr/bin/python

import os
import re
import time
import subprocess
from lib import rwfile_file
from runner.operation_lib.base_lib.thread_ctrl import cmd_port_thread
from runner.operation_lib.base_lib.ctrl_relay08_threading import control_relay08_port_thread
from runner.operation_lib.base_lib.exception_operation import wait_for_boot
from atf import TestResult, TestLogger

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
count_time = 0
waittime = 0
resume_complete = False


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    host_passwd = ""
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read()
    return host_passwd


def kill_USB2():
    host_passwd = _get_passwd()
    fgrep = os.popen('ps -aux | grep USB2').readlines()
    for lines in fgrep:
        item = lines.split()
        os.system('echo '+host_passwd+'|sudo -S kill -9 '+item[1])


def wait_for_dev():
    for i in range(100):
        time.sleep(1)
        if os.popen('adb devices').readlines()[1] == '\n':
            continue
        else:
            return True
    else:
        return False


def wait_for_device():
    if os.popen('adb devices').readlines()[1] == '\n':
        return False
    else:
        return True


def wait_dev_online():
    for i in range(100):
        time.sleep(1)
        if os.popen('adb devices').readlines()[1][-2] == 'e':
            return True
        else:
            continue
    else:
        return False


def wait_for_complete(timeout=70):
    global waittime
    for i in range(timeout):
        time.sleep(1)
        if os.popen('adb shell getprop dev.bootcomplete').readlines()[0] == '1':
            waittime = i
            return True

    return False


def serial_port_check(passwd, usb_name='ttyUSB2'):
    id = ''
    find_line = os.popen("ps -aux | grep " + usb_name +
                         " | grep 'sudo minicom'").readline()
    if not "ps -aux" in find_line:
        id = find_line.split()[1]
    if id == '':
        return True
    else:
        if os.system("echo " + passwd + "|sudo -S kill -9 " + id) == 0:
            return True
        else:
            return False


def parse_dmesg_resume_time(logs, out_dir):
    item_start = 0
    item_end = 0
    dmesg_time = ""
    kernel_resume_time = ""
    try:
        with open(os.path.join(out_dir, 'dmesg.txt'), "r") as fread:
            line = fread.readlines()
            if line:
                llist = open(os.path.join(out_dir, 'dmesg.txt')).readlines()
                llist.reverse()
                line = ''
                line_end = ''
                for index in llist:
                    if index.count('PM: resume of devices complete after') == 1:
                        line = index
                        r = re.search(r'.(?P<time>\d+\.\d+)', line, re.M | re.I).group('time')
                        item_start = float(r)
                        try:
                            result_time = re.search(r'.(?P<time>\d+\.\d+).msec', line, re.M | re.I).group('time')
                            dmesg_time = float(result_time)
                        except Exception, e:
                            logs.error('%s' % e)
                            return 0
                for index in llist:
                    if index.count('PM: suspend exit') == 1:
                        line_end = index
                        try:
                            t = re.search(r'.(?P<time>\d+\.\d+)', line_end, re.M | re.I).group('time')
                        except Exception, e:
                            logs.error('%s' % e)
                            return 0
                        item_end = float(t)
            delta = round(float((item_end - item_start) * 1000), 3)
            kernel_resume_time = delta + dmesg_time
            print kernel_resume_time
            if kernel_resume_time == "":
                return 0
            else:
                return kernel_resume_time

    except Exception, e:
        logs.error('%s' % e)
        return 0


def get_suspend_resume_time_stamp(logs, out_dir, passwd):
    global count_time
    global waittime
    count_time += 1

    passwd = _get_passwd()
    reboot_cmd = "echo " + passwd + "|sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"
    sus_start = 0
    if wait_for_boot():
        os.system('adb root')
        time.sleep(2)
        os.system('adb push ' + os.path.join(CUR_DIR, 'lib', 'abl_dumper_app') + ' /data')
        time.sleep(5)
        os.system('adb push ' + os.path.join(CUR_DIR, 'lib', 'android.sh') + ' /sdcard/')
        time.sleep(5)
        os.system('adb shell <' + os.path.join(CUR_DIR, 'capture-start.txt'))
        time.sleep(2)
        ctl_button = control_relay08_port_thread(port_id=1)
        ctl_button.start()
        for i in range(1000):
            time.sleep(1)
            if wait_for_device():
                continue
            else:
                logs.info('into suspend')
                logs.info(i)
                break
            sus_start += 1
        time.sleep(10)
    os.system('echo ' + passwd + '|sudo -S python runner/operation_lib/base_lib/relay08_ctrl_button.py -p 1')
    time.sleep(2)
    print sus_start
    if sus_start > 15:
        os.system(reboot_cmd)
        return False
    else:
        if wait_for_boot():
            print "resume done"
            time.sleep(2)
            os.system('adb root')
            time.sleep(2)
            cmd = 'adb shell cat /d/suspend_stats >' + os.path.join(out_dir, 'suspend_stats.txt')
            logs.info(cmd)
            os.popen(cmd)
            time.sleep(5)
            f = open(os.path.join(out_dir, 'suspend_stats.txt'))
            line = f.readlines()
            if len(line) == 0:
                time.sleep(5)
                logs.info(cmd)
                os.system(cmd)
                time.sleep(5)
                f = open(os.path.join(out_dir, 'suspend_stats.txt'))
                line = f.readlines()
            # logs.debug(line)
            for i in line:
                if 'success:' in i:
                    # try:
                    item = re.search(r"\d+", i).group(0)
                    os.system('adb root')
                    os.system('adb shell <' + os.path.join(CUR_DIR, 'abl_dump.txt'))
                    os.system('adb shell <' + os.path.join(CUR_DIR, 'capture-end.txt'))
                    os.system('adb pull /data/abl_dump.txt ' + os.path.join(out_dir, 'abl_dump.txt'))
                    os.system('adb pull /sdcard/ftrace.txt ' + os.path.join(out_dir, 'ftrace.txt'))
                    os.system('adb pull /sdcard/dmesg.txt ' + os.path.join(out_dir, 'dmesg.txt'))
                    os.system('adb pull /sdcard/log.txt ' + os.path.join(out_dir, 'log.txt'))
                    p = subprocess.Popen('python ' + os.path.join(CUR_DIR, 'lib/analyze_suspend.py') + ' -ftrace ' + os.path.join(out_dir, 'ftrace.txt') + ' -dmesg ' + os.path.join(out_dir, 'dmesg.txt'), shell=True, cwd=out_dir)
                    p.wait()
                    os.system('adb logcat -d > ' + os.path.join(out_dir, 'logcat.txt'))
                    try:
                        os.rename(os.path.join(out_dir, 'output.html'), os.path.join(out_dir, 'output.h5'))
                    except Exception, e:
                        logs.error(e)
                    get_abl_data(out_dir)
                    if item == 0:
                        os.system(reboot_cmd)
                        return False
                    else:
                        return True
        else:
            os.system(reboot_cmd)
            time.sleep(1)
            return False


def get_kernel_resume_time(logs, out_dir):
    try:
        with open(os.path.join(out_dir, 'output.h5'), "r") as fread:
            line = fread.readlines()
            if line:
                llist = open(os.path.join(out_dir, 'output.h5')).readlines()
                line = ''
                for index in llist:
                    if index.count('Kernel Resume Time') == 1:
                        line = index
                        try:
                            t = re.search(r'Kernel Resume Time: <b>(.+) ms<', line).group(1)
                        except Exception, e:
                            logs.error('%s' % e)
                            return 0
            kernel_resume_time = float(t)
            print kernel_resume_time
            if kernel_resume_time == "":
                return 0
            else:
                return kernel_resume_time

    except Exception, e:
        logs.error('%s' % e)
        return 0


def get_abl_data(out_dir):
    try:
        with open(os.path.join(out_dir, 'abl_dump.txt'), "r") as fread:
            lines = fread.readlines()
            flag = False
            llines = []
            for i in lines:
                if i.count("Index") == 1:
                    flag = True
                if flag:
                    llines.append(i)
                    i = i.split('\n')
                    for item in i:
                        item = item.split('\t')
                        if item[0] == '55':
                            item[1] = float(item[1])
                            jti = round(float(item[1]), 3)
                            return jti
        return 0
    except Exception, e:
        print e
        return 0


def get_ioc_data(logs, out_dir):
    item_start = 0
    item_end = 0
    try:
        with open(os.path.join(out_dir, 'USB2_outttylog.txt'), "r") as fread:
            r = re.compile(r'(\d+):(\d+)\s(\d+)s(\d+)')
            for line in fread:
                if 'Wakeup button state' in line:
                    item = r.findall(line)[0]
                    item_start = float(item[0]) * 3600 + float(item[1]) * 60 + float(item[2]) + float(item[3]) / 1000
                if 'SoC startup' in line:
                    item = r.findall(line)[0]
                    item_end = float(item[0]) * 3600 + float(item[1]) * 60 + float(item[2]) + float(item[3]) / 1000
                    break
        delta = round(float((item_end - item_start) * 1000), 3) if item_start > 0 else 0
        return delta if delta > 0 and delta < 1000 else 0
    except Exception, e:
        logs.error(e)
        return 0


def renew_ttylog(logs, out_dir, filename):
    rwfile_file.rewrite_file(os.path.join(out_dir, filename+"_ttylog.txt"), os.path.join(out_dir, filename+"_outttylog.txt"))
    time.sleep(1)
    get_ioc_data(logs, out_dir)


def main():
    result = {}
    tr = TestResult(__file__)
    out_dir = tr.result_dir
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    logs = TestLogger().get_logger("process")
    serial_thread_state = os.path.join(out_dir, 'serial_state')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("0\n")

    passwd = _get_passwd()
    kill_USB2()
    cmd = "echo " + passwd + "|sudo -S python runner/operation_lib/base_lib/seriallog.py -p /dev/ttyUSB2 -o " + out_dir + " -f USB2"
    logs.info(cmd)
    cmd_thread = cmd_port_thread(cmd, 1)
    cmd_thread.start()
    time.sleep(1)
    while not get_suspend_resume_time_stamp(logs, out_dir, passwd):
        time.sleep(20)
        if get_suspend_resume_time_stamp(logs, out_dir, passwd):
            break

    serial_port_check(passwd, usb_name='ttyUSB2')
    kill_USB2()
    renew_ttylog(logs, out_dir, "USB2")
    result['abl_time'] = get_abl_data(out_dir)
    print result['abl_time']
    ioc = get_ioc_data(logs, out_dir)
    result['ioc_time'] = round(float(ioc), 3)
    print result['ioc_time']
    result['kernel_time'] = get_kernel_resume_time(logs, out_dir)
    print result['kernel_time']
    try:
        with open(os.path.join(out_dir, 'raw_data.txt'), "w") as fread:
            fread.write(str(result))
            fread.close()
    except Exception, e:
        logs.error(e)
    resume_time = result['abl_time'] + result['ioc_time'] + result['kernel_time']
    if resume_time == 0:
        logs.error("get resume time failed!!!")
        return False
    logs.info(result)

    os.system('adb shell input keyevent MENU')
    serial_thread_state = os.path.join(out_dir, 'serial_state')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("1\n")
    tr.result(resume_time)
    tr.add_attachment(os.path.join(out_dir, 'raw_data.txt'))
    tr.add_attachment(os.path.join(out_dir, 'dmesg.txt'))
    tr.add_attachment(os.path.join(out_dir, 'ftrace.txt'), 'ftrace.txt')
    tr.add_attachment(os.path.join(out_dir, 'log.txt'), 'log.txt')
    tr.add_attachment(os.path.join(out_dir, 'output.h5'), 'output.h5')
    tr.add_attachment(os.path.join(out_dir, 'abl_dump.txt'))
    tr.add_attachment(os.path.join(out_dir, 'USB2_outttylog.txt'))
    tr.add_attachment(os.path.join(out_dir, 'logcat.txt'))
    for key, val in result.items():
        tr.sub_score(key, str(val))
    tr.save()
    return True


if __name__ == "__main__":
    icount = 0
    ilimite = 2
    while not main():
        if icount > ilimite:
            break
        icount += 1

