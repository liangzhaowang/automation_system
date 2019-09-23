import os,time
from ctrl_relay08_threading import create_relay08_cmd
from ctrl_relay08_threading import control_relay08_port_thread
from uiautomator import Device

#add by yuwei@20170518

dev =Device()

def wait_for_boot():
    for i in range(180):
        time.sleep(1)
        if os.popen('adb shell getprop dev.bootcomplete').read().strip().lstrip() == '1':
            print('boot complete')
            os.system("adb root")
            time.sleep(2)
            return True
    print('can not boot up on image')
    return False

def ged_shell_path():
    sh_path = os.popen("which sh").read().strip()
    return sh_path

def kill_uiautomator(cmds):
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

def check_bxtp_system_state(com_port='/dev/ttyUSB4',port_id='1',passwd='123456'):
    try :
        readline = os.popen('adb shell ps | grep launcher').read()
        #print readline
        status=readline.split()[-2]
        #print status
        status.lower()

        if len(readline)==0 or 'd' in status or 'z' in status or 't' in status:
            os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
            # time.sleep(3)
            # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        else:
            print "system state is ok !!!!"
    except Exception,e:
        print "Error: adb fail,please waitting for reboot!!!"
        os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
        # time.sleep(3)
        # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
        if wait_for_boot():
            print "WARNING reboot is ok !!!!!"
    try:
        if dev(resourceIdMatches=".+/alertTitle$",text="Low memory").exists:
            os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
            # time.sleep(3)
            # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/message$",textContains="Error").exists:
            os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
            # time.sleep(3)
            # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/message$",textContains="has stopped").exists:
            os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
            # time.sleep(3)
            # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
        if dev(resourceIdMatches=".+/alertTitle$",textContains="isn't responding").exists:
            os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
            # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
            # time.sleep(3)
            # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
            if wait_for_boot():
                print "WARNING reboot is ok !!!!!"
    except Exception,e:
        print "Error: uiautomator device fail,please waitting for reboot!!!"
        os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        # create_relay08_cmd(port_id=int(3),comport=com_port,host_passwd=passwd)
        # time.sleep(3)
        # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
        if wait_for_boot():
            print "WARNING reboot is ok !!!!!"

def get_ttyusb_list():
    usblist = os.popen("ls /dev/ttyUSB*").read().split()
    #print usblist
    return usblist
    
def get_define_urlt_usb(ctl_port0=5,ctl_port1=6,passwd="123456"):
    urlt_list = []
    urlt_usb = ""
    urlt_list = get_ttyusb_list()
    print urlt_list
    if len(urlt_list) > 1:
        for item in urlt_list:
            usbthread0 = control_relay08_port_thread(port_id=ctl_port0,stime=2,comport=item,host_passwd=passwd)
            usbthread0.start()
            usbthread1 = control_relay08_port_thread(port_id=ctl_port1,stime=2,comport=item,host_passwd=passwd)
            usbthread1.start()
            time.sleep(1)
            urlt_list_tmp = get_ttyusb_list()
            # print "------------------------"
            # print urlt_list_tmp
            # print "------------------------"
            time.sleep(2)
            usbthread1._Thread__stop()
            usbthread0._Thread__stop()
            if not cmp(urlt_list_tmp,urlt_list) == 0:
                urlt_usb = item
                break
    else:
        urlt_usb = urlt_list[0]
    print urlt_usb
    return urlt_usb  
    
def kill_adb_uiautomator_block(cmd = '',ctl_port0=5,ctl_port1=6,passwd = '123456'):
    # usb_com_port = "/dev/ttyUSB4"#get_define_urlt_usb(ctl_port0,ctl_port1,passwd)
    # kill_uiautomator(cmd)
    # check_bxtp_system_state(usb_com_port,'1',passwd)
    pass

def wait_for_device_reboot(port_id='1',ctl_port0=5,ctl_port1=6,passwd = '123456'):
    com_port =  get_define_urlt_usb(ctl_port0,ctl_port1,passwd)
    os.system("adb reboot")
    
    # os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
    time.sleep(5)
    if not wait_for_boot():
        os.system("echo 123456|sudo -s python " + "./lib/serial_com.py -p /dev/ttyUSB2 -c n1#")
        # create_relay08_cmd(port_id=int(port_id),comport=com_port,host_passwd=passwd)
        wait_for_boot()
    
#add by yuwei@20170518
