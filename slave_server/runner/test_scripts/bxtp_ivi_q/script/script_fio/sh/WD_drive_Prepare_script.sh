./fio --name=WD_FIO_WL_Test_matching_PRD --ioengine=psync --direct=0 --buffered=1 --size=100% --randrepeat=0 --fill_device=1 --norandommap --allow_mounted_write=1 --refill_buffers --log_avg_msec=1000 --group_reporting --filename=/dev/block/by-name/userdata
sleep 1
./fio --name=seq_write --rw=write --bs=4k --size=1024m --iodepth=128 --ioengine=psync --numjobs=32
sleep 10
