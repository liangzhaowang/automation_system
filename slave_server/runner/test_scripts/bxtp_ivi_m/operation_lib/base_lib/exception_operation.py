import os,time,subprocess
import re
from ctrl_relay08_threading import create_relay08_cmd
from ctrl_relay08_threading import control_relay08_port_thread
#from uiautomator import device as dev
from uiautomator import Device
dev = Device()
#CUR_DIR = os.path.dirname(__file__)
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])


def wait_for_boot():
    for i in range(180):
        time.sleep(1)
        if os.popen('adb shell getprop dev.bootcomplete').read().strip().lstrip() == '1':
            print('boot complete')
            os.system("adb root")
            time.sleep(3)
            unclock_screen() #add by yuwei20180115
            if os.path.exists("./preload.sh"):
                os.system("sh < ./preload.sh")
            return True
    print('can not boot up on image')
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
            # print item
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
        dev(resourceIdMatches="com.android.systemui:id/user_name$", text = "Owner").click()
        #os.system('adb shell input keyevent KEYCODE_DPAD_UP')
        #time.sleep(2)
        #os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')
        #time.sleep(2)

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


def check_system_state(com_port='/dev/ttyUSB4',port_id='1'):
    try :
        with open(os.path.join(CUR_DIR,"./../host_passwd")) as pwdfp:
            host_passwd = pwdfp.read()
        # readline = os.popen('adb shell ps | grep launcher').read()
        # #print readline
        # status=readline.split()[-2]
        # #print status
        # status.lower()

        # if len(readline)==0 or 'd' in status or 'z' in status or 't' in status:
        #     os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        #     # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
        #     # time.sleep(3)
        #     # create_relay08_cmd(port_id=int(port_id),comport=com_port)
        #     if wait_for_boot():
        #         print "WARNING reboot is ok !!!!!"
        # else:
        #     print "system state is ok !!!!"
    except Exception,e:
        print "Error: adb fail,please waitting for reboot!!!"
        # os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        create_relay08_cmd(port_id=3,comport=com_port)
        time.sleep(3)
        os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        #create_relay08_cmd(port_id=1,comport=com_port)
        if wait_for_boot():
            print "WARNING reboot is ok !!!!!"
    try:
        #modify by yuwei20180115
        line = os.popen('adb shell wm size').read()
        print line
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
            create_relay08_cmd(port_id=3,comport=com_port)
            time.sleep(3)
            os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                size_flag = False
                print "WARNING reboot is ok !!!!!"

        if dev(resourceIdMatches=".+/alertTitle$",text="Low memory").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            create_relay08_cmd(port_id=3,comport=com_port)
            time.sleep(3)
            os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/message$",textContains="Error").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            create_relay08_cmd(port_id=3,comport=com_port)
            time.sleep(3)
            os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/message$",textContains="has stopped").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            create_relay08_cmd(port_id=3,comport=com_port)
            time.sleep(3)
            os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/alertTitle$",textContains="isn't responding").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " + CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            create_relay08_cmd(port_id=3,comport=com_port)
            time.sleep(3)
            os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=1,comport=com_port)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/ok$",text="GOT IT").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " + CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            dev(resourceIdMatches=".+/ok$",text="GOT IT").click()
        if dev(resourceIdMatches=".+/alertTitle$",text="Remove user?").exists:
            # os.system("echo "+host_passwd+"|sudo -S python " + CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            dev(resourceIdMatches=".+/button2$",text="CANCEL").click()
        if dev.info['currentPackageName'] == "com.android.systemui": #get_o_home_package_activity("com.android.car.settings/.home.HomepageActivity"):
            unclock_android_o_screen()
            if dev(textContains = "Stay fully aware of driving conditions and always obey applicable laws. Directions may be inaccurate, incomplete, dangerous, not suitable, prohibited, or involve crossing administrative areas. Business information may also be inaccurate or incomplete. Data is not real-time, and location accuracy cannot be guaranteed. Do not handle your mobile device or use apps not intended for Android Auto while driving.").exists:
                print "unclock failed wait for reboot"
                create_relay08_cmd(port_id=3,comport=com_port)
                time.sleep(3)
                os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
                # create_relay08_cmd(port_id=1,comport=com_port)
                if wait_for_boot():
                    print "WARNING reboot is ok !!!!!"


    except Exception,e:
        print "Error: uiautomator device fail %s,please waitting for reboot!!!"%e
        # os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        create_relay08_cmd(port_id=3,comport=com_port)
        time.sleep(3)
        os.system("echo "+host_passwd+"|sudo -S python " +CUR_DIR +"../../benchmark/lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        # create_relay08_cmd(port_id=1,comport=com_port)
        if wait_for_boot():
            print "WARNING reboot is ok !!!!!"

def get_ttyusb_list():
    usblist = os.popen("ls /dev/ttyUSB*").read().split()
    #print usblist
    return usblist
    
def get_define_urlt_usb(ctl_port0=5,ctl_port1=6):
    # urlt_list = []
    # urlt_usb = ""
    # urlt_list = get_ttyusb_list()
    #print urlt_list
    # if len(urlt_list) > 1:
    #     for item in urlt_list:
    #         usbthread0 = control_relay08_port_thread(port_id=ctl_port0,stime=2,comport=item)
    #         usbthread0.start()
    #         usbthread1 = control_relay08_port_thread(port_id=ctl_port1,stime=2,comport=item)
    #         usbthread1.start()
    #         time.sleep(1)
    #         urlt_list_tmp = get_ttyusb_list()
            # print "------------------------"
            # print urlt_list_tmp
            # print "------------------------"
            # time.sleep(2)
            # usbthread1._Thread__stop()
            # usbthread0._Thread__stop()
            # if not cmp(urlt_list_tmp,urlt_list) == 0:
            #     urlt_usb = item
            #     break
    # else:
    #     urlt_usb = urlt_list[0]
    #print urlt_usb
    return "/dev/ttyUSB4"#urlt_usb  
    
def kill_adb_uiautomator_block(cmd = '',ctl_port0=5,ctl_port1=6):
    usb_com_port = '/dev/ttyUSB4' #get_define_urlt_usb(ctl_port0,ctl_port1)
    unclock_android_o_screen()
    check_system_state(usb_com_port,'1')

def kill_adb_uiautomator_block_old(cmd = '',ctl_port0=5,ctl_port1=6):
    unclock_android_o_screen()
    usb_com_port = '/dev/ttyUSB4' #get_define_urlt_usb(ctl_port0,ctl_port1)
    kill_uiautomator(cmd)
    check_system_state(usb_com_port,'1')

def wait_for_device_reboot(port_id='1',ctl_port0=5,ctl_port1=6):
    com_port =  '/dev/ttyUSB4' #get_define_urlt_usb(ctl_port0,ctl_port1)
    os.system("adb reboot")
    time.sleep(5)
    if not wait_for_boot():
        create_relay08_cmd(port_id=int(port_id),comport=com_port)
        wait_for_boot()

def app_exception_kill_case(app_name):
    app_name = str(app_name)
    #print app_name
    cur_package = dev.info['currentPackageName']
    flines = os.popen("adb shell ps | grep "+app_name).readlines()
    #print flines
    if app_name == cur_package and len(flines):
        print flines
        return True
    else:
        return False  

