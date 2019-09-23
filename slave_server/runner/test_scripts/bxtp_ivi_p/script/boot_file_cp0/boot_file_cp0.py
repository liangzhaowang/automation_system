import os

import logging
import sys
import subprocess
import time

# p = os.popen('adb reboot bootloader')

"""
This script is developed by suhao at 2018.01.18
"""


prereadFileName = 'preread_zygote64_sysServer_sysUI_vold.csv'


def check_fastboot(sleepTime=16):
    for i in range(sleepTime):
        p = os.popen('fastboot devices')

        for line in p:
            logging.debug(line)
            if 'fastboot' in line:
                logging.info('fastboot available')
                return True
        time.sleep(1)

    logging.warning('Error: enter fastboot failed.')
    return False


def flash_fastboot(cmd):
    logging.info(cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in p.communicate():
        logging.debug(line)
        if 'OKAY' in line:
            logging.info(cmd + ' OKAY')
            return True

    logging.warning('Error: fastboot flashing failed')
    return False


def check_adb_device(sleepTime=60):
    logging.info('Entering adb waiting...')
    for i in range(sleepTime):
        p = os.popen('adb devices')
        deviceNum = 0
        for line in p:
            if 'device' in line:
                deviceNum += 1
        if deviceNum > 1:
            logging.info('adb available')
            return True
        time.sleep(1)
    logging.warning('Error: adb available timeout')
    return False


def check_remount(waitRoot=8):
    q = subprocess.Popen('adb root', shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in q.communicate():
        logging.debug(line)
    time.sleep(waitRoot)

    p = subprocess.Popen('adb remount', shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.communicate():
        logging.debug(line)
        if 'succeeded' in line:
            logging.info('remount OKAY')
            return True
    logging.warning('Error: remount failed')
    return False


def enable_remount():
    if check_adb_device():
        logging.info('Entering fastboot wating...')
        os.system('adb reboot bootloader')
    else:
        return False
    if not check_fastboot():
        return False
    if not flash_fastboot('fastboot flashing unlock'):
        return False
    if not flash_fastboot('fastboot flash vbmeta_a %s/vbmeta_disable_verity.img' % CUR_DIR):
        return False
    if not flash_fastboot('fastboot flashing lock'):
        return False
    os.system('fastboot reboot')
    if not check_adb_device():
        return False

    if not check_remount():
        return False
    if not check_adb_device(sleepTime=5):
        return False

    return True


def get_inode(log_dir):
    logging.info('Getting inode, please wait 20 seconds...')
    p = subprocess.Popen('cd %s/mem_tools;./prepare.sh'% CUR_DIR, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.communicate():
        logging.debug(line)

    q = subprocess.Popen('mv %s/mem_tools/inodes.txt %s' % (CUR_DIR, log_dir), shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in q.communicate():
        logging.debug(line)
        if 'cannot' in line:
            logging.warning('Failed get inode, no inode file')
            return False

    logging.info('Get inodes.txt successfully...')
    return True


def check_trace(log_dir):
    block_count = 0
    with open('%strace' % log_dir, 'r') as file:
        for line in file:
            if 'block' in line:
                block_count += 1
    if block_count > 5000:
        logging.info('block string in /d/tracing/trace more than 5000, seems valid')
        return True
    else:
        logging.warning('Error: /d/tracing/trace seems not valid, please check patches added')
        logging.warning('https://android.intel.com:443/#/c/601001')
        logging.warning('https://android.intel.com:443/#/c/615293')
        return False


def get_trace(log_dir):
    logging.info('adb pulling /d/tracing/trace')
    p = subprocess.Popen('adb pull /d/tracing/trace %s' % log_dir, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.communicate():
        if '[   ?]' not in line:
            logging.debug(line)

    if os.path.isfile('%strace' % log_dir):
        logging.info('/d/tracing/trace pulled successfully')
        if check_trace(log_dir):
            return True
        else:
            return False



    logging.warning('Failed pulling /d/tracing/trace, no such file')
    return False


def calculate_file(log_dir):
    logging.info('calculate file from inodes.txt and trace, please wait 10s...')
    p = subprocess.Popen('cd %s/BlockTraceParser/;ruby cp0_trace_analyzer.rb %strace %sinodes.txt'
                         % (CUR_DIR, log_dir, log_dir),
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.communicate():
        logging.debug(line)
        if 'are writen to' in line:
            return True
    logging.warning('Failed calculating file, pls check debug log')
    return False



def parse_trace_csv(path, output_path):
    raw_array = []
    result_output = []

    zygotePid = None
    systemServerPid = None
    zygoteName = 'zygote64'
    system_server_name = 'system_server'
    voldName = 'vold'
    systemUIName = 'ndroid.systemui'

    with open(path,'r') as file:
        list_tmp = []
        for line in file:
            list_tmp = line.strip().split(', ')
            raw_array.append(list_tmp)

    for i in raw_array:
        if i[1] == zygoteName:
            zygotePid = i[2]
            break
    for i in raw_array:
        if i[1] == system_server_name:
            systemServerPid = i[2]
            break

    for i in raw_array:
        if i[1] == voldName:
            result_output.append(i)
        elif i[2] == zygotePid:
            result_output.append(i)
        elif i[2] == systemServerPid:
            result_output.append(i)
        elif i[1] == systemUIName:
            result_output.append(i)


    for i in result_output:
        # print '\t'.join([i[3],i[4],i[5]])
        print i


    with open(output_path, 'w') as file:
        for i in result_output:
            file.write('\t'.join([i[3],i[4],i[5]])+'\n')

    if os.path.isfile(output_path):
        logging.info('Parse preread.csv successfully...')
        return True
    else:
        logging.warning('Failed parse preread.csv, pls check debug log')
        return False


def main(log_dir, debug=False):
    print 'boot_file_cp0.py running, please waiting 5 min'

    if debug:
        logging.basicConfig(
            stream=sys.stdout,
            format='%(asctime)s %(levelname)s %(message)s',
            level=logging.DEBUG)
    else:
        logging.basicConfig(
            filename='%sdebug.log'%log_dir,
            format='%(asctime)s %(levelname)s %(message)s',
            level=logging.DEBUG)
    if not enable_remount():
        return False
    if not get_inode(log_dir):
        return False
    if not get_trace(log_dir):
        return False
    if not calculate_file(log_dir):
        return False
    if not parse_trace_csv('%strace.csv' % log_dir, '%s%s' % (log_dir,prereadFileName)):
        return False

    logging.info('boot_file_cp0 successfully finished')
    print 'boot_file_cp0.py finished, please check debug.log'
    return True


if __name__ == '__main__':
    CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    out_dir = time.strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join(CUR_DIR, './' + out_dir + '/')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)


    isDebug = False

    isSucess = main(log_dir, debug=isDebug)

    # comment follows for developing and testing in single computer
    # integrate cp0 begin
    if not isDebug:
        from atf import TestResult
        tr = TestResult(__file__)
        if isSucess:
            tr.result('Sucess')
            tr.add_attachment(log_dir+'trace.csv')
            tr.add_attachment( '%s%s' % (log_dir,prereadFileName))
        else:
            tr.result('Faied')
        tr.add_attachment(log_dir+'debug.log')
        tr.save()
    # integrate cp0 end

