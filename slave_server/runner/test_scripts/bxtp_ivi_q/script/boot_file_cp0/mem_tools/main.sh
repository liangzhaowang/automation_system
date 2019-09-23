#!/bin/bash

map={}
indir=$1
outdir=$1/../page_folder/
mkdir $outdir

python html_name_rule.py $1

for i in `ls "$1"`
do

# Find app launch time in ftrace file, filter page cache related lines
launch_time=`cat "$1/$i" | ./py/split_systrace.py`

#num1=`echo $i | awk -F "-" '{print $1}' | awk -F "_" '{print $2}'`
#num2=`echo $i | awk -F "-" '{print $2}'`
#num3=`echo $i | awk -F "-" '{print $3}' | awk -F "." '{print $1}'`

# Add file path according to inode information in ftrace
cat pagecache.txt | ./py/ftraces_enrich_inodes_with_filenames.py > pagecache_enriched.txt

# Analyze pagecache information and dump to csv file
page_number=`cat pagecache_enriched.txt | ./py/analyze_page_cache_ftrace.py`
output=$i-launch_time-$launch_time-page_number-$page_number.csv

mv result.csv $outdir/$output

done

# Analyze IO performance
# ./py/systrace_iostat.py -p launching.txt
