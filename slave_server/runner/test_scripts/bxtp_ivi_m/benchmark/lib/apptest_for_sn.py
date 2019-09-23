#!/usr/bin/python

import os,re,sys
import time
import inspect
import subprocess
from uiautomator import Device

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

class apptest(object):
    """docstring for apptest"""

    def __init__(self,sn,app):
        super(apptest, self).__init__()

        self.sn = sn
        self.app = app
        self.device = Device(self.sn)
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
        if self.device.screen == "off":
            self.logout(self.my_func_name(),"unlock screen...")
            os.system("adb -s %s shell input keyevent 82"%self.sn)
            time.sleep(2)
        else:
            self.logout(self.my_func_name(),"Screen On.")

    def app_install(self):
        installed_app_package = self.get_installed_app_package()
        if installed_app_package == "":
            self.logout(self.my_func_name(),"Install %s"%self.app_name)
            try:
                os.system("adb -s %s install %s"%(self.sn,self.app_path))
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
                os.system("adb -s %s uninstall "%(self.sn,self.app_path))
                time.sleep(2)
                self.logout(self.my_func_name(),"%s uninstall completed")
            except Exception, e:
                print e

    def get_installed_app_package(self):
        installed_app_package = os.popen("adb -s %s shell pm list package -3 |grep -i %s |awk -F ':' '{print$2}'"%(self.sn,self.app_package)).read().strip()
        return installed_app_package

    def enable_3rd_market_app_install(self):
        os.system('adb -s %s shell settings put secure install_non_market_apps 1'%self.sn)
        time.sleep(3)

    def get_package_name(self):
        p = re.compile(r"package: name=\'([\w+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i package"%(self.app_path)).read()
        package_name = re.findall(p,s)
        return ''.join(package_name)

    def get_activity_name(self):
        p = re.compile(r"launchable-activity: name=\'([\w+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i package"%(self.app_path)).read()
        activity_name = re.findall(p,s)
        return ''.join(activity_name)
    
    def get_app_version(self):
        p = re.compile(r"versionName=\'([\d+.]*)\'")
        s = os.popen("./src/aapt dump badging  %s | grep -i package"%(self.app_path)).read()
        version_name = re.findall(p,s)
        return ''.join(version_name)

    def launche_app(self):
        if self.get_installed_app_package() == "":
            self.app_install()
        else:
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        time.sleep(2)
        os.system("adb -s %s logcat -c"%self.sn)
        time.sleep(1)
        os.system("adb -s %s shell am start -n %s/%s"%(self.sn, self.app_package, self.app_activity))

    def clear_app_data(self):
        os.system('adb -s %s shell pm clear %s'%self.sn+self.app_package)

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

    def wait_for_complete(self,complete_text):
        i=0
        while self.device(text=complete_text).exists:
            self.logout(self.my_func_name(),"%s test finshed..."%self.app_name)
        else:
            i+=1
            time.sleep(1)
            sys.stdout.write("\r>>>Please wait for test complete. %s (s)" %i)
            sys.stdout.flush()

    def back_to_root_page(self,root_text):
        self.logout(self.my_func_name(),"Back to %s root page"%self.app_name)
        for i in range(10):
            if self.device(text=root_text).exists:
                break
            else:
                self.device.press.back()
                time.sleep(1)
    
    def kill_app(self):
        self.logout(self.my_func_name(),"Force stop %s"%self.app_name)
        os.system('adb -s %s shell am force-stop %s'%(self.sn,self.app_package))

if __name__ == '__main__':
    pass
