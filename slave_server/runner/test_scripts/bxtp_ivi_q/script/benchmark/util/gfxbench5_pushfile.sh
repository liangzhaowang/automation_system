#!/bin/bash

mem=`adb shell free | tr [:blank:] \\\n | grep [0-9] | sed -n '1p'`
echo `pwd`
if [ $mem -lt 2147483648 ]
then
echo 'push gfx data to 2G board.'
adb shell rm -r /storage/self/primary/Android/data/net.kishonti.gfxbench.gl.v50000.corporate/files/data/gfx
adb push runner/test_src/gfx/  /storage/self/primary/Android/data/net.kishonti.gfxbench.gl.v50000.corporate/files/data
fi