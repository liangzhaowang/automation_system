#!/usr/bin/python

import sys, os.path, getopt
import subprocess
import csv
import re
import parse_logcat_out
from get_summary import get_summaryext
from get_summary import get_summary
CUR_DIR = os.path.dirname(__file__)
#CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
out_dir=''
# all times in us
#a, b ,c = [0,0,0]#open(os.path.join(CUR_DIR,'../'+out_dir+'/offset.txt')).readline().split(" ")
iocTimeOffset = 0 # offset between ioc time and kernel first log time
kernelTimekeeping = 0 # time for kernel first log to kernel timekeeping ready
iocStartupTime = 0 # ioc time when the startup begins aka ignition-on time
iocOffsetReceived = True;
offsetTime = 0; # The offset between monotonic time and the intended 0 point.
offsetAblToMonotonic = 0;

# time used for abl offset calculation
iocAblAckTime = 0; # ioc time when the abl-ack was received


testMode = False; # in testmode external programs are replaced with hardcoded output-files. Does only work in the test directory.

get_summary_is_open = True # if you want print the Pre-CSE to CSE column in summary information please take it False , the default value is True
# one entry is <monotonicTimeUs> <S|R|M> <name> <comment> 
def parseEntry(line):
    line = line.rstrip('\n')
    line = line.rstrip('\r')
    items = line.split(' ')
    
    if len(items) > 3 and items[2].isalnum():
       if  items[3].isdigit(): # as long as systemd_timestamp is used, there are two numbers. The second one is used.
           entry = items[3], items[1], items[4], ' '.join(items[5:])
           return entry
       else: 
           if items[2].isdigit():
              entry = items[2], items[1], items[3], ' '.join(items[4:])
              return entry

def calcOffset():
    global iocOffsetReceived;
    global offsetTime;
    if (iocOffsetReceived):
        offsetTime = iocTimeOffset;
    

def calcTime(time):
    global offsetTime;
    return int(time) + offsetTime


# parsing of dmesg:


def readDmesgTime(line):
    nanoseconds = 0
    regex = re.compile("^\[(?P<time> +\d+\.\d+)\](?P<line>.*)$")
    match = regex.match(line)
    if match:
        try:
            nanoseconds = int(match.groupdict().get('time', '').split('.')[0]) * 1000000 + int(match.groupdict().get('time', '').split('.')[1])
        except IndexError:
            pass
    if nanoseconds == 0:
        return nanoseconds
    else:
        return nanoseconds + kernelTimekeeping

# add by yuwei@20161202 read input config file
def readconfig(inputfile):
    configList=[]
    for line in open(inputfile):
        line = line.strip('\n')
        if line.find("Input"):
                configList.append(line)
    return configList

def readDmesgext(inputfile):
    #print 'into readDmesgext()'
    entryList=[]
    global out_dir
    configList = readconfig(inputfile)
#    print configList
    #llen = len(configList)
    #print "llen is ",str(llen)
    for logline in open(os.path.join(CUR_DIR,'../'+out_dir+'/dmesg.txt')):
        logline = logline.strip('\n').strip('\r').strip(' ')
        text = logline.lstrip('[].1234567890 ')
        for line in configList:
                items = line.split('|')
                item = items[0].strip(' ').strip('\t')
                if text.startswith(item):
                        time = readDmesgTime(logline)
                        if len(items) < 4:
                            entry = time,items[1].strip(' ').strip('\t'),items[2].strip(' ').strip('\t') , items[0].strip(' ').strip('\t')
                        else:
                            entry = time,items[1].strip(' ').strip('\t'),items[2].strip(' ').strip('\t') , items[3].strip()
                        entryList.append(entry)
                        break 
    #print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    #print entryList
    #print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    return entryList
# add by yuwei@20161202 read input config file

def readDmesg():
    global out_dir
    #print "into readDmesg()"
    entryList = []
    for logline in open(os.path.join(CUR_DIR,'../'+out_dir+'/dmesg.txt')):
        logline = logline.strip('\n').strip('\r').strip(' ')
        text = logline.lstrip('[].1234567890 ')

        if text.startswith("init: init started!"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'kernel', 'Root mounted'
            entryList.append(entry)

        elif text.startswith("Waiting for "):
            time = readDmesgTime(logline)
            entry = time, 'S', 'kernel', 'Wait for root filesystem'
            entryList.append(entry)

        elif text.startswith("calling  i915_init"):
            time = readDmesgTime(logline)
            entry = time, 'S', 'i915', 'i915 init start'
            entryList.append(entry)

        elif text.startswith("initcall i915_init"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'i915', 'i915 init end'
            entryList.append(entry)

        elif text.startswith("calling  intel_ipu4_init"):
            time = readDmesgTime(logline)
            entry = time, 'S', 'ipu', 'ipu4 init start'
            entryList.append(entry)

        elif text.startswith("initcall intel_ipu4_init"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'ipu', 'ipu4 init end'
            entryList.append(entry)

        elif text.startswith("intel-ipu4-psys intel-ipu4-psys0: pkg_dir entry count"):
            time = readDmesgTime(logline)
            entry = time, 'S', 'psys', 'psys init start'
            entryList.append(entry)

        elif text.startswith("intel-ipu4-psys intel-ipu4-psys0: psys probe minor"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'psys', 'psys init end'
            entryList.append(entry)

        elif text.startswith("calling  isys_driver_init"):
            time = readDmesgTime(logline)
            entry = time, 'S', 'isys', 'isys init start'
            entryList.append(entry)

        elif text.startswith("initcall isys_driver_init"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'isys', 'isys init end'
            entryList.append(entry)

        elif text.startswith("intel-ipu4 0000:00:03.0: Sending BOOT_LOAD to CSE"):
            time = readDmesgTime(logline)
            entry = time, 'M', 'ipu', 'request ipu bl fw'
            entryList.append(entry)

        elif text.startswith("intel-ipu4 0000:00:03.0: Sending AUTHENTICATE_RUN to CSE"):
            time = readDmesgTime(logline)
            entry = time, 'M', 'ipu', 'request ipu fw'
            entryList.append(entry)

        elif text.startswith("init: Starting service 'rvc'..."):
            time = readDmesgTime(logline)
            entry = time, 'S', 'EV', 'EV Start'
            entryList.append(entry)

        elif text.startswith("Reversing Camera"):
            time = readDmesgTime(logline)
            entry = time, 'R', 'EV', 'First frame from camera'
            entryList.append(entry)
    #print "==================================================="
    #print entryList
    #print "==================================================="
    return entryList
    

# parsing of abl_dumper output:

def createAblTimestamp(items, tstype, component, description):
    time = int(float(items[1]) * 1000) + iocStartupTime
    entry = time, tstype, component, description
    return entry
	

def readAblDump():
    global iocAblAckTime;
    global iocStartupTime;
    global offsetAblToMonotonic;
    global out_dir
    entryList = []
    ablEntryList = []
    inTimestampTable = False
    entry = 0, 'M', 'Pre-CSE', '0'
    ablEntryList.append(entry)
    entry = iocStartupTime, 'S', 'CSE', 'tsc 0'
    ablEntryList.append(entry)
    ablAckTime = 0

    for logline in open(os.path.join(CUR_DIR,'../'+out_dir+'/abl_dump.txt')):
        logline = logline.strip('\n').strip('\r').strip(' ')
        if inTimestampTable:
            items = logline.split()
            if len(items) == 0:
                continue
            if items[0] == '16': # search timestamp matching ABL-Ack from IOC. 16 is 8ms off (too early), but currently the best
                ablAckTime = int(float(items[1]) * 1000)
            if items[0] == '1': # stage-0 starting
                ablEntryList.append(createAblTimestamp(items, 'R', 'CSE', ''))
                ablEntryList.append(createAblTimestamp(items, 'S', 'ABL', 'stage-0 start'))
            elif items[0] == '7': # stage-0 done
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'stage-0 done'))
            elif items[0] == '10':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'CSE ready to send IBBM'))
            elif items[0] == '15':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'stage-1 loaded'))
            elif items[0] == '16':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'pre-MRC hw init done'))
            elif items[0] == '17':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'received ABL config over IPC'))
            elif items[0] == '18':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'probed CPU, PCB, start MRC'))
            elif items[0] == '19':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'MRC parameters loaded'))
            elif items[0] == '20':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'RMT start'))
            elif items[0] == '21':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'send DID'))
            elif items[0] == '22':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'set_punit_reset'))
            elif items[0] == '23':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'stage-1 done'))
            elif items[0] == '24':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'stage-2 start'))
            elif items[0] == '25':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'PCIe Root Port init start'))
            elif items[0] == '28':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'PCIe init done'))
            elif items[0] == '35':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'Image load done'))
            elif items[0] == '36':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'Image CRC done'))
            elif items[0] == '47':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'eMMC/SD init done'))
            elif items[0] == '50':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'image DL start'))
            elif items[0] == '51':
                ablEntryList.append(createAblTimestamp(items, 'M', 'ABL', 'image DL end'))
            elif items[0] == '55': # oshandoff
                ablEntryList.append(createAblTimestamp(items, 'R', 'ABL', 'jump to image'))

        elif logline.startswith('Index'):
            inTimestampTable = True
    iocAblAckTime = ablAckTime
    #if ablAckTime == 0 or iocAblAckTime == 0:
    #    print "Cannot create offset to ABL clock"
    #    return entryList # return empty list if offset cannot be calculated
                
    offsetAblToMonotonic = iocTimeOffset - (iocAblAckTime - ablAckTime)
    for ablEntry in ablEntryList:
        entry = (ablEntry[0] - offsetAblToMonotonic,) + tuple(ablEntry[1:]) 
        entryList.append(entry)
    return entryList
    
    
# parsing of journal
# (does not have a testmode yet)

def readJournal():
    entryList = []
    cmd = subprocess.Popen('/bin/journalctl -b --no-pager -o export', shell=True, stdout=subprocess.PIPE)
    for logline in cmd.stdout:
        if logline.startswith("MESSAGE=BTM "):
            line = logline[8:].lstrip()
            entryList.append(parseEntry(line))
    return entryList
        
        
# end of parsers
        
        
# create dictionary of the starttimes    
def createStartDict(timeStamps):
    startList = []
    for entry in timeStamps:
       if entry[1] == 'S':
           startList.append((entry[2] , entry[0]))
    return dict(startList)
    
    
def printTimestamp(ts): # ts is in microseconds
    negative = False
    if ts < 0:
        negative = True
        ts = ts * -1
    seconds, milliseconds = divmod(ts / 1000, 1000)
    if negative:
        return "-%i.%03i" % (seconds, milliseconds)
    else:
        return "%i.%03i" % (seconds, milliseconds)
        

def printTimetable(tsList):
    for entry in generateReport(tsList):
        print '{:10} {:10} {:15} {:7} {:7} {:20}'.format(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5])
    
    
def generateReport(tsList):
    startDict = createStartDict(tsList)
    report = []
    for entry in tsList:
        diff=""
        if entry[1] == 'S':
            mt=' start '
        if entry[1] == 'M':
            mt=' mark '
        if entry[1] == 'R':
            mt=' ready '
            try:
                diff=printTimestamp(int(entry[0]) - int(startDict[entry[2]]))
            except KeyError:
                diff=""
        entry = printTimestamp(calcTime(entry[0])), printTimestamp(int(entry[0])) , entry[2], mt, diff, entry[3].strip()
        report.append(entry)
    return report
    
    
def createOffsetMessage():
    global iocPmicOkReceived;
    global iocOffsetReceived;
    global offsetTime;
    global iocStartupTime;
    global iocPmicOkTime;
    global offsetAblToMonotonic;
    firstColumn = "monotonic"
    secondColumn = "monotonic"
    
    if (iocOffsetReceived):
        msg = "First column:  starting from Ignition on.\n"
        msg = msg + "Second column: monotonic time.\n"
        firstColumn = "ign-on"

    else:
        msg = "Both time columns are in monotonic time\n"
        
    if (iocOffsetReceived):
        msg = msg + "Time from IOC power-on until ign-on: "+printTimestamp(iocStartupTime)+"\n";
        msg = msg + "Time from ign-on until monotonic time starts: " + printTimestamp(offsetTime) + "\n"
        if (offsetAblToMonotonic != 0):
       	    msg = msg + "Time from ign-on until TSC starts: " + printTimestamp(offsetTime-offsetAblToMonotonic) + " ( " + printTimestamp(offsetAblToMonotonic) + " before monotonic)\n"
#       	    msg = msg + "Time from TSC-0 until monotonic time starts: " + printTimestamp(offsetAblToMonotonic) + "\n"
        msg = msg + "\n"
    msg = msg + firstColumn + " | " + secondColumn + "\n"
    return msg;
    
def add_android_start_time_stamp(entryList):
	start_time=()
	for line in entryList:
		android_start=list(line)
		#print android_start[2]+'-----'+android_start[3]
		if(android_start[2].lstrip().strip()=="kernel" and android_start[3].lstrip().strip()=="ready"):
			android_start[2]="Android"
			android_start[3]=" start"
			android_start[4]=android_start[4].strip("0123456789. ")
			android_start[5]="Android_start"
			#print android_start
			#print '{:10} {:10} {:15} {:7} {:7} {:20}'.format(android_start[0], android_start[1], android_start[2], android_start[3], android_start[4], android_start[5])
 			start_time=tuple(android_start)
			break
	if len(start_time) > 0:
		entryList.append(start_time)
	return entryList

def get_rvc_read_timestamp():
    fmesg = open(os.path.join(CUR_DIR,'../'+out_dir+'/dmesg.txt'),'r')
    lines = fmesg.readlines()
    timestamp ="0.000000"
    for line in lines:
        if "staticSplashShowTimeMs" in line:
            sobj= re.search(r'staticSplashShowTimeMs=(?P<time>\d+\.\d+)',line,re.I|re.M)
            if sobj:
                timestamp = sobj.group('time')
                if timestamp == "0.000000":
                    sobjx = re.search(r'firstCameraFrame=(?P<time>\d+\.\d+)',line,re.I|re.M)
                    if sobjx:
                        timestamp = sobjx.group('time')
                        break
                else:
                    break
    #print "-----"+timestamp
    timestamp = str(round(float(timestamp)/1000,3))
    #print timestamp
    return timestamp

def add_rvc_ready_time_stamp(entryList):
    rvc_time=()
    for line in entryList:
        rvc_start=list(line)
        #print rvc_start[2]+'-----'+rvc_start[3]
        if(rvc_start[2].lstrip().strip()=="RVC" and rvc_start[3].lstrip().strip()=="start"):
            timestp = get_rvc_read_timestamp()
            if timestp == "0.000000":
                print("find staticSplashShowTimeMs and firstCameraFrame error")
                sys.exit()
            rvc_start[0] = str(round(float(rvc_start[0])+float(timestp),3))
            rvc_start[1] = str(round(float(rvc_start[1])+float(timestp),3))
            rvc_start[3]=" ready"
            rvc_start[4]= timestp
            rvc_start[5]="rvc ready"
            #print rvc_start
            print '{:10} {:10} {:15} {:7} {:7} {:20}'.format(rvc_start[0], rvc_start[1], rvc_start[2], rvc_start[3], rvc_start[4], rvc_start[5])
            rvc_time=tuple(rvc_start)
            break
    if len(rvc_time) > 0:
        entryList.append(rvc_time)
    return entryList

    
def writeCsv(fileName, tsList):
    rep = generateReport(tsList)
    rep = add_rvc_ready_time_stamp(rep)
    #print "rep1==",rep
    rep = add_android_start_time_stamp(rep)
    #print "rep2==",rep
    with open(fileName, 'wb') as csvFile:
        writer = csv.writer(csvFile, 'excel-tab')
        csvFile.write(createOffsetMessage())
        for entry in rep:
            writer.writerow(entry)


def printHelp():
    print sys.argv[0],
    print " -h (help) -l <logfile> -j (parse systemd-journal) -c <csv-file> -d (parse dmesg) -a (call abl_dumper)"


def entrySortKey(entry):
    return int(entry[0])
#add by yuwei@20161206
def outreadDmesg(argv):
    global iocPmicOkReceived;
    global iocOffsetReceived;
    global offsetTime;
    global iocTimeOffset
    global kernelTimekeeping
    global iocStartupTime;
    global iocPmicOkTime;
    global offsetAblToMonotonic;
    inputfile = ''
    outputfile = ''
    global out_dir
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'run.py -i <inputfile> [-o <outputfile>]'
        sys.exit(2)
    #print opts
    #print "++++++++++++++++++++++++++"
    #print args
    for opt, arg in opts:
        if opt in ("-i", "--ifile"):
            inputfile = arg
            #print 'input.txt is', inputfile
        elif opt in ("-o", "--ofile"):
            outputfile = arg
            out_dir = outputfile
            #print 'output.txt is ', outputfile
    # print "=================================================="

    a, b ,c = open(os.path.join(CUR_DIR,'../'+out_dir+'/offset.txt')).readline().split(" ")
    iocTimeOffset = int(a); # offset between ioc time and kernel first log time
    kernelTimekeeping = int(b) # time for kernel first log to kernel timekeeping ready
    iocStartupTime = int(c); # ioc time when the startup begins aka ignition-on time
    if inputfile != '':
        return readDmesgext(inputfile)
    else:
        return readDmesg()

#####################################
def main(argv):
    global out_dir
    print 'Boot Time Measurements'
    print "===================================================="
    entryList = []
    #entry = 0, 'S', 'kernel', 'monotonic 0'
    #entryList.apst[i+1][4]pend(entry)
    #entry = kernelTimekeeping, 'M', 'kernel', 'TSC Ready'
    #entryList.append(entry)
     
    #csvFile = os.path.join(CUR_DIR,'../'+out_dir+'/report.csv')
    filterEntry = ""
    entryList = entryList+ outreadDmesg(argv) #readDmesg() modify by yuwei@20161206
    csvFile = os.path.join(CUR_DIR,'../'+out_dir+'/report.csv')
    #print entryList
    calcOffset()


    entryList = entryList + readAblDump()


    if filterEntry != "":
        if offsetTime == 0:
            print "no offset found."
            sys.exit()
        print "Timestamps for messages starting with: " + filterEntry
        for entry in entryList:
            if entry[3].startswith(filterEntry):
                print printTimestamp(calcTime(entry[0]))
        sys.exit()

    entryList.sort(key=entrySortKey)
    print createOffsetMessage();
    printTimetable(entryList);
#    if get_summary_is_open:
#        get_summary(generateReport(entryList))
#    else:
#        get_summaryext(generateReport(entryList))
    if len(csvFile) != 0:
        #print "writing file:",
        #print csvFile
        writeCsv(csvFile, entryList);
        parse_logcat_out.main(out_dir) #add by yuwei@20170103
          
if __name__ == "__main__":
    main(sys.argv[1:])
    
    
