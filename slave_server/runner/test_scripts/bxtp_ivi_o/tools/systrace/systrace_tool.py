import os,re,sys
import time
import yaml
import zipfile
from atf import *
import signal


CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])

sys.path.append(CUR_DIR+'../../operation_lib')
from base_lib.exception_operation import wait_for_boot
from base_lib import UI_interface_operation
args = sys.argv[1:]
script_path = os.path.split(os.path.realpath(args[0]))[0]
out_dir = args[1]
log_dir = os.path.join(script_path, out_dir)
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
os.system('adb root')
os.system("adb shell 'echo 1 > /d/tracing/events/sync_trace/enable'")
os.system("adb shell 'echo 1 > /d/tracing/events/dma_fence/enable'")


def main():
    
    for t in range(500): 
        if wait_for_boot():
            t+=1
            systrace_cmd="echo '123456'|sudo -S python {0}systrace/systrace.py gfx input view webview wm am sm hal app res dalvik rs bionic power pm ss database sched irq i2c freq idle disk mmc load sync workq memreclaim binder_driver binder_lock pagecache -o {1}../../script/{2}/{3}/sys_{4}.html -t 10 -b 32768".format(CUR_DIR, CUR_DIR, args[0].split('/')[4], out_dir, t)
            print systrace_cmd
            os.system(systrace_cmd)   
        else:
            time.sleep(10)


if __name__ == '__main__':
    print 'systrace_tool start'
    main()

   
    
 
