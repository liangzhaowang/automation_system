#!/usr/bin/python

import re
import sys
import csv

def analyze_ftrace(f):
    regexp = re.compile(".*-(\d+).*\((.*)\)")
    result = {}
    for line in f:
        m = regexp.search(line)
        if not m:
            continue
        pid = m.group(1)
        filename = m.group(2)
        if result.has_key(pid) and result[pid].has_key(filename):
            result[pid][filename] = result[pid][filename] + 1
        elif result.has_key(pid):
            result[pid][filename] = 1
        else:
            tmp={}
            tmp[filename] = 1
            result[pid] = tmp
    return result

def dump_to_csv_file(result):
    with open("result.csv", 'wb') as csvFile:
        writer = csv.writer(csvFile)
        line = ["PID", "Filename", "Times"]
        writer.writerow(line)
        sum=0
        total_sum=0
        for pid in result.keys():
            n = 1
            sum = 0
            for filename in result[pid].keys():
                sum = sum + result[pid][filename]
                if n is 1:
                    writer.writerow([pid, filename, result[pid][filename]])
                    n = 0
                else:
                    writer.writerow(["", filename, result[pid][filename]])
            writer.writerow(["sum", sum])
            writer.writerow("")
            total_sum = total_sum + sum
        writer.writerow(["totalsum", total_sum])
    return total_sum

result = analyze_ftrace(sys.stdin)
print dump_to_csv_file(result)
