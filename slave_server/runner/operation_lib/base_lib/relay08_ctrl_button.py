#!/usr/bin/python
import serial
import time
import sys
import getopt


__CMDS = {
        "get_software_version": 90,
        "get_port_states": 91,
        "set_port_states": 92,
        "set_all_port_on": 100,
        "set_all_port_off": 110
}
STATUS = ['On', 'Off']


def Write_com(cmd, serial_port):
    try:
        ser = serial.Serial(serial_port, 19200, 8, serial.PARITY_NONE, serial.STOPBITS_TWO)
        ser.write(cmd)
        ser.close()
    except Exception, e:
        print "serial error: ", str(e)


def set_port_on(comport, port_id):
    """
    Enable the port of IOcard
    :type of port_id is integer
    :value of port_id the number of port,value range:1-8
    """
    cmd = list()
    if int(port_id) in range(1, 9):
        cmd.append(chr(__CMDS["set_all_port_on"] + int(port_id)))
        cmd_str = "".join(list(cmd))
        Write_com(cmd_str, comport)
    else:
        print 'Turn On %d :the value of port should be in range 0~8' % int(port_id)


def set_port_off(comport, port_id):
    """
    Disable the port of IOcard8
    :type of port_id is integer
    :value of port_id the number of port,value range:1-8
    """
    cmd = list()
    if int(port_id) in range(1, 9):
        cmd.append(chr(__CMDS["set_all_port_off"] + int(port_id)))
        cmd_str = "".join(list(cmd))
        Write_com(cmd_str, comport)
    else:
        print 'the value of port should be in range 0~8'


def ctrl_relay08_imitate_button(port_id, stime, comport):
    """
    ctr_relay08_imitate_button
    time default is 0.5s
    comport default is '/dev/ttyUSB4'
    if you want change them please call ctr_relay08_imitate_button(port_id,time,comport)
    """
    set_port_on(comport, port_id)
    time.sleep(stime)
    set_port_off(comport, port_id)


def main(argv):
    port_id = 0
    stime = 0.5
    comport = '/dev/ttyUSB4'
    try:
        opts, args = getopt.getopt(argv,"hp:t:c:")
    except getopt.GetoptError:
        print sys.argv[0],' [[-p]<port_id>] [[-t]<stime>] [[-c]<comport>]'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print '============================================================'
            print sys.argv[0],'[[-p]<port_id>] [[-t]<stime>] [[-c]<comport>]'
            print '-p : port_id :relay08 board port_id for 8 ports id,\n\tThe id number is printed on the board'
            print '-t : stime   :to set the time how long between set \n\tport on and set port off,to realy long press'
            print '-c : comport :to set comport,if you want change the \dev\\ttyUSB*'
            print '============================================================'
            sys.exit()
        elif opt == '-p':
            port_id = int(arg)
        elif opt == '-t':
            stime = float(arg)
        elif opt == '-c':
            comport = arg

    if port_id == 0:
        print 'please set port_id range 1~8'
        sys.exit()
    else:
        ctrl_relay08_imitate_button(port_id, stime, comport)


if __name__ == '__main__':
    main(sys.argv[1:])
