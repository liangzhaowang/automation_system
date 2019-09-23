#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import serial
import ssl
import urllib2
import re
import zipfile
import requests
import json
import yaml
from threading import Thread
from operation_lib.base_lib.ctrl_relay08_threading import create_relay08_cmd
from flash.lib.skip_security import startSkip

rds = slave_conf = yaml.load(open('slave.yaml', 'r')) 
rids = json.loads(requests.get('http://{server}/api/auth_header'.format(server=slave_conf['server'])).content)['Authorization'].split()[1]
ssl._create_default_https_context = ssl._create_unverified_context


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read().strip()
    print "password",host_passwd
    return host_passwd

passwd = _get_passwd()
os.system("echo '"+passwd+"'|sudo -S chmod 777 /dev/ttyUSB3")

class StartAndroid:
    def __init__(self):
        self.passout = 0
        self.serlog = 0
        self.ser = serial.Serial('/dev/ttyUSB3', '115200', 8)

    def readserial(self):
        while True:
            lines = self.ser.readline()
            print "************ %s" % lines
            if lines.find('ACRN:') != -1:
                self.serlog = 1
                print self.serlog
            if self.serlog == 4:
                print "readserial", self.serlog
                time.sleep(1)
                for i in range(300):
                    if os.popen('adb shell getprop dev.bootcomplete').read().strip() == '1':
                        print "********** Android Satrt Success **********"
                        self.ser.close()
                        print "End Flash:%s" % time.ctime()
                        return True
                    else:
                        time.sleep(1)
                break

    def writecommad(self):
        while True:
            if self.serlog == 1 and self.passout == 0:
                self.passout +=1
                time.sleep(1)
                print "********** start sos"
                self.ser.write('sos_console 0\r'.encode())
                time.sleep(20)
                self.serlog += 1
            if self.serlog == 2 and self.passout ==1 :
                self.passout += 1
                for i in range(10):
                    self.ser.write('\b')
                    time.sleep(0.1)
                time.sleep(5)
                print "********** set username"
                self.ser.write('root\r'.encode())
                time.sleep(5)
                for j in range(2):
                    time.sleep(5)
                    print "********** set password"
                    self.ser.write('pnp@1234\r'.encode())
                self.serlog += 1
                print self.serlog
            if self.serlog == 3 and self.passout == 2:
                time.sleep(5)
                # print "mask systemd-timesyncd"
                # self.ser.write('systemctl mask systemd-timesyncd\r'.encode())
                # print "********** cp 'lunch_UOS.sh'"
                # self.ser.write('cp /usr/share/acrn/samples/apl-mrb/launch_uos.sh .\r'.encode())
                # time.sleep(1)
                # print "********** add 'lunch_UOS.sh'"
                # time.sleep(1)
                # self.ser.write('acrnctl add launch_uos.sh -V 2\r'.encode())
                # time.sleep(1)
                # self.ser.write('\r'.encode())
                # print "********** enable acrnd"
                # time.sleep(1)
                # self.ser.write('systemctl enable acrnd\r'.encode())
                # time.sleep(1)
                # self.ser.write('\r'.encode())
                # print "********** start acrnd"
                # time.sleep(1)
                # self.ser.write('systemctl start acrnd\r'.encode())
                time.sleep(1)
                self.ser.write("echo 'PermitRootLogin Yes' > /etc/ssh/sshd_config\r".encode())
                time.sleep(1)
                self.serlog += 1
                break

    def runseriallog(self):
        try:
            a = Thread(target=self.writecommad)
            a.start()
            b = Thread(target=self.readserial)
            b.start()
            a.join()
            b.join()
        except Exception, e:
            print "Run thread Failed:%s"%e


class AcrnFlash:
    def __init__(self, build, build_type, url, target):
        self.timeout = 300
        self.build = build
        self.build_type = build_type
        self.target = target
        self.url = os.path.join(url, self.build, self.target, "userdebug/")
        self.request = urllib2.Request(self.url)
        self.request.add_header("Authorization", "Basic %s" % rids )
        self.reponse = urllib2.urlopen(self.request)
        self.html = self.reponse.read()
        self.filename = (re.search('gordon_peak_acrn-flashfiles.+.zip', self.html)).group().split('>')[-1]
        self.dir = 'runner/flash/image/Acrn_image'
        self.imagedir = os.path.join(self.dir, self.filename.replace(".zip", ""))
        self.flash_list = [
            'ifwi.bin',
            'partition_desc.bin',
            'sos_boot.img',
            'sos_rootfs.img',
            'gordon_peak_acrn_AaaG.img'
        ]
        self.commands = [
            'flashing unlock',
            'flash gpt %s' % (os.path.join(self.imagedir, self.flash_list[1])),
            'flash sos_boot %s' % (os.path.join(self.imagedir, self.flash_list[2])),
            'flash sos_rootfs %s' % (os.path.join(self.imagedir, self.flash_list[3])),
            'flash data_partition %s' % (os.path.join(self.imagedir, self.flash_list[4])),
            'flashing lock',
            'reboot'
        ]
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def get_files(self):
        print "========== imagefile ==========",self.imagedir
        if os.path.exists(self.imagedir):
            print "========== {0} is Exists ==========".format(self.imagedir)
            time.sleep(1)
        else:
            try:
                image_link = self.url+self.filename
                print "========== Download %s ==========" %image_link
                if os.system("wget -P %s --http-user=%s --http-passwd=%s %s --no-check-certificate"% (self.dir, rids.decode('base64').split(':')[0], rids.decode('base64').split(':')[1], image_link)) == 0:
                    print "========== Dowload image {0} success ==========".format(os.path.join(self.dir, self.filename))
            except Exception, e:
                print "Download {0} file failed".format(self.filename), e
                return False
            try:
                downloadfile = os.path.join(self.dir, self.filename)
                print "========== Uzip {download} to {dir} ==========".format(download=downloadfile,dir=self.imagedir)
                zfile = zipfile.ZipFile(downloadfile)
                zfile.extractall(path=self.imagedir)
                zfile.close()
                os.remove(downloadfile)
            except Exception, IOError:
                print "extract error:{0}".format(IOError)
                return False
        return True
    def flash_ifwi(self):
        ifwi_tool_path = '/opt/intel/platformflashtool/bin/ias-spi-programmer'
        path = os.path.join(self.imagedir, self.flash_list[0])
        print "Path =======: ", path
        cmd = 'echo '+passwd+'|sudo -S '+ifwi_tool_path+' --write '+path
        print "CMD =======: ", cmd
        count = 0
        while count < 5:
            print "Traceback info:"
            print "========================================"
            try:
                time.sleep(2)
                create_relay08_cmd(3)
                time.sleep(10)
                create_relay08_cmd(1, 0.5)
                s = os.system(cmd)
                print "========================================"
                if s == 0:
                    print "Flash ifwi successfully"
                    return True
                else:
                    print "Flash ifwi Failed!!!"
                    count += 1
                    print "count is {0}".format(count)
                    time.sleep(10)
            except Exception, e:
                print e

    def flash_images(self):
        time.sleep(2)
        if self.get_files():
            print "==================== Flash ifwi ==================="
            if self.flash_ifwi():
                time.sleep(10)
                print "======== wait for ttyusb3 init ========"
                time.sleep(1)
                cmd = "echo "+passwd+"| sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n4#"
                print cmd
                time.sleep(1)
                os.system(cmd)
                time.sleep(60)
                print "********* Enable Fastboot Mode ********"
                time.sleep(10)
                counts = 0
                while counts < 3:
                    if len((os.popen("fastboot devices")).read()) != 0:
                        time.sleep(2)
                        try:
                            for i in self.commands:
                                print "****** Flash images: {0} ******".format(i)
                                os.system("fastboot %s" % i)
                                time.sleep(2)
                        except Exception, e:
                            print "****** Flash image Failed ******:", e
                            return False
                        time.sleep(10)
                        self.enablesysytem()
                        return True
                    else:
                        print "******Enable Fastboot Mode Failed Try again******"
                        time.sleep(1)
                        counts += 1
		return False
        else:
            print "****** Download Images Failed ******"
            return False

    def enablesysytem(self):
        cmd = "echo 123456| sudo -S python runner/operation_lib/serial_com.py -p /dev/ttyUSB2 -c n1#"
        if os.system(cmd) == 0:
            StartAndroid().runseriallog()
	    startSkip()
        else:
            print "********** device boot failed **********"
            sys.stderr.write("image_flash_failed")
            sys.exit(1)




