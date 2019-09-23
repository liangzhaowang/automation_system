from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import urllib2, base64
import json,time,datetime
import re
from cp0.lib import new_render
from cp0.lib import auth_header
from .merge_data_to_html import create_html_file_from_json
from metrix.models import Mdconfig
import os
import ssl
import random
import collections,requests
# rid = 'Y2hlbmM1eDpIRTdRZ2sjaA=='
import redis
rds = redis.Redis(host='localhost', port=6379)
rid = rds.get('auth_header')
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
GAP_TIMESTAMP = 3600*24*5
# Create your views here.
# query_type=1&project_id=1&device_id=62&dist_id=10&session_type_id=1
# http://10.239.97.183:8080/metrics/ajax_transaction/pnp_metrics/AjaxTrans_quickuse.jsp
# session_a=4816&session_b=4744&project_id=1&device_id=62&dist_id=10&session_type=1
# JIRA SEARCH
# project = "1Android Master" AND "Platform/Program" = Broxton-P AND status in (Open, "In Progress", Reopened, Pending, Triage) AND component in ("Power Management", PnP, System-KPI-Performance, System-KPI-Power) AND summary ~ KPIMETA ORDER BY priority, key

UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
HOUR_FORMAT = '%H%M'
OUT_FORMAT = '%d/%b/%g %I:%M %p'

class Test(object):
    cur_bug_count = 0
    def __init__(self, indicator_id, session_id,prev_session_id):
        self.indicator_id = indicator_id
        self.session_id = session_id
        self.prev_session_id = prev_session_id
        self.cur_bug = []
        self.sub_cur_bug = []
        self.bug_link = []
        self.prev_bug = []
        self.prev_link = []
        self.cur_bug_params = None

    def get_bg_data(self,result):
        bg_data = ''
        if self.positive == True and result >= self.target:
            bg_data = 'success'
        if self.positive == True and result < self.target:
            bg_data = 'danger'
        if self.positive == False and result >= self.target:
            bg_data = 'danger'
        if self.positive == False and result < self.target:
            bg_data = 'success'
        return bg_data

    def add_cur_result(self, result):
        if result == -1:
            self.cur_result = 'Blocked by '
            self.cur_bg = 'info'

        else:
            if result != 'N/A':
                self.cur_result = float(result)
                self.cur_bg = self.get_bg_data(self.cur_result)
            else:
                self.cur_result = result


    def add_prev_result(self, result):
        if result == -1:
            self.prev_result = 'Blocked by '
            self.prev_bg = 'info'

        else:
            if result != 'N/A':
                self.prev_result = float(result)
                self.prev_bg = self.get_bg_data(self.prev_result)
            else:
                self.prev_result = result


    def get_vstarget(self):
        if self.cur_result == 'Blocked by ' or self.cur_result == 'N/A':
            self.vstarget = 'N/A'
            self.absvstarget = 'None'
        else:
            k = 100
            if 'danger' in self.cur_bg:
                k = -100

            if self.target > 0:
                self.vstarget = str(round((self.cur_result - self.target) / self.target, 4) * k) + '%'
                self.absvstarget = round((self.cur_result - self.target) / self.target, 4) * k
            else :
                self.vstarget = 'N/A'
                self.absvstarget = 'None'

    def get_cur_vs_prev(self):
        if self.cur_result == 'Blocked by ' or self.cur_result == 'N/A' or\
                self.prev_result == 'Blocked by ' or self.prev_result == 'N/A':
            self.vs = 'N/A'
        else:
            k = 100
            if 'danger' in self.prev_bg:
                k = -100
            if self.prev_result == self.cur_result:
               self.vs = '=>'
            else:
               self.vs = str(round((self.cur_result - self.prev_result) / self.prev_result, 4) * k) + '%'

    def get_cur_build_name(self,build_dict):
        keys = build_dict.keys()
        cur_key = max(keys)
        return build_dict[cur_key]

    def set_build(self, dict_build):
        if self.session_id == '':
            self.build=self.get_cur_build_name(dict_build)
        else:
            self.build = dict_build[self.session_id]
    
    def set_prev_build(self, dict_build):
        #print self.prev_session_id
        try:
            self.prev_build = dict_build[self.prev_session_id]
        except Exception,e:
            print e

    def set_case(self, dict_case):
        # print dict_case
        # print self.indicator_id
        try:
            self.case = dict_case[self.indicator_id].strip()
        except Exception,e:
            self.case = []

    def set_priority(self,dict_priority):
        try:
            self.priority = dict_priority[self.indicator_id].strip()
        except Exception,e:
            self.priority = 'N/A'

    def set_target(self, unit, power, target):
        self.target = float(target[self.indicator_id])
        if power[self.indicator_id] == '+':
            self.positive = True
        else:
            self.positive = False
        self.target_display = str(target[self.indicator_id]) + ' ' + unit[self.indicator_id] + ' (' + power[self.indicator_id] + ')'

    def set_pvtarget(self, unit, power, pvtarget):
        self.pvtarget = float(pvtarget[self.indicator_id])
        self.pvtarget_display = str(pvtarget[self.indicator_id]) + ' ' + unit[self.indicator_id] + ' (' + power[self.indicator_id] + ')'

    def set_cur_rsd(self, rsd):
        self.cur_rsd = str(rsd * 100) + '%'

    def set_prev_rsd(self, rsd):
        self.prev_rsd = str(rsd * 100) + '%'

    def set_cur_bug(self, bug_dict,result_id):
        res_id = str(result_id)
        # print bug_dict.keys(),'-----',res_id
        if bug_dict.has_key(res_id):
            for item in bug_dict[res_id]:
                self.cur_bug.append(item['bugTitle'])
                self.cur_bug_params = ','.join(self.cur_bug)
                self.bug_link.append(item['bugLink'])


    def set_prev_bug(self, bug_dict,result_id):
        res_id = str(result_id)
        if bug_dict.has_key(res_id):
            for item in bug_dict[res_id]:
                self.prev_bug.append(item['bugTitle'])
                self.prev_bug_params = ','.join(self.prev_bug)
                self.prev_link.append(item['bugLink'])

    def get_remark(self, dict):
        if dict.has_key(self.indicator_id):
            self.remark = dict[self.indicator_id]

    def get_bug(self, dict):
        if dict.has_key(self.indicator_id):
            self.bug = dict[self.indicator_id]
        else:
            self.bug = ''

class Build(object):



    def __init__(self, id, name):
        self.id = id
        self.name = name


def compare(curt, prev):
    return (float(curt) - float(prev)) / prev

def init_sub_data_dict(key_list):
    out_data = collections.OrderedDict()
    for key in key_list:
        out_data[key] = []

    return out_data

def jira_utc2displaytime(date_time_str):
	"""jira UTCtime to display out time"""
	time_date_dict = {}
	robj = re.search(r'(?P<timestr>20\d+-\d+-\d+T\d+:\d+:\d+\.\d+)(?P<tflag>[-\+])(?P<toffset>\d+)',date_time_str,re.M|re.I)
	if robj:
		time_date_dict['tflag'] = robj.group('tflag')
		time_date_dict['toffset'] = robj.group('toffset')
		time_date_dict['timestr'] = datetime.datetime.strptime(robj.group('timestr'),UTC_FORMAT)
	if len(time_date_dict) == 0:
		return ''
	base_offset = datetime.datetime.strptime('0000',HOUR_FORMAT)
	toffset = datetime.datetime.strptime(time_date_dict['toffset'],HOUR_FORMAT)
	offset = toffset - base_offset
	if time_date_dict['tflag'] == '-':
		local_st = time_date_dict['timestr'] + offset
	else:
		local_st = time_date_dict['timestr'] - offset
	local_st = local_st.strftime(OUT_FORMAT)
	# print local_st
	return local_st

def get_sub_data_dict(data_dict,key_list):
    issuelk = collections.OrderedDict()
    out_data = init_sub_data_dict(key_list)
    fields_data = data_dict['fields']
    for key in key_list:
        if 'components' in key:
            for component_data in fields_data[key]:
                out_data[key].append(component_data['name'])
        elif 'issuelinks'in key:
            for il in fields_data[key]:
                if il.has_key('inwardIssue'):
                    il_list = []
                    il_list.append(il['type']['inward'])
                    il_list.append(il['inwardIssue']['fields']['summary'])
                    il_list.append(il['inwardIssue']['fields']['status']['name'])
                    il_list.append(il['inwardIssue']['fields']['status']['statusCategory']['colorName'])
                    issuelk[il['inwardIssue']['key']+'_inward'] = il_list[0:]

                elif il.has_key('outwardIssue'):
                    ol_list = []
                    ol_list.append(il['type']['outward'])
                    ol_list.append(il['outwardIssue']['fields']['summary'])
                    ol_list.append(il['outwardIssue']['fields']['status']['name'])
                    ol_list.append(il['outwardIssue']['fields']['status']['statusCategory']['colorName'])
                    issuelk[il['outwardIssue']['key']+ '_outward'] = ol_list[0:]
            out_data[key] = issuelk
        elif 'assignee' in key:
            if fields_data[key]:
                out_data[key] = fields_data[key]['displayName']
            else:
                out_data[key] = 'Unassigned'
        elif 'status' in key:
            out_data[key] = fields_data[key]['name']
            out_data['colorName'] = fields_data[key]['statusCategory']['colorName']
        elif 'priority' in key:
            out_data[key] = fields_data[key]['name']
        elif 'summary' in key:
            out_data[key] = fields_data[key]
        else:
            out_data[key] = jira_utc2displaytime(fields_data[key])
    # print out_data
    return out_data



def get_result_datajson(key,filedir):
    try:
        with open(filedir+"/resultdata/result_data" + key +".json", "r") as fpr:
            rawdata_json = json.loads(fpr.read())


    except Exception,e:
        print e
    return rawdata_json #output_result

def get_raw_data_filenamejson(filedir):
    data_dict = {}
    cmdliners = os.popen("ls "+filedir+"/resultdata/").read()
    filelist = cmdliners.split()
    for item in filelist:
        key = item[11:].split('.')[0]
        # print key
        tmp_result_dict = get_result_datajson(key,filedir)
        if not key in data_dict.keys():
            data_dict[key] = tmp_result_dict
        if tmp_result_dict['text'].has_key('issuelinks'):
            tmp_items = tmp_result_dict['text']['issuelinks'].items()
            for subkey,val in tmp_items:
                subkey = subkey.rstrip('_inoutward')
                if not subkey in data_dict.keys():
                    if 'Blocks' in val[0]:
                        continue
                    if 'Closed' in val[2]:
                        data_dict[subkey] = {}
                        data_dict[subkey]['text'] = val
                        if 'is blocked by' in val[0]:
                            data_dict[subkey]['parent'] = key
                        else:
                            data_dict[subkey]['parent'] = data_dict[key]['parent']


        #get_result_data(key)
    # print data_dict
    with open(filedir+"/result_total.json", "w+") as fpw:
        result_json = json.dumps(data_dict)
        fpw.write(result_json)



def get_sub_rawdata(filedir,key,parent_item,data_keylist = [],is_brother = False):
    # print "--------------------------------sub rawdata"
    blocks_c = 0
    # print key,"===========",data_keylist
    if not key in data_keylist:
        url = 'https://jira.devtools.intel.com/rest/api/2/issue/' + key + '?fields=summary,assignee,components,created,updated,status,issuelinks,priority'
        response = requests.get(url, timeout=30, verify=False, headers=auth_header()).content
        json_data = json.loads(response)
        # print "+++++++++++++++++++++++++++++++++++++sub add rawdata",key
        keyliststr = url.split('fields=')[-1]
        # print keyliststr
        if len(keyliststr) > 0:
            keylist = keyliststr.split(',')
            # print keylist
            if len(keylist) >= 1:
                output = get_sub_data_dict(json_data, keylist)
                out_dict = {}
                out_dict['text'] = output
                out_dict['parent'] = parent_item
                # print output
                with open(filedir + "/resultdata/result_data" + key + ".json", "w+") as fpw:
                    result_json = json.dumps(out_dict)
                    fpw.write(result_json)
                    fpw.close()
                if not 'Closed' in output['status'] and output.has_key('issuelinks'):
                    len_isslk = len(output['issuelinks'])
                    if len(output) > 0 and len_isslk > 0:
                        isslk_item = output['issuelinks'].items()
                        sub_child_blocks_item = ''
                        for subkey, summary in isslk_item:
                            is_sbrother = False
                            if 'is blocked by' in summary[0]:
                                sub_parent_item = key
                            else:
                                if parent_item != '':
                                    sub_parent_item = parent_item
                                else:
                                    sub_parent_item = ''
                                is_sbrother = True
                            if 'Blocks' in summary[0]:
                                out_dict = {}
                                out_dict['text'] = output
                                out_dict['parent'] = parent_item
                                del output['issuelinks'][subkey]
                                with open(filedir + "/resultdata/result_data" + key + ".json", "w+") as fpw:
                                    result_json = json.dumps(out_dict)
                                    fpw.write(result_json)
                                    fpw.close()
                                continue
                            if not "Closed" in summary:
                                    data_keylist.append(key)
                                    get_sub_rawdata(filedir, subkey.split("_")[0], sub_parent_item, data_keylist,is_sbrother)



# @cache_page(60 * 15)
def get_jira_raw_data(request,key):
    keyitem = key.split(":")
    filedir = keyitem[-1]
    keylist = keyitem[0].split(',')
    data_keylist = []
    out_dict = {}
    # result = []
    blocks_c = 0
    dirpath = CUR_DIR + "/tmp_data/"+filedir+'/'+keyitem[0].replace(",","_")
    if not os.path.exists(dirpath+'/'):
        os.makedirs(dirpath + "/resultdata/")
    else:
        os.system("rm " + dirpath +"/resultdata/*")
        os.system('rm ' + dirpath + '/result_*.json')
    # print "================1"
    # print keylist
    for item in keylist:
        url = 'https://jira.devtools.intel.com/rest/api/2/issue/' + item + '?fields=summary,assignee,components,created,updated,status,issuelinks,priority,created,updated'

        response = requests.get(url, timeout=30, verify=False, headers=auth_header()).content
        json_data = json.loads(response)

        keyliststr = url.split('fields=')[-1]
        # print keyliststr
        if len(keyliststr) > 0:
            keylist = keyliststr.split(',')
            # print keylist
            if len(keylist) >= 1:
                output = get_sub_data_dict(json_data, keylist)
                # print output,':::::::::',output.has_key('issuelinks')
                out_dict['text'] = output
                out_dict['parent'] = ''
                with open(dirpath + "/resultdata/result_data" + item + ".json", "w+") as fpw:
                    result_json = json.dumps(out_dict)
                    fpw.write(result_json)
                    fpw.close()
                if not 'Closed' in output['status'] and output.has_key('issuelinks'):
                    len_isslk = len(output['issuelinks'])
                    if len(output) > 0 and len_isslk > 0:
                        isslk_item = output['issuelinks'].items()
                        for subkey, summary in isslk_item:
                            if 'Blocks' in summary[0]:
                                del output['issuelinks'][subkey]
                                out_dict['text'] = output
                                out_dict['parent'] = ''
                                with open(dirpath + "/resultdata/result_data" + item + ".json", "w+") as fpw:
                                    result_json = json.dumps(out_dict)
                                    fpw.write(result_json)
                                    fpw.close()
                                continue
                            if not "Closed" in summary:
                                if 'is blocked by' in summary[0]:
                                    parent_item = item
                                else:
                                    parent_item = ''

                                data_keylist.append(item)
                                get_sub_rawdata(dirpath, subkey.split("_")[0], parent_item, data_keylist)


    get_raw_data_filenamejson(dirpath)
    return JsonResponse(output)



def get_base(text):
    return base64.b64encode(text)

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data

def get_tree_root_data_dict(data_dict_root = {}):
    data_dict = collections.OrderedDict()
    data_dict['container']="#custom-colored"
    data_dict['nodeAlign']="BOTTOM"
    data_dict['connectors'] = {}
    data_dict['connectors']['type'] = 'step'
    data_dict['node'] = {}
    data_dict['node']['HTMLclass'] = 'nodeExample1'
    data_dict_root['root'] = data_dict
    return data_dict_root

def get_tree_perant_data_dict(key,total,perant_data_dict={}):
    perant_data_dict['text'] = total[key]['text']
    return perant_data_dict

def get_perant_from_child(child,total):
    perant = ''
    subkeys = total.keys()
    if child in subkeys:
        # print "===========111"
        for item in total[child]["parent"]:
            # print item
            if item in subkeys:
                perant = item
                break

    return perant

def get_parent_from_child_ex(child,total):
    perant = ''
    subitems = total.items()
    for key,val in subitems:
        if child in val['child']:
            perant = key
            break
    return perant

def get_childname_from_parent(child,parent_id,total):
    sublink = total[parent_id]['text']['issuelinks']
    for item in sublink:
        if child in item:
            return item

def get_tree_child_data_node(child_key,total):
    child_dict = collections.OrderedDict()
    for child in child_key:
        # print child
        # print child_key
        child_data_dict = collections.OrderedDict()
        if total.has_key(child):
            # print child
            child_data_dict['text'] = total[child]['text']
            child_data_dict['parent'] = get_perant_from_child(child,total)
            child_data_dict['HTMLclass'] = total[child]['text']['colorName']
        else:
            child_data_dict['parent'] = get_parent_from_child_ex(child, total)
            child_name = get_childname_from_parent(child,child_data_dict['parent'],total)
            # print child_name
            child_data_dict['text'] = total[child_data_dict['parent']]['text']['issuelinks'][child_name]
            #child_data_dict['parent'] = get_perant_from_child(child,total)
            child_data_dict['HTMLclass'] = child_data_dict['text'][-1]
        child_dict[child] = child_data_dict
    # print "==================================================="
    # print child_dict
    return child_dict

def get_val_list(keylist):
    klist = []
    for item in keylist:
        klist += item
    return klist

def rewrite_brother_data(brother_data):
    sub_key_list = []
    items = brother_data.items()
    keys = brother_data.keys()
    vals = brother_data.values()
    # print keys
    # print vals
    out_brother_data = {}
    for key in keys:
        pass

    # sub_key_list += brother_data[key]

def examp(request,keys):
    keyitem = keys.split(':')
    filedir = keyitem[-1]
    key = keyitem[0].replace(',','_')
    create_html_file_from_json(key,filedir)
    return JsonResponse({"creat_html": "ok"})

def examp_templates(request,keys):
    return render(request, keys+'.html')

def rm_cache_tmpdata_from_server(nTimeStamp):
    cachels = os.popen('ls ' + '/var/tmp/django_cache/*').read().split()
    for item in cachels:
        timestamp = int(os.stat(item).st_mtime)
        if nTimeStamp - timestamp > GAP_TIMESTAMP/5:
            os.system("rm "+item)

def rm_templates_old_exmapshtml(nTimeStamp):
    exampsls = os.popen('ls ' + CUR_DIR + '/examp_templates/examps*.html').read().split()
    for item in exampsls:
        timestamp = int(os.stat(item).st_mtime)
        if nTimeStamp - timestamp > GAP_TIMESTAMP*12:
            os.system("rm "+item)


def rm_tmp_data_dir(out_dir,prev_label = ''):

    nTimeStamp = int(time.mktime(time.strptime(out_dir.lstrip(prev_label).rstrip(' 0123456789').rstrip('_'), '%Y%m%d_%H%M%S')))
    tmp_data_dirls = os.popen('ls -d ' + CUR_DIR + '/tmp_data/2*').read().split()
    tmp_data_dirls += os.popen('ls -d ' + CUR_DIR + '/tmp_data/searchTree_2*').read().split()
    for item in tmp_data_dirls:
        temp_item_dir = item.split('/')[-1].lstrip('').lstrip(prev_label)
        if temp_item_dir.count('_') == 1:
            itemtmp = item.split('/')[-1].lstrip('').lstrip(prev_label)
        elif temp_item_dir.count('_') == 2:
            itemtmp = item.split('/')[-1].lstrip('').lstrip(prev_label).rstrip('0123456789').rstrip('_')
        try:
            timeArray = time.strptime(itemtmp,"%Y%m%d_%H%M%S")
            timestamp = int(time.mktime(timeArray))
            if nTimeStamp - timestamp > GAP_TIMESTAMP:
                os.system("rm -rf "+item)
        except Exception,e:
            print "errors: %s"%e
    if not os.path.exists(CUR_DIR + "/tmp_data/"+out_dir):
        os.mkdir(CUR_DIR + "/tmp_data/"+out_dir)
    else:
        os.system("rm " + CUR_DIR + "/tmp_data/" + out_dir)
    if not os.path.exists(CUR_DIR + "/examp_templates/"):
        os.mkdir(CUR_DIR + "/examp_templates/")
    rm_templates_old_exmapshtml(nTimeStamp)
    # rm_cache_tmpdata_from_server(nTimeStamp)

def get_rqrmntId_for_rawdata(data_dict):
    rqrmntId_dict = {}
    if len(data_dict)>0:
        for item in data_dict:
            rqrmntId_dict[item['rqrmntId']]=item
    return rqrmntId_dict


#@cache_page(60 * 15)
def metrix_data(request):
    out_dir = time.strftime('%Y%m%d_%H%M%S')
    rdstr = random.random()
    out_dir += '_'+str(rdstr).split('.')[-1]
    content = {}
    attributes_key= ''
    # Default attributes
    url = 'https://metrix.sh.intel.com/sqe/ajax_transaction/metrix/req_report_data_twinbuilds.jsp'
    attributes = 'project=Android&device=BXTP%20IVI%20MRB&distro=1A%20O%20MR1&usergroup=PnP%20SQE&testcycle=Weekly&sessiona=0&sessionb=0'
    if request.is_ajax() and request.method == 'POST':
        post_dict = request.POST
        project = urllib2.quote(post_dict['project'])
        device = urllib2.quote(post_dict['device'])
        sessiona = urllib2.quote(post_dict['sessiona'])
        sessionb = urllib2.quote(post_dict['sessionb'])
        testcycle = urllib2.quote(post_dict['testcycle'])
        distro = urllib2.quote(post_dict['distro'])
        attributes_key = 'project='+project+'&device='+device+"&sessiona="+sessiona+"&sessionb="+ \
                         sessionb+"&testcycle="+testcycle+"&distro="+distro

    if attributes_key != '':
        attributes=attributes_key

    req = urllib2.Request('?'.join([url, attributes]))
    response = urllib2.urlopen(req,timeout=30, context = ssl._create_unverified_context())
    rawdata_dict = json.loads(response.read(),object_hook=_byteify)
    # data = open(CUR_DIR+'/34_33B.json', 'r').read()
    # rawdata_dict = json.loads(data,object_hook=_byteify)

    caselist_data = rawdata_dict[0]
    build_data = rawdata_dict[1]


    # BUILDS
    dict_build = {}
    # raw_data_builds = re.split('({.*?})', full_data[0].lstrip('[').rstrip(']'))
    for item in build_data:
        dict_build[item['build_id']] = item['buildNumber']
    dict_reqrmnt_id = rawdata_dict[-1]
    # CASES
    content['case_list'] = []
    content['cur_bug_count'] = 0
    dict_case = {}
    dict_unit = {}
    dict_power = {}
    dict_pv_target = {}
    dict_target = {}
    dict_priority = {}
    # raw_data_case = pattern_dict.findall(full_data[1].lstrip('[').rstrip(']'))
    for item in caselist_data:
        if dict_reqrmnt_id.has_key(str(item['reqrmnt_id'])):
            content['case_list'].append(item['reqrmnt_id'])
            dict_case[item['reqrmnt_id']] = item['indicName']
            dict_unit[item['reqrmnt_id']] = item['unit']
            dict_power[item['reqrmnt_id']] = item['power']
            dict_target[item['reqrmnt_id']] = item['targetValue']
            dict_priority[item['reqrmnt_id']] = item['priority']


    # CURRENT RESULT
    exp = []
    test_id_list = []
    raw_data_result_curt = rawdata_dict[2]#pattern_dict.findall(full_data[2].lstrip('[').rstrip(']'))
    raw_data_result_curt_dict = get_rqrmntId_for_rawdata(raw_data_result_curt)
    bug_dict = rawdata_dict[-4]

    # PREVIOUS RESULT
    raw_data_result_prev = rawdata_dict[3]#pattern_dict.findall(full_data[3].lstrip('[').rstrip(']'))
    raw_data_result_prev_dict = get_rqrmntId_for_rawdata(raw_data_result_prev)
    cur_build_id = ''
    prev_build_id = ''
    if len(raw_data_result_curt)>0:
        cur_build_id = raw_data_result_curt[0]['build_id']
    if len(raw_data_result_prev)>0:
        prev_build_id = raw_data_result_prev[0]['build_id']

    for item in caselist_data:
        if dict_reqrmnt_id.has_key(str(item['reqrmnt_id'])):
            curtmpdict={}
            prev_tmpdict={}
            if len(raw_data_result_curt_dict) > 0 and raw_data_result_curt_dict.has_key(item['reqrmnt_id']):
                curtmpdict = raw_data_result_curt_dict[item['reqrmnt_id']]

            if len(raw_data_result_prev_dict) > 0 and raw_data_result_prev_dict.has_key(item['reqrmnt_id']):
                prev_tmpdict = raw_data_result_prev_dict[item['reqrmnt_id']]

            test = Test(item['reqrmnt_id'], cur_build_id,prev_build_id)

            test.set_build(dict_build)
            test.set_prev_build(dict_build)
            test.set_case(dict_case)
            test.set_priority(dict_priority)
            test.set_target(dict_unit, dict_power, dict_target)
            if len(dict_pv_target) >0:
                test.set_pvtarget(dict_unit, dict_power, dict_pv_target)

            if len(curtmpdict) > 0:
                test.add_cur_result(curtmpdict['result_value'])
                test.set_cur_bug(bug_dict, curtmpdict['resultId'])
                test.set_cur_rsd(curtmpdict['rsd'])
            else:
                test.add_cur_result('N/A')
            if len(prev_tmpdict) > 0:
                test.add_prev_result(prev_tmpdict['result_value'])
                test.set_prev_bug(bug_dict, prev_tmpdict['resultId'])
                test.set_prev_rsd(prev_tmpdict['rsd'])
            else:
                test.add_prev_result('N/A')
            # test.get_remark(remark_dict)
            # test.get_bug(bug_dict)
            test.get_cur_vs_prev()
            test.get_vstarget()
            exp.append(test)

    content['data'] = sorted(exp, key=lambda Test: Test.absvstarget)
    content['title'] = 'Metrix'
    if len(exp) > 0:
        content['subtitle'] = exp[0].build
    content['outdir'] = out_dir
    return new_render(request, 'metrix.html', content,title='CP0', subtitle='METRIX')

def get_metrix_selection_menu_info(device=False,distro=False):
    url ='https://metrix.sh.intel.com/sqe/ajax_transaction/metrix/iamws_authorizations_endpoint_onestep.jsp'
    username = rid.decode('base64', 'strict').split(':')[0]
    data_d = {'user':'CCR\\'+username}
	
    re = requests.post(url, data=data_d, verify=False)
    raw_text = re.text.strip().lstrip()
    raw_json = json.loads(raw_text,object_hook=_byteify)
    data_dict = dict()
    data_dict['Mproject'] = raw_json[0].keys()
    data_dict['Muser'] = username
    if device:
        data_dict['Mdevice'] = dict()
        if distro:
            data_dict['Mdistro'] = dict()
        for key in raw_json[0].keys():
            data_dict['Mdevice'][key] = raw_json[0][key].keys()
            if distro:
                data_dict['Mdistro'][key] = dict()
                for skey in data_dict['Mdevice'][key]:
                    data_dict['Mdistro'][key][skey]=raw_json[0][key][skey]

    return data_dict

def metrix_index(request):
    prev_label = 'searchTree_'
    out_dir = prev_label+time.strftime('%Y%m%d_%H%M%S')
    rdstr = random.random()
    data_dict = get_metrix_selection_menu_info()
    out_dir += '_'+str(rdstr).split('.')[-1]
    data_dict['searchTree'] = out_dir
    # print data_dict
    rm_tmp_data_dir(out_dir,prev_label)
    return new_render(request, 'metrix_index.html',data_dict,title='CP0', subtitle='METRIX', wide=True)

def Metrix_Defualt_Config(request):
    def_proj = 'Android'
    def_dev = 'BXTP IVI MRB 8G'
    def_distro = '1A O MR1'
    project = ''
    dev = ''
    distro = ''
    if request.method == 'POST':
        def_obj = Mdconfig.objects.all()
        print def_obj
        print 'post'
        return JsonResponse(def_obj)
    elif request.method == 'GET':
        data_dict = get_metrix_selection_menu_info(device=True,distro=True)
        post_dict = request.GET
        # print post_dict
        project = post_dict['project']
        # print project
        if project == '' or not project in data_dict['Mproject']:
            if def_proj in data_dict['Mproject']:
                project = def_proj
            else:
                project = data_dict['Mproject'][0]

        try:
            object_md = Mdconfig.objects.get(project=project)
            print object_md
            dev = object_md.device
            if not dev in data_dict['Mdevice'][project]:
                dev = data_dict['Mdevice'][project][0]
            distro = object_md.distro
            if not def_distro in data_dict['Mdistro'][project][dev]:
                distro = data_dict['Mdevice'][project][dev][0]
        except Exception,e:
            if def_dev in data_dict['Mdevice'][project]:
                dev = def_dev
            else:
                dev = data_dict['Mdevice'][project][0]
            if def_distro in data_dict['Mdistro'][project][dev]:
                distro = def_distro
            else:
                distro = data_dict['Mdevice'][project][dev][0]
            if len(Mdconfig.objects.filter(project=project)) == 0:
                Mdconfig.objects.get_or_create(project=project,device=dev,distro=distro)
            else:
                if project != '' and distro != '' and dev != '':
                    Mdconfig.objects.filter(project=project).update(device=dev,distro=distro)
                else:
                    print e

        # print def_obj
        # print project,dev,distro
        # print 'get'
        return JsonResponse({'project':project, 'device':dev, 'distro':distro})
