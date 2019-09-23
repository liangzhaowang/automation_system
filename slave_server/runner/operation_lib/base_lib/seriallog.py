#!/usr/bin/env python
import sys
import serial
import threading
import time
import getopt
import datetime
verbose = 0


class serial_thread(threading.Thread):
    """
    class control_ignition_thread
    """
    def __init__(self, threadID, name, ser, log_out, serial_state):
        """
        control_ignition_thread __init__
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.ser = ser
        self.log_out = log_out
        self.serial_state = serial_state

    def run(self): 
        """
        threading run
        """
        read_serial_log(self.ser, self.log_out, self.serial_state)


def read_serial_log(ser, log_out, serial_state):
    flag = "0"
    isAddTimestamp = True
    while True:
        strs = ser.readline()
        if strs:
            with open(log_out, 'a') as fp:
                tmpTimestamp = str(datetime.datetime.now()) if isAddTimestamp else ""
                fp.write(tmpTimestamp + ' ' + strs)
                isAddTimestamp = True if '\n' in strs else False
        try:
            with open(serial_state) as fps:
                flag = fps.readline().strip()
        except Exception, e:
            print e
        if flag == "1":
            print "timeout, stop"
            break


def serial_main(com_port, out_dir, filename='', write=None):
    ser = serial.Serial(com_port, 115200, timeout=0.01)
    print out_dir
    if filename == '':
        log_out = out_dir + "/ttylog.txt"
    else:
        log_out = out_dir + "/" + filename + "_ttylog.txt"
    with open(log_out, 'w+') as fps:
        fps.write("start \n")
    serial_thread_state = out_dir+"/serial_state"
    if write:
        ser.write(write)
    sthread = serial_thread(1, com_port, ser, log_out, serial_thread_state)
    sthread.start()


def vprint(message):
    if verbose:
        print(message)


def main(argv):
    port = ''
    outdir = ''
    write = None
    try:
        opts, args = getopt.getopt(argv, "hp:o:f:t", ["port=", "outdir=", "file="])
    except getopt.GetoptError,e:
        print e
        print 'serial_log.py [-p <port>] [-o <outdir>] [-f <file>]'
        sys.exit(2)
    sd = serial.Serial()
    sd.port = "/dev/ttyS0"
    sd.baudrate = 115200
    sd.bytesize = serial.EIGHTBITS
    sd.parity = serial.PARITY_NONE
    sd.stopbits = serial.STOPBITS_ONE
    sd.xonxoff = False
    sd.rtscts = False
    sd.dsrdtr = False
    # specify a read timeout of 1 second
    sd.timeout = 1
    show_time = 0
    show_systime = 0
    endtime = 0

    for opt, arg in opts:
        if opt == '-h':
            print 'python serial_log.py [-p <port>] [-o <outdir>] [-f <file>]'
            sys.exit()
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-o", "--outdir"):
            outdir = arg
        elif opt in ('-f', "--file"):
            filename = arg
        elif opt in ("-t", "--time"):
            show_time=1
            show_systime=0
        elif opt in ("-T", "--systime"):
            show_time=1
            show_systime=0
        elif opt in ("-l", "--launchtime"):
            print('setting basetime to time of program launch')
        elif opt in ("-e", "--endtime"):
            endstr=arg
            try:
                endtime = time.time() + float(endstr)
            except:
                print("Error: invalid endtime %s specified" % arg)
                sd.close()
                sys.exit(3)
        elif opt in ("-w", "--write"):
            write = arg
    if port == '':
        print "error:serial port must not be empty!!!"
        sys.exit()
    vprint("Opening serial port %s" % sd.port)
    vprint("%d:%d%s%s:xonxoff=%d:rtscts=%d" % (sd.baudrate, sd.bytesize,
            sd.parity, sd.stopbits, sd.xonxoff, sd.rtscts))
    if endtime:
        vprint("Program will end in %s seconds" % endstr)
    if show_time:
        vprint("Printing timing information for each line")
    if show_systime:
        vprint("Printing absolute timing information for each line")
    serial_main(port, outdir, filename, write)


if __name__ == '__main__':
    main(sys.argv[1:])

