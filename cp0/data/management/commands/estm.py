from django.core.management.base import BaseCommand
from data.models import Task, Slave, BuildPath, Logger, Project
from django.conf import settings
from django.http import request
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from home.tasks import Testing
from django.utils import timezone
from data.api import broadcast
import requests
import time
import logging
import json
import os
import urllib
import urllib2
import re
import sys
import datetime


timeout = 300
config_dir = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs')
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
columns = 100


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

class Command(BaseCommand):
    logger = logger('estm', os.path.join(settings.BASE_DIR, 'logs', 'estm.log'))

    def total_est_time(self, slaveip):
        try:
            result = requests.get('http://{0}:9001/get_testing_task_total_est/'.format(slaveip)).content
            value = json.loads(result)['result']
            return value
        except Exception as e:
            return 0

    def handle(self, *args, **options):
        while True:
            try:
                self.logger.debug('=' * columns)
                for slave in Slave.objects.all():
                    testing = Testing(slave)
                    if testing.alive:
                        self.logger.debug('slave: #{0} {1}'.format(slave.id, slave.ip))
                        starttime = testing.task.start_time
                        currentime = datetime.datetime.now(tz=timezone.utc)
                        est = int(self.total_est_time(slave.ip))
                        print "task",testing.task.id
                        print "est time",est
                        print "test time",(currentime - starttime).seconds
                        et = -110 if slave.ip == '10.239.93.147' else 7200 
                        if (currentime - starttime).seconds >=(est + et):
                            print "task %s timeout" % (testing.task.id)
                            res = requests.post('http://cubep.sh.intel.com:8000/api/broadcast/', data={'test_id': 'None', 'task_id':testing.task.id, 'msg': 'failed', 'cc': 'shanx.shan@intel.com'})
                            if res.status_code == 200:
                                print 'send mail success!'
                            else:
                                print 'send mail failed:'
                                print res.text
                            Logger.objects.filter(task_id=testing.task.id).update(description='cancel')
                            if testing.task.available:
                                Task.objects.filter(id=testing.task.id).update(available=False)
                                return
                            else:
                                requests.get('http://{0}:9001/reset/'.format(slave.ip), timeout=5)
                                testing.task.end()
                                testing.task.save()
                        self.logger.debug('_' * columns)
                        
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print exc_type, fname, exc_tb.tb_lineno
                print e
            print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'wait 5 mins...'
            time.sleep(timeout)

