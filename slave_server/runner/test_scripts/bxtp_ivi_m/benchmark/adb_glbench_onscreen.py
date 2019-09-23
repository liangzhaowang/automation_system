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
timeWaitActivity = 10
timeWaitTest = 300
result = []
result_str = ''
tr = TestResult(__file__)
# apk_path = '/home/suhao/suhaoDrive/GLBenchmark_2_7_0_Release_a68901_Android_Corporate_Package.apk'
# apk_path = os.path.join(os.path.dirname(__file__), '/lib/GLBenchmark_2_7_0.apk')
apk_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'GLBenchmark_2_7_0.apk')
# apk_path = './src/GLBenchmark_2_7_0.apk'


def waitDisplay(waittime):
	for i in range(100):
		time.sleep(waittime/100)
		sys.stdout.write("\r	testing %d%% done" % (i+1))
		sys.stdout.flush()

def get_result():
	alltext = 'adb logcat -d | grep "Application::FinishCurrentTest" >'+os.path.join(CUR_DIR,out_dir, 'glbench_onscreen.txt')
	os.popen(alltext)
	text = os.popen('adb logcat -d | grep "Application::FinishCurrentTest"').readlines()
	try:
		with open(os.path.join(CUR_DIR,out_dir,'result.txt'),'a') as f:
			f.write(str(text))
			f.write('\n')
			f.close()
	except Exception, e:
		print "con't open result.txt"
		print e
	if len(text) > 0 :
		print text[0]
		array = text[0].replace('frames','@').strip().strip(')').split()
		tr.sub_score(array[11].strip(':').split()[0], array[12])
		return array[14]
	else:
		print 'Error, no result find'
		return 'Error, no result find'



def click_test(onscreen=False,offsreen=False):
	adb.dpad_up()
	adb.dpad_up()
	adb.dpad_up()
	adb.dpad_center()

	adb.dpad_center()
	adb.dpad_center()
	for i in range(16):
		adb.dpad_up()
	if onscreen:
		for i in range(10):
			adb.dpad_down()
	if offsreen:
		for i in range(11):
			adb.dpad_down()
	adb.dpad_center()
	for i in range(20):
		adb.dpad_down()
	os.system('adb shell input keyevent KEYCODE_DPAD_RIGHT')
	adb.dpad_center()


def startGLBench():
	os.system('adb logcat -c')
	clear_data_glbench()
	os.system('adb shell am start -n com.glbenchmark.glbenchmark27/com.glbenchmark.activities.GLBenchmarkDownloaderActivity')
	time.sleep(timeWaitActivity)

def clear_data_glbench():
	os.system('adb shell pm clear com.glbenchmark.glbenchmark27')

def installApk():
	os.system('adb install '+apk_path)
	time.sleep(5)
	adbPressHome()

def adbPressHome():
	os.system('adb shell input keyevent 3')
	time.sleep(timeWaitStep)

def adbUnlockScreen():
	os.system('adb shell input keyevent 82')
	adbPressHome()


def check_device():
	text = os.popen('adb devices').readlines()
	if len(text) != 3 :
		return False
	else:
		return True

def dotest(onscreen=False,offscreen=False):

	for i in range(4):
		startGLBench()
		click_test(onscreen=onscreen,offsreen=offscreen)
		waitDisplay(180)
		result = get_result()
		print 'Result is : '+result
		adb.killapp()
		if result == 'Error, no result find':
			installApk()
			continue
		else:
			break
	return result

def main():
	print CUR_DIR
	if not os.path.exists(os.path.join(CUR_DIR,'./'+out_dir+'/')):
		os.mkdir(os.path.join(CUR_DIR,'./'+out_dir+'/'))
	if not check_device():
		print 'Error no device'
		print 'Quit'
		return

	adbUnlockScreen()

	# comment for debug
	# adb.system_setup(tog_bt=True,tog_wifi=True,tog_gps=True,)
	adb.turn_airplane('0')
	adb.turn_bluetooth('0')
	adb.turn_wifi('0')
	adb.turn_gps('0')
	adb.set_display_time()

	installApk()

	result = dotest(onscreen=True)

	print result

	# comment for debug
	tr.result(result)
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/glbench_onscreen.txt'),'glbench_onscreen.txt')
	tr.add_attachment(os.path.join(CUR_DIR,out_dir+'/result.txt'),'result.txt')
	tr.save()


if __name__ == "__main__":
	main()
