from __future__ import print_function
from django.core.management.base import BaseCommand
from data.models import Project, Task, Slave, User
import logging
from pymongo import MongoClient, errors
from django.db import connection
import sys
import argparse
import os
import requests
import random
import os
import datetime
import string


def logger(name):
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(message)s")
    ch.setFormatter(formatter)
    l.addHandler(ch)
    return l


class Command(BaseCommand):
    help = 'Generate fake data for Developer'

    def __init__(self):
        self.logger = logger(__file__)
        self.mongo_client = self.connect_mongo_db()
        self.projects = [project.name for project in Project.objects.all()]

    def add_arguments(self, parser):
        parser.add_argument('type', type=str)
        parser.add_argument('--clean', action='store_true', help='Clean database before generate data')

    def handle(self, *args, **options):
        if options['clean']:
            self.clean_databases()

        if options['type'] == 'index':
            self.mongo_client.get_database('bxtp_ivi_o').get_collection('raw').create_index([('test_id', -1), ('test_case', 1)])
        else:
            self.generate(data_type=options['type'])

    @staticmethod
    def connect_mongo_db():
        client = MongoClient(host='localhost', port=27017)

        try:
            client.list_database_names()
            return client
        except errors.NetworkTimeout as e:
            print(e)
        except errors.OperationFailure as e:
            print(e)
        sys.exit(0)

    def clean_databases(self):
        # clean MongoDB
        for database in self.mongo_client.list_database_names():
            if database in self.projects:
                self.logger.debug('Clean database %s' % database)
                self.mongo_client.drop_database(database)

    def generate(self, data_type, count=1000):
        self.logger.debug('data type is ' + data_type)
        if os.path.exists('words'):
            words = open('words', 'r').readlines()
            words_list = words
        else:
            word_site = 'http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain'
            words = requests.get(word_site).text
            with open('words', 'w') as f:
                f.write(words)
            words_list = words.splitlines()

        tag_list = ['daily', 'raw', 'bkc']

        now = datetime.datetime.now()

        data_list = []

        for project in self.projects:
            if data_type == 'raw':
                # generate 100 tests(task)
                case_list = [words_list[random.randrange(len(words_list))].strip() for i in range(5)]
                for i in range(count):
                    tag = random.choice(tag_list)
                    dt = now + datetime.timedelta(hours=-random.randrange(1, 12) * i, seconds=-random.randrange(1, 60))
                    test_id = dt.strftime('%Y%m%d_%H%M%S')
                    test_config = ''.join(random.sample(string.ascii_letters + string.digits, 8))

                    # Sqlite3
                    Task(
                        available=False,
                        project=Project.objects.get(id=1),
                        slave=Slave.objects.get(id=1),
                        test_id=test_id,
                        submitter=User.objects.get(id=1),
                        test_config=test_config,
                        comment=' '.join(random.sample(words_list, 5))
                    ).save()

                    # MongoDB
                    # make 5 cases each test
                    for case_name in case_list:
                        # make 1-5 loops each case
                        for loop in range(random.randrange(1, 5)):
                            data_list.append({
                                'task_id': i + 1,
                                'build': str(int(i * 0.3) + 1),
                                'case_name': case_name,
                                'tag': tag,
                                'result': random.randrange(1000),
                                'test_id': test_id,
                                'unit': 'sec',
                                'config_name': '',
                                'sub_score': [['ss1', 1], ['ss2', 2]],
                                'attachments': ['attachment_1.txt', 'attachment_2.txt'],
                                'loop': loop,
                            })

                db = self.mongo_client.get_database(project)
                self.logger.debug('Writing raw data')
                db.get_collection('raw').insert_many(data_list)

            elif data_type == 'daily':
                count = 0
                db = self.mongo_client.get_database(project)
                while count < 50:
                    dt = now + datetime.timedelta(days=-count)
                    reg_test_id = dt.strftime('%Y%m%d')
                    cursors = list(db.get_collection('raw').find({'test_id': {'$regex': reg_test_id}}))
                    if cursors:
                        case_list = [cursor['case_name'] for cursor in cursors]

                        for case_name in list(set(case_list)):
                            data_list.append({
                                'build': reg_test_id,
                                'test_id': cursors[0]['test_id'],
                                'case_name': case_name
                            })
                        count += 1
                self.logger.debug('Writing raw data')
                db.get_collection('daily').insert_many(data_list)
            elif data_type == 'bkc':
                count = 0
                db = self.mongo_client.get_database(project)
                while count < 7:
                    dt = now + datetime.timedelta(days=-count-1)
                    reg_test_id = dt.strftime('%Y%m%d')
                    ww_build = str(dt.year) + '_WW' + str(dt.day)
                    bw_build = str(dt.year) + '_BW' + str(dt.day)
                    cursors = list(db.get_collection('raw').find({'test_id': {'$regex': reg_test_id}}))
                    if cursors:
                        case_list = [cursor['case_name'] for cursor in cursors]

                        for case_name in list(set(case_list)):
                            data_list.append({
                                'build': ww_build,
                                'test_id': cursors[0]['test_id'],
                                'case_name': case_name
                            })
                            data_list.append({
                                'build': bw_build,
                                'test_id': cursors[1]['test_id'],
                                'case_name': case_name
                            })
                        count += 1
                self.logger.debug('Writing bkc/weekly data')
                db.get_collection('bkc').insert_many(data_list)
            else:
                self.logger.error('invalid data type')
        self.mongo_client.close()
