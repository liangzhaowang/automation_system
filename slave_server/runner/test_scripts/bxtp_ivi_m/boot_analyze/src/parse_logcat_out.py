#!/usr/bin/env python
import time,os,sys,re,csv
from get_summary import get_summaryext
from get_summary import get_summary


CUR_DIR = os.path.dirname(__file__)
#CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
out_dir = ''
offsetTime = 0

def calcOffset():
    global offsetTime
    global out_dir
    try:
        with open(os.path.join(CUR_DIR,'../'+out_dir+'/report.csv')) as fp:
            lines = fp.readlines()
            lines.reverse()
            for line in lines:
                if "kernel" in line and "start" in line:
                    offset = re.match(r'(?P<offset>^\d+.\d+)',line.split('\t')[0].strip(), re.M|re.I).group('offset')
                    offsetTime = float(offset)
                    break
    except Exception,e:
        print e


def calcTime(time):
    global offsetTime
    return float(time) + offsetTime

def deal_locat_output_result(input_file, output_file = None):
	with open(input_file,'r') as ifile:
		lines = ifile.readlines()
		ifile.close()
		tmp = []
		for line in lines:#range(0,lines.__len__()):
			#print line
			#matchobj = re.match(r'(?P<item>^[a-zA-z_]+)\,[A-Za-z\[\]\.\,_ ]*[0-9]*\,(?P<time>\d+\.\d+),', line, re.I)
			matchobj = re.match(r'(?P<item>^[a-zA-z0-9_]+)', line, re.I)
			#matchobj = re.match(r'(?P<item>^\w+)\,[A-Za-z\[\]\.\,_ ]*[0-9]*.*[A-Za-z\:\.\/0-9]*\,(?P<time>\d+\.\d+),', line, re.I)
			if matchobj and ('name' not in matchobj.group('item')) and matchobj.group('item') != 'driver_igb_avb_inited':
				#print "===================================================="
				#print line
				time_stamp = line.split(',')[-3][0:-4]#matchobj.group('time')[0:-4]
				#print "item == ",matchobj.group('item'),",time ==",time_stamp
				tmpl = matchobj.group('item')+','+time_stamp+'\n'
				tmp.append(tmpl)

	if len(tmp) > 0 and not output_file == None:
		try:
			with open(output_file,'w+') as ofile:
				ofile.writelines(tmp)
		except Exception,e:
			print e
	return tmp

def writeCsv(fileName, tsList,string):

    with open(fileName, 'wb') as csvFile:
        writer = csv.writer(csvFile, 'excel-tab')
        csvFile.write(string)
        sys.stdout.write("write csv ..")
        sys.stdout.flush()
        for entry in tsList:
            sys.stdout.write('..'+"\b")
            sys.stdout.flush()
            writer.writerow(entry)
        print ""

def printTimetable(tsList):
    global out_dir
    lines = regenerateReport(tsList)
    tmp = []
    try:
        with open(os.path.join(CUR_DIR,'../'+out_dir+'/report.csv')) as freport:
            tmp = freport.readlines()
    except Exception,e:
        print e 
        return
    #print tmp[-1].strip().split('\t')
    lines.insert(0,tuple(tmp[-1].strip().split('\t')))
    #print lines
    string = ''
    tmps = []#tmp[0:]
    stimstamp = 0.0
    rtimstamp = 0.0
    for i in range(0,len(tmp)):


        matchobj = re.match(r'^\d+.\d+',tmp[i],re.M|re.I)
        if matchobj:
            tmps.append(tmp[i].strip().split('\t'))
        else:
            string += tmp[i]

    startflag = False

    for entry in lines:
        #print entry
        if entry[3].lstrip().strip() == 'start':
            startflag = True
            stimstamp = float(entry[0])
            #print stimstamp
        if entry[3].strip().strip()=="ready":
            rtimstamp = float(entry[0])
            #print rtimstamp
        if not rtimstamp == 0.0:
            tmp_e = list(entry)
            tmp_e[4]=str(round(rtimstamp-stimstamp,3))
            entry = tuple(tmp_e)
            print '{:10} {:10} {:15} {:7} {:7} {:20}'.format(entry[0], entry[1], entry[2], entry[3], str(round(rtimstamp-stimstamp,3)),entry[5])
        else:
            print '{:10} {:10} {:15} {:7} {:7} {:20}'.format(entry[0], entry[1], entry[2], entry[3], entry[4],entry[5])
        if not entry[3].lstrip().strip() == 'start':
            tmps.append(entry)
    try:
        if False:
            get_summary(tmps)
        else:
            get_summaryext(tmps)
    except Exception,e:
        print ".....There are some errors in the raw data,Please check them,Thanks......"
        print e
    writeCsv(os.path.join(CUR_DIR,'../'+out_dir+'/report.csv'),tmps,string)


def regenerateReport(tsList):
    report = []
    starttime = 0.0
    boot_end_flag = False
    for line in tsList:

        diff=""
        entry_t = line.strip().split(',')[0].split('_')
        entry = line.strip().split(',')
        if 'boot' in entry_t and  'finished' in entry_t:
            mt=' ready '
            boot_end_flag=True
            try:
                diff= str(round(float(entry[1])-float(starttime),3))
            except KeyError:
                diff=""
        else:
            mt=' mark '

        entrys = str(round(calcTime(entry[1]),3)), entry[1] , 'Android', mt, diff, entry[0].  strip()
        report.append(entrys)
        if boot_end_flag:
            break
    return report


def main(outdir):
    global out_dir
    out_dir=outdir
    calcOffset()
    tslist = deal_locat_output_result(os.path.join(CUR_DIR,'../'+out_dir+'/boot_progress.csv'),os.path.join(CUR_DIR,'../'+out_dir+'/result'))
    if len(tslist) > 0:
        printTimetable(tslist)


