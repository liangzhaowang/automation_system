#!/usr/bin/python

import os,re,sys
import time
import inspect
import subprocess
from uiautomator import Device

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

class apptest(object):
    """docstring for apptest"""

    def __init__(self,app):
        super(apptest, self).__init__()

        self.app = app
        self.device = Device()
        self.app_name = self.app[0]
        self.app_path = self.app[1]
        self.app_package = self.get_package_name()
        self.app_activity = self.get_activity_name()
    
    #get function name
    def my_func_name(self):
        return inspect.stack()[1][3]
    
    #logout
    def logout(self,function_name,log_message):
        print ">>>%s:"%function_name+log_message
    
    #timeout
    def command_timeout(self,cmdline,timeout=60):
        p = subprocess.Popen(cmdline, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        t_beginning = time.time()
        seconds_passed = 0
        while True:
            if p.poll() is not None:
                return True
            seconds_passed = time.time() - t_beginning
            self.logout(self.my_func_name(), "Waiting.......%s (s)"%int(seconds_passed))
            if timeout and seconds_passed > timeout:
                p.terminate()
                return False
            time.sleep(1)

    def screen_on(self):
        time.sleep(5)
        if self.device.screen == "off":
            self.logout(self.my_func_name(),"unlock screen...")
            self.device.wakeup()
            os.system("adb shell input keyevent 82")
            time.sleep(1)
        else:
            self.logout(self.my_func_name(),"Screen On.")

    def app_install(self):
        installed_app_package = self.get_installed_app_package()
        if installed_app_package == "":
            self.logout(self.my_func_name(),"Install %s"%self.app_name)
            try:
                os.system("adb install %s"%self.app_path)
                self.enable_3rd_market_app_install()
                time.sleep(2)
            except Exception, e:
                print e
            installed_app_package = self.get_installed_app_package()
            if installed_app_package != "":
                self.logout(self.my_func_name(), "Install completed, %s is found"%installed_app_package)
            else:
                self.logout(self.my_func_name(), "Install failed, %s not found"%installed_app_package)
        else:
            self.logout(self.my_func_name(), "%s alread installed"%self.app_name)

    def app_uninstall(self):
        installed_app_package = self.get_installed_app_package()
        if installed_app_package == "":
            self.logout(self.my_func_name(), "%s not found"%installed_app_package)
        else:
            try:
                os.system("adb uninstall %s"%self.app_package)
                time.sleep(2)
                self.logout(self.my_func_name(),"%s uninstall completed"%self.app_name)
            except Exception, e:
                print e

    def get_installed_app_package(self):
        installed_app_package = os.popen("adb shell pm list package -3 |grep -i %s |awk -F ':' '{print$2}'"%(self.app_package)).read().strip()
        return installed_app_package

    def enable_3rd_market_app_install(self):
        os.system('adb shell settings put secure install_non_market_apps 1')
        time.sleep(3)

    def get_package_name(self):
        p = re.compile(r"package: name=\'([\w+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i package"%(self.app_path)).read()
        package_name = re.findall(p,s)[0]
        return ''.join(package_name)

    def get_activity_name(self):
        p = re.compile(r"launchable-activity: name=\'([\w+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i activity"%(self.app_path)).read()
        activity_name = re.findall(p,s)[0]
        return ''.join(activity_name)
    
    def get_app_version(self):
        p = re.compile(r"versionName=\'([\d+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i package"%(self.app_path)).read()
        version_name = re.findall(p,s)
        return ''.join(version_name)

    def launch_app(self):
        if self.get_installed_app_package() == "":
            self.app_install()
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        else:
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        time.sleep(2)
        os.system("adb logcat -c")
        self.clear_app_data()
        time.sleep(1)
        os.system("adb shell am start -n %s/%s"%(self.app_package, self.app_activity))

    def clear_app_data(self):
        self.logout(self.my_func_name(),'...')
        os.system('adb shell pm clear %s'%self.app_package)

    def clear_recent(self):
        self.device.press.home()
        time.sleep(2)
        launcher_packsge = self.device.info['currentPackageName']
        time.sleep(2)
        self.device.press.recent()
        time.sleep(2)
        cur_package = self.device.info['currentPackageName']
        #while cur_package != "com.android.launcher":
        while cur_package != launcher_packsge:
#            self.device.swipe(100,640,600,640,steps=10)
            time.sleep(1)
            cur_package = self.device.info['currentPackageName']

    def wait_for_complete(self,complete_text,timeout=3600,skipstep=5):
        i = 0
        while i < timeout:
            if self.device(resourceIdMatches=".+/%s"%complete_text).exists:
                print
                self.logout(self.my_func_name(),"%s test finshed..."%self.app_name)
                break
            else:
                i+=skipstep
                time.sleep(skipstep)
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)" %i)
                sys.stdout.flush()
        else:
            self.logout(self.my_func_name(),"Timeout for %s test"%self.app_name)
            os.system("echo 123456|sudo -S python "+CUR_DIR+"/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            time.sleep(10)
            
    def wait_for_root_page(self,root_text):
        self.logout(self.my_func_name(),"Wait for %s root page"%self.app_name)
        print "----------------------------"
        self.logout(self.my_func_name(),".+/%s$"%root_text)
        for i in range(600):
            if self.device(resourceIdMatches=".+/%s$"%root_text).exists:
                print
                break
            else:
                i+=1
                time.sleep(1)
                sys.stdout.write("\r>>>Please wait for %s root page. %s (s)" %(self.app_name,i))
                sys.stdout.flush()
    
    def kill_app(self):
        self.logout(self.my_func_name(),"Force stop %s"%self.app_name)
        os.system('adb shell am force-stop %s'%(self.app_package))

if __name__ == '__main__':
    pass
