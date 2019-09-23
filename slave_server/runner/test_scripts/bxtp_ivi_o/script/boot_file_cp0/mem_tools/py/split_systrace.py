#!/usr/bin/python

import sys
import re

SYSTRACE_LAUNCH_FILE="launching.txt"
SYSTRACE_PAGECACHE_FILE="pagecache.txt"

def split_systrace(f):
    reg_pagecache = re.compile('\d')
    launch_flag = 0
    start_time = 0
    end_time = 0
    with open(SYSTRACE_LAUNCH_FILE, 'w') as output_launching, open(SYSTRACE_PAGECACHE_FILE, 'w') as output_pagecache:
        for line in f:
            if launch_flag == 0:
                index = line.find("launching")
                if index <> -1:
                    launch_flag = 1
                    output_launching.write(line)
                    start_time = line.split(":")[0].split(" ")[-1]
#                    print start_time
                    continue
                else:
                    continue
            if launch_flag == 1:
                output_launching.write(line)
                index = line.find("mm_filemap_add_to_page_cache")
                if index <> -1:
                    output_pagecache.write(line)
                    continue
                index = line.find("launching")
                if index <> -1:
                    end_time = line.split(":")[0].split(" ")[-1]
#                    print end_time
                    break

    return float(end_time)-float(start_time)

print split_systrace(sys.stdin)

