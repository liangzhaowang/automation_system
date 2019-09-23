#!/usr/bin/env python
# coding=utf-8

import os, sys
import logging.config
import logging
import time

class makelog():
	
	def __init__(self, filename="", filepath=""):
 		self.filename = filename
		self.filepath = filepath
		self.makelogfile()
		self.logger = logging.getLogger()
		self.write()

		
	def makelogfile(self):
		if(os.path.exists(self.filepath)):
			pass
			# cmd = 'gedit %s/%s'%(self.filepath, self.filename)
			# os.system(cmd)
		else:
			print self.filepath
			cmd = 'mkdir %s'%(self.filepath)
			os.system(cmd)
			self.makelogfile()

	def write(self):
		logging.basicConfig(filename =self.filepath + self.filename)
		self.logger.setLevel(logging.DEBUG)
		fh = logging.FileHandler(self.filepath + self.filename)
		fh.setLevel(logging.DEBUG)
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s")
		ch.setFormatter(formatter)
		fh.setFormatter(formatter)
		self.logger.addHandler(ch)
		self.logger.addHandler(fh)

file_path = "./log_info/"
file_name = "log_message_20170912_075156.txt"
print file_path
log_info = makelog(filepath = file_path, filename = file_name)
