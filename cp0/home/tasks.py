import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.conf import settings
# from datetime import timedelta, datetime, tzinfo, date
import datetime
from django.contrib.syndication.views import Feed
from cp0.lib import new_render
from django.urls import reverse
import urllib2
import os
from data.models import DailySummary, RawData, Project, Slave, RawData2, Logger, Task, is_number, TestConfig
import redis
import requests
import warnings


warnings.filterwarnings(
    'ignore', r"DateTimeField .* received a naive datetime",
    RuntimeWarning, r'django\.db\.models\.fields',
)

rds = redis.Redis(host='localhost', port=6379)
DATA_PATH = os.path.join(settings.BASE_DIR, 'data', 'data')


class TaskFeed(Feed):
    title = 'Task status'
    link = '/task/'
    description = 'test'

    def items(self):
        return Task.objects.order_by('-create_time')[:5]

    def item_title(self, item):
        return '#{0}, build: {1}'.format(item.pk, item.build())

    def item_description(self, item):
        if item.available:
            return 'New task added'
        else:
            return ''
    
    def item_link(self, item):
        return 'http://10.239.93.171:8000'


class Testing(object):
    def __init__(self, slave):
        self.ip = ':'.join([slave.ip, '9001'])
        self.task_id = None
        self.test_id = None
        self.task = None
        self.alive = False
        self.config = None
        self.progress = 0
        self.current = 'Download & Flashing'
        self.fetch()
        self.id = slave.id

    @property
    def build_link(self):
        try:
            self.task = Task.objects.get(id=int(self.task_id))
            dic = TestConfig(self.task.test_config)
            build_type = dic['build_type']
            build = dic['build']
            patch_method = dic['patch_method']
            if 'buildbot_link' in dic:
                return build, '', dic['buildbot_link']
            elif patch_method != 'td':
                if 'base_build' in dic:
                    base_build = dic['base_build']
                else:
                    base_build = build
                    build = 'building'
                link = os.path.join('https://buildbot.sh.intel.com/absp/builders',self.task.project.builder_name+'-engineering','builds',build)
                return build, ' based on ' + base_build, link
            else:
                link = os.path.join('https://buildbot.sh.intel.com/absp/builders',self.task.project.builder_name+'-'+build_type,'builds',build)
                return build, '', '#'
        except Exception, e:
            return '', '', '#'

    def fetch(self):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get('/'.join(['http:/', self.ip, 'stat/']), timeout=0.3).text
            d = json.loads(response)
            if d['atf_task_id'] != 'None':
                self.alive = True
                self.task_id = d['atf_task_id']
                self.test_id = d['atf_test_id']
                self.task = Task.objects.get(id=int(self.task_id))
                self.config = self.task.test_config
                config_path = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', self.config)
                self.config = json.load(open(config_path, 'r'))
                case_loop = 0 if d['atf_case_index'] =='None' else int(self.config['case_loop'][int(d['atf_case_index'])])
                case_index_stat =0 if d['atf_case_index'] =='None' else int(d['atf_case_index'])
                case_loop_stat = 0 if d['atf_loop_index'] =='None' else int(d['atf_loop_index'])
                progress = case_loop * case_index_stat + case_index_stat + case_loop_stat
                summary = sum(map(lambda x: int(x), self.config['case_loop']))
                self.progress = round(float(progress * 100 / summary), 3)
                self.current = '{0} ({1}/{2})'.format(self.config['case_name'][case_index_stat], case_loop_stat, case_loop)
        except Exception, e:
            print self.ip, e
            pass


def index(request):
    today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
    logger = map(logger_format, Logger.objects.filter(create_time__range=(today_min, today_max)))
    slaves = Slave.objects.all()
    testing_tasks = []
    tasks_estimate = []
    slave_estimate = []

    for slave in slaves:
        testing = Testing(slave)
        if testing.alive:
            testing_tasks.append(testing)
    
    available_tasks = Task.objects.filter(available=True)
    manual_tasks = [l.task for l in Logger.objects.filter(description='mt') if l.result_link == '#']

    context = {
        'subtitle': 'Overview',
        'loggers': logger[::-1],
        'testing': testing_tasks,
        'queue': list(available_tasks) + manual_tasks,
        'warning': rds.get('tasks'),
        'current_time': datetime.datetime.now(tz=timezone.utc),
        'tasks_estimate': tasks_estimate,
        "slave_estimate": slave_estimate,
    }
    return new_render(request, 'tasks.html', context, title='CP0', subtitle='Tasks')


def logger_format(logger):
    seconds = (datetime.datetime.now().replace(tzinfo=UTC(8)) - logger.create_time).seconds
    if seconds > 3600:
        interval_text = '{0} hr, {1} min ago'.format(int(seconds / 3600), int(seconds % 3600 / 60))
    elif seconds > 60:
        interval_text = '{0} min ago'.format(int(seconds % 3600 / 60))
    else:
        interval_text = 'Just now'
    logger.time_interval = interval_text
    return logger


class UTC(datetime.tzinfo):
    def __init__(self,offset=0):
        self._offset = offset

    def utcoffset(self, dt):
        return datetime.timedelta(hours=self._offset)

    def tzname(self, dt):
        return "UTC +%s" % self._offset

    def dst(self, dt):
        return datetime.timedelta(hours=self._offset)
