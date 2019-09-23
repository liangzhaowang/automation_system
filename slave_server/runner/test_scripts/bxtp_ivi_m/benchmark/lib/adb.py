import os
import time


def get_screen_off_time():
    time.sleep(3)
    text = os.popen('adb shell settings get system screen_off_timeout').readlines()
    current_state = 'Error'
    if len(text) > 0:
        current_state = text[0].strip()
        print 'current screen off time is {t}'.format(t=current_state)
    return current_state

def set_display_time():
    if get_screen_off_time() == '1800000':
        print 'screen off time is already 30 mins'
    else:
        os.system('adb shell am force-stop com.android.settings')
        os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
        dpad_up()
        dpad_up()
        for i in range(3):
            dpad_down()
        dpad_center()
        for i in range(8):
            dpad_down()
        dpad_up()
        dpad_center()
        killapp()





def get_state(key):
    time.sleep(3)
    text = os.popen('adb shell settings get global '+key).readlines()
    former_state = 'Error'
    if len(text) > 0:
        former_state = text[0].strip()
        print key+' current state is : %s' % former_state
    return former_state


def get_gps_state():
    time.sleep(3)
    text = os.popen('adb shell settings get secure location_providers_allowed').readlines()
    length = len(text[0].strip())
    if length == 0:
        result = '0'
    else:
        result = '1'
    print 'gps current state is : %s' % result
    return result
    # former_state = 'Error'
    # if len(text) > 0:
    #     former_state = text[0].strip()
    #     print 'airplane former state is : %s' % former_state
    # return former_state

def turn_gps(state):
    if state == get_gps_state():
        print 'gps already turned '+ state
        return True

    for i in range(4):
        os.system('adb shell am force-stop com.android.settings')
        os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()
        if state == get_gps_state():
            return True

    return False


def turn_airplane(state):

    if state == get_state('airplane_mode_on'):
        print 'airplane already turned '+ state
        return True

    for i in range(4):
        os.system('adb shell am force-stop com.android.settings')
        os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()
        if state == get_state('airplane_mode_on'):
            return True

    return False

# wifi_on
def turn_wifi(state):

    if state == get_state('wifi_on'):
        print 'wifi already turned '+ state
        return True

    for i in range(4):
        os.system('adb shell am force-stop com.android.settings')
        os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()
        if state == get_state('wifi_on'):
            return True

    return False

# bluetooth_on
def turn_bluetooth(state):

    if state == get_state('bluetooth_on'):
        print 'bluetooth already turned '+ state
        return True

    for i in range(4):
        os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()
        if state == get_state('bluetooth_on'):
            return True

    return False


def clear_data(package):
    os.system('adb shell pm clear '+package)

def click(x, y):
    os.system('adb shell input tap %d %d' % (x, y))
    time.sleep(3)


def killapp():
    os.system('adb shell input keyevent KEYCODE_APP_SWITCH')
    dpad_down()
    dpad_down()
    os.system('adb shell input keyevent DEL')
    os.system('adb shell input keyevent 3')

def dpad_center():
    os.system('adb shell input keyevent KEYCODE_DPAD_CENTER')

def dpad_up():
    os.system('adb shell input keyevent KEYCODE_DPAD_UP')

def dpad_down():
    os.system('adb shell input keyevent KEYCODE_DPAD_DOWN')

def system_setup(tog_airplane = False,
                tog_wifi = False,
                tog_bt = False,
                tog_gps = False,
                tog_display = True
                ):
    '''

    :return:
    '''

    '''
    initial state
    airplane    off
    wifi        on
    bt          on
    gps         on
    display     15sec
    '''

    # open air mode

    # os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
    # os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
    # os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
    # os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')




    # toggle airplane state
    if(tog_airplane):
        os.system('adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()

    # toggle wifi
    if(tog_wifi):
        os.system('adb shell am start -a android.settings.WIFI_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()

    # toggle gps
    if(tog_gps):
        os.system('adb shell am start -a android.settings.LOCATION_SOURCE_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()

    # toogle bluetooth
    if(tog_bt):
        os.system('adb shell am start -a android.settings.BLUETOOTH_SETTINGS')
        dpad_up()
        dpad_up()
        dpad_up()
        dpad_center()
        killapp()

    # set longest display sleep time
    if(tog_display):
        os.system('adb shell am start -a android.settings.DISPLAY_SETTINGS')
        dpad_up()
        dpad_up()
        for i in range(3):
            dpad_down()
        dpad_center()
        for i in range(8):
            dpad_down()
        dpad_up()
        dpad_center()
        killapp()

    os.system('adb shell am force-stop com.android.settings')


def main():
    # turn_wifi(state='0')
    # turn_bluetooth(state='1')
    # turn_airplane(state='1')
    # turn_gps('0')
    set_display_time()


if __name__ == "__main__":

    main()

