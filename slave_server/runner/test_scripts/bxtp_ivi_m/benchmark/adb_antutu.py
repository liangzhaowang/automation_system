import os
import time
import sys
#import adb
sys.path.append('./lib')
sys.path.append('lib')
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lib'))
import adb
# for debug, comment it
from atf import *

CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
out_dir=time.strftime('%Y%m%d_%H%M%S')
testTimes = 3
timeWaitStep = 2
timeWaitActivity = 20
timeWaitTest = 255
result = []
result_str = ''
apk_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'AnTuTu_v5.6.apk')
tr = TestResult(__file__)

class Coordinate(object):
	def __init__(self,device,antutuver,timeWaitTest,
	 startx,starty,testx,testy,
	 killappax,killappay,killappbx):
		self.device = device
		self.antutuver = antutuver
		self.timeWaitTest = timeWaitTest
		self.startx = startx
		self.starty = starty
		self.testx = testx
		self.testy = testy
		self.killappax = killappax
		self.killappay = killappay
		self.killappbx = killappbx

chtAntutu_5_6_coord = Coordinate(
	device='cherryTrail',
	antutuver='5.6',
	timeWaitTest=255,
	startx=70,
	starty=337,
	testx=400,
	testy=295,
	killappax=180,
	killappay=720,
	killappbx=570,
)
chtAntutu_6_33_coord = Coordinate(
	device='cherryTrail',
	antutuver='6.3.3',
	timeWaitTest=650,
	startx=70,
	starty=337,
	testx=400,
	testy=295,
	killappax=180,
	killappay=720,
	killappbx=570,
)

bxtpAntutu_5_6_coord = Coordinate(
	device='broxtonp',
	antutuver='5.6',
	timeWaitTest=250,
	startx=0,
	starty=0,
	testx=964.7,
	testy=350,
	killappax=956.2,
	killappay=970,
	killappbx=1695.2,
)
coord = bxtpAntutu_5_6_coord

result = []

def dpad_center():
	os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')

def dpad_up():
	os.system('adb shell input keyevent KEYCODE_DPAD_UP')

def dpad_down():
	os.system('adb shell input keyevent KEYCODE_DPAD_DOWN')



def killapp():
	os.system('adb shell input keyevent KEYCODE_APP_SWITCH')
	dpad_down()
	dpad_down()
	os.system('adb shell input keyevent DEL')
	adbPressHome()

def prepareAPK():
	os.system('adb uninstall com.antutu.ABenchMark')
	os.system('adb uninstall com.antutu.benchmark.bench64')

	# for bxtp
	enable_x = 1210
	enable_y = 666#652 716
	enable_64_install_x = 1155
	enable_64_install_y = 950 #915#1029
	enable_64_install_done_x = 750 #754 #750
	enable_64_install_done_y = 920#913#1030

	# os.system('adb install ' + os.path.join(os.path.dirname(__file__), 'AnTuTu_v5.6.apk'))
	os.system('adb install '+apk_path)
	enable_3rd_market_app_install()
	start_antutu()
	adbClick(enable_x,enable_y)
	adbClick(enable_64_install_x,enable_64_install_y)
	time.sleep(4)
	adbClick(enable_64_install_done_x,enable_64_install_done_y)
	adbPressHome()


def adbUnlockScreen():
	os.system('adb shell input keyevent 82')
	adbPressHome()


def enable_3rd_market_app_install():
	os.system('adb shell settings put secure install_non_market_apps 1')
	time.sleep(timeWaitStep)

def install_64bit_antutu():
	os.system('adb install bench64.apk')

def start_antutu():
	clear_data_antutu()
	os.system('adb logcat -c')
	# name = 'com.antutu.ABenchMark'
	# os.system('adb shell monkey -p ' + name + ' -c android.intent.category.LAUNCHER 1 > /dev/null')
	os.system('adb shell am start -n com.antutu.ABenchMark/.ABenchMarkStart')
	time.sleep(timeWaitActivity)

def collect_result():
	os.system('adb root')
	time.sleep(2)
	allresult = 'adb logcat -d | grep -i antutubenchmarkscore >'+os.path.join(CUR_DIR,out_dir, 'antutu.txt')
	# print allresult
	os.popen(allresult)
	result = os.popen('adb logcat -d | grep -i antutubenchmarkscore').readlines()
	print 'antutu result array is :'

	if(len(result)>2):
		for line in result:
			resultList = line.strip().split()
			tr.sub_score(resultList[-3], resultList[-1])
			print resultList
		try:
			with open(os.path.join(CUR_DIR,out_dir,'result.txt'),'a') as f:
				f.write(str(resultList))
				f.write('\n')
				f.close()
		except Exception, e:
			print "con't open result.txt"
			print e
		lastline = result[-1].strip().split()
		print lastline
		print 'The total socre is: %s'% lastline[-1]
		result_str ='The total socre is: %s \n'% lastline[-1]
		return lastline[-1]
	else:
		return 'error, no result found'
	# tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/antutu.txt'))

def adbPressHome():
	os.system('adb shell input keyevent 3')
	os.system('adb shell input keyevent 4')
	time.sleep(timeWaitStep)

def adbPressRecent():
	os.system('adb shell input keyevent KEYCODE_APP_SWITCH')
	time.sleep(timeWaitStep)

def clear_data_antutu():
	os.system('adb shell pm clear com.antutu.ABenchMark')

def adbClick(x, y):
	os.system('adb shell input tap %d %d' % (x, y))
	time.sleep(timeWaitStep)

def adbSwipeKill(ax,ay,bx,by):
	os.system('adb shell input swipe %d %d %d %d'%(ax,ay,bx,by))

def waitDisplay(waittime):
	for i in range(100):
		time.sleep(waittime/100)
		sys.stdout.write("\r	testing %d%% done" % (i+1))
		sys.stdout.flush()


def doTestGetResult():
	os.system('adb devices')

	# start antutu and wait
	start_antutu()
	# click test button to start test and wait,
	# meanwhile, output progress
	adbClick(coord.testx, coord.testy)
	waitDisplay(coord.timeWaitTest)

	# press Recent and kill antutu
	# killapp()
	# killapp()

	# collect antutu test result
	result = collect_result()
	time.sleep(timeWaitStep)

	return result



def main():
	print CUR_DIR
	if not os.path.exists(os.path.join(CUR_DIR,'./'+out_dir+'/')):
		os.mkdir(os.path.join(CUR_DIR,'./'+out_dir+'/'))
	adbUnlockScreen()

	# for debug, comment it
	adb.turn_airplane('1')
	adb.turn_bluetooth('0')
	adb.turn_wifi('0')
	adb.turn_gps('0')
	adb.set_display_time()

	prepareAPK()

	for i in range(4):
		result = doTestGetResult()

		if result == 'error, no result found':
			os.system('adb reboot')
			continue
		else:
			break

	print 'Test Result of Antutu is : ',result

	# for debug, comment it
	
	tr.result(result)
	# tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/result.txt'))
	tr.add_attachment(os.path.join(CUR_DIR,out_dir,'antutu.txt'),'antutu.txt')
	# tr.result('antutu_5.6_total_result', result, 'score')
	# tr.add_attachment('/home/bxtp/atf_slave2/runner/scripts/script_benchmark/20170815_032034/antutu.txt')
	tr.save()

if __name__ == "__main__":
	main()
