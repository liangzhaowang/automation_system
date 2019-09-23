#!/usr/bin/env python
def printsummary(itemList):
    print "------------------------------------"
    print "Summary:"
    print "stage                 time_cost(s)      ready_time_stamp(s)"
    #print itemList
    for item in itemList:
        if item[2] == '':
            print '{:25} {:5}'.format(item[0], item[1])
        else:
            print '{:25} {:15} {:15}'.format(item[0], item[1], item[2])
    print "------------------------------------"

def output_summary(slist):
    items = []
    tmp=[]
    for i in range(0,len(slist)-1):
        if slist[i][4] != '' and slist[i+1][4] == '':
            if float(slist[i][0]) == float(slist[i+1][0]):
                tmp= ['['+slist[i][2]+']',slist[i][4],slist[i][0]]
            else:
                tmp = ['['+slist[i][2]+'->'+slist[i+1][2]+']',float(slist[i+1][0])-float(slist[i][0]),'']
        elif slist[i][4] == '' and slist[i+1][4] != '':
            if slist[i][2] == slist[i+1][2]:
                tmp = ['['+slist[i+1][2]+']',slist[i+1][4],slist[i+1][0]]
        elif slist[i][4] == '' and slist[i+1][4] == '':
            tmp = ['['+slist[i][2]+'->'+slist[i+1][2]+']',float(slist[i+1][0])-float(slist[i][0]),'']
        else:
            tmp = []
        if items.count(tmp) == 0:
            items.append(tmp)
    printsummary(items)
#add by yuwei20161211
def get_summaryext(generateList):
    tmp = []
    for items in generateList:
        if items[3].lstrip().strip() == 'ready' or items[3].lstrip().strip() == 'start':
            tmp.append(list(items))
        elif items[2].lstrip().strip() == 'Pre-CSE':
            tmp.append(list(items))
#    print tmp
    output_summary(tmp)

#end by yuwei20161211
def get_summary(generateList):
    tmp = []
    isnext = False
    for items in generateList:
        if isnext:
            tmp.append(list(items))
            isnext = False
        if items[4] != '':
            tmp.append(list(items))
            isnext = True
    output_summary(tmp)

#add by yuwei@20161206  
