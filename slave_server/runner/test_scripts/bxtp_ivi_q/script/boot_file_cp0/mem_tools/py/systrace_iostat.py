#!/usr/bin/python

# systrace for io stat
__author__ = ['"Chen, Tingjie": <tingjie.chen@intel.com>']

import sys
import os
import shutil
import getopt

BLK_SIZE = 512

CMD_READ_SING_BLK = 17
CMD_READ_MULTI_BLK = 18
CMD_WRITE_SING_BLK = 24
CMD_WRITE_MULTI_BLK = 25

io_dict = {}

io_name_dict = {}
io_name_dict[CMD_READ_SING_BLK] = 'READ_SINGLE_BLK'
io_name_dict[CMD_READ_MULTI_BLK] = 'READ_MULTI_BLK'
io_name_dict[CMD_WRITE_SING_BLK] = 'WRITE_SINGLE_BLK'
io_name_dict[CMD_WRITE_MULTI_BLK] = 'WRITE_MULTI_BLK'


def get_name_from_cmd(self, cmd):
	switch 

class io_property:
	def __init__(self):
		self.op_num = 0
		self.total_time = 0.0
		self.max_time = 0.0
		self.min_time = 0.0
		self.avg_time = 0.0
		self.total_wl = 0
		self.max_wl = 0
		self.min_wl = 0
		self.avg_wl = 0
		self.throughput = 0.0

	def new_operation(self, time, workload):
		self.op_num += 1
		self.total_time += time
		self.total_wl += workload
		
		if (time > self.max_time):
			self.max_time = time

		if (time < self.min_time) or (self.min_time == 0):
			self.min_time = time

		if (workload > self.max_wl):
			self.max_wl = workload

		if (workload < self.min_wl) or (self.min_wl == 0):
			self.min_wl = workload

	def get_throughput(self):
		if (self.op_num != 0):
			self.avg_wl = self.total_wl / self.op_num
			self.avg_time = self.total_time / self.op_num

		if (self.total_time != 0):
			self.throughput = self.total_wl / (self.total_time * 1024 * 1024)
		return self.throughput

def filter_str_path(path, startstr, finishstr):
	is_working = 0
	cur_start_ms = 0
	cur_finish_ms = 0
	cur_wl = 0
	cur_cmd = 0
	invalid_start_num = 0
	invalid_finish_num = 0

	io_dict[CMD_READ_SING_BLK] = io_property()
	io_dict[CMD_READ_MULTI_BLK] = io_property()
	io_dict[CMD_WRITE_SING_BLK] = io_property()
	io_dict[CMD_WRITE_MULTI_BLK] = io_property()

	if os.path.isfile(path):
		with open(path) as f:
			lines = f.readlines()
		for line in lines:
			if line.find(startstr) != -1:
				if (is_working != 0):
					invalid_start_num += 1
					continue
				is_working = 1
				cur_cmd = int(line.split('cmd=')[1].split(',addr=')[0])
				cur_wl = int(line.split('size=0x')[1].split('\\n')[0], 16) * BLK_SIZE
				cur_start_ms = line.split(']')[1].split(':')[0].split()[1]
			if line.find(finishstr) != -1:
				if (is_working == 0):
					invalid_finish_num += 1
					continue
				temp_cmd = int(line.split('cmd=')[1].split(',addr=')[0])
				if (cur_cmd != temp_cmd):
					invalid_finish_num += 1
					continue
				temp_wl = int(line.split('size=0x')[1].split('\\n')[0], 16) * BLK_SIZE
				if (cur_wl != temp_wl):
					invalid_finish_num += 1
					continue
				cur_finish_ms = line.split(']')[1].split(':')[0].split()[1]
				cur_time = float(cur_finish_ms) - float(cur_start_ms)
				if (cur_time < 0):
					print("Time duration < 0 ...")
					continue
				io_dict[cur_cmd].new_operation(cur_time, cur_wl)
				is_working = 0
	elif os.path.isdir(path):
		print("Please enter full filename!")
	print("invalid start:%d, invalid finish:%d\n" %(invalid_start_num, invalid_finish_num))
	return io_dict

def get_throughputs(iodict):

	for i in iodict:	
		print("%s:\n-----------------------------\nWORKLOAD: %f KB, TIME: %f S, OP_NUM: %d, THROUGHPUT: %f MB/S, \
			\nMAX_WORKLOAD: %d, MIN_WORKLOAD: %d, AVG_WORKLOAD: %d, MAX_TIME: %f, MIN_TIME: %f, AVG_WORKLOAD: %f\n" %(io_name_dict[i], \
			iodict[i].total_wl/1024, iodict[i].total_time, iodict[i].op_num, iodict[i].get_throughput(), \
			iodict[i].max_wl, iodict[i].min_wl, iodict[i].avg_wl, iodict[i].max_time, iodict[i].min_time, iodict[i].avg_time))


if __name__ == "__main__":
	opts, args = getopt.getopt(sys.argv[1:], "hp:")
	path = ''
	start_str = 'mmc_blk_rw_start'
	finish_str = 'mmc_blk_rw_end'
	for op, value in opts:
		if op == "-p":
			path = value
			print("Get file {0}".format(path))
			iodict = filter_str_path(path, start_str, finish_str)
			get_throughputs(iodict)
			sys.exit()
		elif op == "-h":
			print("Usage: python systrace_rw_filter.py -p YOUR_FULL_PATH_NAME")
			sys.exit()

