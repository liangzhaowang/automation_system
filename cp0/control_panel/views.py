# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from cp0.lib import new_render, dict_utf8_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required
from data.models import Project
from collections import OrderedDict
from django.conf import settings
from pymongo import MongoClient, errors
import json
import redis
import requests
import subprocess
import os

# Create your views here.


rds = redis.Redis(host='localhost', port=6379)
branch_url = 'https://buildbot.sh.intel.com/absp/json_config/branches.json'
branch_nodes = '{}/android_p/products/available_products'


@permission_required('is_staff')
def index(request):
    redis_dict = {}
    for key in rds.keys():
        if rds.type(key) == 'list':
            redis_dict[key] = ', '.join(rds.lrange(key, 0, -1))
        elif rds.type(key) == 'string':
            redis_dict[key] = rds.get(key)

    # df
    if 'cp0_dev' in os.environ:
        fss = [['/dev/sda1', '30', '9', '21', '30%', 'fake data in dev mode']]
    else:
        df_list = ['/dev/sda2', '/dev/sdb']
        fss = map(lambda x:
                  subprocess.Popen('df -h ' + x, shell=True,
                                   stdout=subprocess.PIPE).communicate()[0].split("\n")[1].split(), df_list)

    context = {
        'branch_url': branch_url,
        'branch_nodes': branch_nodes,
        'redis_dict': OrderedDict(sorted(redis_dict.items(), key=lambda t: t[0])),
        'fss': fss,
        'mongo_st': mongodb_unavailable()
    }

    return new_render(request, 'cp.html', context=context)


def mongodb_unavailable():
    try:
        if settings.DEBUG:
            db_client = MongoClient(
                host='localhost', port=27017, serverSelectionTimeoutMS=1000)
        else:
            db_client = MongoClient(host='localhost', port=27017, username='cp0_admin',
                                    password='Pw$g09e3', serverSelectionTimeoutMS=1000)
        db_client.server_info()
        return ', '.join(db_client.list_database_names())
    except errors.ServerSelectionTimeoutError as e:
        return [0, e]
    except errors.OperationFailure as e:
        return [0, e]


def get_available_products(request):
    branch_dict = json.loads(requests.get(branch_url, verify=False).content)
    for project in Project.objects.all():
        if project.builder_name in branch_dict.keys():
            for product in get_product(branch_dict, branch_nodes.format(project.builder_name).split('/')):
                if product not in rds.lrange('products_' + project.builder_name, 0, -1):
                    rds.rpush('products_' + project.builder_name, product)
    return JsonResponse({'products': '1'})


def get_product(d, keys):
    for i in keys:
        if d.get(i) is not None:
            dict_values = d.get(i)
        d = dict_values
    return d
