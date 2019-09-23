#!/bin/sh

adb wait-for-device
adb root
adb wait-for-device
adb remount
adb wait-for-device

CORE=4
now=$(date +"%m_%d_%Y_%H_%M_%S")
File="out_cpu_gpu_cur_"$now".csv"
inter=","
echo "no"$inter"cpu0"$inter"cpu1"$inter"cpu2"$inter"cpu3"$inter"cpu_max"$inter"gpu_act"$inter"gpu_req" > $File

no=0
while true 
do
    echo -n $no$inter | tee -a $File
    no=$((no+1))

    i=0
    max=0
    while [ $i -lt $CORE ]
    do
        cpu_cur="/sys/devices/system/cpu/cpu"$i"/cpufreq/scaling_cur_freq"
        freq=`adb shell "cat $cpu_cur" | grep -o '[0-9]\+'`
        freq=$(($freq/1000))
        if [ $freq -gt $max ]
        then
            max=$freq
        fi
        echo -n $freq$inter | tee -a $File 
        i=$((i+1))
    done
    echo -n $max$inter | tee -a $File

    gpu_node="/d/dri/0/i915_frequency_info"
    act_freq=`adb shell cat $gpu_node | grep "Actual freq"  | grep -o '[0-9]\+'`
    req_freq=`adb shell cat $gpu_node | grep "Current freq" | grep -o '[0-9]\+'`
    echo -n $act_freq$inter | tee -a $File 
    echo $req_freq | tee -a $File 
    sleep 0.1
done
