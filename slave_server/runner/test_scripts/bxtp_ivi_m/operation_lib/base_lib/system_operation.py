import os
import time
from uiautomator import Device 
from exception_operation import kill_adb_uiautomator_block_old
from exception_operation import kill_adb_uiautomator_block
from exception_operation import wait_for_device_reboot
from makelog import makelog
from makelog import log_info
CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
device = Device()

def reboot_system():
	wait_for_device_reboot()

def get_screen_off_time(log_mes):
    time.sleep(3)
    text = os.popen('adb shell settings get system screen_off_timeout').readlines()
    current_state = 'Error'
    if len(text) > 0:
        current_state = text[0].strip()
        log_mes.info( 'current screen off time is {t}'.format(t=current_state))
    return current_state

def set_display_time(log_mes,displaytime = 1800000):
    """
    displaytime = 15000 | 30000 | 60000 | 120000| 300000 | 600000 | 1800000
    displaytime default is 1800000 
    """
    kill_adb_uiautomator_block_old()
    if int(get_screen_off_time(log_mes)) == displaytime:
        if int(displaytime) >= 60000:
            log_mes.info( 'screen off time is already %s mins'%(displaytime/60000))
        else:
            log_mes.info('screen off time is already %s secs'%(displaytime/1000))
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

def get_state(key,log_mes):
    time.sleep(3)
    text = os.popen('adb shell settings get global '+key).readlines()
    former_state = 'Error'
    if len(text) > 0:
        former_state = text[0].strip()
        log_mes.info( key+' current state is : %s' % former_state)
    return former_state

def screen_on(log_mes):
    time.sleep(5)
    kill_adb_uiautomator_block()
    if device.screen == "off":
        log_mes.info("unlock screen...")
        kill_adb_uiautomator_block_old()
        device.wakeup()
        #os.system("adb shell input keyevent 82")
        time.sleep(1)
    else:
        log_mes.info("Screen On.")

def get_gps_state(log_mes):
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
    log_mes.info( 'gps current state is : %s' % result)
    return result

def turn_gps(state,log_mes):
    if state == get_gps_state(log_mes):
        log_mes.info( 'gps already turned '+ state)
        return True

    for i in range(4):
        kill_adb_uiautomator_block_old()
        if state == '0':
            os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
            if device(resourceIdMatches=".+/switch_widget$" ,text="ON").exists:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="ON").click.wait(timeout=20)
        else:
            os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
            if device(resourceIdMatches=".+/switch_widget$" ,text="OFF").exists:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="OFF").click.wait(timeout=20)
        
        os.system('adb shell am force-stop com.android.settings')
        if state == get_gps_state(log_mes):
            return True
    
    return False

def turn_airplane(state,log_mes):
    if state == get_state('airplane_mode_on',log_mes):
        log_mes.info( 'airplane already turned '+ state)
        return True

    for i in range(4):
        os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
        kill_adb_uiautomator_block_old()
        device(text="Airplane mode").click.wait()
        time.sleep(1)
        os.system('adb shell am force-stop com.android.settings')
        if state == get_state('airplane_mode_on',log_mes):
            return True
    return False

# wifi_on
def turn_wifi(state,log_mes):
    if state == get_state('wifi_on',log_mes):
        log_mes.info( 'wifi already turned '+ state)
        return True
    
    for i in range(4):
        if state == '0':
            os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
            kill_adb_uiautomator_block_old()
            time.sleep(1)
            if device(resourceIdMatches=".+/switch_widget$" ,text="OFF").exists:
                log_mes.info( 'Wi-Fi current state is : 0')
                os.system('adb shell am force-stop com.android.settings')
                return True
            else:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="ON").click.wait(timeout=20)
        else:
            os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
            time.sleep(2)
            kill_adb_uiautomator_block_old()
            if device(resourceIdMatches=".+/switch_widget$" ,text="ON").exists:
                log_mes.info( 'Wi-Fi current state is : 1')
                os.system('adb shell am force-stop com.android.settings')
                return True
            else:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="OFF").click.wait(timeout=20)
        
        os.system('adb shell am force-stop com.android.settings')
        if state == get_state('wifi_on',log_mes):
            return True
    
    return False

def set_wifi(log_mes,state):
    if state == '1':
        log_mes.info( ">>>Enable wifi...")
        os.system("adb shell svc wifi enable")
    else:
        log_mes.info(">>>Disable wifi...")
        os.system("adb shell svc wifi disable")

def connect_wifi(log_mes):
    log_mes.info("connect_wifi")
    set_wifi(log_mes,'1')
    time.sleep(1)
    conf_file = CUR_DIR+"/../"+'./src/wifi_in.conf'
    os.system("adb push %s /data/misc/wifi/wpa_supplicant.conf"%conf_file)
    time.sleep(1)
    set_wifi(log_mes,'0')
    time.sleep(2)
    set_wifi(log_mes,'1')
    time.sleep(3)

def modify_wifi(log_mes):
    turn_wifi('1',log_mes)
    time.sleep(1)
    wifi_config=CUR_DIR+"/../"+'./src/wifi_out.conf'
    os.system("adb  push %s /data/misc/wifi/wpa_supplicant.conf"%wifi_config)
    time.sleep(1)
    set_wifi(log_mes,'0')
    time.sleep(2)
    set_wifi(log_mes,'1')
    time.sleep(3)

def get_index_from_list(app_dev,index_count,key_value):
    index_list = []
    for nu in range(index_count):
        kill_adb_uiautomator_block_old()
        try:
            string = app_dev.child(index = nu).child(resourceIdMatches='.+/widget_text1').info['text']
            if string == key_value:
                index_list.append(nu)
        except Exception,e:
            log_info.logger.error("get index errors: %s"%e)
    return index_list

def change_swith_status(dev,log_mes):
    kill_adb_uiautomator_block_old()
    app_dev = dev(resourceIdMatches='.+/list')
    kill_adb_uiautomator_block_old()
    if app_dev.exists:
        index_nu = app_dev.info['childCount']
        log_mes.info(index_nu)
        iter_list = get_index_from_list(app_dev,index_nu,'Yes')
        log_mes.info(iter_list)
        if len(iter_list) > 0:
            for item in iter_list:
                kill_adb_uiautomator_block_old()
                app_dev.child(index = int(item)).child(resourceIdMatches='.+/widget_text1').click()
                time.sleep(2)
                if dev(resourceIdMatches=".+/switchWidget$" ,text="ON").exists:
                    kill_adb_uiautomator_block_old()
                    dev(resourceIdMatches=".+/switchWidget$" ,text="ON").click.wait(timeout=20)
                os.system('adb shell input keyevent BACK')
    time.sleep(1)
    os.system("adb shell input keyevent HOME")

def check_perssion_st(dev,log_mes):			
    os.system("adb shell am start -n 'com.android.settings/.Settings\$OverlaySettingsActivity'")		
    change_swith_status(dev,log_mes)


# bluetooth_on
def turn_bluetooth(state,log_mes):
    if state == get_state('bluetooth_on',log_mes):
        log_mes.info( 'bluetooth already turned '+ state)
        return True

    for i in range(4):
        if state == '0':
            os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
            kill_adb_uiautomator_block_old()
            time.sleep(1)
            if device(resourceIdMatches=".+/switch_widget$" ,text="OFF").exists:
                log_mes.info( 'Bluetooth current state is : 0')
                os.system('adb shell am force-stop com.android.settings')
                return True
            else:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="ON").click.wait(timeout=20)
        else:
            kill_adb_uiautomator_block_old()
            os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
            if device(resourceIdMatches=".+/switch_widget$" ,text="ON").exists:
                log_mes.info( 'Bluetooth current state is : 1')
                os.system('adb shell am force-stop com.android.settings')
                return True
            else:
                kill_adb_uiautomator_block_old()
                device(resourceIdMatches=".+/switch_widget$" ,text="OFF").click.wait(timeout=20)
        
        os.system('adb shell am force-stop com.android.settings')
        if state == get_state('bluetooth_on', log_mes):
            return True

    return False


def get_screen_orientation(log_mes):
    kill_adb_uiautomator_block()
    os.system("adb root")
    time.sleep(1)
    orientation_st = device.orientation
    log_mes.info("the screen display orientation is %s"%orientation_st)
    kill_adb_uiautomator_block()
    return orientation_st.lstrip().strip()

def set_display_orientaion(set_orientation,log_mes):
    log_mes.info("the screen display set_orientation is %s"%set_orientation)
    orientation_st = get_screen_orientation(log_mes)
    if not set_orientation is orientation_st:
        device.orientation = set_orientation
    kill_adb_uiautomator_block()

def main():
    # turn_wifi(state='0')
    # turn_bluetooth(state='1')
    # turn_airplane(state='1')
    # turn_gps('0')
    set_display_time()


if __name__ == "__main__":

    main()

