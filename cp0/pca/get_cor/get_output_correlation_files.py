#!/bin/env python
import json
import re
import os
# import math
import numpy
import xlwt
from collections import OrderedDict
from numpy import *

# data_normal = []
# data = []
# unit = OrderedDict()
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
REMOV_UNIT=['3DMark_total_score','Geekbench_Score','GLbench_T-Rex_HD_C24Z16_onscreen','Gfx_manhattan_offscreen','Gfx_manhattan_onscreen','GLbench_T-Rex_HD_C24Z16_offscreen','Resume_time_manual','ST_PERF_Cold_boot_to_Android_UI','ST_PERF_Cold_boot_to_splash_screen','ST_PERF_Cold_boot_to_animation','eavb_avbaudio_time']
data_json_path = '/../raw_data/data_json.json'
unit_json_path = "/../raw_data/unit_json.json"

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


class correlation_rawdata(object):
    def load_json_file(self):
        self.data_normal = list()
        self.unit = OrderedDict()

        with open(CUR_DIR + data_json_path, 'r') as json_file:
            self.data_normal = json.load(json_file, object_hook=byteify)
            json_file.close()
        with open(CUR_DIR + unit_json_path, 'r') as json_file:
            self.unit = json.load(json_file, object_hook=byteify)
            for key in REMOV_UNIT:
                if self.unit.has_key(key):
                    del self.unit[key]
            self.keys = self.unit.keys()
            json_file.close()

    def cov(self,i, a):
        sum = 0
        sum_i = 0
        sum_a = 0
        data = xlwt.Workbook()
        table = data.add_sheet('correlation')
        table.write(0, 0, 'build_name')
        table.write(0, 1, i+'__'+a+'_average')
        table.write(0, 2, i+'_rawdata')
        table.write(0, 3, a+'__'+i+'_average')
        table.write(0, 4, a + '_rawdata')
        count = 1
        for daily in self.data_normal:
            items = daily.items()
            for date, date_val in items:
                if (daily[date].has_key(i) and daily[date].has_key(a)):
                    temp1 = daily[date][i] - self.case_average_normal[i+'__'+a]
                    temp2 = daily[date][a] - self.case_average_normal[a+'__'+i]
                    table.write(count, 0, date)
                    table.write(count, 1, self.case_average_normal[i+'__'+a])
                    table.write(count, 2, daily[date][i])
                    table.write(count, 3, self.case_average_normal[a+'__'+i])
                    table.write(count, 4, daily[date][a])
                    count += 1
        data.save(self.excl_path + '/' + str(i) + '__' + str(a) + '.xls')

    def cov_new2(self,i, a):
        # if i != a:
        data_old_i = -1.0
        data_old_a = -1.0
        temp1 = 0
        temp2 = 0
        data = xlwt.Workbook()
        table = data.add_sheet('correlation')
        table.write(0, 0, 'build_name')
        table.write(0, 1, i + '_diff')
        table.write(0, 2, a + '_diff')
        count = 1
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                if data_old_i == -1.0 and data_old_a == -1.0 and (daily[date].has_key(i) and daily[date].has_key(a)):
                    data_old_i = daily[date][i]
                    data_old_a = daily[date][a]
                    table.write(count, 0, date)
                    table.write(count, 1, temp1)
                    table.write(count, 2, temp2)
                    count += 1
                elif data_old_i != -1.0 and data_old_a != -1.0 and (daily[date].has_key(i) and daily[date].has_key(a)):
                    # print "elif is ok !!!"
                    temp1 = daily[date][i] - data_old_i
                    temp2 = daily[date][a] - data_old_a
                    data_old_i = daily[date][i]
                    data_old_a = daily[date][a]
                    table.write(count, 0, date)
                    table.write(count, 1, temp1)
                    table.write(count, 2, temp2)
                    count += 1

        data.save(self.excl_path +'/'+ str(i)+'__'+ str(a) + '.xls')

    def init_dict(self):
        self.excl_path = CUR_DIR+'/../excls'
        self.case_count = OrderedDict()
        self.case_sum = OrderedDict()
        self.case_average = OrderedDict()
        self.case_average_normal = OrderedDict()
        self.unit_stadiv = OrderedDict()
        self.unit_count = OrderedDict()
        self.unit_average = OrderedDict()
        if not os.path.exists(self.excl_path):
            os.mkdir(self.excl_path)
        else:
            print self.excl_path
            os.system('rm '+self.excl_path+'/*')

        for case in self.unit:
            self.case_count[case] = 0.0
            self.case_sum[case] = 0.0
            self.case_average[case] = 0.0
            self.case_average_normal[case] = 0.0

        for case,val in self.unit.items():
            if not self.unit_stadiv.has_key(val):
                self.unit_stadiv[val] = 0.0
                self.unit_count[val] = 0.0
                self.unit_average[val] = 0.0


    def average(self):
        # print 'average--------------------------------------'
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date,date_val in items:
                for case in self.keys:
                    if date_val.has_key(case):
                        self.case_count[case]+=1
                        self.case_sum[case]+=round(float(daily[date][case]),3)

        for case,val in self.case_average.items():
            self.case_average[case]=round(self.case_sum[case]/self.case_count[case],3)
            self.unit_average[self.unit[case]] += self.case_average[case]
            self.unit_count[self.unit[case]] += 1

        for Unit in self.unit_average:
            self.unit_average[Unit] = round(self.unit_average[Unit]/self.unit_count[Unit],3)
        # print self.case_average



    def reverse(self):
        # print'reverse------------------'
        i = 0
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date,date_val in items:
                for case in self.keys:
                    if ((self.unit[case] == 'sec') or (self.unit[case] == 'msecs')):
                        # print 'unit[case] ==',self.unit[case]
                        if self.data_normal[i][date].has_key(case):
                            self.data_normal[i][date][case] = self.case_average[case]-(daily[date][case]-self.case_average[case])
            i += 1
        # print self.data_normal

    def difference_set(self):
        keys = self.unit.keys()
        for key in REMOV_UNIT:
            keys.remove(key)
        return keys

    def get_effict_data(self,input_mat,matrix_row_num,t_flag = False):
        # print "-----------------------------------------"
        if t_flag:
            out_mat = mat(ones((1, matrix_row_num)))
        else:
            out_mat = mat(ones((1,matrix_row_num))).T
        for index in self.collect_effict_data:
            out_mat=numpy.insert(out_mat,len(out_mat.T),values=input_mat[:,index].T,axis=1)

        out_mat = numpy.delete(out_mat,0,axis=1)

        for index in self.fault_data:
            out_mat=numpy.insert(out_mat,len(out_mat.T),values=input_mat[:,index].T,axis=1)

        return out_mat



    def reverse_feature_vector(self):
        temp_list = sum(self.V, 0).tolist()
        i = 0
        for sd in temp_list[0]:
            # print sd
            if sd < 0:
                self.V[:,i] *= -1
                # self.A[0,i] *= -1
            i += 1
        # print self.V

    def get_each_average_for_case(self,i,a):
        i_list = list()
        a_list = list()
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                if (daily[date].has_key(i) and daily[date].has_key(a)):
                    i_list.append(daily[date][i])
                    a_list.append(daily[date][a])
        tempi = numpy.average(numpy.array(i_list))
        tempa = numpy.average(numpy.array(a_list))

        return tempi,tempa


    def output_each_average_for_case(self):
        for case_i in self.keys:
            for case_a in self.keys:
                self.case_average_normal[case_i+'__'+case_a],self.case_average_normal[case_a+'__'+case_i]=self.get_each_average_for_case(case_i,case_a)

        # for key,val in self.case_average_normal.items():
        #     print key,val


    def get_correlation_rawdata_main(self):
        self.output_each_average_for_case()
        # print 'PCA-----------------------------------'
        matrix_row_num=len(self.unit)
        count_cov = mat(ones((matrix_row_num,matrix_row_num)))
        Cov= mat(ones((matrix_row_num,matrix_row_num)))
        # print Cov
        i=-1

        for case_i in self.keys:
            for case_a in self.keys:
                # self.cov_new2(case_i,case_a)
                self.cov(case_i,case_a)



    def __init__(self,current_list = []):
        self.load_json_file()
        if len(current_list) > 0:
            tmp_dict = OrderedDict()
            # print self.unit
            for key in current_list:
                # print key
                tmp_dict[key] = self.unit[key]
            self.unit = tmp_dict
            self.keys = self.unit.keys()
        self.init_dict()
        self.average()
        self.reverse()
        # print self.data_normal
        self.get_correlation_rawdata_main()


get_cor = correlation_rawdata()