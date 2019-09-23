from django.core.management.base import BaseCommand
from data.models import Task, Slave, BuildPath, Logger, Project
from data.buildbot import Buildbot
from django.conf import settings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
import time
import logging
import json
import os
import urllib
import urllib2
import re
import sys


timeout = 30
config_dir = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs')
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
columns = 500


def logger(name, file_path):
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    fh = logging.FileHandler(file_path)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    l.addHandler(ch)
    l.addHandler(fh)
    return l


base_buildbot_link = 'https://buildbot.sh.intel.com/absp/json/builders/{}-engineering/'


class Command(BaseCommand):
    logger = logger('taskm', os.path.join(settings.BASE_DIR, 'logs', 'taskm.log'))

    def new_test_id(self):
        test_id = time.strftime('%Y%m%d_%H%M%S')
        return test_id

    def create_raw_folder(self, project, build, test_id):
        data_dir = os.path.join(settings.BASE_DIR, 'data', 'data')
        target_dir = os.path.join(data_dir, project, 'raw', build, test_id)
        self.logger.debug('create dir %s', target_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    def fetch_eb_number(self, task):
        config = json.load(open(os.path.join(config_dir, task.test_config), 'r'))
        if config['patch_method'] == 'bap':
            self.logger.debug('#{}, {}'.format(task.id, task.test_config))
            project = config['project_name']
            builder = Project.objects.get(name=project).builder_name
            buildbot_link = base_buildbot_link.format(builder)
            building_list = json.loads(requests.get(buildbot_link, verify=False).text)['currentBuilds']
            query_attrs = '&'.join(map(lambda x: 'select='+str(x), building_list))
            building_info_url = buildbot_link + 'builds?' + query_attrs
            building_info = json.loads(requests.get(building_info_url, verify=False).content)
            
            if 'base_build' not in config:
                self.logger.debug('\tsearching EB number with reason: %s' % task.test_config)
                for k, v in building_info.items():
                    if v is None or 'properties' not in v:
                        continue
                    for item in v['properties']:
                        if task.test_config in item:
                            self.logger.debug('new eb: %s' % k)
                            with open(os.path.join(config_dir, task.test_config), 'w') as fs:
                                config['base_build'] = config['build']
                                config['build'] = k
                                config['build_url'] = BuildPath.objects.get(project__name=config['project_name'], build_type=0).url
                                fs.write(json.dumps(config))
                                fs.close()
            else:
                self.logger.debug('\tEB number already fetched')


    def handle(self, *args, **options):
        while True:
            try:
                self.logger.debug('=' * columns)
                for slave in Slave.objects.all():
                    self.logger.debug('_' * columns)
                    self.logger.debug('slave: #{0} {1}'.format(slave.id, slave.ip))
                    tasks = Task.objects.filter(available=True, slave=slave)
                    if len(tasks):
                        self.logger.debug('queue: {}'.format(', '.join(map(lambda x: str(x.id), tasks))))

                        self.logger.debug('[**********fetch EB number**********]')
                        for task in tasks:
                            self.fetch_eb_number(task)

                        for i in range(len(tasks)):
                            task = tasks[i]
                            task_logger = Logger.objects.filter(task=task) if Logger.objects.filter(task=task) else None
                            test_id = None
                            self.logger.debug('current task: #{0} {1}'.format(task.id, task.test_config))
                            cfg_detail = json.load(open(os.path.join(config_dir, task.test_config), 'r'))
                            self.logger.debug('type: {0}'.format(cfg_detail['tag']))

                            # check slave status
                            try:
                                session = requests.Session()
                                session.trust_env = False
                                url = 'http://{}:9001/stat/'.format(slave.ip)
                                stat = json.loads(requests.get(url, timeout=5).text)
                            except Exception as e:
                                self.logger.debug(e)
                                self.logger.debug('slave is offline, skip')
                                break

                            # build with all patch
                            if cfg_detail['patch_method'] == 'bap':
                                self.logger.debug('test method: {0}'.format('bap'))
                                self.logger.debug('project: {0}'.format(cfg_detail['project_name']))
                                project = cfg_detail['project_name']
                                builder = Project.objects.get(name=project).builder_name
                                buildbot_link = base_buildbot_link.format(builder)
                                building_list = json.loads(requests.get(buildbot_link, verify=False).text)['currentBuilds']
                                query_attrs = '&'.join(map(lambda x: 'select='+str(x), building_list))

                                building_info_url = buildbot_link + 'builds?' + query_attrs
                                building_info = json.loads(requests.get(building_info_url, verify=False).content)

                                # if config base build is not exist
                                if 'base_build' not in cfg_detail:
                                    self.logger.debug('searching EB number with reason: %s' % task.test_config)

                                    for k, v in building_info.items():
                                        if v is None or 'properties' not in v:
                                            continue
                                        for item in v['properties']:
                                            if task.test_config in item:
                                                self.logger.debug('new eb: %s' % k)
                                                with open(os.path.join(config_dir, task.test_config), 'w') as fs:
                                                    cfg_detail['base_build'] = cfg_detail['build']
                                                    cfg_detail['build'] = k
                                                    cfg_detail['build_url'] = BuildPath.objects.get(project__name=cfg_detail['project_name'], build_type=0).url
                                                    fs.write(json.dumps(cfg_detail))
                                                    fs.close()
                                    break

                                # check eb status
                                else:
                                    eb_url = '{0}builds/{1}'.format(buildbot_link, cfg_detail['build'])
                                    status = json.loads(requests.get(eb_url, verify=False).content)['text']
                                    self.logger.debug('EB {0} status: {1}'.format(cfg_detail['build'], status))
                                    if len(status) == 0:
                                        task_logger.update(description='bp')
                                        task_logger.update(build=cfg_detail['build'])
                                        continue
                                    elif status[1] == 'successful' or status[1] == 'Exception occured!':
                                        task_logger.update(description='bs')
                                        test_id = self.new_test_id()
                                    elif status[0] in ['failed', 'exception']:
                                        tasks.update(available=False, comment=status[2])
                                        task_logger.update(description='bf')
                                        continue
                                    else:
                                        self.logger.debug('skip this task\n')
                                        continue

                            # test directly
                            elif cfg_detail['patch_method'] == 'td':
                                # send task
                                test_id = self.new_test_id()

                            # slave is online
                            if 'atf_task_id' in stat:
                                if stat['atf_task_id'] != 'None' and stat['atf_task_id'] != '':
                                    self.logger.debug('atf_task_id: ' + stat['atf_task_id'])
                                    self.logger.debug('slave is busy')
                                    break
                                if cfg_detail['building'] == True:
                                    build_type_id = cfg_detail['build_type_id']
                                    project_id = cfg_detail['project_id']
                                    buildpath = BuildPath.objects.get(build_type=build_type_id, project__id=project_id)
                                    self.logger.debug('buildpath id:' + str(buildpath.id))
                                    buildbot_link = buildpath.buildbot_link
                                    self.logger.debug('buildbot: ' + buildbot_link)
                                    builder = re.search(r'builders/(.+)', buildbot_link).group(1)
                                    buildbot = Buildbot(builder, auth=('weiyunyx', 'ZAQxsw@123456'))
                                    status = buildbot.check_build_status(cfg_detail['build'])
                                    if status['finished']:
                                        if status['status'] in ['success', 'warnings', 'exception']:
                                            task_logger.update(description='bs')
                                        else:
                                            task.available = False
                                            task.save()
                                            task_logger.update(description='bf')
                                            self.logger.debug('build failed')
                                            break
                                    else:
                                        self.logger.debug('building')
                                        continue
                            else:
                                self.logger.debug('slave has no redis server')
                                break

                            # send task to slave
                            self.logger.debug('slave: #{0} {1}, {2} in queue'.format(slave.id, slave.ip, len(tasks)))
                            self.logger.debug('recent task({0}): {1}'.format(task.id, task.test_config))
                            self.logger.debug('type: {0}'.format(cfg_detail['tag']))
                            self.logger.debug('build: {0}'.format(cfg_detail['build']))
                            self.logger.debug('send task to slave')

                            if test_id is not None:
                                self.create_raw_folder(test_id=test_id, project=cfg_detail['project_name'], build=cfg_detail['build'])
                                url = '/'.join(['http:/', slave.ip + ':9001', 'test/'])
                                data = urllib.urlencode({
                                    'test_config': task.test_config,
                                    'task_id': task.id,
                                    'test_id': test_id
                                })
                                self.logger.debug(data)
                                if urllib2.urlopen(url, data, timeout=1).read() == 'Aye Sir':
                                    print 'task sent'
                                    task.test_id = test_id
                                    task.available = False
                                    task.start()
                                    task.save()
                                    time.sleep(1)
                                break
                    else:
                        self.logger.debug('No tasks, skip')
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print exc_type, fname, exc_tb.tb_lineno
                print e
            time.sleep(timeout)
