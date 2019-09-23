#!/usr/bin/python
# -*- coding: UTF-8 -*-

import threading
import time,os,sys

CUR_DIR = os.path.dirname(__file__)

#CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])

def create_relay08_cmd(port_id,stime=0.5,comport='/dev/ttyUSB4',host_passwd='123456'):
    """
    create_relay08_cmd
    auto create relay08 cmd,and run it
    """
    cmd = 'echo '+host_passwd
    cmd = cmd+' | sudo -S python '
    cmd = cmd + os.path.join(CUR_DIR,'./relay08_ctrl_button.py')

    if port_id in range(1,9):
        cmd = cmd + ' -p '+ str(port_id)
    else:
        print '******please input correct port_id which in (1~8)********'
        sys.exit()

    if not stime == 0.5:
        cmd = cmd + ' -t ' + str(stime)

    if not comport == '/dev/ttyUSB4':
        cmd = cmd + ' -c ' + str(comport)
    os.system(cmd)

class control_relay08_port_thread (threading.Thread):
    """
    class control_ignition_thread
    """

    def __init__(self, threadID, name, port_id,stime=0.5,comport='/dev/ttyUSB4',host_passwd='123456'):
        """
        control_ignition_thread __init__
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.port_id = port_id
        self.stime = stime
        self.comport = comport
        self.host_passwd = host_passwd

    def run(self): 
        """
        threading run
        """
        create_relay08_cmd(self.port_id,self.stime,self.comport,self.host_passwd)
        

