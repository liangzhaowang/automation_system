#!/bin/env python
import json
import re
import os
# import math
import numpy
from collections import OrderedDict
from numpy import *

from get_data_from_eb import regenerate_all_json_files
from pcaLib import *
import numpy as np
from compiler.ast import flatten

# from get_data_from_eb import get_rawdata_from_build

# data_normal = []
# data = []
# unit = OrderedDict()
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
REMOV_UNIT = ['3DMark_total_score', 'Geekbench_Score', 'GLbench_T-Rex_HD_C24Z16_onscreen', 'Gfx_manhattan_offscreen',
              'Gfx_manhattan_onscreen', 'GLbench_T-Rex_HD_C24Z16_offscreen', 'Resume_time_manual',
              'ST_PERF_Cold_boot_to_Android_UI', 'ST_PERF_Cold_boot_to_splash_screen', 'ST_PERF_Cold_boot_to_animation',
              'eavb_avbaudio_time', 'eavb', 'cold_boot_to_audio', "GFX5_openGL_high", "gallery_imge_list",
              "GFX5_openGL_normal", "GFX5_openGL_Car_Chase", "GFX5_openGL_Manhattan31_1080_offscreen",
              "GFX5_openGL_Manhattan311_1440_offscreen", "GFX5_openGL_gl_manhattan_wqhd_off", "GFX5_openGL_Manhattan",
              "GFX5_openGL_Manhattan31", "GFX5_openGL_high_off", "GFX5_openGL_normal_off", "Resume_time"]
data_json_path = '/../raw_data/data_json.json'
unit_json_path = "/../raw_data/unit_json.json"


def byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            byteify(key, ignore_dicts=True): byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


def get_pca_raw_data_from_json(data_type="", force_rewrite=False):
    """
    :param force_rewrite: force rewrite json file
    :param data_type: 'unit','raw',""(the default is none)
    :return: get the keys dictionary from units json file, or return raw data dictionary from data json file,
            or return both of them.
    """
    raw_data = list()
    unit = OrderedDict()
    if force_rewrite:
        regenerate_all_json_files(CUR_DIR + '/../../data/data/bxtp_ivi_o', CUR_DIR + data_json_path,
                                  CUR_DIR + unit_json_path, force_rewrite)
    if not data_type == 'unit':
        with open(CUR_DIR + data_json_path, 'r') as json_file:
            raw_data = json.load(json_file, object_hook=byteify)
            json_file.close()

    if not data_type == 'raw':
        with open(CUR_DIR + unit_json_path, 'r') as json_file:
            unit = json.load(json_file, object_hook=byteify)
            for key in REMOV_UNIT:
                if unit.has_key(key):
                    del unit[key]
            json_file.close()

    if len(raw_data) > 0 and len(unit) > 0:
        return raw_data, unit
    elif len(raw_data) > 0:
        return raw_data
    elif len(unit):
        return unit


def matrix_to_list(cov, t_flag=False):
    m_list = list()
    # print cov
    if t_flag:
        cov = cov.T
    s_list = cov.tolist()
    # print s_list
    for line in s_list:
        for i in range(len(line)):
            temp_float = float(line[i])
            if isinstance(temp_float, (float)):
                line[i] = '{:.4f}'.format(temp_float)

        m_list.append(line)

    return m_list


class pca_calc(object):
    def load_json_file(self):
        self.data_normal, self.unit = get_pca_raw_data_from_json(force_rewrite=True)
        self.keys = self.unit.keys()

    def get_diff_std(self, case_i):
        diff_std_list = list()
        data_old_i = -1.0
        count = 0
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                if data_old_i == -1.0 and (daily[date].has_key(case_i)):
                    data_old_i = daily[date][case_i]
                elif data_old_i != -1.0 and (daily[date].has_key(case_i)):
                    diff_std_list.append(daily[date][case_i] - data_old_i)
                    count += 1
        diff_std_array = numpy.array(diff_std_list)
        # print case_i,count
        self.case_diff_std[case_i] = numpy.std(diff_std_array)

    def cov(self, i, a):
        sum = 0
        sum_i = 0
        sum_a = 0
        count = 0
        for daily in self.data_normal:
            items = daily.items()
            for date, date_val in items:
                if daily[date].has_key(i) and daily[date].has_key(a):
                    temp1 = daily[date][i] - self.case_average_normal[i + '__' + a]
                    temp2 = daily[date][a] - self.case_average_normal[a + '__' + i]

                    temp3 = temp1 * temp2
                    sum += temp3

                    temp4 = temp1 * temp1
                    sum_i += temp4

                    temp5 = temp2 * temp2
                    sum_a += temp5
                    count += 1

        if (count > 2) and (sum_i * sum_a) != 0:
            return sum / math.sqrt(sum_i * sum_a), count
        else:
            return 0, count

    def mutualInfoRate(self,x_name,y_name):
        #Takes in two string type test case names, output a float that is the mutual infomation rate of these two test casesate
        x_list = []
        y_list = []

        for daily in self.data_normal:
            items = daily.items()
            for date, date_val in items:
                if daily[date].has_key(x_name) and daily[date].has_key(y_name):
                    x_list+=[deepcopy(daily[date][x_name])]
                    y_list+=[deepcopy(daily[date][y_name])]
        x_lists,y_lists=standardize([x_list,y_list])
        mutualinfoxy=mutualinfo(x_lists,y_lists,-5,5,7)
        mutualinfoxx=mutualinfo(x_lists,x_lists,-5,5,7)
        mutualinfoyy=mutualinfo(y_lists,y_lists,-5,5,7)
        return mutualinfoxy/sqrt(mutualinfoxx*mutualinfoyy),len(x_list)

    def coef(self,corrmat_o):#Takes in matrix type correlation matrix, output a list of correction coefficients
        corrmat=matrix_to_list(corrmat_o)
        coefList=sumcorrcoef(corrmat)
        for i in range(0,len(corrmat)):
            coefList[i]/=len(corrmat)
            coefList[i]=1-sqrt(1-(coefList[i]-1)**2)
        return coefList

    def init_dict(self):
        self.case_count = OrderedDict()
        self.case_sum = OrderedDict()
        self.case_average = OrderedDict()
        self.case_average_normal = OrderedDict()
        self.case_stadiv_sum = OrderedDict()
        self.case_diff_std = OrderedDict()
        self.case_stadiv = OrderedDict()
        self.unit_stadiv = OrderedDict()
        self.unit_count = OrderedDict()
        self.unit_average = OrderedDict()
        self.weight = OrderedDict()
        self.weight_factor = OrderedDict()
        self.case_level = OrderedDict()
        self.case_level_average = OrderedDict()

        for case in self.unit:
            self.case_count[case] = 0.0
            self.case_sum[case] = 0.0
            self.case_average[case] = 0.0
            self.case_average_normal[case] = 0.0
            self.case_stadiv_sum[case] = 0.0
            self.case_stadiv[case] = 0.0
            self.weight[case] = 0.0
            self.weight_factor[case] = 0.0

        for case, val in self.unit.items():
            if not self.unit_stadiv.has_key(val):
                self.unit_stadiv[val] = 0.0
                self.unit_count[val] = 0.0
                self.unit_average[val] = 0.0

    def average(self):
        # print 'average--------------------------------------'
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                for case in self.keys:
                    if date_val.has_key(case):
                        self.case_count[case] += 1
                        self.case_sum[case] += round(float(daily[date][case]), 3)

        for case, val in self.case_average.items():
            self.case_average[case] = round(self.case_sum[case] / self.case_count[case], 3)
            self.unit_average[self.unit[case]] += self.case_average[case]
            self.unit_count[self.unit[case]] += 1

        for Unit in self.unit_average:
            self.unit_average[Unit] = round(self.unit_average[Unit] / self.unit_count[Unit], 3)
            # print self.case_average

    def out_diff_std(self):
        for case_i in self.keys:
            self.get_diff_std(case_i)

    def standard_divation(self):
        # print 'divation----------------------------------------'
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                # print date_val
                for case in self.keys:
                    if date_val.has_key(case):
                        self.case_stadiv_sum[case] += (daily[date][case] - self.case_average[case]) * (
                        daily[date][case] - self.case_average[case])

        for case, val in self.case_stadiv.items():
            self.case_stadiv[case] = math.sqrt(
                self.case_stadiv_sum[case] / (self.case_count[case]))  # the standard divation of a case
            self.unit_stadiv[self.unit[case]] += self.case_stadiv[case]
            # unit_count[unit[case]] += 1  #already gotten in former function
            # print self.case_stadiv

    def rm_case_from_diff_std(self):
        diff_std_list = list()
        data_old_i = -1.0
        for case_i in self.keys:
            i = 0
            for daily in self.data_normal[0:]:
                items = daily.items()
                for date, date_val in items:
                    if data_old_i == -1.0 and (daily[date].has_key(case_i)):
                        data_old_i = daily[date][case_i]
                    elif data_old_i != -1.0 and (daily[date].has_key(case_i)) and (
                        daily[date][case_i] - data_old_i) > 2 * self.case_diff_std[case_i]:
                        del self.data_normal[i][date][case_i]

                if len(self.data_normal[i]) == 0:
                    del self.data_normal[i]
                    i -= 1

                i += 1

    def get_effictive_normal_data(self):
        i = 0
        for daily in self.data_normal[0:]:
            # items = daily.items()
            # for date, date_val in items:
            #     for case in self.keys:
            #         # print 'unit[case] ==',self.unit[case]
            #         if self.data_normal[i].has_key(date):
            #             if self.data_normal[i][date].has_key(case):
            #                 # print float(self.data_normal[i][date][case]),self.case_average[case],self.case_stadiv[case]*3,case,date
            #
            #                 if not abs(float(self.data_normal[i][date][case]) - self.case_average[case]) < float(
            #                                 self.case_stadiv[case] * 6):
            #                     # print 'delete',self.data_normal[i][date][case]
            #                     del self.data_normal[i][date][case]

            if len(self.data_normal[i]) == 0:
                del self.data_normal[i]
                i -= 1
            i += 1
            # with open(CUR_DIR +data_json_path,'w+') as wfp:
            #     json.dump(self.data_normal, wfp, ensure_ascii=False)
            #     wfp.close()

    def reverse(self):
        # print'reverse------------------'
        i = 0
        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                for case in self.keys:
                    if ((self.unit[case] == 'sec') or (self.unit[case] == 'msecs')):
                        # print 'unit[case] ==',self.unit[case]
                        if self.data_normal[i][date].has_key(case):
                            self.data_normal[i][date][case] = self.case_average[case] - (
                            daily[date][case] - self.case_average[case])
            i += 1
            # print self.data_normal

    def difference_set(self):
        keys = self.unit.keys()
        for key in REMOV_UNIT:
            keys.remove(key)
        return keys

    def get_effict_data(self, input_mat, matrix_row_num, t_flag=False):
        # print "-----------------------------------------"
        if t_flag:
            out_mat = mat(ones((1, matrix_row_num)))
        else:
            out_mat = mat(ones((1, matrix_row_num))).T
        for index in self.collect_effict_data:
            out_mat = numpy.insert(out_mat, len(out_mat.T), values=input_mat[:, index].T, axis=1)

        out_mat = numpy.delete(out_mat, 0, axis=1)

        for index in self.fault_data:
            out_mat = numpy.insert(out_mat, len(out_mat.T), values=input_mat[:, index].T, axis=1)

        return out_mat

    def get_effective_out_sum_of_vector(self):
        matrix_row_num = len(self.V)
        vector_mat = mat(ones((matrix_row_num, matrix_row_num)))

        for i in range(len(vector_mat)):
            for j in range(len(vector_mat.T)):
                if abs(self.V[i, j]) < 0.3:
                    vector_mat[i, j] = 0
                else:
                    vector_mat[i, j] = self.V[i, j]
        self.v_cp = vector_mat

    def reverse_feature_vector(self):
        self.get_effective_out_sum_of_vector()
        temp_list = sum(self.v_cp, 0).tolist()
        i = 0

        for sd in temp_list[0]:
            # print sd
            if sd < 0:
                self.V[:, i] *= -1
                # self.A[0,i] *= -1
            i += 1
            # print self.V

    def get_each_average_for_case(self, i, a):
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

        return tempi, tempa

    def output_each_average_for_case(self):
        for case_i in self.keys:
            for case_a in self.keys:
                self.case_average_normal[case_i + '__' + case_a], self.case_average_normal[
                    case_a + '__' + case_i] = self.get_each_average_for_case(case_i, case_a)

    def PCA(self):
        # print 'PCA-----------------------------------'
        matrix_row_num = len(self.unit)
        count_cov = mat(ones((matrix_row_num, matrix_row_num)))
        Cov = mat(ones((matrix_row_num, matrix_row_num)))
        # print Cov
        i = -1

        for case_i in self.keys:
            i += 1
            a = -1
            for case_a in self.keys:
                a += 1
                if self.parse_config == "pearson":
                    Cov[i, a], count_cov[i, a] = self.cov(case_i, case_a)
                else:
                    Cov[i, a], count_cov[i, a] = self.mutualInfoRate(case_i, case_a)
        # print count_cov
        self.Cov_copy = Cov
        self.coef_list = self.coef(Cov)
        self.correlation_matrix = matrix_to_list(Cov)
        A, V = numpy.linalg.eig(Cov)
        self.count_mat = matrix_to_list(count_cov)
        # print self.count_mat
        self.A = mat(A)
        self.collect_effict_data = list()
        self.fault_data = list()
        icount = 0
        for index in range(len(self.A.T)):
            # print self.A[0, index]
            if (abs(float(self.A[0, index])) >= 1.0):
                self.collect_effict_data.append(icount)
            else:
                self.fault_data.append(icount)
            icount += 1
        # print "self.collect_under_data === %s"%self.collect_effict_data
        self.V = mat(V)
        # print self.V
        # print self.A
        self.V = self.get_effict_data(self.V, matrix_row_num)
        # print self.V
        self.A = self.get_effict_data(self.A, 1, True)

    def factor_score_function(self):
        # print 'factor_score -----------------------------------'
        self.factor_score = (self.V.T * (self.V * self.V.T).I).T
        # print self.factor_score
        wet_sum = numpy.sum(self.factor_score, 1)
        self.weight = list()
        i = 0
        for key in self.unit:
            if not key in REMOV_UNIT:
                self.weight.append(round(wet_sum[i, 0], 5))
                i += 1
        self.weight_copy = self.weight;
        self.weight = matrix_to_list(mat(self.weight))
        self.factor_score = matrix_to_list(self.factor_score, True)
    def image_score_function(self):
        # print 'image_score_function-----------------------------------'
        self.testcase_score = np.matmul(self.weight_copy,self.Cov_copy)
        matrix_col_num = len(self.unit)
        matrix_row_num = 0
        i = 0
        j = 0

        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:
                matrix_row_num += 1
        data = mat(zeros((matrix_col_num, matrix_row_num)))
        self.image_version = mat(zeros(matrix_row_num))

        for daily in self.data_normal[0:]:
            items = daily.items()
            for date, date_val in items:  
                self.image_version[j,i] = date  
                for case in self.keys:
                    if date_val.has_key(case):
                        data[j, i] = daily[date][case]
                    j += 1
                j = 0
                i += 1  
        

        self.image_score = np.matmul(self.testcase_score,data)   #(1,12)*(12*71)
        image_version_list = self.image_version.tolist()
        self.image_version_show = flatten(image_version_list)
        for v in range(len(self.image_version_show)):
            self.image_version_show[v] = int(self.image_version_show[v])

        image_score_list = self.image_score.tolist()
        self.image_score_show = flatten(image_score_list)
        for s in range(len(self.image_score_show)):
            self.image_score_show[s] = round(float(self.image_score_show[s]), 2)


    def __init__(self, current_list=[], parse_config='pearson'):
        self.parse_config = parse_config
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
        self.standard_divation()
        self.get_effictive_normal_data()
        self.reverse()
        self.output_each_average_for_case()

        self.PCA()
        self.reverse_feature_vector()
        self.feature_vector = matrix_to_list(self.V, True)

        self.feature_val = matrix_to_list(self.A)
        self.factor_score_function()
        self.image_score_function()
