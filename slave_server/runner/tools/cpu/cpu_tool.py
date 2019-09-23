import os
import sys
import time
from runner.operation_lib.base_lib.exception_operation import wait_for_boot
cmd_path = os.getcwd()


args = sys.argv[1:]
out_dir = os.path.join("runner", "test_results", args[3], "tool", "cpu")
if not os.path.exists(out_dir):
    os.makedirs(out_dir)


def _get_passwd(passwd_path="runner/operation_lib/host_passwd"):
    with open(passwd_path) as pwdfp:
        host_passwd = pwdfp.read().strip()
    return host_passwd


def main():
    host_passwd = _get_passwd()
    for t in range(500): 
        if wait_for_boot():
            t += 1
            if os.path.isdir(out_dir):
                os.system('cp "./runner/tools/cpu/GPUCPU/cat_cpu_gpu.sh" {0}'.format(out_dir))
                os.system('cp "./runner/tools/cpu/GPUCPU/plot.sh" {0}'.format(out_dir))
                os.chdir(os.path.join(cmd_path +'/'+ out_dir))
                os.system("./cat_cpu_gpu.sh")   
        else:
            time.sleep(10)


if __name__ == '__main__':
    print 'cpu_tool start'
    main()
