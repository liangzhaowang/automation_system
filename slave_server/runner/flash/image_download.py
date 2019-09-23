#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import commands
# -*- coding: utf-8 -*-

class Download:
	def __init__(self, *args):
		self._username = args[0]
		self._password = args[1]
		self.image_url = args[2]
		self.image_dir = args[3]
		self.image_zip = self.image_url.split("/")[-1]

	def download(self):
		print "|==========================================================================================================|"
		print "|-----------------------> Step 1 :: Downloading Android flashfile <----------------------------------------|"
		print "|==========================================================================================================|"
		print "start to download Image file %s from artifactory !" % self.image_zip.split(".")[0]
		image_log = commands.getoutput("wget --timeout 60 -t 30 --waitretry=1 --http-user={} --http-password={}  {} --directory-prefix={} --no-check-certificate ".format(self._username,self._password,self.image_url,self.image_dir))
		if self.image_zip in image_log and "100%" in image_log: 
			print "complete to download Image file %s !" % self.image_zip.split(".")[0]
			return self.image_dir + "/" + self.image_zip
		else:
			print "failed to download Image file %s !" % self.image_zip.split(".")[0]
		print image_log

	def delete(self):
		print "start to delete Image file %s from local !" % self.image_zip.split(".")[0]
		image_log = commands.getoutput("sudo rm -rf -v {} {}".format(self.image_dir + "/" + self.image_zip,self.image_dir+"/"+self.image_zip.split(".")[0]))
		if "removed ‘{}’".format(self.image_dir + "/" + self.image_zip) and "removed directory: ‘{}’".format(self.image_dir+"/"+self.image_zip.split(".")[0])in image_log:
			print "complete to delete Image file %s and %s !" % (self.image_zip,self.image_zip.split(".")[0])
			return
		else:
			print "failed to delete Image file %s !" % self.image_zip

#if __name__ == "__main__":
#     image = Download(sys_pmbot, vdwad92@, "https://mcg-depot.intel.com/artifactory/cactus-absp-jf/build/eng-builds/celadon/PSI/weekly/2019_WW19/cel_kbl/userdebug/cel_kbl-flashfiles-OC0000071.zip","/tmp/")
#     image.download()
    #image.delete()
