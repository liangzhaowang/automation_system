import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import wait_for_boot

args = sys.argv[1:]
out_dir = os.path.join("runner", "test_results", args[3], "tool", "systrace")
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
os.system('adb root')
os.system("adb shell 'echo 1 > /d/tracing/events/sync_trace/enable'")
os.system("adb shell 'echo 1 > /d/tracing/events/dma_fence/enable'")


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read().strip()
    return host_passwd


def main():
    host_passwd = _get_passwd()
    for t in range(500): 
        if wait_for_boot():
            t += 1
            systrace_cmd = "echo '"+host_passwd+"'|sudo -S python runner/tools/systrace/systrace/systrace.py gfx input view webview wm am sm hal app res dalvik rs bionic power pm ss database sched irq i2c freq idle disk mmc load sync workq memreclaim binder_driver binder_lock pagecache -o {0}/sys_{1}.html -t 10 -b 32768".format(out_dir, str(t))
            print systrace_cmd
            os.system(systrace_cmd)   
        else:
            time.sleep(10)


if __name__ == '__main__':
    print 'systrace_tool start'
    main()
