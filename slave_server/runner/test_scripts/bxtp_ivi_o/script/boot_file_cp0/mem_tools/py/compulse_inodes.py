#!/usr/bin/python

import os
import re
import sys

CMD_FILENAME = 'debugfs_cmd.txt'
DEBUGFS_CMD = 'debugfs'
PROP_MODEL = "ro.product.model"

# Will be populated by populate_automatically_partitions
partitions = { \
#    '/dev/block/mmcblk0p7' : '/system', \
#    '/dev/block/mmcblk0p0' : '/data', \
}

def exec_adb(cmd):
    adb_device=sys.argv[1]
    out = os.popen('adb -s %s %s' % (adb_device, cmd)).readlines()
    return map(lambda x: x.strip(), out)

def special_for_dm(mountpoint):
    cmd = "shell getprop %s" %(PROP_MODEL)
    lines = exec_adb(cmd)
    for line in lines:
        if line:
            model = line

    if model:
        cmd = "shell cat /fstab.%s" %(model)
        lines = exec_adb(cmd)
        regexp = re.compile('^(/dev/(disk|block)/[^ ]*) +(/[\w]+)\s')
        for line in lines:
            if line:
                m = regexp.search(line)
                if m:
                    resultpoint = m.group(3)
                    if (resultpoint == mountpoint):
                        bdev = m.group(1)
                        return bdev
    return None

def populate_automatically_partitions():
    parts = {}
    vparts = {}
    converted = {}
    lines = exec_adb('shell cat /proc/mounts')
    regexp = re.compile('^(/dev/(disk|block)/[^ ]*) +(/[\w]+)\s')
    regdm= re.compile('^(/dev/(disk|block)/dm\-\d+) +(/[\w]+)\s')
    for line in lines:
        m = regexp.search(line)
        m_dm = regdm.search(line)
        if m_dm:
            vdev = m.group(1)
            mountpoint = m.group(3)
            bdev = special_for_dm(mountpoint)
            if bdev:
                parts[bdev] = mountpoint
                vparts[bdev] = vdev
        elif m:
            bdev = m.group(1)
            mountpoint = m.group(3)
            parts[bdev] = mountpoint

    # hardcode for system_a
    bdev = "/dev/block/by-name/system_a"
    parts[bdev] = "/system"

    for part in parts.keys():
#        cmd = "shell stat -L -c %%T %s" %(part)
        cmd = "shell ls -l %s" %(part)
        #regexp = re.compile('\d+:\d+ [\w]+ \-> /dev/block/mmcblk0p(\d+)$')
        regexp = re.compile('\d+:\d+ .+ \-> /dev/block/mmcblk(\d+)p(\d+)$')
        lines = exec_adb(cmd)
        for line in lines:
            if line:
                #partnumber = line
                #bdev = "/dev/block/mmcblk0p%s" % int(partnumber,16)
                #converted[bdev] = parts[part]
                m = regexp.search(line)
                if m:
                    blk_no = m.group(1)
                    partnumber = m.group(2)
                    bdev = "/dev/block/mmcblk%sp%s" % (int(blk_no), int(partnumber))

        if partnumber:
            major = ""
            minor = ""
            start = ""
            size = ""
            dmpoint = None

            if vparts.has_key(part):
                dmpoint = vparts[part]

            #cmd = "shell /system/xbin/stat -L -c %%o %s" %(parts[part])
            cmd = "shell stat -c %%o %s" %(parts[part])
            regexp = re.compile('(\d+)$')
            lines = exec_adb(cmd)
            for line in lines:
                if line:
                    m = regexp.search(line)
                    if m:
                        bsize = line
        
            cmd = "shell cat /sys/block/mmcblk%s/queue/hw_sector_size" %(blk_no)
            regexp = re.compile('(\d+)$')
            lines = exec_adb(cmd)
            for line in lines:
                if line:
                    m = regexp.search(line)
                    if m:
                        ssize = line

            cmd = "shell cat /sys/block/mmcblk%s/mmcblk%sp%s/dev" %(blk_no, blk_no, partnumber)
            regexp = re.compile('(\d+):(\d+)$')
            lines = exec_adb(cmd)
            for line in lines:
                if line:
                    m = regexp.search(line)
                    if m:
                        major = m.group(1)
                        minor = m.group(2)
    
            cmd = "shell cat /sys/block/mmcblk%s/mmcblk%sp%s/start" %(blk_no, blk_no, partnumber)
            regexp = re.compile('(\d+)$')
            lines = exec_adb(cmd)
            for line in lines:
                if line:
                    m = regexp.search(line)
                    if m:
                        start = line
    
            cmd = "shell cat /sys/block/mmcblk%s/mmcblk%sp%s/size" %(blk_no, blk_no, partnumber)
            regexp = re.compile('(\d+)$')
            lines = exec_adb(cmd)
            for line in lines:
                if line:
                    m = regexp.search(line)
                    if m:
                        size = line
    
            converted[bdev] = (parts[part], major, minor, start, size, bsize, ssize, dmpoint)

    return converted

def get_partition_files_inodes(mount_point):
    files = {}
    regexp = re.compile('%s/(.*)-(\d+)$' % (mount_point))

    files_txt = exec_adb('shell \"find %s -type f -exec stat -c "%%n-%%i" {} \;\"' % (mount_point))
    for line in files_txt:
        m = regexp.search(line)
        if m:
            # workaround for system partition, since it's mmcblk points to /, but we only need info under /system
            if mountpoint == "/system":
                filename = mount_point + "/" + m.group(1)
            else:
                filename = m.group(1)
            files[filename] = { 'inode': int(m.group(2)), 'blocks': [] }
    return files

def get_partition_files(mount_point):
    files = exec_adb('shell find %s -type f' % (mount_point))
    files = map(lambda f: f[len(mount_point) + 1:], files)
    return files

def enrich_files_with_blocks(partition, files):
    cmd_file = open(CMD_FILENAME, 'w')
    cmd_file.write('open %s\n' % (partition))
    for f in files.keys():
        cmd_file.write('ex \"%s\"\n' % (f))
    cmd_file.write('close\n')
    cmd_file.close()
    exec_adb('push %s /mnt/asec/' % (CMD_FILENAME))
    extents_txt = exec_adb('shell %s -f /mnt/asec/%s ' % (DEBUGFS_CMD, CMD_FILENAME))

    regexp = re.compile('(\d+) *- *(\d+) +\d+$')
    current_filename = None
    debugfs_header = 'debugfs: ex '

    for line in extents_txt:
        if debugfs_header == line[0:len(debugfs_header)]:
            current_filename = line[len(debugfs_header)+1:len(line)-1]
            continue
        if current_filename == None:
            continue
        m = regexp.search(line)
        if m is not None:
            files[current_filename]['blocks'].append('%d-%d' % (int(m.group(1)), int(m.group(2))))
    cmd_file.close()
    os.remove(CMD_FILENAME)

def print_partition_files(blockdevice, dmpoint, mountpoint, major, minor):
    files = get_partition_files_inodes(mountpoint)
    # for debugfs, has to use dmpoing instead of blockdevice
    if dmpoint:
        enrich_files_with_blocks(dmpoint, files)
    else:
        enrich_files_with_blocks(blockdevice, files)
    for f in files.keys():
        # workaround for system partition, since it's mmcblk points to /, but we only need info under /system
        if mountpoint  == "/system":
            print '%s %s:%s \"%s\" %d %s' % (blockdevice,  major, minor, f, files[f]['inode'], ','.join(files[f]['blocks']))
        else:
            print '%s %s:%s \"%s/%s\" %d %s' % (blockdevice,  major, minor, mountpoint, f, files[f]['inode'], ','.join(files[f]['blocks']))

### MAIN
partitions = populate_automatically_partitions()
print 'Block_Device File Inode Blocks'
for info in partitions.iteritems():
    block_device = info[0]
    mountpoint = info[1][0]
    major = info[1][1]
    minor = info[1][2]
    start = info[1][3]
    size = info[1][4]
    bsize = info[1][5]
    ssize = info[1][6]
    dmpoint = info[1][7]
    print "%s %s %s:%s start=%s size=%s bsize=%s ssize=%s dmpoint=%s" %(block_device, mountpoint, major, minor, start, size, bsize, ssize, dmpoint)

for info in partitions.iteritems():
    block_device = info[0]
    mountpoint = info[1][0]
    major = info[1][1]
    minor = info[1][2]
    dmpoint = info[1][7]
    print_partition_files(block_device, dmpoint, mountpoint, major, minor)
