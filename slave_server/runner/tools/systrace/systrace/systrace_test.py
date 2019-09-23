adb root
adb shell "echo 1 > /d/tracing/events/sync_trace/enable"
adb shell "echo 1 > /d/tracing/events/dma_fence/enable"
echo "Please input file_name:"
read file_name 
echo "please enter the time"
read time
systrace.py gfx input view webview wm am sm hal app res dalvik rs bionic power pm ss database sched irq i2c freq idle disk mmc load sync workq memreclaim binder_driver binder_lock pagecache -o ${file_name}.html -t ${time}
exit 0



./systrace.py gfx input view webview wm am sm hal app res dalvik rs bionic power pm ss database sched irq freq idle disk load workq memreclaim binder_driver binder_lock -o 111.html -t 30
