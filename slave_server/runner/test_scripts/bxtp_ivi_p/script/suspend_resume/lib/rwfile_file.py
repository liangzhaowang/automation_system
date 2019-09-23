#!/usr/bin/env python

import os
import re
import sys

lines = []
re_str = [r"\[\d+;\d+.", r"\x1b", r"\x16", r"\x85", r"\xb0", r"\x04UUU", r"\x00", r"\r", r"\|[a-zA-Z0-9]+[\x08]+", r"\[\?..."]


def find_all_from_compile(lines, re_str):
    obj = re.compile(re_str)
    for i in range(0, len(lines)):
        lines[i] = lines[i].lstrip()
        find_list = obj.findall(lines[i])
        for item in find_list:
            lines[i] = lines[i].replace(item, '')
    return lines


def rewrite_file(infile_path, outfile_path):
    global lines
    try:
        with open(infile_path, 'r') as fp:
            lines = fp.readlines()
    except Exception, e:
        print e
    lines = lines[1:-1]
    for item in re_str:
        lines = find_all_from_compile(lines, item)
    with open(outfile_path, 'w+') as fp:
        fp.writelines(lines)


def main():
    out_dir = sys.argv[1]
    filename = sys.argv[2]
    rewrite_file(os.path.join(out_dir, filename+"_ttylog.txt"), os.path.join(out_dir, filename+"_outttylog.txt"))


if __name__ == "__main__":
    main()
