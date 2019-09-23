from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from django.http import JsonResponse
from cp0.lib import new_render
from django.conf import settings
from data.models import Project
from bar_data import CSV_PARSE
import json
import os
import re
DATA_ROOT = os.path.join(settings.BASE_DIR, 'data', 'data')


phases = {
    '0_Prekernel': {
        'from': '0',
        'to': 'Console ready'
    },'kernel': {
        'from': 'Console ready',
        'to': 'Root mounted'
    }, 'Kernel_EVS': {
        'from': 'Root mounted',
        'to': 'EVS Start'
    },'EVS': {
        'from': 'EVS Start',
        'to': 'EVS ready'
    },'init1_init2':{
        'from': 'Android_start',
        'to': 'init_2_start'
    },'init2_android': {
        'from': 'init_2_start',
        'to': 'android_start'
    },'android_finished': {
        'from': 'android_start',
        'to': 'boot_is_finished'
    }
}

phases_kernel = {
    'Pre-CSE': {
        'from': '0',
        'to': 'tsc 0'
    },'CSE': {
        'from': 'tsc 0',
        'to': 'CSE ready to send IBBM'
    },'ABL': {
        'from': 'stage-0 start',
        'to': 'jump to image'
    },'pre-kernel': {
        'from': 'jump to image',
        'to': 'Console ready'
    },'kernel': {
        'from': 'Console ready',
        'to': 'Root mounted'
    }, 'Kernel_EVS': {
        'from': 'Root mounted',
        'to': 'EVS Start'
    },'EVS': {
        'from': 'EVS Start',
        'to': 'EVS ready'
    },'init1_init2':{
        'from': 'Android_start',
        'to': 'init_2_start'
    },'init2_android': {
        'from': 'init_2_start',
        'to': 'android_start'
    },'android_finished': {
        'from': 'android_start',
        'to': 'boot_is_finished'
    }
}

categories = {
    'CSE': {
        'from': 'tsc 0',
        'to': 'CSE ready to send IBBM'
    },
    'ABL stage 0': {
        'from': 'stage-0 start',
        'to': 'stage-0 done'
    },
    'ABL stage 1': {
        'from': 'stage-0 done',
        'to': 'stage-2 start'
    },
    'ABL config': {
        'from': 'received ABL config over IPC',
        'to': 'probed CPU, PCB, start MRC'
    },
    'MRC': {
        'from': 'probed CPU, PCB, start MRC',
        'to': 'send DID'
    },
    'stage 2 load': {
        'from': 'stage-1 done',
        'to': 'stage-2 start'
    },
    'ABL stage 2': {
        'from': 'stage-2 start',
        'to': 'PCIe Root Port init start'
    },
    'rp pcie init': {
        'from': 'PCIe Root Port init start',
        'to': 'PCIe init done'
    },
    'eMMC init': {
        'from': 'PCIe init done',
        'to': 'Image load done'
    },
    'Image dl and auth': {
        'from': 'Image load done',
        'to': 'Image CRC done'
    },
    'VMM ready': {
        'from': 'VMM start',
        'to': 'VMM  ready'
    },
    'Bootloader1  ready': {
        'from': 'VMM  ready',
        'to': 'Bootloader1  ready'
    },
    'Trusty  ready': {
        'from': 'Bootloader1  ready',
        'to': 'Trusty  ready'
    },
    'Bootloader2 ready': {
        'from': 'Trusty  ready',
        'to': 'Bootloader2 ready'
    },
    'Kernel&early init': {
        'from': 'Bootloader2 ready',
        'to': 'Kernel&early  ready'
    },
    'kernel init': {
        'from': 'Console ready',
        'to': 'Root mounted'
    },
    'Kernel_EVS': {
        'from': 'Root mounted',
        'to': 'EVS Start'
    },
    'EVS': {
        'from': 'EVS Start',
        'to': 'EVS ready'
    },
}

phases_kernel_m = {
    'Pre-CSE': {
        'from': '0',
        'to': 'tsc 0'
    },'CSE': {
        'from': 'tsc 0',
        'to': ''
    },'ABL': {
        'from': '',
        'to': 'jump to image'
    },'ABL-prekernel':{
        'from': 'jump to image',
        'to': 'VMM start'
    },'pre-kernel': {
        'from': 'VMM start',
        'to': 'Lk/trusty  ready'
    },'Pre_kernel->kernel':{
        'from': 'Lk/trusty  ready',
        'to': 'Console ready'
    },'kernel': {
        'from': 'Console ready',
        'to': 'Root mounted'
    }, 'Kernel_RVC': {
        'from': 'Root mounted',
        'to': 'rvc Start'
    },'RVC': {
        'from': 'rvc Start',
        'to': 'rvc ready'
    }
}


phases_m = {
    'Pre-CSE': {
        'from': '0',
        'to': 'tsc 0'
    },'CSE': {
        'from': 'tsc 0',
        'to': ''
    },'ABL': {
        'from': '',
        'to': 'jump to image'
    },'ABL-prekernel':{
        'from': 'jump to image',
        'to': 'VMM start'
    },'pre-kernel': {
        'from': 'VMM start',
        'to': 'Lk/trusty  ready'
    },'Pre_kernel->kernel':{
        'from': 'Lk/trusty  ready',
        'to': 'Console ready'
    },'kernel': {
        'from': 'Console ready',
        'to': 'Root mounted'
    }, 'init1_init2':{
        'from': 'Android_start',
        'to': 'init_2_start'
    }, 'init2_android': {
        'from': 'init_2_start',
        'to': 'android_start'
    }, 'android_finished': {
    'from': 'android_start',
    'to': 'boot_is_finished'
    }
}


categories_m = {
    'Pre-CSE': {
        'from': '0',
        'to': 'tsc 0'
    },
    'CSE': {
        'from': 'tsc 0',
        'to': ''
    },
    'ABL stage 0': {
        'from': '',
        'to': 'stage-0 done'
    },
    'ABL stage 1': {
        'from': 'stage-0 done',
        'to': 'stage-1 done'
    },
    'ABL stage1-2':{
        'from': 'stage-1 done',
        'to': 'stage-2 start'
    },
    'ABL stage 2': {
        'from': 'stage-2 start',
        'to': 'PCIe Root Port init start'
    },
    'rp pcie init': {
        'from': 'PCIe Root Port init start',
        'to': 'PCIe init done'
    },
    'eMMC init': {
        'from': 'PCIe init done',
        'to': 'Image load done'
    },
    'Image dl and auth': {
        'from': 'Image load done',
        'to': 'Image CRC done'
    },
    'ABL ready': {
        'from': 'Image CRC done',
        'to': 'jump to image'
    },
    'ABL->prekernel':{
        'from': 'jump to image',
        'to': 'VMM start'
    },
    'pre-kernel': {
        'from': 'VMM start',
        'to': 'Lk/trusty  ready'
    },
    'Pre_kernel->kernel': {
        'from': 'Lk/trusty  ready',
        'to': 'Console ready'
    },
    'kernel init': {
        'from': 'Console ready',
        'to': 'Root mounted'
    },
    'Kernel_RVC': {
        'from': 'Root mounted',
        'to': 'rvc Start'
    },
    'RVC': {
        'from': 'rvc Start',
        'to': 'rvc ready'
    },
}

class Line2Raw(object):
    caution = None
    real_duration = 0
    index = 0
    id = 0

    def __init__(self, line):
        column = line.split('\t')
        self.next_raw = None
        self.start = column[0].strip()
        self.stage = column[2].strip()
        self.status = column[3].strip()
        self.duration = column[4].strip()
        if len(column) == 5:
            self.remark = ''
        else:
            self.remark = column[5].strip()
        if self.remark.strip() == '':
            self.remark == 'null'


class CategoryData(object):
    def __init__(self, key, start, end):
        self.key = key
        self.start = float(start)
        self.end = float(end)

    @property
    def duration(self):
        return round(self.end - self.start, 3)


class ParseReportCSV(object):
    def __init__(self, project, build, test_id, case_name, attachment_name):
        test_path = os.path.join(DATA_ROOT, project, 'raw', build, test_id)
        self.start = 0
        self.remark = None
        self.display_remark = None
        self.next_start = 0
        self.build = build
        self.test_id = test_id
        self.case_name = case_name
        self.project = project
        self.attachment_path = os.path.join(test_path, case_name, attachment_name)
        self.loop = attachment_name.split('.')[0].split('_')[-1]
        self.result_path = os.path.join(test_path, '_'.join([case_name, self.loop]))
        self.parsed = []

    @property
    def result(self):
        d = json.load(open(self.result_path, 'r'))
        return d['result']

    def parse(self):
        if os.path.exists(self.attachment_path):
            parsed_list = []
            lines = open(self.attachment_path, 'r').readlines()
            lines.reverse()
            last_start = 0
            last_remark = ''
            i = 0
            for line in lines:
                if not line.startswith('ign-on'):
                    remark = 'null'
                    p = line.split('\t')
                    start = p[0]
                    if len(p) == 6:
                        remark = p[5].strip()
                    parsed_list.append({
                        'next_remark': last_remark,
                        'start': start,
                        'next_start': last_start,
                        'delta': round(float(last_start) - float(start), 3),
                        'remark': remark,
                        'cmp_start': [],
                        'cmp_next_start': [],
                        'cmp_delta': [],
                        'cmp_delta_class': []
                    })
                    print remark, start
                    last_start = start
                    last_remark = remark
                    i += 1
                else:
                    break
            parsed_list.reverse()
            parsed_list = parsed_list[:-1]
            self.parsed = parsed_list
            return parsed_list

        else:
            return False

    def add_cmp_data(self, new):
        for stage in self.parsed:
            for new_stage in new.parsed:
                if new_stage['remark'] == stage['remark']:
                    start_delta = round(float(stage['start']) - float(new_stage['start']), 3)
                    if start_delta > 0:
                        cmp_start = '{0} (+{1})'.format(new_stage['start'], start_delta)
                    else:
                        cmp_start = '{0} ({1})'.format(new_stage['start'], start_delta)
                    stage['cmp_start'].append(cmp_start)
                    next_start = new.get_start(stage['next_remark'])
                    stage['cmp_next_start'].append(next_start)
                    delta = round(float(new_stage['next_start']) - float(new_stage['start']), 3)
                    if delta - float(stage['delta']) > 0:
                        new_delta = '{0} (+{1})'.format(delta, delta - float(stage['delta']))
                        stage['cmp_delta_class'] = 'text-danger'
                    else:
                        new_delta = '{0} ({1})'.format(delta, delta - float(stage['delta']))
                        stage['cmp_delta_class'] = 'text-success'
                    if float(new_stage['start']) > float(next_start):
                        new_delta = None
                    stage['cmp_delta'].append(new_delta)
                    break
                else:
                    continue
                stage['cmp_start'].append('not found')

    def get_start(self, remark):
        for stage in self.parsed:
            if stage['remark'] == remark:
                return stage['start']
            else:
                continue
        return False


def view(request, project, build, test_id, case_name, attachment_name):
    api_link = '/'.join([project, build, test_id, case_name, attachment_name])
    path = os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id, case_name, attachment_name)
    log_file = open(path).read()
    if project=='bxtp_ivi_m':
        return new_render(request, 'stackbar_m.html', context={'link': api_link}, title='CP0', subtitle=None,wide=True)
    elif project=='mmr1_bxtp_ivi_maint':
        return new_render(request, 'stackbar_m.html', context={'link': api_link}, title='CP0', subtitle=None,wide=True)
    elif project == 'upload':
        return new_render(request, 'stackbar.html', context={'link': api_link}, title='CP0', subtitle=None, wide=True)
    else:
        if log_file.find('step_') != -1:
            return new_render(request, 'stackbar.html', context={'link': api_link}, title='CP0', subtitle=None,wide=True)
        else:
            return new_render(request, 'stackbar_old.html', context={'link': api_link}, title='CP0', subtitle=None,wide=True)

def comparision(request):
    # project, build, test_id, case_name, attachment_name
    # bxtp_ivi_m/20171025_664/20171025_100339/0
    cmp_list = request.session.get("cmp", None)
    print cmp_list
    case_name= 'full boot'
    if cmp_list:
        current = cmp_list[0]
        project, build, test_id, case, loop = current.split('/')

        attachment_name = 'report_{0}.csv'.format(loop)
    else:
        return HttpResponseRedirect('/')
    curr_data = ParseReportCSV(project, build, test_id, case_name, attachment_name)
    curr_raw = curr_data.parse()
    cmp_data = []

    for i, test in enumerate(cmp_list[1:]):
        new_project, new_build, new_test_id, new_case, new_loop = test.split('/')
        new_attachment_name = 'report_{0}.csv'.format(new_loop)
        new = ParseReportCSV(new_project, new_build, new_test_id, case_name, new_attachment_name)
        if new.parse() is False:
            print 'parse fail'
            return HttpResponseRedirect('/')
        cmp_data.append(new)
        curr_data.add_cmp_data(new)

    for i in range(3 - len(cmp_data)):
        cmp_data.append(None)

    context = {
        'curr_raw': curr_raw,
        'curr_data': curr_data,
        'cmp_data': cmp_data,
        'projects': Project.objects.all()
    }
    return new_render(request, 'comparision.html', context=context, title='CP0', subtitle=None)


def api(request, project, build, test_id, case_name, attachment_name):
    path = os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id, case_name, attachment_name)
    log_file = open(path).read()
    if project == 'bxtp_ivi_m':
        api_dict = {
            'kernel': {
                'starts': [0],
                'phases': [],
                'durations': [0],
                'categories': []
            },
            'android': {
                'starts': [0, 0],
                'phases': [],
                'durations': [0,0],
                'categories': []
            }
        }
        lines = open(path, 'r').readlines()
        kernel_raw_data = []
        all_raw_data = []
        end_of_kernel = False

        # generate kernel and full series raw data
        last_raw_remark = ''
        for line in lines:
            if re.match(r'\d+\.\d+', line):
                raw = Line2Raw(line)
                all_raw_data.append(raw)
                api_dict['android']['starts'].append(float(raw.start))
                api_dict['android']['categories'].append(last_raw_remark + '->' + raw.remark)

                if len(all_raw_data) > 1:
                    all_raw_data[-1].real_duration = round(float(raw.start) - float(all_raw_data[-1].start), 3)
                    api_dict['android']['durations'].append(round(float(raw.start) - float(all_raw_data[all_raw_data.index(raw)-1].start), 3))
                if raw.remark != 'Android_start':
                    if not end_of_kernel:
                        kernel_raw_data.append(raw)
                else:
                    end_of_kernel = True
                last_raw_remark = raw.remark
        api_dict['android']['categories'].append('Total')
        api_dict['android']['durations'].append(round(float(all_raw_data[-1].start)- float(all_raw_data[0].start), 3))
        api_dict['android']['durations'][-1] = round(float(all_raw_data[-1].start) - 0, 3)
        api_dict['android']['starts'][-1] = 0

        # make stack bar data
        categories_list = []
        phases_list = []
        phases_list_m = []
        for key in categories_m:
            try:
                start = filter(lambda x: x.remark == categories_m[key]['from'], all_raw_data)[0].start
                end = filter(lambda x: x.remark == categories_m[key]['to'], all_raw_data)[0].start
                categories_list.append(CategoryData(key, start, end))
            except Exception as e:
                continue

        for key in phases_m:
            try:
                start = filter(lambda x: x.remark == phases_m[key]['from'], all_raw_data)[0].start
                end = filter(lambda x: x.remark == phases_m[key]['to'], all_raw_data)[0].start
                phases_list.append(CategoryData(key, start, end))
            except Exception as e:
                continue

        for key in phases_kernel_m:
            try:
                start = filter(lambda x: x.remark == phases_kernel_m[key]['from'], all_raw_data)[0].start
                end = filter(lambda x: x.remark == phases_kernel_m[key]['to'], all_raw_data)[0].start
                phases_list_m.append(CategoryData(key, start, end))
            except Exception as e:
                continue


        for ctg in sorted(categories_list, key=lambda x: x.start):
            api_dict['kernel']['starts'].append(ctg.start)
            api_dict['kernel']['durations'].append(ctg.duration)
            api_dict['kernel']['categories'].append(ctg.key)

        for phase in sorted(phases_list, key=lambda x: x.start):
            # print "android_phases:",phase.key,phase.start,phase.duration
            api_dict['android']['phases'].append(phase.duration)

        for phase in sorted(phases_list_m, key=lambda x: x.start):
            api_dict['kernel']['phases'].append(phase.duration)

        return JsonResponse(api_dict)
    else:
        if log_file.find('step_') == -1:
            api_dict = {
                'kernel': {
                    'starts': [0],
                    'phases': [],
                    'durations': [0],
                    'categories': []
                },
                'android': {
                    'starts': [0, 0],
                    'phases': [],
                    'durations': [0, 0],
                    'categories': []
                }
            }
            lines = open(path, 'r').readlines()
            kernel_raw_data = []
            all_raw_data = []
            end_of_kernel = False

            # generate kernel and full series raw data
            last_raw_remark = ''
            for s in range(len(lines)):
                if lines[s].find("Kernel&early") != -1 or lines[s].find("VMM start") != -1 or lines[s].find("Console ready") != -1:
                    line_new = lines[s:]
            for i in lines:
                if i.find("Pre-CSE") != -1:
                    line_new.insert(0, i)

            for line in line_new:
                # if re.match(r'\d+\.\d+', line):
                raw = Line2Raw(line)
                all_raw_data.append(raw)
                api_dict['android']['starts'].append(float(raw.start))
                api_dict['android']['categories'].append(last_raw_remark + '->' + raw.remark)

                if len(all_raw_data) > 1:
                    all_raw_data[-1].real_duration = round(float(raw.start) - float(all_raw_data[-1].start), 3)
                    api_dict['android']['durations'].append(
                        round(float(raw.start) - float(all_raw_data[all_raw_data.index(raw) - 1].start), 3))
                if raw.remark != 'Android_start':
                    if not end_of_kernel:
                        kernel_raw_data.append(raw)
                else:
                    end_of_kernel = True
                last_raw_remark = raw.remark
            api_dict['android']['categories'].append('Total')
            api_dict['android']['durations'].append(
                round(float(all_raw_data[-1].start) - float(all_raw_data[0].start), 3))
            api_dict['android']['durations'][-1] = round(float(all_raw_data[-1].start) - 0, 3)
            api_dict['android']['starts'][-1] = 0
            leng = len(api_dict['android']['durations'])
            icount = 0
            temp_list = list()
            for i in range(leng):
                if api_dict['android']['durations'][i] < 0:
                    temp_list.append(i)
                    print "api_dict['android']['durations'][i]", i, api_dict['android']['durations'][i]

            for i in temp_list:
                api_dict['android']['durations'].remove(api_dict['android']['durations'][i - icount])
                api_dict['android']['starts'].remove(api_dict['android']['starts'][i - icount])
                api_dict['android']['categories'].remove(api_dict['android']['categories'][i - icount - 1])
                icount += 1
            # make stack bar data
            categories_list = []
            phases_list = []
            phases_list_new = []
            all_new_raw = []
            line_raw = open(path, 'r').readlines()
            for line in line_raw:
                if re.match(r'\d+\.\d+', line):
                    raws = Line2Raw(line)
                    all_new_raw.append(raws)
            for key in categories:
                try:
                    start = filter(lambda x: x.remark == categories[key]['from'], all_new_raw)[0].start
                    end = filter(lambda x: x.remark == categories[key]['to'], all_new_raw)[0].start
                    categories_list.append(CategoryData(key, start, end))

                except Exception as e:
                    continue

            for key in phases:
                try:
                    start = filter(lambda x: x.remark == phases[key]['from'], all_raw_data)[0].start
                    end = filter(lambda x: x.remark == phases[key]['to'], all_raw_data)[0].start

                    phases_list.append(CategoryData(key, start, end))

                except Exception as e:
                    continue

            for key in phases_kernel:
                try:
                    start1 = filter(lambda x: x.remark == phases_kernel[key]['from'], all_new_raw)[0].start
                    end1 = filter(lambda x: x.remark == phases_kernel[key]['to'], all_new_raw)[0].start
                    phases_list_new.append(CategoryData(key, start1, end1))
                except Exception as e:
                    continue
            for ctg in sorted(categories_list, key=lambda x: x.start):
                # print '%-25s%-15s%-15s' % (ctg.key, ctg.start, ctg.duration)
                api_dict['kernel']['starts'].append(ctg.start)
                api_dict['kernel']['durations'].append(ctg.duration)
                api_dict['kernel']['categories'].append(ctg.key)

            for phase in sorted(phases_list, key=lambda x: x.start):
                api_dict['android']['phases'].append(phase.duration)

            for phase_kernel in sorted(phases_list_new, key=lambda x: x.start):
                api_dict['kernel']['phases'].append(phase_kernel.duration)

            if (api_dict['kernel']['categories'][-1] != 'EVS'):
                api_dict['android']['phases'].insert(6, 0)
                api_dict['android']['phases'].insert(8, 0)
                api_dict['kernel']['phases'].insert(6, 0)
                api_dict['kernel']['phases'].insert(8, 0)
            return JsonResponse(api_dict)
        else:
            api_dict = CSV_PARSE(path).bar_total()
            return JsonResponse(api_dict)

