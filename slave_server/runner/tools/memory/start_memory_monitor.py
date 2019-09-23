#!/usr/bin/env python
import os
import sys
import getopt
import subprocess


def start_memory_monitor(name, dir):
    print "===================start memory_monitor.rb======================"
    try:
        cmd = " ".join(["ruby", "runner/tools/memory/memory_monitor.rb", name, dir])
        subprocess.Popen(cmd, shell=True, close_fds=True)
    except Exception, e:
        print "start memeory monitor error: ", e.message
    print "-------------------------------------------------------------"


def main(argv):
    name = ''
    dir = ''
    try:
        opts, args = getopt.getopt(argv, "hn:d:", ["name=", "dir="])
    except getopt.GetoptError:
        print 'start_memory_monitor.py [-n <name>] [-d <dir>]'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print 'start_memory_monitor.py [-n <process name>] [-d <dir>]'
            sys.exit()
        elif opt in ("-n", "--process_name"):
            name = arg
        elif opt in ("-d", "--dir"):
            dir = arg
    if name == '':
        print "error:process name  must not be empty!!!"
        sys.exit()
    if dir == '':
        print "directory must not be empty!!!"
        sys.exit()

    out_dir = os.path.join("runner", "test_results", dir, "tool", "memory")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    start_memory_monitor(name, out_dir)


if __name__ == '__main__':
    main(sys.argv[1:])
