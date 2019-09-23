#!/usr/bin/env python
import sys
import time
import getopt
from serial import *


def serial_command(port, cmd, aps='115200'):
    print "===================serial communication======================"
    try:
        ser = Serial(port, aps, 8)
        print ser.portstr
        if port.split('/')[-1] == 'ttyUSB2':
            print 'is ttyusb2'
            ser.write('2')
            ser.write('r')
            time.sleep(0.5)
        if not cmd == '':
            ser.write(cmd)
        ser.close()
    except Exception, e:
        print "serial error: ", e.message
    print "-------------------------------------------------------------"


def main(argv):
    port = ''
    cmd = ''
    aps = ''
    try:
        opts, args = getopt.getopt(argv, "hp:c:a:", ["port=", "command=", "aps="])
    except getopt.GetoptError:
        print 'serial_com.py [-p <port>] [-c <command>][-a <aps>]'
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print 'python serial_com.py [-p <port>] [-c <command>][-a <aps>]'
            sys.exit()
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--command"):
            cmd = arg
        elif opt in ("-a", "--aps"):
            aps = arg
    if port == '':
        print "error:serial port must not be empty!!!"
        sys.exit()
    if (not port.split('/')[-1] == 'ttyUSB2') and cmd == '':
        print "error:if serial port isn't 'ttyUSB2',command must not be empty!!!"
        sys.exit()

    if aps == '':
        serial_command(port, cmd)
    else:
        serial_command(port, cmd, aps)


if __name__ == '__main__':
    main(sys.argv[1:])
