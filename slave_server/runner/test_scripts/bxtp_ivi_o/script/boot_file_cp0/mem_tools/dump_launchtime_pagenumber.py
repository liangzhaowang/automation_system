#!/usr/bin/python

## dump_launchtime_pagenumber.py ##page_folder##

import os
import re
import sys
import csv
import string
import numpy as np

RE_init=re.compile("trace_(activity\S+)_\d+_\d+_init\.html\-launch_time\-(\d+\.\d+)\-page_number\-(\d+).csv")
RE_cold=re.compile("trace_(activity\S+)_\d+_\d+_cold\.html\-launch_time\-(\d+\.\d+)\-page_number\-(\d+).csv")
RE_stress=re.compile("trace_(activity\S+)_\d+_\d+_stress\.html\-launch_time\-(\d+\.\d+)\-page_number\-(\d+).csv")

map={}
outdir=sys.argv[1]
result_init=outdir+"/../result_data/launchtime_pagecache_init.csv"
result_cold=outdir+"/../result_data/launchtime_pagecache_cold.csv"
result_stress=outdir+"/../result_data/launchtime_pagecache_stress.csv"

def main(RE, result):
    for filename in os.listdir(outdir):
        if re.search(RE, filename):
#            print filename 
            app_name=re.search(RE, filename).groups(1)[0]
#            print app_name
            launch_time=re.search(RE, filename).groups(1)[1]
            page_number=re.search(RE, filename).groups(1)[2]
            if map.has_key(app_name):
                map[app_name].append((launch_time, page_number))
            else:
                map[app_name]=[(launch_time, page_number)]
    
    with open(result, 'wb') as csvFile:
        writer = csv.writer(csvFile)
        title="APP,"+ "max_t,min_t,avg_t,len_t" + ",max_p,min_p,avg_p,len_p"
        writer.writerow(title.split(','))
        isFileEmpty = False
        for app_name in map.keys():
            tmp=[]
            page=[]
            info=""
            infop=""
            infot=""
            for item in map[app_name]:
                if item[1] <> "0":
                    infot=infot+","+item[0]
                    infop=infop+","+item[1]
                    tmp.append(float(item[0]))
                    page.append(float(item[1]))
                else:
                    infot=infot+","
                    infop=infop+","
                    #print app_name + " "+  item[0]+" "+ item[1]
            if len(tmp)>0:
                maxv=str(max(tmp))
                minv=str(min(tmp))
                avg=str(np.array(tmp).mean())
                lenv=str(len(tmp))
                pmaxv=str(max(page))
                pminv=str(min(page))
                pavg=str(np.array(page).mean())
                plenv=str(len(page))
    
                info=app_name+","+maxv+","+minv+","+avg+","+lenv+","+pmaxv+","+pminv+","+pavg+","+plenv+","+infot
                writer.writerow(info.split(','))
                info=app_name+","+","+","+","+","+","+","+","+","+infop
                writer.writerow(info.split(','))
                isFileEmpty = True
    if not isFileEmpty:
        os.remove(result)

##### main #####
main(RE_init, result_init)
print "init parsing done!!"
map={}
main(RE_cold, result_cold)
print "cold parsing done!!"
main(RE_stress, result_stress)
print "stress parsing done!!"
