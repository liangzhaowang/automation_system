#!/bin/bash

adb_device=$1
adb_cmd=`which adb`
if [ -z $adb_device ]; then
    echo "no device keyin"
    adb_device=`$adb_cmd devices | sed '1d' | awk '{print $1}' | head -n1`
fi
adb_cmd="$adb_cmd -s $adb_device"

bindir=$2
echo $bindir
if [ -z $bindir ]; then
    echo "bindir empty"
    bindir="x86"
fi


$adb_cmd root
$adb_cmd wait-for-device
$adb_cmd remount
$adb_cmd wait-for-device

$adb_cmd push "bin/$bindir/busybox" /data/local/
#$adb_cmd push "bin/$bindir/debugfs" /data/local/
$adb_cmd push "bin/$bindir/debugfs.1.43.3" /data/local/debugfs
$adb_cmd push "bin/$bindir/libext2_ss.so" /system/lib64/libext2_ss.so

$adb_cmd shell 'ln -s /data/local/busybox /system/xbin/find'
$adb_cmd shell 'ln -s /data/local/busybox /system/xbin/stat'
$adb_cmd shell 'ln -s /data/local/debugfs /system/xbin/debugfs'

$adb_cmd shell 'echo 1 > /sys/kernel/debug/tracing/events/filemap/enable'
#$adb_cmd shell 'echo 1 > /sys/kernel/debug/tracing/events/mmc/enable'

./py/compulse_inodes.py $adb_device > inodes.txt
