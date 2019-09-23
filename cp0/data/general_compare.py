from django.conf import settings
import api
import os
from collections import OrderedDict
import json


class GeneralTestResultCompare(object):
    """
    cmp_list: project, build, test, case, loop
    """
    base_dir = os.path.join(settings.BASE_DIR, 'data', 'data')

    def __init__(self, cmp_list):
        self.cmp_list = cmp_list
        self.key_list = self.get_key_list()
        self.full_dicts = []
    def dict_data(self, cmp_path):
        project, build, test_id, case, loop = cmp_path.split('/')
        if loop:
            sub_score_data = api.raw_case_data(project, test_id, case)[int(loop)]
        else:
            sub_score_data = api.raw_case_data(project, test_id, case)[0]
        sub_score_dict = {'Result': sub_score_data['result']}
        for ss in sub_score_data['sub_score']:
            sub_score_dict[ss[0]] = ss[1]
        self.full_dicts.append(sub_score_dict)

    def get_key_list(self):
        project, build, test_id, case, loop = self.cmp_list[0].split('/')
        return [ss[0] for ss in api.raw_case_data(project, test_id, case)[0]['sub_score']]

    def header(self):
        data = []
        if len(self.cmp_list) > 0:
            for i, cmp_path in enumerate(self.cmp_list):
                project, build, test, case, loop = cmp_path.split('/')
                data.append({
                    'project': str(project),
                    'build': str(build),
                    'test': str(test),
                    'case': str(case),
                    'loop': str(loop)
                })
            for i in range(4 - len(self.cmp_list)):
                data.append({
                    'project': '',
                    'build': '',
                    'test': '',
                    'case': '',
                    'loop': ''
                })

            return data
        else:
            return False

    def result(self):
        data = {}
        if len(self.cmp_list) > 0:
            for i, cmp_path in enumerate(self.cmp_list):
                self.dict_data(cmp_path)
                for key in self.key_list:
                    if i == 0:
                        data[str(key)] = [str(self.full_dicts[i][key])]
                    else:
                        difference = round(float(self.full_dicts[i][key]) - float(self.full_dicts[0][key]), 3) if self.full_dicts[i].has_key(key) else 0
                        rate = '%.2f%%'%(abs(difference)/float(self.full_dicts[0][key])*100)
                        data[str(key)].append([str(self.full_dicts[i][key]), float(difference), rate]) if self.full_dicts[i].has_key(key) else\
                        data[str(key)].append(['0', float(difference), rate])
            return data
        else:
            return False


