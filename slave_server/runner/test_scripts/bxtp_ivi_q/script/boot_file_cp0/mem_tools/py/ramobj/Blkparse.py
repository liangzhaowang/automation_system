import re
import os
import sys
from Inodes import *

BLKPARSE_CMD = 'blkparse -i mmcblk0.blktrace. -t | grep "179," | grep " [ACD] "'
BLKPARSE_LIVE_CMD = 'cat mmcblk0.blktrace.0 | blkparse -i - -t | grep "179," | grep " [ACD] "'
BLKPARSE_CAT_CMD = 'cat mmcblk0.blktrace.txt | grep "179," | grep " [ACD] "'

def create_dict_processes(filename):
    adict = {}
    with open(filename) as f:
        for line in f:
            pid, name = line.strip().split(' ')
            adict[int(pid)] = name
    return adict

def find_inode(dict_blocks, bdev, block):
    inode = -1
    if dict_blocks.has_key(bdev):
            inode = dict_blocks[bdev].get(block, -1)
    return inode

# It is assumed that /dev/block/mmblk0 has a major device number of 179
def translate_bdev(bdev):
    if bdev[0:4] == '179,':
        return '/dev/block/mmcblk0p' + bdev[4:]
    return bdev

# Ext2fs has blocks of 4096 bytes, while block device (eMMC) blocks are
# 512 bytes wide. Convert eMMC to Ext2 block number
def blk_abs2part(block):
    return block / 8

def create_operation(timestamp, op, rws, time_ns, inode, blockinpart, block, nbblocks, \
        bdev, pid, dict_inodes, dict_processes):
    pname = dict_processes.get(pid, '')
    if dict_inodes.has_key(bdev):
        filename = dict_inodes[bdev].get(inode, 'Unknown')
    else:
        filename = 'Unknown'
    io_op = { 'bdev' : bdev, 'timestamp' : timestamp, 'op' : op, \
                'time_ns' : time_ns, 'inode' : inode, 'blockinpart' : blockinpart, \
                'block' : block, 'nbblocks' : nbblocks, 'filename' : filename, \
                'pid' : pid, 'pname' : pname, 'rws': rws }
    return io_op

def blkparse(dict_files, dict_processes):
    regexp_op = re.compile('^\d+,\d +\d+ +\d+ +(\d+\.\d+) +(\d+) +(\w) +(\w+) +([^ ].*)$')
    regexp_op_add = re.compile('^(\d+) [+] (\d+) <- \((\d+,\d+)\) +(\d+)$')
    regexp_op_dispatch = re.compile('^(\d+) [+] (\d+) \( *(\d+)\)')
    regexp_op_complete = re.compile('^(\d+) [+] (\d+) \( *(\d+)\)')

    # Check which command to use
    if os.path.isfile("mmcblk0.blktrace.txt"):
        sys.stderr.write("File already generated, just read it...\n")
        out = os.popen(BLKPARSE_CAT_CMD).readlines()
    elif os.path.isfile("mmcblk0.blktrace.1"):
        sys.stderr.write("Using common blkparse options ...\n")
        out = os.popen(BLKPARSE_CMD).readlines()
    else:
        sys.stderr.write("Using blkparse live options (will take some time)...\n")
        out = os.popen(BLKPARSE_LIVE_CMD).readlines()

    current_inodes_bdev = {}
    current_inodes_blockinpart = {}
    current_inodes_pid = {}
    ops = []

    dict_inodes = dict_file_2_dict_inodes(dict_files)
    dict_blocks = dict_file_2_dict_blocks(dict_files)

    for line in out:
        m = regexp_op.search(line.strip())
        if not m:
            continue
        timestamp, pid, op, rws, cdr = \
            float(m.group(1)), int(m.group(2)), m.group(3), m.group(4), m.group(5)
        if op == 'A':
            m = regexp_op_add.search(cdr)
            if not m:
                continue
            block, nbblocks, bdev, blockinpart = \
                int(m.group(1)), int(m.group(2)), translate_bdev(m.group(3)), int(m.group(4))
            blockinpart = blk_abs2part(blockinpart)
            current_inodes_bdev['%d+%d' % (block, nbblocks)] = bdev
            current_inodes_blockinpart[block] = blockinpart
            current_inodes_pid[block] = pid
            continue
        if op == 'D':
            m = regexp_op_dispatch.search(cdr)
            if not m:
                continue
            block, nbblocks, time_ns = \
                int(m.group(1)), int(m.group(2)), int(m.group(3))
            inode = find_inode(dict_blocks, bdev, \
                                   current_inodes_blockinpart.get(block, -1))
            pid = current_inodes_pid.get(block, pid)
            io_op = create_operation(timestamp, 'D', rws, time_ns, inode, \
                    blockinpart, block, nbblocks, \
                    current_inodes_bdev.get('%d+%d' % (block, nbblocks),''), \
                    pid, dict_inodes, dict_processes)
            ops.append(io_op)
        if op == 'C':
            m = regexp_op_dispatch.search(cdr)
            if not m:
                continue
            block, nbblocks, time_ns = \
                int(m.group(1)), int(m.group(2)), int(m.group(3))
            inode = find_inode(dict_blocks, bdev, \
                                   current_inodes_blockinpart.get(block, -1))
            pid = current_inodes_pid.get(block, pid)
            io_op = create_operation(timestamp, 'C', rws, time_ns, inode, \
                    blockinpart, block, nbblocks, \
                    current_inodes_bdev.get('%d+%d' % (block, nbblocks), ''), \
                    pid, dict_inodes, dict_processes)
            ops.append(io_op)
            if current_inodes_bdev.has_key('%d+%d' % (inode, block)):
                current_inodes_bdev.pop('%d+%d' % (inode, block))
            if current_inodes_blockinpart.has_key(block):
                current_inodes_blockinpart.pop(block)
            if current_inodes_pid.has_key(block):
                current_inodes_pid.pop(block)
    return ops

