#!/bin/bash

org_file=$1
if [ -z $org_file ]
then
    echo "please input csv_file and title (optional) like:"
    echo "\t \"./plot.sh test.csv ["T-Rex OnScreen"]\""
    exit
fi

name=${org_file%%.*}
date=${name:0-20:20}
MAX=2500
Title="Benchmark CPU & GPU Freq"

if [ ! -z $2 ]
then
    echo "set title to " $2
    Title="$2"
    name=$Title$date
    File=$name".csv"
    mv $org_file $File
fi

Png=$name".png"
File=$name".csv"

gnuplot << eor
set terminal png large size 1600, 810 
set output '$Png'
set grid
set style data lines
set datafile separator ","
set title "$Title" font "Arial,25"
set xlabel "times"
set ylabel "freq"
set yrange [0:$MAX]
set xtics 2 rotate
set mxtics 1
set ytics 100
set mytics 50
plot "$File" u 1:2 w l t 'CPU0', "$File" u 1:3 title 'CPU1', "$File" u 1:4 title 'CPU2', "$File" u 1:5 title 'CPU3', "$File" u 1:6 lw 5 title 'CPU_MAX', "$File" u 1:7 lw 5 title 'GPU_ACT', "$File" u 1:8 lw 5 title 'GPU_REQ'
eor

