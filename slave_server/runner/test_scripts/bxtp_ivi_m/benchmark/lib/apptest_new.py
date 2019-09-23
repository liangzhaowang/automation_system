#!/usr/bin/python

import os,re,sys
import time
import inspect
import subprocess
import Queue
from uiautomator import device as app_device
from kill_uiautomator import kill_adb_uiautomator_block
CUR_DIR = os.path.join(os.path.dirname(__file__), os.path.pardir)
print CUR_DIR
aapt_path = os.path.join(CUR_DIR, 'src', 'aapt')

def _byteify(data, ignore_dicts = False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return {  
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data

def app_excetion_kill_case(app_name):
    app_name = str(app_name)
    #print app_name
    flines = os.popen("adb shell ps | grep "+app_name).readlines()
    #print flines
    if len(flines):
        print flines
        return True
    else:
        return False

class apptest(object):
    """docstring for apptest"""

    def __init__(self,app):
        super(apptest, self).__init__()
        self.app = app
        self.device = app_device
        self.app_name = str(self.app[0]).lower()
        print self.app_name
        self.app_path = self.app[1]
        print self.app_path
        self.app_package = self.get_package_name()
        self.app_activity = self.get_activity_name()
        self.data = Queue

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
        kill_adb_uiautomator_block()
        if self.device.screen == "off":
            self.logout(self.my_func_name(),"unlock screen...")
            kill_adb_uiautomator_block()
            self.device.wakeup()
            #os.system("adb shell input keyevent 82")
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
        s = os.popen(aapt_path +" dump badging  %s | grep -i package"%(self.app_path)).read()
        package_name = re.findall(p,s)[0]
        return ''.join(package_name)

    def get_activity_name(self):
        p = re.compile(r"launchable-activity: name=\'([\w+.]*)\'")
        print aapt_path
        s = os.popen(aapt_path +" dump badging  %s | grep -i activity"%(self.app_path)).read()
        activity_name = re.findall(p,s)[0]
        return ''.join(activity_name)
    
    def get_app_version(self):
        p = re.compile(r"versionName=\'([\d+.]*)\'")
        s = os.popen(aapt_path +" dump badging  %s | grep -i package"%(self.app_path)).read()
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

    def clear_app_data(self,app_nam=''):
        self.logout(self.my_func_name(),'...')
        os.system('adb shell pm clear %s'%self.app_package)
        if not app_nam == "":
            self.logout(self.my_func_name(),"... %s"%app_nam)
            os.system('adb shell pm clear %s'%(app_nam))

    def clear_recent(self):
        kill_adb_uiautomator_block()
        self.device.press.home()
        time.sleep(2)
        kill_adb_uiautomator_block()
        launcher_packsge = self.device.info['currentPackageName']
        time.sleep(2)
        kill_adb_uiautomator_block()
        self.device.press.recent()
        time.sleep(2)
        kill_adb_uiautomator_block()
        cur_package = self.device.info['currentPackageName']
        #while cur_package != "com.android.launcher":
        while cur_package != launcher_packsge:
#            self.device.swipe(100,640,600,640,steps=10)
            time.sleep(1)
            cur_package = self.device.info['currentPackageName']

    def wait_for_complete(self,complete_text,timeout=3600):
        i = 0
        failed_time = 0
        kill_adb_uiautomator_block()
        while i < timeout:
            kill_adb_uiautomator_block()
            if not app_excetion_kill_case(self.app_package):
                if failed_time > 2:
                    return False
                failed_time +=1
                continue
            app_dev = self.device(resourceIdMatches=".+/%s$"%complete_text)
            if app_dev:
		        if app_dev.exists:
		            print
		            self.logout(self.my_func_name(),"%s test finshed..."%self.app_name)
		            return True
            else:
                i+=5
                time.sleep(5)
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)"%i)
                sys.stdout.flush()
                failed_time = 0
        else:
            self.logout(self.my_func_name(),"Timeout for %s test"%self.app_package)
            return False

    def wait_for_complete_by_text(self,complete_text,timeout=3600):
        i = 0
        failed_time = 0
        self.logout(self.my_func_name(),"%s test waiting..."%self.app_package)
        kill_adb_uiautomator_block()
        while i < timeout:
            if self.device(text=complete_text).exists:
                print
                self.logout(self.my_func_name(),"%s test finshed..."%self.app_package)
                return True
            else:
                i+=5
                kill_adb_uiautomator_block()
                time.sleep(5)
                if not app_excetion_kill_case(self.app_package):
                    if failed_time > 2:
                         self.logout(self.my_func_name(),"%s test is failed..."%self.app_package)
                         return False
                    failed_time +=1
                    continue
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)" %i)
                sys.stdout.flush()
                failed_time = 0
        else:
            self.logout(self.my_func_name(),"Timeout for %s test"%self.app_name)
            return False
    def wait_for_complete_ex(self,complete_text,timeout=3600):
        i = 0
        failed_time = 0
        self.logout(self.my_func_name(),"%s test waiting..."%self.app_package)
        kill_adb_uiautomator_block()
        while i < timeout:
            if self.device(resourceId="%s"%complete_text).exists:
                print
                self.logout(self.my_func_name(),"%s test finshed..."%self.app_package)
                return True
            else:
                i+=5
                kill_adb_uiautomator_block()
                time.sleep(5)
                if not app_excetion_kill_case(self.app_package):
                    if failed_time > 2:
                         self.logout(self.my_func_name(),"%s test is failed..."%self.app_package)
                         return False
                    failed_time +=1
                    continue
                sys.stdout.write("\r>>>Please wait for test complete. %s (s)" %i)
                sys.stdout.flush()
                failed_time = 0
        else:
            self.logout(self.my_func_name(),"Timeout for %s test"%self.app_name)
            return False
    def wait_for_root_page(self,root_text = "",decription_text = ""):
        failed_time = 0
        self.logout(self.my_func_name(),"Wait for %s root page"%self.app_name)
        #self.logout(self.my_func_name(),"Wait %s ------"%root_text)
        for i in range(600):
            if i % 5 == 0:
                kill_adb_uiautomator_block()
            if decription_text == "":
                if self.device(resourceIdMatches=".+/%s$"%root_text).exists:
                    print
                    break
            else:
                if self.device(description="%s"%decription_text).exists:
                    print
                    break
            i+=1
            time.sleep(1)
            if not app_excetion_kill_case(self.app_package):
                if failed_time > 6:
                     self.logout(self.my_func_name(),"%s test is failed..."%self.app_package)
                     return False
                failed_time +=1
                continue
            sys.stdout.write("\r>>>Please wait for %s root page. %s (s)" %(self.app_name,i))
            sys.stdout.flush()
            failed_time = 0
    
    def kill_app(self,app_nam=''):
        self.logout(self.my_func_name(),"Force stop %s"%self.app_name)
        os.system('adb shell am force-stop %s'%(self.app_package))
        if not app_nam == "":
            self.logout(self.my_func_name(),"Force stop %s"%app_nam)
            os.system('adb shell am force-stop %s'%(app_nam))

    def get_score_info_data(self,key_code,info_code,timeout=10):
        icount = 0
        score = ""
        kill_adb_uiautomator_block()
        while icount < timeout:
            # print 'icount = %s'%icount
            app_dev = self.device(resourceIdMatches=".+/%s$"%key_code)
            if app_dev.exists:
                info_dict = app_dev.info
                info_dict = _byteify(info_dict)
                # print 'info_code = %s'%info_code             
                score = info_dict[info_code]
                # print 'score = %s'%score
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block()
        return score
    
    def click_ui_button_by_resourceIdMatches(self,key_code,timeout=10):
        icount = 0
        kill_adb_uiautomator_block()
        while icount < timeout:
            if not app_excetion_kill_case(self.app_package):
                self.logout(self.my_func_name(),"%s test is failed..."%self.app_package)
                return False
            app_dev = self.device(resourceIdMatches=".+/%s$"%key_code)
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block()
        if icount > 0:
            return False
        else:
            return True

    def click_ui_button_by_text(self,key_code="",textcont="",timeout=10):
        icount = 0
        kill_adb_uiautomator_block()
        while icount < timeout:
            if not app_excetion_kill_case(self.app_package):
                self.logout(self.my_func_name(),"%s test is failed..."%self.app_package)
                return False
            if "" == textcont:
                app_dev = self.device(text=key_code)
            else:
                app_dev = self.device(textContains=key_code)
            if app_dev.exists:
                app_dev.click()
                icount = 0
                break
            time.sleep(1)
            icount += 1
            kill_adb_uiautomator_block()
        if icount > 0:
            return False
        else:
            return True

if __name__ == '__main__':
    pass
