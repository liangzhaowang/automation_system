import os
import time
from lib import rwfile_file
from runner.operation_lib.base_lib.thread_ctrl import cmd_port_thread
from atf import TestResult, TestLogger


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read().strip()
    return host_passwd


def kill_USB2():
    passwd = _get_passwd()
    fgrep = os.popen('ps -aux | grep USB2').readlines()
    for lines in fgrep:
        item = lines.split()
        os.system("echo "+passwd+" | sudo -S kill -9 " + item[1])


def kill_USB3():
    passwd = _get_passwd()
    fgrep = os.popen('ps -aux | grep USB3').readlines()
    for lines in fgrep:
        item = lines.split()
        os.system("echo "+passwd+" | sudo -S kill -9 " + item[1])


def serial_port_check(passwd, usb_name='ttyUSB2'):
    id = ''
    find_line = os.popen("ps -aux | grep " + usb_name + " | grep 'sudo minicom'").readline()
    if "ps -aux" not in find_line:
        id = find_line.split()[1]
    if id == '':
        return True
    else:
        if os.system('"echo {0}|sudo -S kill -9 {1}"'.format(passwd, id)) == 0:
            return True
        else:
            return False


def renew_ttylog(logs, out_dir, filename):
    rwfile_file.rewrite_file(out_dir, filename)


def main():
    tr = TestResult()
    out_dir = tr.result_dir
    logs = TestLogger().get_logger("process")
    i = 0
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    serial_thread_state = os.path.join(out_dir, 'serial_state')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("0\n")

    passwd = _get_passwd()
    os.system("adb root")
    os.system("adb shell 'echo 7 >/proc/sys/kernel/printk'")
    os.system("adb shell 'echo N >/sys/module/printk/parameters/console_suspend'")
    cmd = "echo "+passwd+"|sudo -S python runner/operation_lib/base_lib/seriallog.py -p /dev/ttyUSB2 -o " + out_dir + " -f USB2"
    logs.info(cmd)
    cmd_usb3 = "echo "+passwd+"|sudo -S python runner/operation_lib/base_lib/seriallog.py -p /dev/ttyUSB3 -o " + out_dir + " -f USB3"
    logs.info(cmd_usb3)
    cmd_thread = cmd_port_thread(cmd, 1)
    cmd_thread.start()
    cmd_thread = cmd_port_thread(cmd_usb3, 1)
    cmd_thread.start()
    time.sleep(1)
    
    while True:
        i += 1
        logs.info(str(i))
        os.system("echo "+passwd+" | sudo -S python runner/operation_lib/base_lib/relay08_ctrl_button.py -p 1")
        time.sleep(40)
    serial_port_check(passwd, usb_name='ttyUSB2')
    kill_USB2()
    kill_USB3()    
    renew_ttylog(logs, out_dir, "USB2")
    renew_ttylog(logs, out_dir, "USB3")
    serial_thread_state = os.path.join(out_dir, 'serial_state')
    with open(serial_thread_state, 'w+') as fp:
        fp.write("1\n")
    tr.result('finished')
    tr.add_attachment(os.path.join(out_dir, 'USB2_outttylog.txt'))
    tr.add_attachment(os.path.join(out_dir, 'USB3_outttylog.txt'))
    tr.save()


if __name__ == "__main__":
    main()
