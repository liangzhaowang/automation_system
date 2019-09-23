from cp0.lib import new_render
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.shortcuts import render, HttpResponse
import urllib2, base64
from collections import OrderedDict
import os
from pca_core.PCA import pca_calc
from pca_core.PCA import matrix_to_list
from pca_core.PCA import byteify
from pca_core.PCA import get_pca_raw_data_from_json
from functools import partial
from pymongo import MongoClient, errors as mongo_error
try:
    DEV = 'cp0_dev' in os.environ
    if DEV:
        db_client = MongoClient(host='localhost', port=27017)
    else:
        db_client = MongoClient(host='localhost', port=27017, username='cp0_admin',password='Pw$g09e3')
    mongo_db = db_client.get_database('bxtp_ivi_o')
except mongo_error:
    print mongo_error
import collections
import numpy as np
import time
CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def get_default_valIndex_list(len):
    vallist = list()
    for i in range(len):
        vallist.append(i)
    return vallist


def mat_string_to_float(mat_data):
    row_len = len(mat_data)
    col_len = len(mat_data.T)
    temp_mat = np.mat(np.ones((row_len, col_len)))
    for row in range(row_len):
        for col in range(col_len):
            temp_mat[row,col] = float(str(mat_data[row,col]))
    return temp_mat


def get_weight(feature_vector,feature_value,feature_vallist):
    feature_vector = np.mat(feature_vector)
    mat_len = len(feature_vector.T)

    val_mat = np.mat(np.ones((mat_len,1)))
    for i in range(0,mat_len):
        val_mat[i,0]=float(feature_value[i])
    #print val_mat,'\n'

    check_mat=np.zeros((1,mat_len))
    for i in range(0,len(feature_vallist)):
        check_mat[0,int(feature_vallist[i])]=1
    check_mat=np.ndarray.tolist(check_mat)[0]
    check_mat=np.diag(check_mat)
    #print check_mat,'\n'


    vec_mat = np.mat(np.ones((1, mat_len)))
    # print feature_value
    for item in feature_vector:
        vec_mat = np.vstack([vec_mat,item])
    vec_mat = np.delete(vec_mat, 0, axis=0)
    vec_mat = mat_string_to_float(vec_mat)
    #print vec_mat

    weight_sum = np.transpose(np.matmul(check_mat,vec_mat))
    #print '1',weight_sum
    weight_sum = np.matmul(weight_sum,val_mat)
    #print '2',weight_sum
    weight_sum = matrix_to_list(weight_sum)
    #print '3',weight_sum
    return weight_sum


def parse_raw_data(key,data_item):
    """
    :param key: case name
    :param data_item: iterable item
    :return:
    The temp[0] is eb number, temp[1] is the score of test case
    """
    temp = list()
    # print data_item
    eb = data_item.keys()[0]
    temp.append(eb)
    temp.append(data_item[eb].get(key))
    return temp


def pca_modify_data_configuration(request):
    if request.method == 'POST':
        try:
            ebNum = byteify(request.POST.get('ebNum'))
            modify_style = byteify(request.POST.get('modify_style'))
            if modify_style == "delete":
                filter_dict = {
                    'build': ebNum,
                    "test_tag": "pca_raw"
                }
                mongo_db.get_collection('raw').update(filter_dict,{'$set': {'test_tag': "pca_raw_delete"}}, multi=True)
            elif modify_style == "add":
                filter_dict = {
                    'build': ebNum,
                    "test_tag": "pca_raw_delete"
                }
                mongo_db.get_collection('raw').update(filter_dict,{'$set': {'test_tag': "pca_raw"}}, multi=True)

            get_pca_raw_data_from_json(force_rewrite=True)
            return JsonResponse({'success': True})
        except Exception, e:
            print e
            return JsonResponse({'success': False})

def get_eb_name_from_mongodb(filter):
    return list(set(map(lambda x: x["build"].encode('utf-8') if isinstance(x["build"], unicode) else x["build"], mongo_db.get_collection('raw').find({"test_tag": filter}))))

def pca_data_chart(request):
    try:
        data = OrderedDict()
        raw_data, unit = get_pca_raw_data_from_json(force_rewrite=True)
        keys = unit.keys()
        data['keys'] = unit.keys()
        data['raw'] = dict()
        delete_ebList = get_eb_name_from_mongodb("pca_raw_delete")
        pca_eb = get_eb_name_from_mongodb("pca_raw")
        pca_eb.sort()
        # pca_eb_dict = map(lambda x, y: {x: y},[x for x in xrange(len(pca_eb))], pca_eb)
        # print pca_eb_dict
        # print delete_ebList
        # print pca_eb
        data["delete_list"] = delete_ebList
        data["pca_list"] = pca_eb
        for key in keys:
            func = partial(parse_raw_data, key)
            data["raw"][key] = filter(lambda x: not str(x[1]) == "None", map(func, raw_data))

        return new_render(request, 'pca_data_chart.html', data, title='CP0', subtitle='PCA', wide=True)
    except Exception, e:
        print e
        return render_to_response('500.html')


def pca_index(request):
    data = OrderedDict()
    data['keys'] = get_pca_raw_data_from_json("unit", force_rewrite=True).keys()
    return new_render(request, 'pca_index.html', data, title='CP0', subtitle='PCA', wide=True)


def pca_data(request):
    if request.method == 'POST':
        caselist =  byteify(request.POST.getlist('case'))
        parseconf = byteify(request.POST.getlist('parseconf'))
    #print parseconf
    data = OrderedDict()
    pca = pca_calc(caselist,parseconf[0])

    data['correlation_matrix'] = pca.correlation_matrix
    data['count_mat'] = pca.count_mat
    # print pca.count_mat
    data['feature_vector'] = pca.feature_vector
    data['feature_val'] = pca.feature_val
    data['weight'] = get_weight(pca.feature_vector,pca.feature_val[0],get_default_valIndex_list(len(pca.keys)))
    data['collect_effict_data'] = pca.collect_effict_data
    data['keys'] = pca.keys
    data['len'] = len(pca.keys)
    data['coeffient'] = pca.coef_list
    #print pca.coef_list
    data['image_score'] = pca.image_score_show
    data['image_version'] = pca.image_version_show

    return new_render(request, 'pca_data.html', data, title='CP0', subtitle='PCA')


def html_list_to_pylist(hmtl_list):
    hmtl_list = hmtl_list[0]
    hmtl_list = hmtl_list.replace('[[', '')
    hmtl_list = hmtl_list.replace(']]', '')
    hmtl_list = hmtl_list.replace('], [', ';')
    # print hmtl_list
    return hmtl_list


def pca_val_data(request):
    if request.is_ajax() and request.method == 'POST':
        case_list = byteify(request.POST.getlist('case'))
        fea_vactor = byteify(request.POST.getlist('vactor'))
        fea_vactor = html_list_to_pylist(fea_vactor)
        fea_value = byteify(request.POST.getlist('values'))
        fea_value = fea_value[0].strip("'").lstrip("'").split(',')
        coef = byteify(request.POST.getlist('coefs'))
        keys = byteify(request.POST.getlist('keys'))[0]
        # print keys
        keys=keys.replace("['","").replace("']","").split("', '")

        fea_vactor = np.mat(fea_vactor)

    data = OrderedDict()
    data['casename'] = case_list
    # print case_list
    # weight = get_weight(fea_vactor,case_list)
    data['feature_vector'] = fea_vactor
    data['weight'] = get_weight(fea_vactor,fea_value,case_list)
    data['keys'] = keys
    data['coef'] = coef

    return new_render(request, 'pca_weight.html', data, title='CP0', subtitle='PCA')
