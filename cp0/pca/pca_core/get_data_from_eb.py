#!/bin/env python
import json
import re
import os
import json,time,datetime
from collections import OrderedDict
from pymongo import MongoClient, errors as mongo_error

try:
    DEV = 'cp0_dev' in os.environ
    if DEV:
        db_client = MongoClient(host='localhost', port=27017)
    else:
        db_client = MongoClient(host='localhost', port=27017, username='cp0_admin',password='Pw$g09e3')
except mongo_error:
    print mongo_error

CUR_DIR = os.path.abspath(__file__).strip(os.path.abspath(__file__).split('/')[-1])
# data_list_all = list()
# data_unit_dict = dict()

UNVALUABLE=['demo','stability_resume']

GAP_TIMESTAMP = 3600*24
def byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            byteify(key, ignore_dicts=True): byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


def get_list_average(val_list):
    sum = 0
    for item in val_list:
        sum += float(item)
    average = round(sum/len(val_list),3)
    return average

def daily_raw_data_eb(dir_path):
    value = ''
    unit = ''
    with open(dir_path, 'r') as fp:
        jsdata = json.load(fp, object_hook=byteify)
        # print jsdata.has_key('result')
        if jsdata.has_key('result'):
            items = jsdata.items()
            for key, val in items:
                # print case
                if key == 'result':
                    sobj = re.search(r'^[0-9\. ]*$',val)
                    if sobj:
                        value = val
                    break
        if jsdata.has_key('unit'):
            unit = jsdata['unit']
        fp.close()
    return value,unit

def list_str_to_float(value_list):
    temp_list  = list()
    for line in value_list:
        temp_list.append(float(line.strip().lstrip()))
    return temp_list

def get_med_value(value_list):
    med_val = 0.0
    vallen = len(value_list)
    temp_list = list()
    value_list = list_str_to_float(value_list)
    value_list.sort()
    # print value_list
    if vallen%2 == 0:
        temp_list.append(value_list[vallen/2])
        temp_list.append(value_list[(vallen / 2)-1])
        med_val = min(temp_list)
    else:
        med_val = value_list[vallen/2]
    return med_val

def excetion_case_name_normal(case_name):
    case_name = case_name.strip().lstrip()
    case_name = case_name.replace(' ','_')
    if 'fullboot' in case_name:
        case_name = case_name.replace(case_name,'full_boot')
    elif case_name.endswith('_m'):
        case_name = case_name.strip('_m')
    elif case_name.endswith('_o'):
        case_name = case_name.strip('_o')
    elif 'antutu_5.6_total_result' in case_name:
        case_name = case_name.replace(case_name, 'Antutu_5_6')
    elif 'RL_Benchmark_overall' in case_name or 'RL_benchmark_overall' in case_name:
        case_name = case_name.replace(case_name, 'Rlbench')
    elif 'bootanalyze_google' in case_name:
        case_name = case_name.replace(case_name, 'quick_boot')

    return case_name

def generate_json_timestamp_flag(json_file):
    if os.path.exists(json_file):
        now_time = int(time.time())
        timestamp = int(os.stat(json_file).st_mtime)
        if now_time - timestamp > GAP_TIMESTAMP:
            return True
        else:
            return False
    else:
        return True

def get_rawdata_from_build(dirname,data_json,unit_json):
    raw_data_path = data_json.strip(data_json.split('/')[-1])
    if not os.path.exists(raw_data_path):
        os.mkdir(raw_data_path)
    out_json_flag = generate_json_timestamp_flag(data_json)
    out_json_flag = out_json_flag and generate_json_timestamp_flag(unit_json)
    # print out_json_flag
    # out_json_flag = True
    if out_json_flag:
        flag_run_old = ''
        # print out_json_flag
        result_list = []
        unit_dict = {}
        for maindir, subdir, file_name_list in os.walk(dirname):
            # print maindir
            data_dict_eb = OrderedDict()
            jump_flag = False
            if len(file_name_list) == 1 and 'demo' in file_name_list[0]:
                jump_flag = True
            if not jump_flag:
                sobj=re.search(r'.*/raw/(?P<name>[0-9a-z_]+)$',maindir,re.I)
                if sobj and flag_run_old != sobj.group('name'):

                    build_name = sobj.group('name')
                    flag_run_old = build_name

                    case_file_list = list()

                    for spath in subdir:
                        for m,s,sl in os.walk(maindir+'/'+spath):
                            smobj = re.search(r'.*/raw/.*/\d+_\d+$',m)
                            if smobj:
                                case_file_list.extend(sl)
                                # case_path_list.append(smobj.group())
                    case_file_list = list(set(case_file_list))
                    case_list = []
                    for line in case_file_list:
                        ssobj = re.search(r'(?P<sname>.*)_\d',line,re.I)
                        if ssobj:
                            case_name = ssobj.group('sname')
                            if not '_trace' in case_name and not 'demo' == case_name and not case_name in case_list:
                                case_list.append(case_name)
                    temp_dict = OrderedDict()
                    for case in case_list:
                        unit = ''
                        temp_list = list()
                        for line in case_file_list:
                            # print line
                            if case in line:
                                # print line
                                for spath in subdir:
                                    # print sobj.group()
                                    # print spath
                                    path = sobj.group()+'/'+spath+'/'+line
                                    # print path
                                    if os.path.exists(path):
                                        # print path
                                        val,unit = daily_raw_data_eb(path)
                                        if val != '':
                                            # print val
                                            if 'full' in path and 'boot' in path:
                                                # print path
                                                # print val
                                                if float(val) > 7.0 and float(val) < 20.0:
                                                    temp_list.append(val)
                                            else:
                                                temp_list.append(val)
                        # print case,temp_list
                        name_obj = re.search(r'20\d+_[0-9a-z_]+',build_name,re.I)
                        if not name_obj:
                            if len(temp_list)>=3:
                                case = excetion_case_name_normal(case)
                                if unit != '':
                                    if not unit_dict.has_key(case):
                                        unit_dict[case] = unit
                                med_val = get_med_value(temp_list)
                                if med_val != 0.0:
                                    temp_dict[case] = med_val

                    if len(temp_dict)>0:
                        data_dict_eb[build_name] = temp_dict
                        result_list.append(data_dict_eb)


        with open(data_json, 'w+') as json_file:
            json.dump(result_list, json_file, ensure_ascii=False)
            json_file.close()

        with open(unit_json, 'w+') as json_file:
            json.dump(unit_dict, json_file, ensure_ascii=False)
            json_file.close()

def dailyweekly_raw_data(dir_path,data_unit_dict):
    # print dir_path
    data_dict = OrderedDict()
    sobj = re.search(r'.*\/(?P<name>\w+)\.m',dir_path,re.I|re.M)
    if sobj:
        name = sobj.group('name')
        data_dict[name]={}
        with open(dir_path) as fp:
            jsdata = json.load(fp)
            items = jsdata.items()
            for key,val in items:
                key = key.strip().lstrip().replace(' ', '_')
                if not 'demo' in key:
                    if not data_unit_dict.has_key(key):
                        if len(val['unit'])>0:
                            data_unit_dict[key] = val['unit']
                    if isinstance(val['result'],float):
                        # print key
                        if ('full' in key and 'boot' in key) or 'quick' in key:
                            if float(val['result']) > 7.0 and float(val['result']) < 20.0:
                                data_dict[name][key]= val['result']
                        else:
                            data_dict[name][key] = val['result']


    return data_dict,data_unit_dict


def get_rawdata_path(dir_path,data_json,unit_json):
    data_list_all = list()
    data_unit_dict = OrderedDict()
    # print data_json
    # print unit_json
    if os.path.exists(unit_json):
        with open(unit_json, 'r') as fp:
            data_unit_dict = json.load(fp, object_hook=byteify)
            fp.close()

    if os.path.exists(data_json):
        with open(data_json, 'r') as fp:
            data_list_all = json.load(fp, object_hook=byteify)
            fp.close()

    # print dir_path
    lslist = os.popen('ls '+ dir_path+'*.m')

    for filename in lslist:
        tmp,data_unit_dict = dailyweekly_raw_data(filename.strip(),data_unit_dict)
        if len(tmp) > 0:
            data_list_all.append(tmp)

    with open(data_json,'w+') as data_fpw:
        data_fpw.write(json.dumps(data_list_all))

    with open(unit_json,'w+') as unit_fpw:
        unit_fpw.write(json.dumps(data_unit_dict))

def get_mongo_data(data_json,unit_json):

    try:
        mongo_db = db_client.get_database('bxtp_ivi_o')
        data_list_all = list()
        data_unit_dict = OrderedDict()
        # if os.path.exists(unit_json):
        #     with open(unit_json, 'r') as fp:
        #         data_unit_dict = json.load(fp, object_hook=byteify)
        #         fp.close()
        #
        # if os.path.exists(data_json):
        #     with open(data_json, 'r') as fp:
        #         data_list_all = json.load(fp, object_hook=byteify)
        #         fp.close()
        data_dict = mongo_db.get_collection('raw').find({"test_tag": "pca_raw"})
        data_reog = dict()

        for sub_data in data_dict:
            result = str(sub_data["result"]).strip().lstrip()
            build = sub_data["build"]
            case_name = excetion_case_name_normal(sub_data["case_name"])
            if "Resume_time" in sub_data["case_name"]:
                if len(result.split(".")[0]) > 4:
                    continue
            if ( not "-" in sub_data["result"]) and (result.replace('.','').isdigit()):
                if not data_reog.has_key(sub_data["build"]):
                    # print '0'
                    data_reog[build] = dict()
                # print '1'
                if not data_reog[build].has_key(case_name):
                    data_reog[build][case_name] = dict()
                if not data_reog[build][case_name].has_key("value"):
                    data_reog[build][case_name]["value"] = list()
                data_reog[build][case_name]["value"].append(result)
                data_reog[build][case_name]["med_val"] = get_med_value(data_reog[build][case_name]["value"])
                if not case_name in data_unit_dict:
                    data_unit_dict[case_name] = sub_data["unit"]
        # print data_reog
        raw_items = data_reog.items()
        for key,val in raw_items:
            temp_dict = dict()
            temp_dict[key] = dict()
            # kk = map(lambda x:val[x]["med_val"], val.keys())
            # print kk
            for skey in val.keys():
                temp_dict[key][skey] = val[skey]["med_val"]
            # print temp_dict
            data_list_all.append(temp_dict)
        # print data_list_all
        with open(data_json, 'w+') as data_fpw:
            data_fpw.write(json.dumps(data_list_all))

        with open(unit_json, 'w+') as unit_fpw:
            unit_fpw.write(json.dumps(data_unit_dict))
    except Exception,e:
        print "error"
        print e


def regenerate_all_json_files(main_dir, data_json, unit_json, force_rewrite):
    out_json_flag = generate_json_timestamp_flag(data_json)
    out_json_flag = out_json_flag and generate_json_timestamp_flag(unit_json)
    # if force_rewrite:
    #     if os.path.exists(data_json):
    #         os.remove(data_json)
    #     if os.path.exists(unit_json):
    #         os.remove(unit_json)
    # print force_rewrite
    if force_rewrite or out_json_flag :
        get_mongo_data(data_json, unit_json)