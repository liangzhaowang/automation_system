#!/usr/bin/env python

import serial
import threading,time,os,sys,getopt
CUR_DIR = os.path.abspath(__file__).strip(
    os.path.abspath(__file__).split('/')[-1])
def read_serial_log(ser,log_out,serial_state):
    flag = "0"
    while True:    
        strs = ser.readall()
        if strs:  
            #print strs
            with open(log_out,'a') as fp:
                fp.write(strs)
        try:
           with open(serial_state) as fps:
               flag = fps.readline().strip()
        except Exception,e:
            print e
        if flag == "1":
            print "timeout ,stop"
            break


class serial_thread(threading.Thread):
    """
    class control_ignition_thread
    """

    def __init__(self,threadID,name,ser,log_out,serial_sate):
        """
        control_ignition_thread __init__
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.ser = ser
        self.log_out = log_out
        self.serial_state = serial_sate
    def run(self): 
        """
        threading run
        """
        read_serial_log(self.ser,self.log_out,self.serial_state)

def serial_main(com_port,out_dir):
    ser = serial.Serial(com_port,115200,timeout=0.01)
    print out_dir
    log_out = out_dir+"/ttylog.txt"
    print log_out
    with open(log_out,'w+') as fps:
        fps.write("start \n")
	serial_thread_state = out_dir+"/serial_sate"
    sthread = serial_thread(1,com_port,ser,log_out,serial_thread_state)
    sthread.start()

def main(argv):
	port = ''
	outdir = ''
	try:
		opts, args = getopt.getopt(argv,"hp:o:",["port=","outdir="])
	except getopt.GetoptError:
		print 'serial_log.py [-p <port>] [-o <outdir>]'
		sys.exit(2)
	
	for opt, arg in opts:
		if opt == '-h':
			print 'python serial_log.py [-p <port>] [-o <outdir>]'
			sys.exit()
		elif opt in ("-p","--port"):
			port = arg
		elif opt in ("-o","--outdir"):
			outdir = arg

	if port == '':
		print "error:serial port must not be empty!!!"
		sys.exit()
	serial_main(port,outdir)

if __name__ == '__main__':
	main(sys.argv[1:])
   
