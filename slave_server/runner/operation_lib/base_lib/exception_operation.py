import os,time,subprocess
import re
from ctrl_relay08_threading import create_relay08_cmd
from atf import TestLogger
from uiautomator import Device
dev = Device()
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
reboot_cmd = "echo 123456"+"|sudo -S python " + CUR_DIR + "../serial_com.py -p /dev/ttyUSB2 -c n1#"
logger = TestLogger().get_logger("process")

def wait_for_boot():
    for i in range(180):
        time.sleep(1)
        if os.popen('adb shell getprop dev.bootcomplete').read().strip().lstrip() == '1':
            logger.debug('boot complete')
            os.system("adb root")
            time.sleep(3)
            if os.path.exists("./preload.sh"):
                os.system("sh < ./preload.sh")
            return True
    logger.debug('can not boot up on image')
    os.system(reboot_cmd)
    return False


def kill_uiautomator(cmds=""):
    if cmds == '':
        cmdfp = os.popen("ps -aux | grep 'adb' | grep 'com.github.uiautomatorstub.Stub'")
    else:
        cmdfp = os.popen("ps -aux | grep 'adb' | grep 'com.github.uiautomatorstub.Stub' | grep '"+cmds+"'")
    lines = cmdfp.readlines()
    killlist = []
    sh_path = ged_shell_path()
    for item in lines:
        if not sh_path in item and "grep" not in item:
            killlist.append(item.split()[1])
    if len(killlist) > 0:
        for item in killlist:
            os.system("kill -9 "+item)	


def get_o_home_package_activity(activity_name):
    activity_lines = os.popen("adb shell dumpsys activity activities | grep 'act=android.intent.action.MAIN'").readlines()
    if len(activity_lines) > 0:
        if ("cmp="+activity_name) in activity_lines[0]:
            return True
    return False


def unclock_android_o_screen():
    kill_uiautomator()
    if dev(textContains = "Stay fully aware of driving conditions and always obey applicable laws. Directions may be inaccurate, incomplete, dangerous, not suitable, prohibited, or involve crossing administrative areas. Business information may also be inaccurate or incomplete. Data is not real-time, and location accuracy cannot be guaranteed. Do not handle your mobile device or use apps not intended for Android Auto while driving.").exists:
        kill_uiautomator()
    if dev(resourceIdMatches="com.android.systemui:id/user_name$", text="Owner").exists:
        dev(resourceIdMatches="com.android.systemui:id/user_name$", text="Owner").click()

def unclock_screen():
    #add by yuwei20180115
    lockstat = subprocess.Popen('adb shell dumpsys window policy|grep mShowingLockscreen', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    if "mShowingLockscreen=true" in lockstat.communicate()[0].strip():
        p = subprocess.Popen('adb shell getprop ro.build.version.release', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ver=p.communicate()[0].strip()
        if ver=='6.0.1':
            os.system('adb shell input keyevent 82') 
        else:
            unclock_android_o_screen()


def ged_shell_path():
    sh_path = os.popen("which sh").read().strip()
    return sh_path


def check_system_state(com_port='/dev/ttyUSB4', port_id='1'):
    try :
        with open(os.path.join(CUR_DIR, "./../host_passwd")) as pwdfp:
            pass

    except Exception,e:
        logger.debug("Error: adb fail,please waitting for reboot!!!")
        create_relay08_cmd(port_id=3, comport=com_port)
        time.sleep(3)
        os.system(reboot_cmd)
        if wait_for_boot():
            logger.debug("WARNING reboot is ok !!!!!")
    try:
        #modify by yuwei20180115
        line = os.popen('adb shell wm size').read()
        logger.debug(line)
        size_flag = False

        if len(line) > 0:
            sobj = re.search(r'.+\s+(?P<size>\d+[xX]\d+)\w*',line,re.M|re.I)
            if sobj:
                sz = sobj.group('size')
                if len(sz) > 0:
                    ssobj=re.search(r'1920[xX]1080',sz)
                    if not ssobj:
                        size_flag = True
                else:
                    size_flag = True
            else:
                size_flag = True

        else:
            size_flag = True
        if size_flag:
            os.system('adb shell wm size 1920x1080')
            time.sleep(2)
            create_relay08_cmd(port_id=3, comport=com_port)
            time.sleep(3)
            os.system(reboot_cmd)
            if wait_for_boot():
                size_flag = False
                logger.debug("WARNING reboot is ok !!!!!")
        if dev(resourceIdMatches=".+/alertTitle$",text="Low memory").exists:
            create_relay08_cmd(port_id=3, comport=com_port)
            time.sleep(3)
            os.system(reboot_cmd)
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                logger.debug("WARNING reboot is ok !!!!!")
        if dev(resourceIdMatches=".+/message$",textContains="Error").exists:
            create_relay08_cmd(port_id=3, comport=com_port)
            time.sleep(3)
            os.system(reboot_cmd)
            if wait_for_boot():
                logger.debug("WARNING reboot is ok !!!!!")
        if dev(resourceIdMatches=".+/message$",textContains="has stopped").exists:
            create_relay08_cmd(port_id=3, comport=com_port)
            time.sleep(3)
            os.system(reboot_cmd)
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                logger.debug("WARNING reboot is ok !!!!!")
        if dev(resourceIdMatches=".+/alertTitle$",textContains="isn't responding").exists:
            create_relay08_cmd(port_id=3, comport=com_port)
            time.sleep(3)
            os.system(reboot_cmd)
            if wait_for_boot():
                logger.debug("WARNING reboot is ok !!!!!")
        if dev(resourceIdMatches=".+/ok$", text="GOT IT").exists:
            dev(resourceIdMatches=".+/ok$", text="GOT IT").click()
        if dev(resourceIdMatches=".+/alertTitle$", text="Remove user?").exists:
            dev(resourceIdMatches=".+/button2$", text="CANCEL").click()
        if dev.info['currentPackageName'] == "com.android.systemui": #get_o_home_package_activity("com.android.car.settings/.home.HomepageActivity"):
            unclock_android_o_screen()
            if dev(textContains = "Stay fully aware of driving conditions and always obey applicable laws. Directions may be inaccurate, incomplete, dangerous, not suitable, prohibited, or involve crossing administrative areas. Business information may also be inaccurate or incomplete. Data is not real-time, and location accuracy cannot be guaranteed. Do not handle your mobile device or use apps not intended for Android Auto while driving.").exists:
                logger.debug("unclock failed wait for reboot")
                create_relay08_cmd(port_id=3, comport=com_port)
                time.sleep(3)
                os.system(reboot_cmd)
                if wait_for_boot():
                    logger.debug("WARNING reboot is ok !!!!!")

    except Exception, e:
        logger.debug("Error: uiautomator device fail %s,please waitting for reboot!!!"%e)
        create_relay08_cmd(port_id=3, comport=com_port)
        time.sleep(3)
        os.system(reboot_cmd)
        kill_adb_uiautomator_block()
        time.sleep(2)
        if wait_for_boot():
            logger.debug("WARNING reboot is ok !!!!!")


def get_ttyusb_list():
    usblist = os.popen("ls /dev/ttyUSB*").read().split()
    return usblist


def get_define_urlt_usb():
    return "/dev/ttyUSB4"


def kill_adb_uiautomator_block():
    #if len(os.popen("adb devcies").read()) > 30:
       # build_info = os.popen('adb shell getprop |grep ro.build.fingerprint').read()
       # build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)
        #if not build_version and build_version[0] == '10':
         #   unclock_android_o_screen()
    usb_com_port = '/dev/ttyUSB4'
    check_system_state(usb_com_port, '1')


def kill_adb_uiautomator_block_old(cmd=''):
   # build_info = os.popen('adb shell getprop |grep ro.build.fingerprint').read()
   # build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)
   # if not build_version and build_version[0] == '10':
    #    unclock_android_o_screen()
    usb_com_port = '/dev/ttyUSB4'
    kill_uiautomator(cmd)
    check_system_state(usb_com_port,'1')


def wait_for_device_reboot(port_id='1'):
    com_port = '/dev/ttyUSB4'
    os.system("adb reboot")
    time.sleep(5)
    if not wait_for_boot():
        create_relay08_cmd(port_id=int(port_id), comport=com_port)
        wait_for_boot()


def app_exception_kill_case(app_name):
    app_name = str(app_name)
    cur_package = dev.info['currentPackageName']
    flines = os.popen("adb shell ps | grep "+app_name).readlines()
    if app_name == cur_package and len(flines):
        logger.debug(flines)
        return True
    else:
        return False
