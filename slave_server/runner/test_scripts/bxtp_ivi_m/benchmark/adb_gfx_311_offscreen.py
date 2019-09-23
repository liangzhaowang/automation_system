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
timeWaitTest = 140
result = []
tr = TestResult(__file__)
# apkpath = '/home/bxtp/suhao/gfxbench_gl-4.0.13-candidate+corporate.x86.apk/'
# apkpath = os.path.join(os.path.dirname(__file__), 'GFXBench_3_1_1_Corporate_Android_Binary_10_12_2015.apk')
apk_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'GFXBench_3_1_1_Corporate_Android_Binary_10_12_2015.apk')
# apkpath = './src/GFXBench_3_1_1_Corporate_Android_Binary_10_12_2015.apk'
# launch_activity = 'net.kishonti.gfxbench.gl.v40013.corporate/net.kishonti.app.MainActivity'
launch_activity = 'net.kishonti.gfxbench.gl.v30101.corporate/net.kishonti.app.MainActivity'
package_name = 'net.kishonti.gfxbench.gl.v30101.corporate'



def dpad_center():
	os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')

def dpad_right():
	os.system('adb shell input keyevent KEYCODE_DPAD_RIGHT')

def dpad_up():
	os.system('adb shell input keyevent KEYCODE_DPAD_UP')

def dpad_down():
	os.system('adb shell input keyevent KEYCODE_DPAD_DOWN')



def waitDisplay(waittime):
	for i in range(100):
		time.sleep(waittime/100)
		sys.stdout.write("\r	testing %d%% done" % (i+1))
		sys.stdout.flush()

def get_result():
	result_str = ''
	alltext = 'adb logcat -d | grep -e _logcat.*score -e _logcat.*fps | cut -d ":" -f 4,5 >' +os.path.join(CUR_DIR,out_dir, 'manhattan_offscreen.txt')
	os.popen(alltext)
	text = os.popen('adb logcat -d | grep -e _logcat.*score -e _logcat.*fps | cut -d ":" -f 4,5 ').readlines()
	if len(text) == 2:
		for idx,line in enumerate(text):
			print line
			result = line.strip().split(':')
			
			
			if idx == 0:
				fps = result[1][0:6]
				tr.sub_score(result[0].strip('""').split()[0],fps)
			elif idx == 1:
				score = result[1][0:8]
				tr.sub_score(result[0].strip('""').split()[0],score)
		# result_str = 'onscreen : %s @ %s fps;   offscreen : %s @ %s fps ' \
		#	   %(onscreen_score,onscreen_fps,offscreen_score,offscreen_fps)
		#result_str = '%s @%s fps' % (onscreen_score, onscreen_fps)
		result_str = fps
		# score['score'] =score
		# for key,val in result.items():
		# 	tr.sub_score(key,str(val))
		print 'onscreen result   fps : %s   score: %s' %(fps,score)
	else:
		result_str = 'Error, result not found'
		print result_str

	# if result_str == 'Error, result not found':
	# 	continue
	# else:
	# 	break
	return result_str

def click_test_offscreen_gfx311():
	# click Test selection
	adb.click(1180,780)

	# clear high level
	adb.click(1120,150)

	# clear low level
	adb.click(1120,540)

	# clear special tests
	adb.click(1600, 930)

	# set offscreen
	adb.click(1750,330)

	# start test
	adb.click(1880, 75)




def startGFX_brxtp():
	os.system('adb logcat -c')
	adb.clear_data(package_name)
	os.system('adb shell am start -n '+launch_activity)
	time.sleep(timeWaitActivity)
	for i in range(5):
		dpad_right()
	dpad_center()
	print 'wait copy assest'
	# for bxtp, need 60 sec to copy
	waitDisplay(100)

def installApk():
	text = os.popen('adb shell pm list packages -3 | grep kishonti.gfxbench.gl').readlines()
	if len(text) == 0:
		os.system('adb install '+apk_path)
		time.sleep(5)


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


def main():
	print CUR_DIR
	if not os.path.exists(os.path.join(CUR_DIR,'./'+out_dir+'/')):
		os.mkdir(os.path.join(CUR_DIR,'./'+out_dir+'/'))
	if not check_device():
		print 'Error no device'
		print 'Quit'
		return
	adbUnlockScreen()

	# system setup
	adb.turn_airplane('1')
	adb.turn_bluetooth('0')
	adb.turn_wifi('0')
	adb.turn_gps('0')
	adb.set_display_time()

	installApk()
	for i in range(4):
		startGFX_brxtp()
		click_test_offscreen_gfx311()
		waitDisplay(180)
		result_str = get_result()
		adb.killapp()
		adb.clear_data(package_name)
		if result_str == 'Error, result not found':
			continue
		else:
			break

	print 'The Result is: \n'+result_str

	# for debug, comment it
	
	tr.result(result_str)
	tr.add_attachment(os.path.join(CUR_DIR,out_dir, 'manhattan_offscreen.txt'),'manhattan_offscreen.txt')
	tr.save()


if __name__ == "__main__":
	main()
