from django.test import TestCase
from data.models import Slave
import requests
import time
import logging

logger = logging.getLogger('django_test')


# Create your tests here.
class SlaveConnectionTest(TestCase):
    def test_get_slave_info(self):
        print 'with proxy'
        for slave in Slave.objects.all():
            start = time.time()
            requests.get('http://%s:9001/stat/' % slave.ip)
            time_delta = time.time() - start
            print '{}\t{:.3}s'.format(slave.ip, time_delta)
        self.assertEqual(1, 1)
   
    def test_get_slave_info_no_proxy(self):
        print 'no proxy'
        session = requests.Session()
        session.trust_env = False
        for slave in Slave.objects.all():
            start = time.time()
            session.get('http://%s:9001/stat/' % slave.ip)
            time_delta = time.time() - start
            print '{}\t{:.3}s'.format(slave.ip, time_delta)
            self.assertEqual(1, 1)
