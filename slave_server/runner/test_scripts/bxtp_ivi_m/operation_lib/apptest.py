#!/usr/bin/python

import os,re,sys
import time
import inspect
import subprocess

#from uiautomator import device as app_device
from uiautomator import Device
from base_lib.exception_operation import kill_adb_uiautomator_block
from base_lib.exception_operation import kill_adb_uiautomator_block_old
from base_lib.exception_operation import kill_uiautomator
from base_lib.exception_operation import app_exception_kill_case
from base_lib.makelog import makelog
from base_lib.makelog import log_info
from base_lib.UI_interface_operation import ui_operation
from base_lib.UI_interface_operation import Swiping
app_device = Device()
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])

class apptest(object):
    """docstring for apptest"""

    def __init__(self,args,app=[],app_package = "",app_activity = "",url="",case_name=""):
        super(apptest, self).__init__()

        self.device = app_device
        self.output_path = args[0]
        self.current_loop = args[1]
        if len(app) > 0:
            self.app = app
            self.app_name = str(self.app[0]).lower()
            self.case_name = self.app_name
            self.app_path = self.app[1]

        self.app_package = app_package
        self.app_activity = app_activity
        if not case_name == "":
            self.case_name = case_name
            self.app_name = self.case_name
        if self.app_package == "":
            self.app_package = self.get_package_name()
        if self.app_activity == "":
            self.app_activity = self.get_activity_name()
        self.isinstalled = False
        self.ui_operation = ui_operation(self.output_path,self.current_loop,self.app_package,self.app_name)
        self.swiping = Swiping(self.device)
        self.log = log_info.logger
        self.url = url


    
    def get_output(self, args):
        if args.index('-o') < len(args) - 1:
            return args[args.index('-o') + 1]
        else:
            return None

    #get function name
    def my_func_name(self):
        return inspect.stack()[1][3]
    
    #logout
    def logout(self,function_name,log_message):
        self.log.info( ">>>%s:"%function_name+log_message)

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


    def app_install(self):
        installed_app_package = self.get_installed_app_package()
        if installed_app_package == "":
            self.logout(self.my_func_name(),"Install %s"%self.app_name)
            try:
                os.system("adb install %s"%(CUR_DIR+"/../"+self.app_path))
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
        installed_app_package = os.popen("adb shell pm list package |grep -i %s |awk -F ':' '{print$2}'"%(self.app_package)).read().strip()
        return installed_app_package

    def enable_3rd_market_app_install(self):
        os.system('adb shell settings put secure install_non_market_apps 1')
        time.sleep(3)

    def get_package_name(self):
        p = re.compile(r"package: name=\'([\w+.]*)\'")
        s = os.popen(CUR_DIR.strip()+"/../src/aapt dump badging  %s | grep -i package"%(CUR_DIR+"/../"+self.app_path)).read()
        package_name = re.findall(p,s)[0]
        return ''.join(package_name)

    def get_activity_name(self):
        p = re.compile(r"launchable-activity: name=\'([\w+.]*)\'")
        s = os.popen(CUR_DIR.strip()+"/../src/aapt dump badging  %s | grep -i activity"%(CUR_DIR+"/../"+self.app_path)).read()
        activity_name = re.findall(p,s)[0]
        return ''.join(activity_name)
    
    def get_app_version(self):
        p = re.compile(r"versionName=\'([\d+.]*)\'")
        s = os.popen(CUR_DIR.strip()+"/../src/aapt dump badging  %s | grep -i package"%(CUR_DIR+"/../"+self.app_path)).read()
        version_name = re.findall(p,s)
        return ''.join(version_name)

    def check_system_app_package(self,package_name_key):
        get_packes=os.popen("adb shell pm list packages | grep "+package_name_key).readlines()
        if len(get_packes) > 0:
            for item in get_packes:
                package_name = item.lstrip("package").strip().lstrip(":")
                os.system("adb uninstall %s"%package_name)
                self.logout(self.my_func_name(), "%s is uninstalled"%package_name)
        else:
            self.logout(self.my_func_name(), "DUT have no packages")

    def launch_app(self):
        self.logout(self.my_func_name(), "adb shell am start -n %s/%s"%(self.app_package, self.app_activity))
        if self.get_installed_app_package() == "":
            self.isinstalled = False
            self.app_install()
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        else:
            self.isinstalled = True
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        time.sleep(2)
        os.system("adb logcat -c")
        self.clear_app_data()
        time.sleep(1)
        os.system("adb shell am start -n %s/%s"%(self.app_package, self.app_activity))
    
    def launch_app_ext(self):
        self.logout(self.my_func_name(), "adb shell am start -n %s/%s"%(self.app_package, self.app_activity))
        if self.get_installed_app_package() == "":
            self.isinstalled = False
            self.app_install()
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        else:
            self.isinstalled = True
            self.logout(self.my_func_name(), "Launch %s"%self.app_name)
        time.sleep(2)
        os.system("adb logcat -c")
        self.clear_app_data_ext()
        time.sleep(1)
        os.system("adb shell am start -n %s/%s"%(self.app_package, self.app_activity))

    def clear_app_data(self,app_nam=''):
        self.logout(self.my_func_name(),'...')
        os.system('adb shell pm clear %s'%self.app_package)
        if not app_nam == "":
            self.logout(self.my_func_name(),"... %s"%app_nam)
            os.system('adb shell pm clear %s'%(app_nam))
        self.ui_operation.clear_recent()

	def clear_app_data_ext(self,app_nam=''):
		self.logout(self.my_func_name(),'...')
		os.system('adb shell pm clear %s'%self.app_package)
		if not app_nam == "":
			self.logout(self.my_func_name(),"... %s"%app_nam)
			os.system('adb shell pm clear %s'%(app_nam))
	
    def kill_app(self,app_nam=''):
        self.logout(self.my_func_name(),"Force stop %s"%self.app_name)
        os.system('adb shell am force-stop %s'%(self.app_package))
        if not app_nam == "":
            self.logout(self.my_func_name(),"Force stop %s"%app_nam)
            os.system('adb shell am force-stop %s'%(app_nam))

    def launch_chrome_with_page(self,text=""):
        cmd = "adb shell am start -t text/html -n "+self.app_activity+" -d "+self.url
        os.system(cmd)
        time.sleep(5)
        if len(text)>0:
            self.ui_operation.click_ui_button_by_resourceIdMatches(text)
            time.sleep(1)
        if app_exception_kill_case(self.app_package):
            return True
        return False

    def skip_chrome_wizard(self):
        os.system("adb shell pm clear %s"%self.app_package)
        os.system("adb shell am start -n %s"%self.app_activity)
        time.sleep(2)
        self.ui_operation.wait_for_open_spacial_function("Welcome to Chrome")
        self.ui_operation.click_ui_button_by_resourceIdMatches('terms_accept')
        self.ui_operation.wait_for_open_spacial_function("Sign in to Chrome")
        self.ui_operation.click_ui_button_by_resourceIdMatches('negative_button')
        self.ui_operation.wait_for_open_spacial_function(resourceIdMatches_txt="search_box_text")
        self.kill_app()
	
    def run_google_set(self):
        self.logout(self.my_func_name(),"run_google_set")
        time.sleep(2)
        try:
            if self.ui_operation.click_ui_button_by_resourceIdMatches("auto_backup_switch"):
                self.ui_operation.click_by_event("BACK")
            # kill_adb_uiautomator_block()
            time.sleep(3)
            if self.device(text="Keep backup off?").exists:
                self.ui_operation.click_ui_button_by_resourceIdMatches("button2")
                # kill_adb_uiautomator_block()
        except Exception,e:
            self.logout(self.my_func_name(),"run google set is error: %s"%e)
            return False

