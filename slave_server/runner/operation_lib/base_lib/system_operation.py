import os
import time
import re
from uiautomator import Device
from atf import TestLogger
from exception_operation import kill_adb_uiautomator_block_old
from exception_operation import kill_adb_uiautomator_block
from exception_operation import wait_for_device_reboot
device = Device()
logger = TestLogger().get_logger("process")

build_info = os.popen('adb shell getprop |grep system.build.fingerprint').read()
build_version = re.findall('gordon_peak:([0-9.]+)/',build_info)


def reboot_system():
    wait_for_device_reboot()


def get_screen_off_time():
    time.sleep(3)
    text = os.popen('adb shell settings get system screen_off_timeout').readlines()
    current_state = 'Error'
    if len(text) > 0:
        current_state = text[0].strip()
        logger.info('current screen off time is {t}'.format(t=current_state))
    return current_state


def set_display_time(displaytime=1800000, menu_display=False):
    """
    displaytime = 15000 | 30000 | 60000 | 120000| 300000 | 600000 | 1800000
    displaytime default is 1800000
    judgment wether the dut version is Q 
    """
    kill_adb_uiautomator_block_old()
    if int(get_screen_off_time()) == displaytime:
        if int(displaytime) >= 60000:
            logger.info( 'screen off time is already %s mins'%(displaytime/60000))
        else:
            logger.info('screen off time is already %s secs'%(displaytime/1000))
    else:
        os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
        device(text="Sleep").click()
        kill_adb_uiautomator_block_old()
        if int(displaytime) >= 60000:
            device(text="%s minutes"%(displaytime/60000)).click()
        else:
            device(text="%s seconds"%(displaytime/1000)).click()
        time.sleep(1)
        os.system("adb shell am force-stop com.android.settings")


def get_state(key):
    time.sleep(3)
    text = os.popen('adb shell settings get global '+key).readlines()
    former_state = 'Error'
    if len(text) > 0:
        former_state = text[0].strip()
        logger.info(key+' current state is : %s' % former_state)
    return former_state


def screen_on():
    if build_version and build_version[0] == '10':
        os.system("adb shell svc power stayon true")
    else:
        time.sleep(5)
        kill_adb_uiautomator_block()
        if device.screen == "off":
            logger.info("unlock screen...")
            kill_adb_uiautomator_block_old()
            device.wakeup()
            time.sleep(1)
        else:
            logger.info("Screen On.")


def get_gps_state():
    time.sleep(3)
    text = os.popen('adb shell settings get secure location_providers_allowed').readlines()
    if len(text) > 0:
        length = len(text[0].strip())
        if length == 0:
            result = '0'
        else:
            result = '1'
    else:
        result = '0'
    logger.info('gps current state is : %s' % result)
    return result


def turn_gps(state):
    if state == get_gps_state():
        logger.info('gps already turned ' + state)
        return True

    for i in range(4):
        kill_adb_uiautomator_block_old()
        if state == '0':
            os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
            if device(resourceIdMatches=".+/switch_widget$", text="ON").exists:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$", text="ON").click.wait(timeout=20)
        else:
            os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
            if device(resourceIdMatches=".+/switch_widget$", text="OFF").exists:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$", text="OFF").click.wait(timeout=20)
        
        os.system('adb shell am force-stop com.android.settings')
        if state == get_gps_state():
            return True
    return False


def turn_airplane(state):
    if state == get_state('airplane_mode_on'):
        logger.info('airplane already turned ' + state)
        return True

    for i in range(4):
        os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
        kill_adb_uiautomator_block_old()
        if device(text='ACCEPT').exists:
            logger.info('airplane security tips find')
            device(text='ACCEPT').click.wait(timeout=20)
        kill_adb_uiautomator_block_old()
        device(text="Airplane mode").click.wait()
        time.sleep(1)
        os.system('adb shell am force-stop com.android.settings')
        if state == get_state('airplane_mode_on'):
            return True
    return False


def turn_wifi(state):
    if build_version and build_version[0] == '10':
        if state == get_state('wifi_on'):
            logger.info('wifi already turned ' + state)
            return True
        else:
            os.system("adb shell svc wifi enable")
    else:
        if state == get_state('wifi_on'):
            logger.info('wifi already turned ' + state)
            return True
        
        for i in range(4):
            if state == '0':
                os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
                kill_adb_uiautomator_block_old()
                time.sleep(1)
                if device(resourceIdMatches=".+/switch_widget$", text="OFF").exists:
                    logger.info('Wi-Fi current state is : 0')
                    os.system('adb shell am force-stop com.android.settings')
                    return True
                else:
                    kill_adb_uiautomator_block_old()
                    device(resourceIdMatches=".+/switch_widget$", text="ON").click.wait(timeout=20)
            else:
                os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
                time.sleep(2)
                kill_adb_uiautomator_block_old()
                if device(resourceIdMatches=".+/switch_widget$", text="ON").exists:
                    logger.info('Wi-Fi current state is : 1')
                    os.system('adb shell am force-stop com.android.settings')
                    return True
                else:
                    kill_adb_uiautomator_block_old()
                    device(resourceIdMatches=".+/switch_widget$", text="OFF").click.wait(timeout=20)
            
            os.system('adb shell am force-stop com.android.settings')
            if state == get_state('wifi_on'):
                return True
        
        return False


def set_wifi(state):
    if state == '1':
        logger.info(">>>Enable wifi...")
        os.system("adb shell svc wifi enable")
    else:
        logger.info(">>>Disable wifi...")
        os.system("adb shell svc wifi disable")


def connect_wifi():
    logger.info("connect_wifi")
    set_wifi('1')
    time.sleep(1)
    conf_file = 'runner/test_src/wifi_in.conf'
    os.system("adb root; adb push %s /data/misc/wifi/wpa_supplicant.conf" % conf_file)
    time.sleep(1)
    set_wifi('0')
    time.sleep(2)
    set_wifi('1')
    time.sleep(3)


def connect_wifi_manual(ap, pwd):
    logger.info("connect_wifi manual")
    os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
    time.sleep(3)
    if device(text="Connected").exists:
        logger.info("Wifi connected")
    else:
        set_wifi('1')
        time.sleep(10)
        while True:
            time.sleep(1)
            swipe_down()
            if device(resourceIdMatches="android:id/title", text="Add network").exists:
                time.sleep(1)
                device(resourceIdMatches="android:id/title", text="Add network").click.wait(timeout=20)
                time.sleep(2)
                device(resourceIdMatches="com.android.settings:id/ssid", text="Enter the SSID").set_text(ap)
                time.sleep(2)
                # minput_keyboard()
                device(resourceIdMatches="android:id/text1", text="None").click.wait(timeout=20)
                time.sleep(1)
                device(resourceIdMatches="android:id/text1", text="WPA/WPA2 PSK").click.wait(timeout=20)
                time.sleep(1)
                device(resourceIdMatches="com.android.settings:id/password").set_text(pwd)
                time.sleep(2)
                # minput_keyboard()
                # time.sleep(2)
                device(resourceIdMatches="android:id/button1", text="SAVE").click.wait(timeout=20)
                time.sleep(30)
                logger.info("wifi connected")
                break


def swipe_down():
    display_h = device.info['displayHeight']
    display_w = device.info['displayWidth']
    icon_sx = display_w * 58 / 100
    icon_sy = display_h * 70 / 100
    icon_ex = display_w * 58 / 100
    icon_ey = display_h * 30 / 100
    device.swipe(icon_sx, icon_sy, icon_ex, icon_ey)


def modify_wifi():
    turn_wifi('1')
    time.sleep(1)
    wifi_config = 'runner/test_src/wifi_out.conf'
    os.system("adb push %s /data/misc/wifi/wpa_supplicant.conf" % wifi_config)
    time.sleep(1)
    set_wifi('0')
    time.sleep(2)
    set_wifi('1')
    time.sleep(3)


def get_index_from_list(app_dev, index_count, key_value):
    index_list = []
    for nu in range(index_count):
        kill_adb_uiautomator_block_old()
        try:
            string = app_dev.child(index=nu).child(resourceIdMatches='.+/widget_text1').info['text']
            if string == key_value:
                index_list.append(nu)
        except Exception, e:
            logger.error("get index errors: %s" % e)
    return index_list


def change_swith_status(dev):
    kill_adb_uiautomator_block_old()
    app_dev = dev(resourceIdMatches='.+/list')
    kill_adb_uiautomator_block_old()
    if app_dev.exists:
        index_nu = app_dev.info['childCount']
        logger.info(index_nu)
        iter_list = get_index_from_list(app_dev, index_nu, 'Yes')
        logger.info(iter_list)
        if len(iter_list) > 0:
            for item in iter_list:
                kill_adb_uiautomator_block_old()
                app_dev.child(index = int(item)).child(resourceIdMatches='.+/widget_text1').click()
                time.sleep(2)
                if dev(resourceIdMatches=".+/switchWidget$", text="ON").exists:
                    kill_adb_uiautomator_block_old()
                    dev(resourceIdMatches=".+/switchWidget$", text="ON").click.wait(timeout=20)
                os.system('adb shell input keyevent BACK')
    time.sleep(1)
    os.system("adb shell input keyevent HOME")


def check_perssion_st(dev):
    os.system("adb shell am start -n 'com.android.settings/.Settings\$OverlaySettingsActivity'")        
    change_swith_status(dev)


def turn_bluetooth(state):
    if build_version and build_version[0] == '10':
        if state == get_state('wifi_on'):
            logger.info('wifi already turned ' + state)
            return True
        else:
            os.system("adb shell svc wifi enable")
    else:
        if state == get_state('bluetooth_on'):
            logger.info('bluetooth already turned ' + state)
            return True

        for i in range(4):
            if state == '0':
                os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
                kill_adb_uiautomator_block_old()
                time.sleep(1)
                if device(resourceIdMatches=".+/switch_widget$", text="OFF").exists:
                    logger.info('Bluetooth current state is : 0')
                    os.system('adb shell am force-stop com.android.settings')
                    return True
                else:
                    kill_adb_uiautomator_block_old()
                    device(resourceIdMatches=".+/switch_widget$" ,text="ON").click.wait(timeout=20)
            else:
                kill_adb_uiautomator_block_old()
                os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
                if device(resourceIdMatches=".+/switch_widget$" ,text="ON").exists:
                    logger.info( 'Bluetooth current state is : 1')
                    os.system('adb shell am force-stop com.android.settings')
                    return True
                else:
                    kill_adb_uiautomator_block_old()
                    device(resourceIdMatches=".+/switch_widget$" ,text="OFF").click.wait(timeout=20)
            
            os.system('adb shell am force-stop com.android.settings')
            if state == get_state('bluetooth_on'):
                return True
        return False

def turn_bluetooth_p(state):
    if state == get_state('bluetooth_on'):
        logger.info('bluetooth already turned ' + state)
        return True
    else:
        os.system('adb shell am start -n com.android.car.settings/.common.CarSettingActivity')
        os.system('adb shell input tap 768 317')
        time.sleep(5)
        os.system('adb shell am force-stop com.android.car.settings')
    if state == get_state('bluetooth_on'):
        return True
    else:
        return False

def get_screen_orientation():
    kill_adb_uiautomator_block()
    os.system("adb root")
    time.sleep(1)
    orientation_st = device.orientation
    logger.info("the screen display orientation is %s" % orientation_st)
    kill_adb_uiautomator_block()
    return orientation_st.lstrip().strip()


def set_display_orientaion(set_orientation):
    logger.info("the screen display set_orientation is %s" % set_orientation)
    orientation_st = get_screen_orientation()
    if set_orientation is not orientation_st:
        device.orientation = set_orientation
    kill_adb_uiautomator_block()


def main():
    set_display_time()


if __name__ == "__main__":
    main()
