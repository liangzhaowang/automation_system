#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import re
from runner.operation_lib.base_lib.ctrl_relay08_threading import create_relay08_cmd


class CWP_FLASH:
    def __init__(self):
        self.test_tag = sys.argv[8]
        self.build = sys.argv[4]
        self.url = {
            'weekly': 'https://mcg-depot.intel.com/artifactory/cactus-absp-jf/build/eng-builds/master/PSI/weekly/%s/%s/userdebug/' % (self.build, self.test_tag),
            'latest': 'https://shstor001.sh.intel.com/artifactory/cactus-hypervisor-sh/hypervisor_dec_rel-latest/'
        }
        self.usr = 'eXV4aWFuMng='
        self.pwd = 'TW16Mnl1IUAjJA=='
        self.path = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
        self.dir = os.path.join(self.path, 'cwp_images', self.build)
        self.command_list = ['ifwi_gr_mrb_b1.bin']
        self.commands = [
            'flashing unlock',
            'flash gpt %s/partition_desc.bin' % self.dir,
            'flash sos_boot %s/sos_boot.img' % self.dir,
            'flash sos_rootfs %s/sos_rootfs.img' % self.dir,
            'flash data_partition %s/gordon_peak_cwp_AaaG.img' % self.dir,
            ' flashing lock',
            'reboot'
        ]
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
        with open(passwd_path) as pwdfp:
            host_passwd = pwdfp.read().strip()
        return host_passwd

    def get_weekly(self):
        AaaG_image = os.path.join(self.dir, 'gordon_peak_cwp_AaaG.img')
        if os.path.exists(AaaG_image):
            print "******AaaG_image is Exists******"
            return True
        else:
            print "******Get weekly %s infomation******" % self.build
            try:
                os.system("wget -O '%s/Aag.html' --http-user=%s --http-passwd=%s %s --no-check-certificate" % (self.dir, self.usr.decode('base64'), self.pwd.decode('base64'), self.url['weekly']))
                AaaG_html = os.path.join(self.dir, 'Aag.html')
                aag = open(AaaG_html).read()
                aag_img = re.findall(r'(\w+_AaaG.img)', aag)[0]
                print "AaaG_image", AaaG_image
                weekly_link = self.url['weekly']+aag_img
            except Exception, e:
                print "Get Aaag.img infomation failed:", e
                return False
            time.sleep(2)
            print "******Download AaaG.img******"
            try:
                os.system("wget -P %s --http-user=%s --http-passwd=%s %s --no-check-certificate" % (self.dir, self.usr.decode('base64'), self.pwd.decode('base64'), weekly_link))
                return True
            except Exception, e:
                print "Download Aaag.img file failed", e
                return False
                
    def get_latest(self):
        file_list = ['partition_desc.bin', 'sos_boot.img', 'sos_rootfs.img', 'ifwi_gr_mrb_b1.bin']
        try:
            for i in file_list:
                latest_file = os.path.join(self.dir, i)
                if not os.path.exists(latest_file):
                    print "******Download latest {0}******".format(i)
                    os.system("wget -O 'latest.html' --http-user=%s --http-passwd=%s %s --no-check-certificate" % (self.usr.decode('base64'), self.pwd.decode('base64'),self.url['latest']))
                    latest_html = os.path.join(self.path, 'latest.html')
                    latest = open(latest_html).read()
                    latest_img = re.findall(r'>(\d+)/', latest)[-1]
                    print "latest image is :", latest_img
                    latest_link = self.url['latest']+latest_img+"/"+i
                    os.system("wget -P %s --http-user=%s --http-passwd=%s %s --no-check-certificate" % (self.dir,self.usr.decode('base64'), self.pwd.decode('base64'),latest_link))
                else:
                    print "******latest file %s is exists******" % i
            return True
        except Exception, e:
            print "******Download latest {0} failed******".format(i), e.message
            return False

    def flash_ifwi(self):
        ifwi_tool_path = '/opt/ias/programming_tools/'
        path = os.path.join(self.dir, self.command_list[0])
        passwd = self._get_passwd()
        print "Path=======:", path
        cmd = 'echo '+passwd+'|sudo -S '+ifwi_tool_path+'ias-spi-programmer --write '+path
        print "CMD=======:", cmd
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

    def flash_cwp(self):
        print "******Del all html files******"
        print "self.test_tag", self.test_tag
        passwd = self._get_passwd()
        time.sleep(2)
        os.system("rm *.html")
        if self.get_weekly() and self.get_latest():
            print "====================Flash ifwi==================="

            if self.flash_ifwi():
                time.sleep(10)
                print "========wait for ttyusb3 init========"
                time.sleep(1)
                cmd = "echo '"+passwd+"' | sudo -S python ~/slave_server/runner/flash/lib/serial_com.py -p /dev/ttyUSB2 -c n2#"
                print "test_cmd:", cmd
                time.sleep(1)
                os.system(cmd)
                time.sleep(60)
                print "==========Enable Fastboot Mode=========="
                time.sleep(10)
                try:
                    # os.system("adb reboot bootloader")
                    # time.sleep(10)
                    if len((os.popen("fastboot devices")).read()) != 0:
                        time.sleep(2)
                        for i in self.commands:
                            print "******Flash images {0}******".format(i)
                            os.system("fastboot %s" % i)
                            time.sleep(2)
                        time.sleep(10)
                        create_relay08_cmd(1)   
                except Exception, e:
                    print "******Flash image Failed******:", e
                    return False
        else:
            print "****** Get_weekly or Get_latest Failed ******"
            return False


if __name__ == "__main__":
    CWP_FLASH().flash_cwp()
