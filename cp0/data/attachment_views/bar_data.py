import re
from collections import OrderedDict
class CSV_PARSE():
    def __init__(self, attch_path):
        self.path = attch_path
        self.project = ''
        self.total = OrderedDict()
        self.project = str(self.path.split('/')[-2])
        self.steps = ['Pre_UOS','pre_kernel', 'kernel', 'UOS_Kernel', 'android', 'UOS_Android']

        for step in self.steps:
            self.total[step] = {"category": [], "start": [], "duration": [], "stage_name": [], "stage_data": [], "org_data": []}

    def bar_total(self):
        try:
            with open(self.path) as lines:
                step = []
                isNewstep = False
                isNewstepdetail = False
                for line in lines:
                    if isNewstep:
                        if re.match("\d+.\d+\s+\w+", line) and len(step) > 0 and step[0] in self.total:
                            self.total[step[0]]["stage_data"].append(float(re.split('\s+', line)[0]))
                            self.total[step[0]]["stage_name"].append(re.split('\s+', line)[1])
                        elif re.findall("step_(.+)_detail:", line) or re.findall("step_(.+)_display:", line):
                            isNewstepdetail = True
                            isNewstep = False
                    elif isNewstepdetail:
                        if re.match("\d+.\d+\s+\w+", line):
                            self.total[step[0]]["org_data"].append((re.split('\s+', line)[0], re.split('\s+', line)[1]))
                        elif re.findall("step_(.+):", line) != []:
                            step = re.findall("step_(.+):", line)
                            isNewstepdetail = False
                            isNewstep = True
                    else:
                        if re.findall("step_(.+):", line):
                            step = re.findall("step_(.+):", line)
                            isNewstep = True
        except Exception,e:
            print repr(e)
        try:
            for step in self.steps:
                for i in range(len(self.total[step]["org_data"])):
                    if i+1 < len(self.total[step]["org_data"]) and float(self.total[step]["org_data"][i+1][0]) - float(self.total[step]["org_data"][i][0]) != 0:
                        self.total[step]["start"].append(float(self.total[step]["org_data"][i][0]))
                        self.total[step]["duration"].append(float('%.3f'%(float(self.total[step]["org_data"][i+1][0]) - float(self.total[step]["org_data"][i][0]))))
                        self.total[step]["category"].append(self.total[step]["org_data"][i][1]+"->"+self.total[step]["org_data"][i+1][1])
            self.total[self.steps[-1]]["start"].append(0)
            self.total[self.steps[-1]]["duration"].append(float('%.3f' % (float(self.total[self.steps[-1]]["org_data"][-1][0]))))
            self.total[self.steps[-1]]["category"].append("Total")
        except Exception, e:
            print e
        return self.total