#!/usr/bin/python

## dump_launchtime_pagenumber.py ##page_folder##

import os
import re
import sys
import csv
import string
import numpy as np

# trace_2-4-809.html
# trace_activity-com.facebook.katana_0_5_cold.html

RE_stress=re.compile("trace_([0-9-]+?)-(\d+)\.html")

apps={"1-1": "com.asus.browser", "1-2": "com.android.chrome", "1-3": "com.google.android.gm", "1-4": "com.google.android.youtube", "1-5": "com.google.android.music",
      "2-1": "com.google.android.videos", "2-2": "com.google.android.apps.maps", "2-3": "com.google.android.apps.photos", "2-4": "com.facebook.katana", "2-5":"com.google.android.apps.docs",
      "3-1": "com.asus.calendar", "3-2": "com.google.android.talk", "3-3": "com.asus.contacts", "3-4": "com.asus.email", "3-5": "com.asus.gallery",
      "4-1": "com.asus.filemanager", "4-2": "com.asus.music", "4-3": "com.android.settings", "4-4": "com.asus.supernote", "4-5": "com.asus.weathertime"}
map={}
outdir=sys.argv[1]

def main(RE):
    for filename in os.listdir(outdir):
        if re.search(RE_stress, filename):
#            print filename 
            app=re.search(RE, filename).group(1)
#            print app
            app_name=apps[app]
#            print app_name
            times=re.search(RE, filename).group(2)
            oldname=outdir+"/"+filename
            newname=outdir+"/trace_activity-"+app_name+"_0_"+times+"_stress.html"
            print oldname
            print newname
            os.rename(oldname, newname)
    
##### main #####
main(RE_stress)
print "html rename done!!"
