#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import serial
import time
import os
import commands
import zipfile
import threading
import shutil
import re
import traceback
import sys
import ssl
import urllib2
import requests
import json
import yaml
from optparse import OptionParser

con = threading.Condition()
flash_result = {}
slave_conf = yaml.load(open('slave.yaml', 'r'))
# auth_header = json.loads(requests.get('http://{server}/api/auth_header'.format(server=slave_conf['server'])).content)['Authorization'].split()[1]
auth_header = json.loads(requests.get('http://{server}/api/auth_header'.format(server=slave_conf['server'])).content)

class Aia_flash(threading.Thread):

    def __init__(self, build, build_type, url, target, **kwargs):
        self.serial = "DW1724778700001"
        self.relay_USB = "/dev/ttyUSB0" #self.get_mapping_dev("relayCard")
        self.udisk = "/dev/sdb1" #self.get_mapping_dev("U_Disk")
        self.image_dir = 'runner/flash/image/KBL_image' #kwargs["image_dir"]
        self.relay_ser = serial.Serial(self.relay_USB, 19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_TWO, None)
        self.mount_dir = os.path.join("/mnt/", self.serial)
        self.relay_udisk_port = [5, 6, 7, 8]
        self.relay_power_port = 1
        self.build = build
        self.build_type = build_type
        self.target = target
        self.url = os.path.join(url, self.build, self.target, "userdebug/")
        print '------------------------------'
        print 'image url: ' + self.url
        print '------------------------------'
        username = auth_header['Authorization'].split()[1].decode('base64').split(':')[0]
        passwd = auth_header['Authorization'].split()[1].decode('base64').split(':')[1]
        self.image_info = requests.get(self.url, verify=False, headers=auth_header).content
        self.filename = (re.search(self.target + '-flashfiles-.+.zip', self.image_info)).group().split('>')[-1]
        self.image_path = os.path.join(self.image_dir, self.filename.replace('.zip', ''))

    def set_flash_result(self, verdict):
        global flash_result
        con.acquire()
        if verdict:
            flash_result[self.serial] = True
        else:
            flash_result[self.serial] = False
        con.release()

    def get_mapping_dev(self, device):
        for dev in os.listdir("/dev/"):
            if device in dev and self.serial in dev:
                return os.path.join("/dev/", dev)
        else:
            raise Exception("{} can't find {}".format(self.serial, device))

    def format_udisk(self):
        status_output = commands.getstatusoutput("mkfs.vfat {}".format(self.udisk))
        if status_output[0] == 0:
            print "----{} format success".format(self.udisk)
        else:
            raise Exception("{} format udisk fail: {}".format(self.udisk, status_output[1]))

    def create_mount_dir(self):
        print "----{} start create mount dir {}".format(self.serial, self.mount_dir)
        if os.path.exists(self.mount_dir):
            shutil.rmtree(self.mount_dir)
        os.makedirs(self.mount_dir)
        if os.path.exists(self.mount_dir):
            print "----{} create success".format(self.mount_dir)
        else:
            raise Exception("{} create fail".format(self.mount_dir))

    def mount_udisk(self):
        if self.udisk not in commands.getoutput("df {}".format(self.mount_dir)):
            cmd = "mount -t vfat -o rw {} {}".format(self.udisk, self.mount_dir)
            print "----{} {}".format(self.serial, cmd)
            status_out = commands.getstatusoutput(cmd)
            if status_out[0] == 0:
                print "----{} {} success".format(self.serial, cmd)
            else:
                raise Exception("{} {} fail {}".format(self.serial, cmd, status_out[1]))

    def umount_udisk(self):
        if self.udisk in commands.getoutput("df {}".format(self.mount_dir)):
            cmd = "umount {}".format(self.mount_dir)
            print "----{} {}".format(self.serial, cmd)
            status_out = commands.getstatusoutput(cmd)
            if status_out[0] == 0:
                print "----{} {} success".format(self.serial, cmd)
            else:
                raise Exception("{} {} fail: {}".format(self.serial, cmd, status_out[1]))

    def copy_image_udisk(self):
        print "----{} start copy {} to {}".format(self.serial, self.image_path, self.mount_dir)
        cmd = "cp -r -v {}/* {}".format(self.image_path, self.mount_dir)
        commands.getoutput(cmd)
        status_output = commands.getstatusoutput("sync")
        if status_output[0] == 0:
            print "----{} copy image success".format(self.mount_dir)
        else:
            raise Exception("{} copy image fail: {}".format(self.mount_dir, status_output[1]))

    def relay_handle(self, port, status):
        #port: 1, 2, 3, 4, 5, 6, 7, 8
        #status: on, off
        if status == "on":
            cmd = 100
        elif status == "off":
            cmd = 110
        cmd += port
        print "----{} set relay port {} {}".format(self.serial, port, status)
        self.relay_ser.write(chr(cmd))
        time.sleep(0.3)

    def switch_udisk_host(self):
        print "----{} switch udisk to host, {} LED will off".format(self.serial, self.relay_udisk_port)
        for port in self.relay_udisk_port:
            self.relay_handle(port, "off")
        time.sleep(3)

    def switch_udisk_aia(self):
        print "----{} switch udisk to aia, {} LED will on".format(self.serial, self.relay_udisk_port)
        for port in self.relay_udisk_port:
            self.relay_handle(port, "on")
        time.sleep(3)

    def press_aia_power(self, press_time=2):
        print "----{} turn on, {} LED will on".format(self.serial, self.relay_power_port)
        self.relay_handle(self.relay_power_port, "on")
        time.sleep(press_time)
        print "----{} turn on, {} LED will off".format(self.serial, self.relay_power_port)
        self.relay_handle(self.relay_power_port, "off")
        time.sleep(2)

    def turn_on_aia(self):
        self.press_aia_power()

    def sleep_aia(self):
        self.press_aia_power()

    def turn_off_aia(self):
        self.press_aia_power(press_time=10)

    def erase_bootloader(self):
        print "----{} dd start".format(self.serial)
        cmd = "adb shell dd if=/dev/zero of=/dev/block/sda1"
        output = commands.getoutput(cmd)
        print "----{} {}".format(self.serial, output)
        print "----{} dd finished".format(self.serial)

    def wait_flash(self, timeout=800):
        while True:
            adb_devices = commands.getoutput("adb devices")
            if self.serial in adb_devices:
                print "----{} is available now".format(self.serial)
                return
            elif timeout > 0:
                time.sleep(10)
                timeout -= 10
                print "----{} {} seconds left to wait flash".format(self.serial, timeout)
            else:
                print "----{} flash timeout".format(self.serial)
                raise Exception("----{} can't be found after wait".format(self.serial))

    def get_device_image_version(self):
        cmd = "adb shell getprop |grep ro.build.fingerprint"
        return commands.getoutput(cmd).split("/")[-2].split(":")[0]

    def check_flash_result(self):
        flash_image_version = self.image_dir.split("-")[-1]
        device_image_version = self.get_device_image_version()
        if flash_image_version == device_image_version:
            self.set_flash_result(True)
        else:
            self.set_flash_result(False)

    def prepare_flash_udisk(self):
        self.create_mount_dir()
        self.switch_udisk_host()
        self.format_udisk()
        self.mount_udisk()
        self.copy_image_udisk()
        self.umount_udisk()
        self.switch_udisk_aia()

    def run(self):
        try:
            self.prepare_flash_udisk()
            self.erase_bootloader()
            self.turn_off_aia()
            self.turn_on_aia()
            self.wait_flash()
            self.check_flash_result()
        except Exception, e:
            self.set_flash_result(False)
            print traceback.format_exc()
            print e
        finally:
            self.switch_udisk_host()
    
    def root_device(serials):
        for serial in serials:
            print "----adb -s {} root".format(serial)
            print commands.getoutput("adb root")

    def flash_aias(self, **kwargs):
        self.root_device([self.serial])
        image_zip = self.download_image(self.image_dir)
        if image_zip:
            self.image_dir = self.unzip(image_zip)
            self.start_flash()


        # self.start_flash_threads(serials, self.unzip(Download(kwargs["username"], kwargs["password"], image_url, image_dir).download()))
        global flash_result
        print flash_result
        # Download(kwargs["username"], kwargs["password"], image_url, image_dir).delete()
        return flash_result
    def download_image(self, image_dir):
        auth_header = json.loads(requests.get('http://{server}/api/auth_header'.format(server=slave_conf['server'])).content)
        username = auth_header['Authorization'].split()[1].decode('base64').split(':')[0]
        passwd = auth_header['Authorization'].split()[1].decode('base64').split(':')[1]
        image_info = requests.get(self.url, verify=False, headers=auth_header).content
        filename = (re.search(self.target + '-flashfiles-.+.zip', image_info)).group().split('>')[-1]
        image_path = os.path.join(image_dir, filename.replace('.zip', ''))
        if os.path.exists(image_path) or os.path.exists(os.path.join(image_dir, filename)):
            print "========== {0} is Exists ==========".format(image_path)
            return filename
        else:
            image_link = self.url + filename
            print "========== Download %s ==========" % image_link
            try:
                if os.system("wget -P %s --http-user=%s --http-passwd=%s %s --no-check-certificate"% (image_dir, username, passwd, image_link)) == 0:
                    print "========== Dowload image {0} success ==========".format(os.path.join(image_dir, filename))
                    return filename
                else:
                    return ''
            except Exception, e:
                print "Download {0} file failed".format(self.filename), repr(e)
                return ''
    def unzip(self, image_path):
        try:
            downloadfile = os.path.join(self.image_dir, self.filename)
            print "========== Uzip {download} to {dir} ==========".format(download=downloadfile,dir=self.image_path)
            zfile = zipfile.ZipFile(downloadfile)
            zfile.extractall(path=self.image_path)
            zfile.close()
            os.remove(downloadfile)
        except Exception, IOError:
            print "extract error:{0}".format(IOError)
            return False


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--image_dir", dest="image_dir",
                      metavar="IMAGE_DIR",
                      help="the dir for image save")

    parser.add_option("-s", "--serialnumber", dest="serialnumber",
                      metavar="SERIALNUMBER",
                      help="the flash image's devices such as  -s \"G6BN746008NY, G6BN746008HA\" ")
    (opts, args) = parser.parse_args()
    if not (opts.url and opts.username and opts.password and opts.serialnumber):
        parser.print_help()
        exit(-1)

# def root_device(serials):
#     for serial in serials:
#         print "----adb -s {} root".format(serial)
#         print commands.getoutput("adb -s {} root".format(serial))

# def unzip(image_zip):
#     image_zip = os.path.abspath(image_zip)
#     image_dir = os.path.join(os.path.dirname(image_zip), os.path.basename(image_zip).split(".")[0])
#     if os.path.exists(image_dir):
#         shutil.rmtree(image_dir)
#     os.makedirs(image_dir)
#     if os.path.exists(image_dir):
#         print "----created image dir {}".format(image_dir)
#     print "----start unzip {} to {}".format(image_zip, image_dir)
#     zfile = zipfile.ZipFile(image_zip, 'r')
#     zfile.extractall(image_dir)
#     return image_dir

# def start_flash_threads(serials, image_dir):
#     threads = []
#     for serial in serials:
#         threads.append(AIA(serial=serial, image_dir=image_dir))
#     for t in threads:
#         t.start()
#     for t in threads:
#         t.join()

# def flash_aias(serials, image_url, image_dir):
#     root_device(serials)
#     image_url = image_url
#     if image_dir:
#         image_dir = image_dir
#     else:
#         image_dir = os.getcwd()
#     # start_flash_threads(serials, unzip(Download(kwargs["username"], kwargs["password"], image_url, image_dir).download()))
#     global flash_result
#     print flash_result
#     # Download(kwargs["username"], kwargs["password"], image_url, image_dir).delete()
#     get_files(self)
#     return flash_result


# if __name__ == "__main__":

#     parser = OptionParser()
#     parser.add_option("-u", "--url", dest="url",
#                       metavar="URL",
#                       help="url for download the image")
#     parser.add_option("-d", "--image_dir", dest="image_dir",
#                       metavar="IMAGE_DIR",
#                       help="the dir for image save")
#     parser.add_option("-n", "--username", dest="username",
#                       metavar="USERNAME",
#                       help="download image's account")
#     parser.add_option("-p", "--password", dest="password",
#                       metavar="PASSWOED",
#                       help="download image's password")
#     parser.add_option("-s", "--serialnumber", dest="serialnumber",
#                       metavar="SERIALNUMBER",
#                       help="the flash image's devices such as  -s \"G6BN746008NY, G6BN746008HA\" ")
#     (opts, args) = parser.parse_args()
#     if not (opts.url and opts.username and opts.password and opts.serialnumber):
#         parser.print_help()
#         exit(-1)
#     flash_aias(opts.serialnumber.split(","),image_url=opts.url,username=opts.username,password=opts.password,image_dir=opts.image_dir)
