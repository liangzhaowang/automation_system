#!/usr/bin/python
# Goal: enrich a ftrace.txt with filenames
#       The filename/inode/block_device matrix should have been previously
#       generated into FILE_INODES in lines in the standard format, one
#        for each file:
#       <Block_device> <Filename> <Inode number> <Blocks list>
# Usage:
#       cat ftrace.txt | ./$0
import re
import sys
from ramobj.Inodes import *

FILE_INODES = 'inodes.txt'

def enrich_ftrace(dict_inodes, dict_dev, f):
    regexp = re.compile('.*dev ([^ ]*):([^ ]*) ino ([^+]*) .* .* ofs=([0-9]*)')
    for line in f:
        if line[0] == '#':
            continue
        m = regexp.search(line)
        major = m.group(1)
        minor = m.group(2)
        inode = int(m.group(3), 16)
        filename = 'unknown'
        bdevice = ""
        for bd in dict_dev.keys():
            if dict_dev[bd]['major'] == major and dict_dev[bd]['minor'] == minor:
                bdevice = bd 

        if dict_inodes.has_key(bdevice) and dict_inodes[bdevice].has_key(inode):
            filename = dict_inodes[bdevice][inode]
        print '%s %d(%s)' % (line.strip(), inode, filename)

dict_files = create_dict_files(FILE_INODES)
dict_inodes = dict_file_2_dict_inodes(dict_files)
dict_dev = dict_file_2_dict_dev(dict_files)
enrich_ftrace(dict_inodes, dict_dev, sys.stdin)
