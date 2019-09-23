from __future__ import unicode_literals

import json
import os
import re
from collections import OrderedDict, namedtuple
from itertools import groupby
import logging
from django.contrib.auth.models import User
from django.db import models
from django import forms
from django.forms import ModelForm
from django.utils import timezone
import requests
import subprocess
import datetime


# Create your models here.
logger = logging.getLogger('django.request')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
BUILD_TYPE_CHOICES = (
    (0, 'engineering'),
    (1, 'daily'),
    (2, 'weekly'),
    (3, 'merge request'),
    (4, 'candidate'),
    (5, 'candidate mr1'),
    (6, 'merge request mr1'),
    (7, 'weekly mr1'),
    (8, 'latest'),
    (9, 'candiate mr0'),
    (10,'local'),
    (11, 'preintegration')
)

POLICY_CHOICES = (
    (0, "public"),
    (1, "private")
)

RAM_CHOICES = (
    (2, '2'),
    (4, '4'),
    (8, '8')
)
INSTALL_STATUS_CHOICES = (
    (0, 'installing'),
    (1, 'success'),
    (2, 'failed')
)


case_list = [
    'Cold_boot_to_early_RVC',
    'Resume_time_manual',
    'ST_PERF_Cold_boot_to_Android_UI',
    'ST_PERF_Cold_boot_to_animation',
    'ST_PERF_Cold_boot_to_splash_screen',
]



class ConfigTemplate(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    content = models.CharField(max_length=3000)
    template_name = models.CharField(max_length=50, blank=True, null=True)
    public = models.BooleanField(default=False)
    available_fields = [
        'project_id',
        'build_type_id',
        'build_url',
        'test_target',
        'case_info',
        'slave_info'
    ]

    @property
    def serialize(self):
        json_data = json.loads(self.content)
        case_info = []
        json_data['case_info'] = case_info
        slave = Slave.objects.get(id=json_data['slave_id'])
        json_data['slave_info'] = {'display': slave.num, 'id': slave.id}
        for index, case_name in enumerate(json_data['case_name']):
            case_info.append({
                'case_name': case_name,
                'case_loop': json_data['case_loop'][index]
            })
        for key in json_data.keys():
            if key not in self.available_fields:
                json_data.pop(key, None)
        return json_data

    def __str__(self):
        if self.public:
            return 'Public config: ' + self.template_name
        return 'Private config: ' + self.template_name


class Production(models.Model):
    name = models.CharField(max_length=30)
    short_name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=30)
    builder_name = models.CharField(max_length=30, default='')
    slave_project = models.CharField(max_length=30, default='')
    OS_version = models.CharField(max_length=30, default='')
    build_label = models.CharField(max_length=30, default='')
    board_type = models.CharField(max_length=30, default='')
    active = models.BooleanField(default=True)
    production = models.ForeignKey(Production, on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def build_paths(self):
        build_paths = BuildPath.objects.filter(project=self.id)
        return build_paths

    @property
    def serialize(self):
        return {
            'name': self.name,
            'active': self.active,
            'production': self.production.name if self.production else 'Not set',
            'owner': 'Admin'
        }


class BuildPath(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    url = models.URLField()
    build_type = models.IntegerField(choices=BUILD_TYPE_CHOICES)
    buildbot_link = models.URLField()

    def __str__(self):
        return str(self.build_type)        


ResultGroup = namedtuple(
    'ResultGroup',
    ['case_name', 'unit', 'maximum', 'minimum', 'median', 'average', 'raw', 'result', 'fluc', 'vic'])


def get_raw(entries, raw_data=False, med_and_avg=False, max_and_min=False):
        entries = sorted(list(entries), key=lambda x: x['case_name'])
        grouped = groupby(entries, key=lambda x: x['case_name'])
        result_list = []
        for case_name, group in grouped:
            json_data = [result for result in group]
            results = [result['result'] for result in json_data]
            unit = [result['unit'] for result in json_data][0]

            if med_and_avg:
                try:
                    num_results = filter(is_number, results)
                    results = [float(result) for result in num_results]
                    results.sort()
                    median = results[int(len(results) / 2)] if len(results) % 2 else None
                    avg = sum(results) / len(results) if median is None else None
                    result = median if median else avg
                except ZeroDivisionError:
                    result = 'N/A'
                    avg = 'N/A'
                    median = 'N/A'
                except TypeError:
                    result = 'N/A'
                    avg = 'N/A'
                    median = 'N/A'
                except ValueError:
                    result = 'N/A'
                    avg = 'N/A'
                    median = 'N/A'
            else:
                median = None
                avg = None
            try:
                if max_and_min:
                    max_val = max(results)
                    min_val = min(results)
                else:
                    max_val = None
                    min_val = None
            except ValueError:
                max_val = None
                min_val = None

            vic_dict = {
                'full boot': {
                    'stack_bar': ('report', 'csv', 'boot chart'),
                },
                'boot_analyze_2.0':  {
                    'stack_bar': ('report', 'csv', 'boot chart'),
                },
                'full_boot': {
                    'stack_bar': ('report', 'csv', 'boot chart'),
                },
                'Acrn_boot_time': {
                    'stack_bar': ('report', 'csv', 'boot chart'),
                },
                'instance_90': {
                    'usage_chart': ('aic_instance', 'json', 'usage trend')
                },
                'game_90': {
                    'usage_chart_by_instances': ('aic_game', 'json', 'usage trend')
                },
                'instance_ins': {
                    'usage_chart_v2': ('aic_instance', 'json', 'usage trend')
                }
            }

            if raw_data:
                if case_name in vic_dict:
                    vic = vic_dict[case_name]
                else:
                    vic = None
                raw = json_data
            else:
                vic = None
                raw = None

            rg = ResultGroup(
                case_name=case_name,
                unit=unit,
                maximum=max_val,
                minimum=min_val,
                median=median,
                average=avg,
                raw=raw,
                result=result,
                fluc=None,
                vic=vic
            )
            result_list.append(rg)

        return result_list


class Slave(models.Model):
    ip = models.GenericIPAddressField(default='')
    comment = models.CharField(default='', max_length=100, null=True, blank=True)
    sn = models.CharField(max_length=30, null=True, blank=True)
    num = models.CharField(max_length=30, null=True, blank=True)
    user_name = models.CharField(max_length=30, null=True, blank=True)
    host_name = models.CharField(max_length=30, null=True, blank=True)
    ram = models.IntegerField(default=0, choices=RAM_CHOICES)
    policy = models.IntegerField(default=0, choices=POLICY_CHOICES)
    owner = models.ForeignKey(User, blank=True, null=True, db_index=True)
    install_status = models.IntegerField(default=1, choices=INSTALL_STATUS_CHOICES)
    projects = models.ManyToManyField(Project, related_name='project_slave', blank=True, null=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'num': self.num,
            'name': self.sn
        }

    def alive(self):
        retry = 1
        for i in range(retry):
            try:
                session = requests.Session()
                session.trust_env = False
                return session.get('http://' + self.ip + ':9001', timeout=0.3).status_code == 200
            except Exception, e:
                logging.debug(self.ip + ' ' + e.message)
                return False
        return False

    def status(self):
        try:
            session = requests.Session()
            session.trust_env = False
            resp_info = session.get('http://' + self.ip + ':9001/stat/', timeout=0.5)
            status = json.loads(resp_info.text)
            if status['pid'] == 'None':
                status['style'] = 'navy-bg'
            else:
                status['style'] = 'yellow-bg'
            return status
        except Exception as e:
            print e
            return {
                'alive': False,
                'style': 'red-bg',
                'error': 'Slave is offline'
            }

    def __str__(self):
        return self.ip


class SlaveForm(ModelForm):
    ip = forms.CharField(required=True)
    user_name = forms.CharField(required=True)
    host_name = forms.CharField(required=True)
    num = forms.CharField(required=True, label='Name', widget=forms.TextInput(attrs={'placeholder': 'GP8gD001'}))
    ram = forms.IntegerField(required=True, widget=forms.Select(choices=RAM_CHOICES, attrs={'class': 'form-control'}))
    policy = forms.IntegerField(required=True, widget=forms.Select(choices=POLICY_CHOICES, attrs={'class': 'form-control'}))

    class Meta:
        model = Slave
        fields = ('ip', 'user_name', 'host_name', 'num', 'ram', 'sn', 'comment', 'policy')

    def clean_ip(self):
        ip = self.cleaned_data["ip"]
        username = self.data["user_name"]
        passwd = self.data["passwd"]
        if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip):
            raise forms.ValidationError('the ip is invalid!', code='invalid ip')
        p = subprocess.Popen("sshpass -p '{0}' ssh -p 22 -o StrictHostKeyChecking=no {1}@{2} 'pwd'".format(passwd, username, ip), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if len(p.stdout.readlines()) == 0:
            raise forms.ValidationError('connect with ip failed, please check it!', code='invalid ip')
        return ip

    def clean_host_name(self):
        hostname = self.cleaned_data["host_name"]
        username = self.data["user_name"]
        passwd = self.data["passwd"]

        p = subprocess.Popen("sshpass -p '{0}' ssh -p 22 -o StrictHostKeyChecking=no {1}@{2} 'pwd'".format(passwd, username, hostname), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if len(p.stdout.readlines()) == 0:
            raise forms.ValidationError('connect with hostname failed, please check it!', code='invalid hostname')
        return hostname

    def clean_num(self):
        num = self.cleaned_data["num"]
        if Slave.objects.filter(num=num).count() > 0:
            raise forms.ValidationError('this name is exist!', code='invalid num')
        return num


class TestConfig(dict):
    def __init__(self, test_config):
        self.test_config = test_config
        try:
            self.dict = json.load(open(os.path.join(DATA_PATH, 'test_configs', self.test_config)))
            self.update()
        except OSError:
            self.dict = {}
        except IOError:
            self.dict = {}

    def __contains__(self, key):
        if key in self.dict:
            return True
        return False  

    def __getitem__(self, key):
        if key not in self.dict:
            return 'missing config'
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __repr__(self):
        return '%r' % (self.dict)

    def update(self):
        for k, v in self.dict.iteritems():
            self[k] = v


class Task(models.Model):
    test_config = models.CharField(max_length=8)
    available = models.NullBooleanField(default=True)
    pid = models.IntegerField(default=0)
    project = models.ForeignKey(Project)
    slave = models.ForeignKey(Slave, blank=True, null=True)
    test_id = models.CharField(default='null', max_length=15)
    create_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(blank=True, null=True, db_index=True)
    end_time = models.DateTimeField(blank=True, null=True, db_index=True)
    submitter = models.ForeignKey(User, db_index=True)
    comment = models.CharField(null=True, blank=True, max_length=100)
    favorites = models.ManyToManyField(User, related_name='task_user', blank=True, null=True)

    def build(self):
        try:
            return TestConfig(self.test_config)['build']
        except Exception as e:
            print e

    def status(self):
        d = TestConfig(self.test_config)
        try:
            logger = Logger.objects.filter(test_config=self.test_config)[0]
            if self.available:
                if d['patch_method'] =='td':
                        self.style = 'label-warning'
                        return 'queue'
                else:
                    if logger.description =='nt':
                        self.style = 'label-warning'
                        return 'building'
                    else:
                        self.style = 'label-warning'
                        return 'queue'
            else:
                if self.test_id == 'null':
                    if d['patch_method'] =='td':
                        self.style = 'label-default'
                        return 'cancel'
                    else:
                        if logger.description == 'bf':
                            self.style = 'label-danger'
                            return 'build failed'
                        elif logger.description == 'cancel':
                            self.style = 'label-default'
                            return 'cancel'
                        elif logger.description == 'bs':
                            self.style = 'label-warning'
                            return 'queue'
                        else:
                            self.style = 'label-danger'
                            return 'failed'
                else:
                    self.style = 'label-warning'
                    return 'testing'
        except Exception as e:
            return 'import'


    @property
    def test_tag(self):
        d = TestConfig(self.test_config)
        if 'test_tag' in d:
            if d['test_tag'].strip() == '':
                return None
            else:
                return d['test_tag'].strip()
        else:
            return None

    def start(self):
        try:
            self.start_time = datetime.datetime.now(tz=timezone.utc)
            self.save()
            return True
        except:
            return False

    def end(self):
        try:
            self.end_time = datetime.datetime.now(tz=timezone.utc)
            self.save()
            return True
        except:
            return False

    def duration(self):
        if self.end_time:
            if self.start_time:
                return (self.end_time - self.start_time).seconds
            return (self.end_time - self.create_time).seconds
        return False
    def duration_time(self):
        if self.end_time:
            if self.start_time:
                return (self.end_time - self.start_time)
            return (self.end_time - self.create_time)
        return False
    @property
    def create(self):
        return self.create_time.month


class TrendsData(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    build = models.CharField(max_length=30)
    case = models.CharField(max_length=30)
    result = models.CharField(max_length=10)
    build_type = models.CharField(max_length=20)


class RawData(object):
    def __init__(self, project_name, build, test_id, file_name):
        self.project = project_name
        self.build = build
        self.test_id = test_id
        self.path = os.path.join(DATA_PATH, project_name, 'raw', build, test_id, file_name)

    @property
    def data(self):
        json_data = json.load(open(self.path, 'r'))
        attach_path = '/'.join([json_data['path'], json_data['name'], json_data['loop']])
        data = {
            'name': json_data['name'],
            'unit': json_data['unit'],
            'loop': int(json_data['loop']),
            'att_name': map(lambda x: (x.split('/')[-1], attach_path), json_data['attachments']),
            'result': json_data['result'],
            'post2': map(lambda x: x if x else None, json_data['post2'])
        }
        return data


class RawData2(object):
    def __init__(self, project_name, build, test_id, file_name):
        self.project = project_name
        self.build = build
        self.test_id = test_id
        self.path = os.path.join(os.path.dirname(__file__), 'data', project_name, 'raw', build, test_id)
        self.file_name = file_name
        self.case_name = None
        self.loop = None
        self.result = None
        self.unit = None
        self.sub_score = []
        self.attachments = []
        self.vic = []
        self.parse_data()

    def parse_data(self):
        json_data = json.load(open(os.path.join(self.path, self.file_name), 'r'))
        self.loop = json_data['loop']
        self.case_name = json_data['case_name']
        attachment_dir = '/'.join([self.path, self.case_name])
        if os.path.exists(attachment_dir):
            attachments = os.listdir(attachment_dir)
            self.attachments = filter(lambda x: x.endswith('_' + str(self.loop) + '.' + x.split('.')[-1]), attachments)
            self.attachments.sort()
        for attachment in self.attachments:
            # bxtp_ivi_m/20170914_624/20170914_162026/full%20boot/report_0.csv/
            if attachment.startswith('report') and attachment.endswith('csv'):
                self.vic.append(('Stack bar',
                                 '/'.join(
                                     ['chart', 'stack_bar', self.project, self.build, self.test_id, self.case_name,
                                      attachment])))
                # self.vic.append(('Comparision',
                #                  '/'.join(
                #                      [self.project, self.build, self.test_id, self.case_name, str(self.loop)])))
            if attachment.startswith('result') and attachment.endswith('json'):
                self.attachments.pop(self.attachments.index(attachment))

        self.result = json_data['result']
        self.unit = json_data['unit']
        for i in range(len(json_data['sub_score_scores'])):
            self.sub_score.append((json_data['sub_score_names'][i], json_data['sub_score_scores'][i]))
        self.cmp = '/'.join([self.project, self.build, self.test_id, self.case_name, str(self.loop)])


class Logger(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    description = models.CharField(max_length=100)
    slave = models.ForeignKey(Slave, on_delete=models.CASCADE, null=True, blank=True)
    create_time = models.DateTimeField(auto_now=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    test_config = models.CharField(max_length=8, null=True, blank=True)
    build = models.CharField(max_length=20, null=True, blank=True)
    user = models.ForeignKey(User)

    @property
    def result_link(self):
        if self.task:
            if not self.task.test_id == 'null':
                if os.path.exists(os.path.join(DATA_PATH, self.project.name, 'raw', self.build, self.task.test_id)):
                    return '/'.join(['raw', self.project.name, self.build, self.task.test_id])
        return '#'

    @property
    def icon(self):
        if self.description == 'nt':
            return 'fa fa-tasks'

    @property
    def event(self):
        if self.description == 'nt':
            return 'new'
        if self.description == 'mt':
            return 'manual test'
        if self.description == 'ma':
            return 'manual'
        elif self.description == 'bp':
            return 'building'
        elif self.description == 'bs':
            return 'build success'
        elif self.description == 'bf':
            return 'build failed'
        elif self.description == 'cancel':
            return 'cancel'
        elif self.description == 'ff':
            return 'flash failed'
    
    @property
    def label_class(self):
        if self.description == 'bp':
            return 'warning'
        elif self.description == 'bf' or self.description == 'ff':
            return 'danger'
        elif self.description == 'bs':
            return 'success'
        elif self.description == 'cancel':
            return 'muted'
        return 'primary'
          
    @property
    def build_link(self):
        if self.test_config is None:
            return 'unknown', '', '#'
        
        target = os.path.join(DATA_PATH, 'test_configs', self.test_config)
        
        if not os.path.exists(target):
            return 'unknown', '', '#'
        try:
            dic = json.load(open(target))
            build = dic['build']
        except:
            dic = {}
            build = 'Unknown' 
        if 'buildbot_link' in dic:
            return build, '', dic['buildbot_link']
        elif 'patch_method' in dic:
            if dic['patch_method'] == 'td' or dic['patch_method'] == 'mt':
                return build, '', '#'
            elif 'base_build' in dic:
                base_build = dic['base_build']
            else:
                base_build = build
                build = 'building'
            link = os.path.join('https://buildbot.sh.intel.com/absp/builders', self.project.builder_name+'-engineering', 'builds', build)
            return build, ' based on ' + base_build, link
        else:
            return build, '', '#'


class DailySummary(object):
    def __init__(self, project_name, build, prev_build):
        self.unit = None
        self.build = build
        self.project = project_name
        self.current_dict = self.get_dict(build)
        self.prev_dict = self.get_dict(prev_build)

    @staticmethod
    def fluctuation(curt, prev, unit):

        assessment = None
        value = curt - prev
        rate = value * 100 / curt
        if value > 0:
            assessment = True
        elif value < 0:
            assessment = False

        if unit in ['ms', 's', 'sec', 'second', 'msec']:
            assessment = not assessment
        return round(value, 3), round(rate, 3), assessment

    def get_test_result(self):
        test_results = []
        build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, 'daily', self.build)
        files = os.listdir(build_path)
        for file_name in files:
            data = json.load(open(os.path.join(build_path, file_name), 'r'))
            test_results.append((data['test_id'], file_name))
        return test_results

    def get_dict(self, build):
        raw = {}
        results = {}
        build_dir = os.path.join(os.path.dirname(__file__), 'data', self.project, 'daily', build)
        for file_name in os.listdir(build_dir):
            build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, 'daily', build)
            data = json.load(open(os.path.join(build_path, file_name), 'r'))
            raw_data = RawData2(self.project, build, data['test_id'], file_name)
            if is_number(raw_data.result):
                if raw_data.case_name in raw:
                    raw[raw_data.case_name]['results'].append(float(raw_data.result))
                else:
                    raw[raw_data.case_name] = {
                        'results': [float(raw_data.result)],
                        'unit': raw_data.unit
                    }
        for case in raw:
            if len(raw[case]['results']) % 2:
                raw[case]['results'].sort()
                result = raw[case]['results'][len(raw[case]['results']) / 2]
            else:
                result = round(sum(raw[case]['results']) / len(raw[case]['results']), 3)
            results[case] = [result, raw[case]['unit']]
        return results

    @property
    def result(self):
        result = OrderedDict({})
        union_dict = list(set(self.current_dict.keys()).union(set(self.prev_dict.keys())))

        # make full boot to top
        if 'full boot' in union_dict:
            union_dict.remove('full boot')
            union_dict = ['full boot'] + union_dict

        for case in union_dict:
            if case not in self.prev_dict:
                result[case] = {
                    'result': round(self.current_dict[case][0], 3),
                    'prev': 'N/T',
                    'unit': self.current_dict[case][1],
                    'fluc': 'N/T'
                }
            elif case not in self.current_dict:
                result[case] = {
                    'result': 'N/T',
                    'prev': round(self.prev_dict[case][0], 3),
                    'unit': self.prev_dict[case][1],
                    'fluc': 'N/T'
                }
            else:
                fluc = self.fluctuation(
                    self.current_dict[case][0],
                    self.prev_dict[case][0],
                    self.current_dict[case][1]
                )
                result[case] = {
                    'result': round(self.current_dict[case][0], 3),
                    'prev': round(self.prev_dict[case][0], 3),
                    'unit': self.current_dict[case][1],
                    'fluc': fluc
                }
        um = os.path.join(os.path.dirname(__file__), 'data', self.project, 'daily', '.'.join([self.build, 'um']))
        m = os.path.join(os.path.dirname(__file__), 'data', self.project, 'daily', '.'.join([self.build, 'm']))
        if os.path.exists(um):
            print 'calculate data'
            with open(um, 'w') as f:
                f.write(json.dumps(result))
                f.close()
            os.renames(um, m)
        elif os.path.exists(m):
            print 'use static data'
        else:
            print 'generate data'
            with open(m, 'w') as f:
                f.write(json.dumps(result))
                f.close()
        return result


class RawSummary(object):
    def __init__(self, project_name, build, test_id=None):
        self.unit = None
        self.build = build
        self.test_id = test_id
        self.project = project_name

    def get_test_result(self):
        test_results = []
        build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, 'raw', self.build)
        files = os.listdir(build_path)
        for file_name in files:
            if os.path.isfile(os.path.join(build_path, file_name)):
                data = json.load(open(os.path.join(build_path, file_name), 'r'))
                test_results.append((data['test_id'], file_name))
        return test_results

    def get_dict(self):
        raw = {}
        if self.test_id:
            target_dir = os.path.join(os.path.dirname(__file__), 'data', self.project, 'raw', self.build, self.test_id)
        else:
            target_dir = os.path.join(os.path.dirname(__file__), 'data', self.project, 'raw', self.build)
        for file_name in os.listdir(target_dir):
            if os.path.isfile(os.path.join(target_dir, file_name)):
                data = json.load(open(os.path.join(target_dir, file_name), 'r'))
                raw_data = RawData2(self.project, self.build, data['test_id'], file_name)
                if is_number(raw_data.result):
                    if raw_data.case_name in raw:
                        raw[raw_data.case_name]['results'].append(float(raw_data.result))
                    else:
                        raw[raw_data.case_name] = {
                            'results': [float(raw_data.result)],
                            'unit': raw_data.unit
                        }
        # mid value
        for case in raw:
            if len(raw[case]['results']) % 2:
                raw[case]['results'].sort()
                mid_result = raw[case]['results'][len(raw[case]['results']) / 2]
            else:
                mid_result = round(sum(raw[case]['results']) / len(raw[case]['results']), 3)
            raw[case]['mid'] = mid_result
            raw[case]['min'] = min(raw[case]['results'])
            raw[case]['max'] = max(raw[case]['results'])
        return raw

class TagSummary(object):
    def __init__(self, tag_name, project_name, build, prev_build):
        self.tag = tag_name
        self.unit = None
        self.build = build
        self.project = project_name
        self.current_dict = self.get_dict(build)
        self.prev_dict = self.get_dict(prev_build)

    @staticmethod
    def fluctuation(curt, prev, unit):
        assessment = None
        value = curt - prev
        rate = value * 100 / curt
        if value > 0:
            assessment = True
        elif value < 0:
            assessment = False

        if unit in ['ms', 's', 'sec', 'second', 'msec']:
            assessment = not assessment
        return round(value, 3), round(rate, 3), assessment

    def get_test_result(self):
        test_results = []
        build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, self.tag, self.build)
        files = os.listdir(build_path)
        for file_name in files:
            data = json.load(open(os.path.join(build_path, file_name), 'r'))
            test_results.append((data['test_id'], file_name))
        return test_results

    def get_dict(self, build):
        raw = {}
        results = {}
        build_dir = os.path.join(os.path.dirname(__file__), 'data', self.project, self.tag, build)
        for file_name in os.listdir(build_dir):
            build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, self.tag, build)
            data = json.load(open(os.path.join(build_path, file_name), 'r'))
            raw_data = RawData2(self.project, build, data['test_id'], file_name)
            if is_number(raw_data.result):
                if raw_data.case_name in raw:
                    raw[raw_data.case_name]['results'].append(float(raw_data.result))
                else:
                    raw[raw_data.case_name] = {
                        'results': [float(raw_data.result)],
                        'unit': raw_data.unit
                    }
        for case in raw:
            if len(raw[case]['results']) % 2:
                raw[case]['results'].sort()
                result = raw[case]['results'][len(raw[case]['results']) / 2]
            else:
                result = round(sum(raw[case]['results']) / len(raw[case]['results']), 3)
            results[case] = [result, raw[case]['unit']]
        return results

    @property
    def result(self):
        result = {}
        for case in self.current_dict:
            if case in self.prev_dict:
                fluc = self.fluctuation(
                    self.current_dict[case][0],
                    self.prev_dict[case][0],
                    self.current_dict[case][1]
                )
                result[case] = {
                    'result': round(self.current_dict[case][0], 3),
                    'prev': round(self.prev_dict[case][0], 3),
                    'unit': self.current_dict[case][1],
                    'fluc': fluc
                }
        um = os.path.join(os.path.dirname(__file__), 'data', self.project, self.tag, '.'.join([self.build, 'um']))
        m = os.path.join(os.path.dirname(__file__), 'data', self.project, self.tag, '.'.join([self.build, 'm']))
        if os.path.exists(um):
            print 'calculate data'
            with open(um, 'w') as f:
                f.write(json.dumps(result))
                f.close()
            os.renames(um, m)
        elif os.path.exists(m):
            print 'use static data'
        else:
            print 'generate data'
            with open(m, 'w') as f:
                f.write(json.dumps(result))
                f.close()
        return result


class BKCSummary(object):
    def __init__(self, project_name, build, prev_build):
        if build == None:
            build = prev_build
            prev_build = None
        elif prev_build == None:
            pass
        else:
            pass

        self.unit = None
        self.build = build
        self.project = project_name
        self.current_dict = self.get_dict(build)
        self.prev_dict = self.get_dict(prev_build)
        self.year = build[:4]
        self.week = build[7:9]
        self.union_dict = list(set(self.current_dict).union(self.prev_dict))

    @staticmethod
    def fluctuation(curt, prev, unit):
        assessment = None
        value = curt - prev
        rate = value * 100 / curt
        if value > 0:
            assessment = True
        elif value < 0:
            assessment = False

        if unit in ['ms', 's', 'sec', 'second', 'msec']:
            assessment = not assessment
        return round(value, 3), round(rate, 3), assessment

    def get_test_result(self, build):
        if build:
            test_results = []
            build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, 'bkc', build)
            files = os.listdir(build_path)
            for file_name in files:
                data = json.load(open(os.path.join(build_path, file_name), 'r'))
                test_results.append((data['test_id'], file_name))
            return test_results
        else:
            return {}

    def get_dict(self, build):
        if build:
            raw = {}
            results = {}
            build_dir = os.path.join(os.path.dirname(__file__), 'data', self.project, 'bkc', build)
            if not os.path.exists(build_dir):
                return {}
            for file_name in os.listdir(build_dir):
                build_path = os.path.join(os.path.dirname(__file__), 'data', self.project, 'bkc', build)
                data = json.load(open(os.path.join(build_path, file_name), 'r'))
                raw_data = RawData2(self.project, build, data['test_id'], file_name)
                if is_number(raw_data.result):
                    if raw_data.case_name in raw:
                        raw[raw_data.case_name]['results'].append(float(raw_data.result))
                    else:
                        raw[raw_data.case_name] = {
                            'results': [float(raw_data.result)],
                            'unit': raw_data.unit
                        }
            for case in raw:
                if len(raw[case]['results']) % 2:
                    raw[case]['results'].sort()
                    result = raw[case]['results'][len(raw[case]['results']) / 2]
                else:
                    result = round(sum(raw[case]['results']) / len(raw[case]['results']), 3)
                results[case] = [result, raw[case]['unit']]
            return results
        else:
            return {}

    def result(self, mannual=True):
        result = {}
        if mannual:
            union_dict = filter(lambda x: x in case_list, self.union_dict)
        else:
            union_dict = filter(lambda x: x not in case_list, self.union_dict)

        for case in union_dict:
            if case in self.prev_dict and case in self.current_dict:
                fluc = self.fluctuation(
                    self.current_dict[case][0],
                    self.prev_dict[case][0],
                    self.current_dict[case][1]
                )
                result[case] = {
                    'result': round(self.current_dict[case][0], 3),
                    'prev': round(self.prev_dict[case][0], 3),
                    'unit': self.current_dict[case][1],
                    'fluc': fluc
                }
            elif case in self.prev_dict:
                result[case] = {
                    'result': None,
                    'prev': round(self.prev_dict[case][0], 3),
                    'unit': self.prev_dict[case][1],
                    'fluc': None
                }
            else:
                result[case] = {
                    'result': round(self.current_dict[case][0], 3),
                    'prev': None,
                    'unit': self.current_dict[case][1],
                    'fluc': None
                }

        # save to m file
        um = os.path.join(os.path.dirname(__file__), 'data', self.project, 'bkc', '{0}.um'.format(self.build))
        m = os.path.join(os.path.dirname(__file__), 'data', self.project, 'bkc', '{0}.m'.format(self.build))
        if os.path.exists(um):
            print 'calculate data'
            with open(um, 'w') as f:
                f.write(json.dumps(result))
                f.close()
            os.renames(um, m)
        elif os.path.exists(m):
            print 'use static data'
        else:
            print 'generate data'
            with open(m, 'w') as f:
                f.write(json.dumps(result))
                f.close()
        return result


def is_number(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


class ReportCSV(object):
    def __init__(self, session):
        project, build, test, case, loop = session.split('/')
        self.project = project
        self.build = build
        self.test = test
        self.loop = loop
        self.case = case
        self.result = 0


class CompareCart(object):
    def __init__(self, *args, **kwargs):
        self.items = []
        self.query = ''

    def add_test(self, project, build, test, loop):
        return self.items.append(ReportCSV(project, build, test, loop))
