import os
import re
import sys
import time
from lib import rwfile_file
from runner.operation_lib.base_lib.thread_ctrl import cmd_port_thread
from runner.operation_lib.base_lib.ctrl_relay08_threading import control_relay08_port_thread
from runner.operation_lib.base_lib.exception_operation import wait_for_boot
from atf import TestResult, TestLogger

count_time = 0
lines = 0
lists_all = []
result_time = 0
waittime = 0
count_suc = 0
count_fail = 0
item_start = 0
item_end = 0
resume_complete = False
re_str = [r"\[\d+;\d+.", r"\x1b", r"\x00", r"\r", r"\|[a-zA-Z0-9]+[\x08]+", r"\[\?..."]


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    host_passwd = ""
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read().strip()
    return host_passwd


def kill_USB2(passwd):
    fgrep = os.popen('ps -aux | grep USB2').readlines()

    for lines in fgrep:
        item = lines.split()
        os.system("echo "+passwd+" | sudo -S kill -9 " + item[1])


def kill_USB3(passwd):
    fgrep = os.popen('ps -aux | grep USB3').readlines()

    for lines in fgrep:
        item = lines.split()
        os.system("echo "+passwd+" | sudo -S kill -9 " + item[1])


def wait_for_dev():
    for i in range(100):
        time.sleep(1)
        if os.popen('adb devices').readlines()[1] == '\n':
            continue
        else:
            return True
    else:
        return False


def adb(cmd):
    adb_command = 'adb ' + cmd
    return os.popen(adb_command).read()


def kill_fork_server():
    passwd = _get_passwd()
    fgrep = os.popen('ps -aux | grep adb').readlines()
    for lines in fgrep:
        if lines.count('fork-server') == 1:
            item = lines.split()
            os.system("echo "+passwd+" | sudo kill " + item[1])


def device_state():
    passwd = _get_passwd()
    reboot_cmd = "echo "+passwd+"|sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"
    if os.popen('adb devices').readlines()[1].split('\t')[1].strip() == 'offline':
        os.system(reboot_cmd)
    else:
        return True


def wait_for_complete(timeout=70):
    global waittime
    passwd = _get_passwd()
    for i in range(timeout):
        #        print i
        time.sleep(1)
        if adb('shell getprop dev.bootcomplete').lstrip().strip() == '1':
            waittime = i
            return True
    kill_fork_server()
    device_state()
    time.sleep(2)
    return False


def serial_port_check(passwd, usb_name='ttyUSB2'):
    id = ''
    find_line = os.popen("ps -aux | grep " + usb_name + " | grep 'sudo minicom'").readline()
    if not "ps -aux" in find_line:
        id = find_line.split()[1]
    if id == '':
        return True
    else:
        if os.system('"echo {0}|sudo -S kill -9 {1}"'.format(passwd, id)) == 0:
            return True
        else:
            return False


def parse_dmesg_resume_time(logs, out_dir):
    global item_start
    global item_end
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
                        r =re.search(r'.(?P<time>\d+\.\d+)', line, re.M|re.I).group('time')
                        item_start = float(r)
                        try:
                            result_time = re.search(r'.(?P<time>\d+\.\d+).msec', line, re.M|re.I).group('time')
                            dmesg_time = float(result_time)
                            f = open(os.path.join(out_dir, 'data_result.txt'), 'a')
                            f.write(str(result_time) + '\n')
                            f.close()
                        except Exception, e:
                            logs.error('%s' % e)
                            return 0
                for index in llist:
                    if index.count('PM: suspend exit') == 1:
                        line_end = index
                        try:
                            t = re.search(r'.(?P<time>\d+\.\d+)', line_end, re.M|re.I).group('time')
                        except Exception, e:
                            logs.error('%s' % e)
                            return 0
                        item_end = float(t)
            delta = round(float((item_end - item_start)*1000), 3)
            kernel_resume_time = delta + dmesg_time
            print kernel_resume_time
            if kernel_resume_time == "":
                return 0
            else:
                return kernel_resume_time

    except Exception, e:
        logs.error('%s' % e)
        return 0


def get_suspend_resume_time_stamp(logs, out_dir):
    global count_time
    global waittime
    global lists_all
    passwd = _get_passwd()
    list_tmp =[]
    count_time += 1
    reboot_cmd="echo "+passwd+"|sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"
    list_tmp.append(count_time)
    if wait_for_boot():
        ctl_button = control_relay08_port_thread(port_id=1)
        ctl_button.start()
        for i in range(500):
            time.sleep(1)
            if wait_for_dev():
                continue
            else:
                logs.info('into suspend')
                break
        time.sleep(10)
    os.system("echo "+passwd+" | sudo -S python runner/operation_lib/base_lib/relay08_ctrl_button.py -p 1")
    time.sleep(2)

    if wait_for_boot():
        kill_fork_server()
        device_state()
        os.system('adb root')
        time.sleep(1)
        cmd = 'adb shell cat /d/suspend_stats >' + os.path.join(out_dir, 'suspend_stats.txt')
        logs.info(cmd)
        os.popen(cmd)
        time.sleep(1)
        f = open(os.path.join(out_dir, 'suspend_stats.txt'))
        line = f.readlines()
        if len(line) ==0:
            time.sleep(1)
            logs.info(cmd)
            os.system(cmd)
            time.sleep(1)
            f = open(os.path.join(out_dir, 'suspend_stats.txt'))
            line = f.readlines()
        else:
            pass
        for i in line:
            if 'success:' in i:
                try:
                    item = re.search(r"\d+", i).group(0)
                    if item == '0':
                        list_tmp.append('0')
                        list_tmp.append('1')
                        lists_all.append(list_tmp)
                        return False
                except Exception, e:
                    print e
            else:

                cmd = 'adb shell dmesg >' + os.path.join(out_dir, 'dmesg.txt')
                os.popen(cmd)

                list_tmp.append('1')
                list_tmp.append('0')
                lists_all.append(list_tmp)
                run_case(logs,out_dir)
                return True
    else:
        time.sleep(1)
        list_tmp.append('0')
        list_tmp.append('1')
        lists_all.append(list_tmp)
        return False
    logs.info(count_time)


def print_wait_process_ex(times=1.0):
    sys.stdout.write('parsing')
    sys.stdout.flush()
    for i in range(1, 50):
        if i % 10 == 0:
            pass
            sys.stdout.write('\b' * 9 + ' ' * 9 + '\b' * 9)
        else:
            pass
            sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(times / 100)
    print ""


def cat_status(logs, out_dir):
    if wait_for_complete():
        os.system('adb root')
        time.sleep(5)
        os.system('adb shell cat /d/suspend_stats >'+os.path.join(out_dir, 'suspend_stats.txt'))
        time.sleep(5)
        f = open(os.path.join(out_dir, 'suspend_stats.txt'))
        line = f.readlines()
        if len(line) ==0:
            os.system('adb root')
            time.sleep(5)
            os.system('adb shell cat /d/suspend_stats >'+os.path.join(out_dir, 'suspend_stats.txt'))
            time.sleep(5)
            f = open(os.path.join(out_dir, 'suspend_stats.txt'))
            line = f.readlines()
        else:
            pass
        for i in line:
            if i.count('success:') ==1:
                try:
                    item = re.search(r"\d+", i).group(0)
                    if item == '0':
                        print 'hang'
                except Exception, e:
                    print e


def run_case(logs,out_dir):
    os.system('adb shell input keyevent KEYCODE_DPAD_UP')
    time.sleep(2)
    os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')
    time.sleep(2)
    os.system('adb shell input keyevent 4')
    time.sleep(1)
    cat_status(logs, out_dir)


def renew_ttylog(logs, out_dir, filename):
    rwfile_file.rewrite_file(out_dir, filename)


def main():
    result = {}
    tr = TestResult(__file__)
    global count_suc
    global count_fail
    out_dir = tr.result_dir
    logs = TestLogger().get_logger("process")
    global lists_all
    global count_time
    global waittime
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    serial_thread_state = os.path.join(out_dir, 'serial_sate')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("0\n")
    passwd = _get_passwd()
    kill_fork_server()
    device_state()
    kill_USB2(passwd)
    kill_USB3(passwd)
    reboot_cmd='"echo {0}|sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"'.format(passwd)
    logs.info(reboot_cmd)
    cmd = "echo "+passwd+"|sudo -S python runner/operation_lib/base_lib/seriallog.py -p /dev/ttyUSB2 -o " + out_dir + " -f USB2"
    logs.info(cmd)
    os.system("adb root")
    time.sleep(2)
    os.system("adb shell 'echo 7 >/proc/sys/kernel/printk'")
    time.sleep(2)
    os.system("adb shell 'echo N >/sys/module/printk/parameters/console_suspend'")
    time.sleep(2)
    cmd_usb3 = "echo "+passwd+"|sudo -S python runner/operation_lib/base_lib/seriallog.py -p /dev/ttyUSB3 -o " + out_dir + " -f USB3"
    logs.info(cmd_usb3)
    cmd_thread = cmd_port_thread(cmd, 1)
    cmd_thread.start()
    cmd_thread = cmd_port_thread(cmd_usb3, 1)
    cmd_thread.start()
    time.sleep(1)

    for i in range(2000):
        i += 1
        print i
        os.system('adb root')
        if get_suspend_resume_time_stamp(logs, out_dir):
            os.system("adb root")
            time.sleep(2)
            os.system("adb shell 'echo 7 >/proc/sys/kernel/printk'")
            time.sleep(2)
            os.system("adb shell 'echo N >/sys/module/printk/parameters/console_suspend'")
            time.sleep(2)
            run_case(logs, out_dir)
            parse_dmesg_resume_time(logs, out_dir)
            logs.info(count_time)

        else:
            os.system(reboot_cmd)
            time.sleep(10)

    print count_time
    serial_port_check(passwd,usb_name='ttyUSB2')
    kill_USB2(passwd)
    kill_USB3(passwd)
    renew_ttylog(logs, out_dir, "USB2")
    renew_ttylog(logs, out_dir, "USB3")
    serial_thread_state = os.path.join(out_dir, 'serial_sate')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("1\n")
    for i in lists_all:
        try:
            with open(os.path.join(out_dir, 'count.txt'), 'a') as f:
                f.write(str(i) + '\n')
                f.close()
        except Exception, e:
            print "con't open count.txt"
            print e
    for item in lists_all:

        if item[2] == '1':
            print item[0]
            try:
                with open(os.path.join(out_dir, 'count.txt'), 'a') as f:
                    f.write(str(item[0]))
                    f.write('\n')
                    f.close()
            except Exception, e:
                print "con't open count.txt"
                print e
            count_fail += 1
        elif item[1] == '1':
            count_suc += 1

    result = 'total_times : %s passed : %s failed : %s' % (count_time, count_suc, count_fail)

    print result
    try:
        with open(os.path.join(out_dir, 'count.txt'), 'r') as h:
            s = h.read()
            try:
                with open(os.path.join(out_dir, 'report.txt'), 'a') as g:
                    g.write(str(result) + '\n')
                    g.write(s)
                    g.close()
            except Exception, e:
                print "con't open report.txt"
                print e
        h.close()
    except Exception, e:
        print "con't open count.txt"
        print e
    print ""
    tr.result(result)
    tr.add_attachment(os.path.join(out_dir, 'dmesg.txt'))
    tr.add_attachment(os.path.join(out_dir, 'USB2_outttylog.txt'))
    tr.add_attachment(os.path.join(out_dir, 'USB3_outttylog.txt'))
    tr.add_attachment(os.path.join(out_dir, 'report.txt'))
    tr.save()


if __name__ == "__main__":
    main()
