#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import getopt
from runner.conf import conf
from runner.operation_lib.base_lib.ctrl_relay08_threading import create_relay08_cmd
from runner.operation_lib import utiliy
from lib.downloadimg import down_load_image
from lib.parse_json import parse_flash_json
from atf import TestLogger
logger = TestLogger().get_logger("process")


class DownloadAndFlash:
    def __init__(self, device_type, imagePath, platform_path):
        self.device_type = device_type
        self.imagePath = imagePath
        self.platform_path = platform_path
        self.command_list = parse_flash_json(conf.flash[device_type.lower()]['configurations'], self.imagePath+'/').output_command_list()

    def flash_ioc(self):
        path = os.path.join("runner/flash", self.imagePath, conf.flash[self.device_type.lower()]['ioc'])
        cmd = 'echo ' + conf.host.PASSWD + '|sudo -S ' + self.platform_path + 'ioc_flash_server_app -s ' + conf.flash[self.device_type.lower()]['ioc_port'] + ' -t ' + path
        logger.debug("flash ioc: " + cmd)
        count = 0
        while count < 5:
            ret = os.system(cmd)
            if ret == 0:
                logger.debug("Flash ioc successfully")
                return True
            else:
                count += 1
                time.sleep(3)
                logger.debug("Flash ioc Failed!!!")
                logger.debug("count is {0}".format(count))
        if count == 5:
            time.sleep(2)

    def flash_ifwi(self):
        """
        download_ifwi
        """
        path = os.path.join("runner/flash", self.imagePath, self.command_list[0])
        cmd = 'echo ' + conf.host.PASSWD + '|sudo -S ' + self.platform_path + 'ias-spi-programmer --write ' + path
        logger.debug("flash ifwi: " + cmd)
        count = 0
        while count < 10:
            time.sleep(2)
            create_relay08_cmd(3)
            time.sleep(3)
            create_relay08_cmd(1, 0.2)

            time.sleep(0.2 + count * 0.02)
            ret = os.system(cmd)
            if ret == 0:
                logger.debug("Flash ifwi successfully")
                return True
            else:
                logger.debug("Flash ifwi Failed!!!")
                count += 1
                logger.debug("count is {0}".format(count))
        if count == 10:
            sys.stderr.write("ifwi_flash_error:image_flash_failed")
            time.sleep(2)
            sys.exit(1)

    def flash_image(self):
        flash_image_exe = self.platform_path + 'fastboot'
        for item in self.command_list[1]:
            try:
                logger.debug(flash_image_exe + ' ' + item)
                os.system(flash_image_exe + ' ' + item)
            except Exception, e:
                logger.error('download %s error: %s' % (item, repr(e)))
                sys.exit()
        return True


def serial_port_check(usb_name='ttyUSB3'):
    id = ''
    find_line = os.popen("ps -aux | grep "+usb_name+" | grep 'sudo minicom'").readline()
    if "ps -aux" not in find_line:
        logger.debug(find_line)
        id = find_line.split()[1]
    if id == '':
        return True
    else:
        logger.debug("id is %s" % id)
        if os.system("echo "+conf.host.PASSWD+"|sudo kill " + id) == 0:
            logger.debug("killing %s ...." % id)
            return True
        else:
            logger.debug("kill %s is failed!!!" % id)
            return False


def main(argv):
    """
    main
    """
    device_type = ''
    build_number = ''
    url = ''
    cfg = ''
    build_info = ''
    force_down = False
    platform_path = os.popen('cat `which platformflashtool`').readlines()[-1].split(' ')[0].rstrip('platformflashtool')
    if platform_path == '':
        logger.debug('============<<<ERROR>>>============')
        logger.debug('please install platformflashtool')
        logger.debug('===================================')
        sys.exit()

    serial_port_check(usb_name='ttyUSB2')
    try:
        opts, args = getopt.getopt(argv, "hd:b:fu:c:i:", ["device_type=", "build_number=", "url=", "config=", "buildinfo="])
    except getopt.GetoptError:
        logger.debug('autodown_flash.py [-d <device_type>] [-b <build_number>] [-f]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            logger.debug('./autodown_flash.py [-d <device_type>] [-b <build_number>] [-u <url>] [-f]')
            sys.exit()
        elif opt in ("-d", "--device_type"):
            device_type = arg
        elif opt in ("-b", "--build_number"):
            build_number = arg
        elif opt == '-f':
            force_down = True
        elif opt in ("-u", "--url"):
            url = arg
        elif opt in ("-c", "--config"):
            cfg = arg
        elif opt in ("-i", "--build_info"):
            build_info = arg
    if device_type == '':
        logger.debug('device_type is empty!!!!!')
        sys.stderr.write("image_flash_failed")
        sys.exit(1)
    logger.debug('down load image.....')
    imagePath= down_load_image(device_type, build_number, url, cfg, build_info, force_down)
    if imagePath == '':
        logger.debug('download image error!!')
        sys.stderr.write("image_flash_failed")
        sys.exit(1)
    dflash = DownloadAndFlash(device_type, imagePath, platform_path)
    if len(dflash.command_list) == 1:
        logger.debug('get ifwi is error......')
        sys.exit()
    utiliy.reconnect_power()
    utiliy.reconnect_usb()
    dflash.flash_ioc()
    dflash.flash_ifwi()
    utiliy.reconnect_power()
    utiliy.reconnect_usb()
    time.sleep(5)
    utiliy.press_power_key()
    time.sleep(90)
    logger.debug('========> enter fastboot mode')
    utiliy.enter_fastboot_mode()
    logger.debug('========> start flash image')
    dflash.flash_image()
    time.sleep(1)
    utiliy.reconnect_power()
    utiliy.reconnect_usb()
    time.sleep(10)
    logger.debug('========> startup board by usb')
    utiliy.startup_by_usb()
    timeout = 300
    reboot_times = 1
    builder_name = re.findall('flashfiles-(.+)', imagePath)[0]
    while True:
        if timeout > 0:
            if os.popen('adb shell getprop dev.bootcomplete').read().strip() == '1':
                logger.debug("Devices boot complete")
                if re.search(builder_name, os.popen('adb shell getprop |grep ro.bootimage.build.fingerprint').read()):
                    logger.debug("Verify flash build success: %s" % builder_name)
                    break
                else:
                    logger.debug("Flash build failed current build:{0},target build:{1}".format(os.popen('adb shell getprop |grep ro.bootimage.build.fingerprint').read(), builder_name))
                    logger.debug("Progress will stop after 2sec")
                    sys.stderr.write("getprop error:image_flash_failed")
                    sys.exit(1)
            else:
                logger.debug("No device was found, wait for boot...")
                time.sleep(10)
                timeout -= 10
        else:
            if reboot_times > 0:
                logger.debug("Device boot Failed, reboot try again")
                reboot_times -= 1
                timeout = 300
                utiliy.hard_reboot()
            else:
                logger.debug("Device boot Failed, progress will stop after 2sec")
                sys.stderr.write("boot timeout:image_flash_failed")
                sys.exit(1)


if __name__ == "__main__":
    logger.debug("=======================================================")
    logger.debug("Notes:please make sure the DUT USB is connection \nand replug USB of debug board")
    logger.debug("=======================================================")
    main(sys.argv[1:])
