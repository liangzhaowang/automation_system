# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.contrib.auth.models import User
from models import Project, BuildPath, BUILD_TYPE_CHOICES, Task, get_raw, Slave, Logger, is_number, ConfigTemplate
from home.models import Message
from itertools import groupby
from collections import OrderedDict
from cp0.lib import auth_header
from data.buildbot import Buildbot
import pytz
import redis
import json
import subprocess
import re
import time
import urllib2
import os
import sys
import datetime
import socket
import requests
import logging
import xlwt
from mail import MailSender
from pymongo import MongoClient
reload(sys)
sys.setdefaultencoding("utf8")

data_path = os.path.join(os.path.dirname(__file__), 'data')
null_proxy_handler = urllib2.ProxyHandler({})
opener = urllib2.build_opener(null_proxy_handler)
urllib2.install_opener(opener)
rds = redis.Redis(host='localhost', port=6379)
logger = logging.getLogger('django.request')

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.0 Chrome/30.0.1599.101 Safari/537.36',
    'Connection': 'keep-alive'
}

DEV = 'cp0_dev' in os.environ
if DEV:
    db_client = MongoClient(host='localhost', port=27017)
else:
    db_client = MongoClient(host='localhost', port=27017, username='cp0_admin', password='Pw$g09e3')

# db_client.get_database('bxtp_ivi_o').get_collection('raw').ensure_index({'test_id': -1, 'case_name': 1})


def auth_header_api(request):
    return JsonResponse(auth_header())


def active_project(request):
    try:
        project_id = int(request.POST['id'])
        active = True if request.POST['active'] == 'true' else False
        project = Project.objects.get(id=project_id)
        project.active = active
        project.save()
        return HttpResponse(str(project.active))
    except expression as identifier:
        return HttpResponse(str(project.active))


def set_current_build_test_tag(project, tag, build, subData):
    try:
        dataList = list()
        for i in xrange(len(subData)):
            find_one_data = {'build': build, "case_name": subData[i][0]}
            dataList.append(db_client.get_database(project).get_collection(tag).find_one(find_one_data))
        flag = True
        pca_raw_tag = {"test_tag": "pca_raw"}
        raw_collection = db_client.get_database(project).get_collection("raw")
        for item in dataList:
            if "bkc" == tag:
                find_data = {
                    "build": item.get("build"),
                    "case_name": item.get("case_name"),
                    "test_id": item.get("test_id")
                }
                flags = raw_collection.update(find_data, {"$set": pca_raw_tag}, multi=True)
            else:
                find_data = {
                     "build": item.get("build"),
                     "case_name": item.get("case_name"),
                     "result":item.get("result")
                }
                flags = raw_collection.update(find_data, {"$set": pca_raw_tag}, multi=True)
            flag &= flags['updatedExisting']

        if flag:
            return True
        else:
            return False
    except Exception, e:
        print e
        return False


def retest(request):
    try:
        config_name = request.POST['config_name']
        new_task = Task(
            test_config=config_name,
            project=Project.objects.get(id=int(request.POST['project_id'])),
            slave=Slave.objects.get(id=int(request.POST['slave_id'])),
            submitter=request.user,
            comment="retest"
        )
        new_task.save()

        Logger(
            project=new_task.project,
            slave=new_task.slave,
            description='nt',
            user=request.user,
            build=request.POST['build'],
            test_config=config_name,
            task=new_task
        ).save()
        return JsonResponse({'success': True, 'msg': str(new_task.id)})
    except Exception as e:
        return JsonResponse({'success': False, 'msg': repr(e)})


def autotest(request):
    try:
        config_name = time.strftime("%m%d%H%M", time.localtime(time.time()))
        config_template = json.load(open(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', 'template', request.POST['template_name']), 'r'))
        config_template['build'] = request.POST['build']
        with open(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', config_name), 'w+') as config_file:
            config_file.write(json.dumps(config_template, indent=4))

        new_task = Task(
            test_config=config_name,
            project=Project.objects.get(id=int(config_template['project_id'])),
            slave=Slave.objects.get(id=int(config_template['slave_id'])),
            submitter=User.objects.get(id=1),
            comment="autotest"
        )
        new_task.save()

        Logger(
            project=new_task.project,
            slave=new_task.slave,
            description='nt',
            user=User.objects.get(id=1),
            build=request.POST['build'],
            test_config=config_name,
            task=new_task
        ).save()
        return JsonResponse({'success': True, 'msg': str(new_task.id)})
    except Exception as e:
        return JsonResponse({'success': False, 'msg': repr(e)})


def favorite(request):
    task_id = request.POST['task_id']
    task = Task.objects.get(id=int(task_id))
    task.favorites.add(request.user)
    return JsonResponse({'success': True})


def unfavorite(request):
    task_id = request.POST['task_id']
    task = Task.objects.get(id=int(task_id))
    task.favorites.remove(request.user)
    return JsonResponse({'success': True})


def progress(request, slave_id):
    try:
        url = '/'.join(['http:/', Slave.objects.get(id=int(slave_id)).ip + ':9001', 'stat/'])
        session = requests.Session()
        session.trust_env = False
        response = session.get(url, headers=header, timeout=0.3).text
        dic_response = json.loads(response)
        if dic_response['atf_current'] == 'None':
            dic_response['atf_current'] = 'Download & Flashing'
            dic_response['atf_progress'] = '0.0'
        return JsonResponse(dic_response, safe=False)
    except:
        return {}


def slave_stat(request):
    stats = {}
    for slave in Slave.objects.all():
        url = '/'.join(['http:/', slave.ip + ':9001', 'stat/'])
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.get(url, headers=header, timeout=0.3).text
            stat = json.loads(response)
            if stat['atf_test_id'] == 'None':
                stat['stat'] = 'standby'
                stat['class'] = 'label label-primary pull-right'
            else:
                stat['stat'] = 'testin'
                stat['class'] = 'label label-warning pull-right'
            stats[str(slave.id)] = stat

        except Exception as e:
            stats[str(slave.id)] = {'stat': 'offline', 'class': 'label label-danger pull-right'}

    return JsonResponse(stats)


def data_maker(request):
    if request.method == 'POST':
        build = request.POST['build']
        project = request.POST['project']
        test_id = request.POST['test_id']
        case = request.POST['case']
        unit = request.POST['unit']
        result = request.POST['result']

        if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build)):
            os.mkdir(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build))
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id)):
            os.mkdir(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id))
        with open(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id, case + '_0'),
                  'w') as fp:
            data = {
                'project': project,
                'sub_score_scores': [],
                'sub_score_names': [],
                'unit': unit,
                'result_file_name': case,
                'result': result,
                'test_id': test_id,
                'tag': 'bkc',
                'case_name': case,
                'loop': 0,
                'build': build
            }
            fp.write(json.dumps(data))
            fp.close()

        if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'bkc', build)):
            os.mkdir(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'bkc', build))
        with open(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'bkc', build, case + '_0'), 'w') as fp2:
            data2 = {
                'test_id': test_id
            }
            fp2.write(json.dumps(data2))
            fp2.close()

        return HttpResponse('success')
    else:
        return HttpResponse('')


def history_builds(request, project):
    start = datetime.datetime.strptime(request.GET['start'], '%Y-%m-%d').strftime('%Y%m%d')
    end = datetime.datetime.strptime(request.GET['end'], '%Y-%m-%d').strftime('%Y%m%d')
    user_id = request.GET['user_id'] if 'user_id' in request.GET else None

    content = []

    query = {'test_id': {'$gt': start + '_000000', '$lt': end + '_000000'}}
    raw = list(db_client.get_database(project).get_collection('raw').find(query).sort('test_id'))
    d = {}

    for entry in raw:
        date_str = entry['test_id'][:8]
        if date_str not in d:
            d[date_str] = []
        if entry['build'] not in d[date_str]:
            if user_id and entry['task_id']:
                try:
                    if Task.objects.get(id=entry['task_id']).submitter.id == int(user_id):
                        d[date_str].append(entry['build'])
                        content.append({
                            'title': entry['build'],
                            'color': '#007500' if entry['test_tag'] == 'mt' else '#3882BA',
                            'start': datetime.datetime.strptime(entry['test_id'], '%Y%m%d_%H%M%S'),
                            'last_test_id': entry['test_id'],
                        })
                except:
                    continue
            if not user_id:
                d[date_str].append(entry['build'])

                content.append({
                    'title': entry['build'],
                    'color': '#007500' if entry['test_tag'] == 'mt' else '#3882BA',
                    'start': datetime.datetime.strptime(entry['test_id'], '%Y%m%d_%H%M%S'),
                    'last_test_id': entry['test_id'],
                })
    return JsonResponse(content, safe=False)


def test_id_list(project, build):
    test_ids = []
    entries = db_client.get_database(project).get_collection('raw').find({'build': build})
    for entry in entries:
        if entry['test_id'] not in test_ids:
            test_ids.append(entry['test_id'])
    return test_ids


def raw_case_data(project, test_id, case_name):
    query_dict = {'case_name': case_name, 'test_id': test_id}
    entries = db_client.get_database(project).get_collection('raw').find(query_dict).sort('test_id')
    return entries


def raw_data(project, build, test_id=None):
    logger.debug('project ' + project)
    query_dict = {'build': build}
    if test_id:
        query_dict['test_id'] = test_id
    logger.debug('query: tid {}, build {}'.format(test_id, build))
    entries = db_client.get_database(project).get_collection('raw').find(query_dict).sort('test_id')
    return entries


def daily_data(project):
    entries = db_client.get_database(project).get_collection('daily').find().sort('build')
    return entries


def weekly_data(project):
    entries = db_client.get_database(project).get_collection('bkc').find().sort('build')
    return entries


def history_builds_tag(request, project, tag):
    content = []
    tag_root = os.path.join(settings.BASE_DIR, 'data', 'data', project, tag)
    if os.path.exists(tag_root):
        builds = filter(lambda x: os.path.isdir(os.path.join(tag_root, x)), os.listdir(tag_root))

    history_root = os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw')
    if os.path.exists(history_root):
        for build in builds:
            first = os.listdir(os.path.join(history_root, build))[0]
            if len(first) == 15:
                dts = [first[:4], first[4:6], first[6:8], first[9:11], first[11:13], first[13:15]]
                dts = list(map(lambda x: int(x), dts))
                content.append({
                    "title": build,
                    "start": datetime.datetime(dts[0], dts[1], dts[2], dts[3], dts[4], dts[5])
                })
    return JsonResponse(content, safe=False)


# @cache_page(60*1)
def history_tests(request, project, build):
    content = []
    history_root = os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build)
    tests = os.listdir(os.path.join(history_root))
    for test in tests:
        start_time = time.localtime(os.stat(os.path.join(history_root, test)).st_ctime)
        content.append({
            "id": test,
            "start": time.strftime("%H", start_time)
        })
    return JsonResponse(content, safe=False)


def test_result(request):
    if request.method == 'POST':
        logger.debug('post data')
        logger.debug(str(request.POST['data']))

        post = json.loads(request.POST['data'])
        project = post['project']
        test_id = post['test_id']
        build = post['build']
        config_name = post['config_name']
        case_name = post['case_name']
        result = post['result']
        loop = post['loop']
        sub_score_scores = post['sub_score_scores']
        sub_score_names = post['sub_score_names']
        unit = post['unit']
        test_tag = post['test_tag'] if 'test_tag' in post else ''

        if case_name.strip() == '':
            return HttpResponse('Empty')

        db = db_client.get_database(project)

        result = 'Null' if result == '' else result
        display_build = ""
        tag = ""
        # check raw folder
        if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id)):
            os.makedirs(os.path.join(settings.BASE_DIR, 'data', 'data', project, 'raw', build, test_id))
        if os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', config_name)):
            if os.path.isfile(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', config_name)):
                d = json.load(open(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', config_name), 'r'))
                display_build = d['display_build'] if 'display_build' in d else post['display_build']
                tag = d['tag']
            elif "tag" in post and "display_build" in post:
                display_build = post['display_build']
                tag = post['tag']
        else:
            display_build = post['display_build']
            tag = post['tag']
        data = {
            'task_id': post['task_id'],
            'build': build,
            'case_name': case_name,
            'tag': tag,
            'test_tag': test_tag,
            'result': result,
            'test_id': test_id,
            'unit': unit,
            'config_name': config_name,
            'sub_score': [[name, sub_score_scores[i]] for i, name in enumerate(sub_score_names)],
            'loop': loop,
        }

        # add test_set
        if 'test_set' in d:
            data['test_set'] = d['test_set']

        db.get_collection('raw').insert(data)
        if tag == 'daily':
            origin_json = {
                'build': display_build,
                'case_name': case_name
            }
            daily_json = {
                'test_id': test_id,
                'build': display_build,
                'case_name': case_name
            }
            if db.get_collection('daily').find(origin_json).count():
                db.get_collection('daily').update(origin_json, daily_json, upsert=True)
            else:
                db.get_collection('daily').insert(daily_json)
        elif tag == 'bkc':
            origin_json = {
                'build': display_build,
                'case_name': case_name
            }
            bkc_json = {
                'test_id': test_id,
                'build': display_build,
                'case_name': case_name
            }
            if db.get_collection('bkc').find(origin_json).count():
                db.get_collection('bkc').update(origin_json, bkc_json, upsert=True)
            else:
                db.get_collection('bkc').insert(bkc_json)
        db_client.close()
        try:
            t = Task.objects.get(id=int(post['task_id']))
            t.end()
            t.save()
        except:
            pass
        return HttpResponse('result uploaded')
    return Http404()


def test_attachment(request):
    if request.method == 'POST':
        project = request.POST['project']
        test_id = request.POST['test_id']
        build = request.POST['build']
        config_name = request.POST['config_name']
        case_name = request.POST['case_name']
        file_name = request.POST['file_name']
        loop = request.POST['loop']

        db = db_client.get_database(project)

        # read config
        d = json.load(open(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', config_name), 'r'))

        # mkdir
        folder = case_name
        dir_path = os.path.join(data_path, project, 'raw', build, test_id, folder)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        http_file_name = file_name
        print 'attachment', http_file_name
        file_ext, file_name = http_file_name.split('.')[-1], '.'.join(http_file_name.split('.')[:-1])
        attachment_name = file_name + '_' + str(loop) + '.' + file_ext
        with open(os.path.join(dir_path, attachment_name), 'wb') as f:
            for chunk in request.FILES['document'].chunks():
                f.write(chunk)
            f.close()

        # add to database
        origin = {
            'build': build,
            'case_name': case_name,
            'test_id': test_id,
            'loop': int(loop),
        }

        cursor = db.get_collection('raw').find_one(origin)
        if 'attachments' in cursor:
            if attachment_name not in cursor['attachments']:
                attachments = cursor['attachments']
                attachments.append(attachment_name)
                db.get_collection('raw').update_one(origin, {'$set': {'attachments': attachments}}, True)
        else:
            db.get_collection('raw').update_one(origin, {'$push': {'attachments': attachment_name}})
        return HttpResponse('attachment uploaded')


def download_daily_excel(request, project_name, build_name):
    builds = build_list(project_name, 'daily')
    current_build_index = builds.index(build_name)
    prev_build = builds[current_build_index + 1] if len(builds) > current_build_index + 1 else None
    current_data = list(get_result_by_tag(project_name, 'daily', build_name, include_raw=True))
    prev_data = list(get_result_by_tag(project_name, 'daily', prev_build)) if prev_build else []
    summary = OrderedDict()
    current_data = sorted(current_data, key=lambda x: [x.case_name in ['full boot']], reverse=True)

    for d in current_data:
        pd = [pd for pd in prev_data if pd.case_name == d.case_name]
        reverse = -1 if d.raw[0]['unit'] in ('sec', 'ms', 'msec') else 1
        result = d.result if is_number(d.result) else False
        prev_result = pd[0].result if len(pd) else False
        if is_number(result) and is_number(prev_result):
            rate = round(((float(result) - float(prev_result)) / float(prev_result) * 100), 2) if prev_result and result else False
            fluc = float(result) - float(prev_result) if prev_result and result else False
        else:
            rate = False
            fluc = False

        summary[d.case_name] = {
            'unit': d.raw[0]['unit'],
            'prev': prev_result,
            'result': d.result,
            'fluc': fluc,
            'rate': rate,
            'down': rate * reverse < 0
        }

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Daily', cell_overwrite_ok=True)
    ws.col(0).width = 6000
    ws.col(3).width = 4000
    ws.col(4).width = 4000
    ws.col(5).width = 3000
    style0 = xlwt.easyxf(
        'font: name Times New Roman, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style1 = xlwt.easyxf(
        'font: name Times New Roman, color-index yellow, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style2 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz left;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    style3 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    titles = [["Test Case", "Unit", "Target", "Previous", "Current", "Fluctuation"], ["", "", "", prev_build, build_name, ""]]
    for i, title in enumerate(titles):
        for j, t in enumerate(title):
            style = style0 if i == 0 else style1
            ws.row(i).height_mismatch = True
            ws.row(i).height = 350
            ws.write(i, j, t, style)
    i = 2
    for key in summary:
        ws.row(i).height_mismatch = True
        ws.row(i).height = 320
        ws.write(i, 0, key, style2)
        ws.write(i, 1, summary[key]['unit'], style3)
        ws.write(i, 2, '', style3)
        ws.write(i, 3, summary[key]['prev'], style3)
        ws.write(i, 4, summary[key]['result'], style3)
        ws.write(i, 5, ('-' if summary[key]['down'] else '') + str(abs(summary[key]['rate'])) + "%", style3)
        i += 1

    wb.save('/tmp/'+build_name+'.xls')

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                ch = f.read(chunk_size)
                if ch:
                    yield ch
                else:
                    break
    excel_name = build_name + '.xls'
    response = StreamingHttpResponse(file_iterator('/tmp/' + build_name + '.xls'))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(excel_name)
    return response

def download_eb_excel_bk(request, project_name, build_name):
    all_casename = []
    case_unit = []
    result_dic = {"test_id":[], "build":[], "unit":[], "case_data":[]}
    case = ''
    for i in request.session['cmp']:
        project = i.split("/")[0]
        build = i.split("/")[1]
        test_id = i.split("/")[2]
        entries = raw_data(project, build, test_id) if build else []
        data = get_raw(entries, raw_data=False, med_and_avg=True, max_and_min=True)
        tmp_data = {}
        for item in data:
            if item.case_name not in all_casename:
                all_casename.append(item.case_name)
                case_unit.append(item.unit)
            tmp_data[item.case_name] = item.average or item.median
        result_dic["case_data"].append(tmp_data)
        result_dic["test_id"].append(test_id)
        result_dic["build"].append(build)

    data_table = []
    fluent = []
    rate = []
    for i, case in enumerate(all_casename):
        row = []
        for index,test_id in enumerate(result_dic["test_id"]):
            if case in result_dic["case_data"][index]:
                row.append(result_dic["case_data"][index][case])
            else:
                row.append("None")

        s = float(result_dic["case_data"][0][case]) if (case in result_dic["case_data"][0] and is_number(result_dic["case_data"][0][case])) else 0
        e = float(result_dic["case_data"][1][case]) if (case in result_dic["case_data"][1] and is_number(result_dic["case_data"][1][case])) else 0
        flu = e-s
        r = '%.2f %s' % (((e-s))/e*100, "%") if e!= 0 else "-"
        fluent.append(flu)
        rate.append(r)
        data_table.append(row)

    wb = xlwt.Workbook()
    ws = wb.add_sheet('raw', cell_overwrite_ok=True)
    ws.col(0).width = 6000
    ws.col(3).width = 4000
    ws.col(4).width = 4000
    ws.col(5).width = 3000
    style0 = xlwt.easyxf(
        'font: name Times New Roman, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style1 = xlwt.easyxf(
        'font: name Times New Roman, color-index yellow, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style2 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz left;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    style3 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    titles = ["Test Case", "Unit", "Target"]
    for k in result_dic["build"]:
        titles.append(k)
    titles.extend(["Fluctuation", "Rate"])

    for i, title in enumerate(titles):
        ws.row(i).height_mismatch = True
        ws.row(i).height = 350
        ws.write(0, i, title, style0)
    i = 1
    for key in all_casename:
        ws.row(i).height_mismatch = True
        ws.row(i).height = 320
        ws.write(i, 0, key, style2)
        i += 1
    i = 1
    for u in case_unit:
        ws.row(i).height_mismatch = True
        ws.row(i).height = 320
        ws.write(i, 1, u, style3)
        ws.write(i, 2, '', style3)
        i +=1 
    i = 1
    k = 3
    for j in data_table:
        for d in j:
            ws.row(i).height_mismatch = True
            ws.row(i).height = 320
            ws.write(i, k, d, style3)
            k +=1
        if k > len(result_dic["test_id"]):
            k = 3
            i += 1
    i = 1
    for f in fluent:
        ws.row(i).height_mismatch = True
        ws.row(i).height = 320
        ws.write(i, len(result_dic["test_id"])+3, f, style3)
        i +=1
    i=1
    for r in rate:
        ws.row(i).height_mismatch = True
        ws.row(i).height = 320
        ws.write(i, len(result_dic["test_id"])+4, r, style3)
        i +=1

    wb.save('/tmp/'+result_dic["build"][-1]+'.xls')

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                ch = f.read(chunk_size)
                if ch:
                    yield ch
                else:
                    break
    excel_name = result_dic["build"][-1] + '.xls'
    response = StreamingHttpResponse(file_iterator('/tmp/' + result_dic["build"][-1] + '.xls'))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(excel_name)
    return response

def download_eb_excel(request, project_name, build_name):
    all_casename = []
    case_unit = []
    raw_build = []
    result_dic = {"build":[], "unit":[], "case_data":[], "test_id":[], "data":[], "week_data":[]}
    for i in request.session['cmp']:
        project = i.split("/")[0]
        if i.split("/")[2] !='':
            test_id = i.split("/")[2]
            build = i.split("/")[1]
            raw_build.append(build)
            eb_data = {}
            for j in range(len(raw_build)):
                entries = raw_data(project, raw_build[j], test_id) if raw_build[j] else []
                data = get_raw(entries, raw_data=False, med_and_avg=True, max_and_min=True)
                tmp_data = {}
                for item in data:
                    if item.case_name not in all_casename:
                        all_casename.append(item.case_name)
                        case_unit.append(item.unit)
                    tmp_data[item.case_name] = item.average or item.median
                eb_data = { raw_build[j] : data }
            # result_dic["case_data"].append(tmp_data)
            result_dic["build"].append(build)
            result_dic["test_id"].append(test_id)
            result_dic["data"].append(eb_data)    
        else:
            tem_data = {}
            build = i.split("/")[1]
            result_dic["build"].append(build)
            if 'W' in build:
                tem_data = { build: get_result_by_tag(project, 'bkc', build, include_raw=True) }
            else:
                tem_data = { build: get_result_by_tag(project, 'daily', build, include_raw=True)}
            result_dic["data"].append(tem_data)

    for da in result_dic["data"]:
        all_data = {}
        for i in da:
            tm_data = {}
            for item in da[i]:
                if item.case_name not in all_casename:
                    all_casename.append(item.case_name)
                    case_unit.append(item.unit)
                tm_data[item.case_name] = item.average or item.median
            all_data = { i : tm_data}
        result_dic["case_data"].append(all_data)
    data_table = []
    for i, case in enumerate(all_casename):
        row = [case,case_unit[i],'']
        reverse = -1 if case_unit[i] in ('sec', 'ms', 'msec') else 1
        for index,build in enumerate(result_dic["case_data"]):
            for com_build in result_dic["case_data"][index]:
                if case in result_dic["case_data"][index][com_build]:
                    row.append(result_dic["case_data"][index][com_build][case])
                else:
                    row.append("None")
        s = float(result_dic["case_data"][0][result_dic["build"][0]][case]) if (case in result_dic["case_data"][0][result_dic["build"][0]] and is_number(result_dic["case_data"][0][result_dic["build"][0]][case])) else 0
        e = float(result_dic["case_data"][-1][result_dic["build"][-1]][case]) if (case in result_dic["case_data"][-1][result_dic["build"][-1]] and is_number(result_dic["case_data"][-1][result_dic["build"][-1]][case])) else 0
        flu = e-s
        rate = '%.2f %s' % ((abs(e-s))/e*100, "%") if e!= 0 else "-"
        row.append(str(flu))
        if flu * reverse > 0:
            row.append(str(rate))
        else:
            row.append("-" + str(rate))
        data_table.append(row)
    
    wb = xlwt.Workbook()
    ws = wb.add_sheet('raw', cell_overwrite_ok=True)
    ws.col(0).width = 6000
    ws.col(3).width = 4000
    ws.col(4).width = 4000
    ws.col(5).width = 3000
    style0 = xlwt.easyxf(
        'font: name Times New Roman, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style1 = xlwt.easyxf(
        'font: name Times New Roman, color-index yellow, bold on;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
        'pattern: pattern solid, pattern_fore_colour ocean_blue, pattern_back_colour ocean_blue'
    )
    style2 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz left;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    style3 = xlwt.easyxf(
        'font: name Times New Roman;'
        'align: vert center, horiz center;'
        'border: left thin,right thin,top thin,bottom thin;'
    )
    titles = ["Test Case", "Unit", "Target"]
    for k in result_dic["build"]:
        titles.append(k)
    titles.extend(["Diff", "Rate"])

    for i, title in enumerate(titles):
        ws.row(i).height_mismatch = True
        ws.row(i).height = 350
        ws.write(0, i, title, style0)
    # i = 0
    # for key in all_casename:
    #     ws.row(i).height_mismatch = True
    #     ws.row(i).height = 320
    #     ws.write(i, 0, key, style2)
    #     i += 1
    # i = 1
    # for u in case_unit:
    #     ws.row(i).height_mismatch = True
    #     ws.row(i).height = 320
    #     ws.write(i, 1, u, style3)
    #     ws.write(i, 2, '', style3)
    #     i +=1
    
    i = 1
    k = 0
    for j in data_table:
        for d in j:
            ws.row(i).height_mismatch = True
            ws.row(i).height = 320
            ws.write(i, k, d, style3)
            k +=1
        if k > len(result_dic["build"]):
            k = 0
            i += 1
    # i = 1
    # for f in fluent:
    #     ws.row(i).height_mismatch = True
    #     ws.row(i).height = 320
    #     ws.write(i, len(result_dic["build"])+2, f, style3)
    #     i +=1
    # i = 1
    # for r in rate:
    #     ws.row(i).height_mismatch = True
    #     ws.row(i).height = 320
    #     ws.write(i, len(result_dic["build"])+3, r, style3)
    #     i +=1

    wb.save('/tmp/'+result_dic["build"][-1]+'.xls')

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                ch = f.read(chunk_size)
                if ch:
                    yield ch
                else:
                    break
    excel_name = result_dic["build"][-1] + '.xls'
    response = StreamingHttpResponse(file_iterator('/tmp/' + result_dic["build"][-1] + '.xls'))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(excel_name)
    return response

def build_list(project_name, tag_name='raw'):
    list_builds = list(db_client.get_database(project_name).get_collection(tag_name).distinct('build'))
    list_builds.sort(reverse=True)
    return list_builds


def get_result_by_tag(project_name, tag_name, build, include_raw=False):
    cursors = list(db_client.get_database(project_name).get_collection(tag_name).find().sort('build'))
    grouped = groupby(cursors, lambda x: x['build'])
    entries = []
    for key, group in grouped:
        key = key[0] if type(key) == list else key
        if key == build and build is not None:
            for g in group:
                rcd = raw_case_data(project_name, g['test_id'], g['case_name'])
                for c in rcd:
                    entries.append(c)
                # entries.extend([c for c in raw_case_data(project_name, g['test_id'], g['case_name'])])
    return get_raw(entries, med_and_avg=True, raw_data=include_raw)


def update_trend_by_id(project_name, tag, _id, result):
    coll = db_client.get_database(project_name).get_collection(tag)
    coll.update({'_id': _id}, {'$set': {'result': result}})


def trends(request, project_name, tag):
    output = {}
    entries = list(db_client.get_database(project_name).get_collection(tag).find().sort('case_name'))
    grouped = groupby(entries, lambda x: x['case_name'])

    for key, group in grouped:
        if key == '':
            continue
        build_list = []
        result_list = []
        group = list(group)
        group.sort(key=lambda x: x['build'])
        for g in group:
            if g['build'] == ['']:
                continue
 
            if 'result' in g:
                result = float(g['result']) if is_number(g['result']) else False
            else:
                rcd = raw_case_data(project_name, g['test_id'], g['case_name'])
                if not rcd.count():
                    continue
                raw = get_raw(rcd, med_and_avg=True)[0]
                result = raw.median if raw.median else raw.average
                update_trend_by_id(project_name, tag, g['_id'], result)
            build_list.append(g['build'])
            result_list.append(result)
        output[key] = {'build': build_list, 'result': result_list}
    return JsonResponse(output)


def build_paths(request, project_id):
    json_data = {'data': []}
    build_path_list = BuildPath.objects.filter(project__id=project_id)
    for build_path in build_path_list:
        json_data['data'].append({
            'url': build_path.url,
            'build_type': BUILD_TYPE_CHOICES[build_path.build_type],
        })
    return JsonResponse(json_data)


def fetch_build_path(request):
    post_url = request.POST['url']
    build_path = BuildPath.objects.filter(url=post_url)
    # use cache
    if build_path and False:
        builds = rds.lrange(post_url, 0, -1)
        data = []
        for build in builds:
            build_num = build.split('/')[0]
            if build_num not in data:
                data.append(build_num)
        return JsonResponse({'data': data, 'type': 'cache'})
    # append building build
    building = []
    if build_path:
        logger.debug('buildbot_link: ' + build_path[0].buildbot_link)
        buildbot_url = re.search(r'builders/(.+)', build_path[0].buildbot_link)
        if buildbot_url:
            logger.debug('requesting ' + buildbot_url.group(1))
            buildbot = Buildbot(buildbot_url.group(1), auth=('chenc5x', '^YHN7ujm'))
            building = [x + ' building' for x in buildbot.get_current_builds()]
    # use http
    logger.debug('fetching url ' + post_url)
    start_time = time.time()
    html = requests.get(post_url, verify=False, headers=auth_header()).content
    logger.debug('cost' + str(time.time() - start_time))
    build_list = re.findall('a href="(?!\.)(.*)/"', html)
    build_list = building + build_list
    build_list.sort(reverse=True)
    json_data = OrderedDict()
    json_data['data'] = build_list
    json_data['type'] = 'http'
    return JsonResponse(json_data)


def fetch_target(request):
    post_url = request.POST['url']
    project = int(request.POST['project'])

    # use cache
    post_build_text = request.POST['build'].split()
    post_build = post_build_text[0]
    
    is_building = len(post_build_text) > 1
    if rds.exists(post_url) and False:
        builds = rds.lrange(post_url, 0, -1)
        data = []
        for build in builds:
            if build.startswith(post_build + '/'):
                target_name = build.split('/')[1]
                if target_name not in data:
                    data.append(target_name)
        return JsonResponse({'data': data, 'type': 'cache'})
    # if building
    if is_building:
        build_path = BuildPath.objects.filter(url=request.POST.get('build_path'))
        if build_path:
            buildbot_url = re.search(r'builders/(.+)', build_path[0].buildbot_link)
            buildbot = Buildbot(buildbot_url.group(1), auth=('chenc5x', '^YHN7ujm'))
            return JsonResponse({'data': buildbot.check_build_target(post_build)})
    url_html_info = requests.get(post_url, verify=False, headers=auth_header()).content
    link_list =[]
    
    key = 'products_' + Project.objects.get(id=project).builder_name
    available_targets = rds.lrange(key, 0, -1)
    if "cel_kbl" in available_targets:
        print available_targets.index("cel_kbl")
    
    if "build_info.json" not in url_html_info:
        link_list = re.findall(r'href="(.*)/"', url_html_info)
        
    else:
        url = request.POST['url'] + '/build_info.json'
        html_build_info = requests.get(url, verify=False, headers=auth_header()).content
        if Project.objects.get(id=project).builder_name == 'e2e_master':
            link_list = json.loads(html_build_info)['buildbot_properties']['buildbot.props.selected_e2e_build_target']
             
        else:
            link_list = json.loads(html_build_info)['buildbot_properties']['buildbot.props.target_products_to_build']
    if link_list == ['buildbot']:
        return JsonResponse({'data': ['null']})
    result = list(set(available_targets).intersection(set(link_list)))
    print result
    return JsonResponse({'data': result})


def test_config(request, name):
    return JsonResponse(json.load(open(os.path.join(os.path.dirname(__file__), 'data', 'test_configs', name))))


def cancel(request, id):
    Logger.objects.filter(task_id=id).update(user=request.user, description='cancel')
    if Task.objects.get(id=id).available:
        Task.objects.filter(id=id).update(available=False)
        return HttpResponse("1")
    else:
        task = Task.objects.get(id=id)
        ip = task.slave.ip
        url = 'http://{0}:9001/reset/'.format(ip)
        try:
            requests.get(url)
            task.end()
            task.save()
            return HttpResponse("1")
        except socket.timeout:
            return HttpResponse("1")


def test_failed(request, task_id, desc):
    print "=============="
    print task_id
    print desc
    print "=============="
    Logger.objects.filter(task_id=task_id).update(description=desc)
    return HttpResponse("1")


def update_test_id(request):
    try:
        task_id = request.POST['task_id']
        test_id = request.POST['test_id']
        task = Task.objects.get(id=task_id)
        task.test_id = test_id
        task.save()
        return HttpResponse('success')
    except Exception as e:
        logger.debug(e)
        return HttpResponse(repr(e))


def add_to_compare_list(request):
    if 'cmp' not in request.session:
        request.session['cmp'] = []
    cmp_list = request.session['cmp']
    if len(cmp_list) > 7:
        return HttpResponse('0')
    else:
        if len(cmp_list) > 0:
            if (request.session['cmp'][0].split("/")[-1] and request.POST['data'].split("/")[-1]) or (not request.session['cmp'][0].split("/")[-1] and not request.POST['data'].split("/")[-1]):
                cmp_list.append(request.POST['data'])
            else:
                return HttpResponse('-1')
        else:
            cmp_list.append(request.POST['data'])
    request.session['cmp'] = cmp_list
    return HttpResponse('1')


def remove(request):
    if 'cmp' not in request.session:
        request.session['cmp'] = []
    cmp_list = request.session['cmp']
    cmp_list.remove(request.POST["cmp_item"])
    request.session['cmp'] = cmp_list
    return HttpResponse('1')


def clear_compare_list(request):
    request.session['cmp'] = []
    return HttpResponse('0')


def broadcast(request):
    data = request.POST
    task_id = int(data['task_id'])
    test_id = data['test_id']
    msg = data['msg']
    cc = data['cc'] if 'cc' in data else ''
    task = Task.objects.get(id=task_id)
    from_addr = data['from'] if 'from' in data else 'chenx.chen@intel.com'

    if 'recipient' in data:
        recipients = [data['recipient']]
    elif task.submitter.email:
        recipients = [task.submitter.email]
        if not request.user.is_anonymous and request.user.email:
            recipients.append(request.user.email)
    else:
        return HttpResponse('error')
    if msg == 'success':
        template = 'alert.html'
        subtitle = 'Test {0} finished'.format(test_id)
        title = 'Your task #{0} is finished'.format(task.id)
        content = 'Build: {0}'.format(task.build())
        link = 'http://cubep.sh.intel.com/{}/{}/{}/{}/'.format('raw', task.project.name, task.build(), task.test_id)
    elif msg == 'failed':
        template = 'alert.html'
        subtitle = 'Test {0} failed'.format(test_id)
        title = 'Your task #{0} is failed'.format(task.id)
        content = 'Build: {0}'.format(task.build())
        link = 'http://cubep.sh.intel.com/{}/{}/{}/{}/'.format('raw', task.project.name, task.build(), task.test_id)
    elif msg == 'new':
        template = 'manual_test.html'
        subtitle = 'New Task'.format(test_id)
        title = 'You get a new task from {}:'.format(request.user.last_name + ", " + request.user.first_name)
        comment = json.loads(task.comment)
        show_items = ['Project:', 'Build:', 'test_id:', 'Board:', 'Display:', 'Keybox:', 'OSC:', 'Image', 'Log:', 'Cases:']
        items_value = [task.project, task.build(), task.test_id, comment['Board'], comment['Display'], comment['Keybox'], comment['OSC'], comment['Image'], comment['Log'], '<br/>'.join(comment['Cases'])]
        if 'Comment' in comment:
            show_items.append('Comment:')
            items_value.append(comment['Comment'].replace('\n', '<br/>').replace(' ', '&nbsp;'))
        content = "<table cellspacing='5px'>"
        for i, item in enumerate(show_items):
            content += "<tr><td class='label'>{0}</td><td>{1}</td></tr>".format(item, items_value[i])
        content += "</table>"
        link = 'http://cubep.sh.intel.com/accounts/mytasks/'

    ms = MailSender(template=template, subtitle=subtitle, title=title, content=content, link=link, from_addr=from_addr, recipients=recipients, cc_addr=cc)
    ms.success()
    response = 'send mail to', ','.join(recipients)
    return HttpResponse(response)


def db_info(project_name):
    dict = db_client.get_database(project_name).command('dbstats')
    dict['collections'] = ', '.join(db_client.get_database(project_name).collection_names())
    dict['builds'] = len(db_client.get_database(project_name).get_collection('raw').distinct('build'))
    return dict


def collection_info(project_name, collection):
    return True


def add_comment(request):
    task_id = request.POST['task_id']
    content = request.POST['content']
    message = Message(user=request.user,
                      content=content,
                      parent_id=int(task_id),
                      title='task_id'
                      )
    message.save()
    create_time = message.create_time
    tz = pytz.timezone(settings.TIME_ZONE)
    create_time.astimezone(tz)
    str_time = create_time.strftime("%b %-d, %Y, %I:%-M %p")
    return JsonResponse({'status': 'success', 'datetime': str_time})


def test_connect(request):
    result = {'result': True, 'msg': "Connect successfull!"}
    ip = request.POST['ip']
    hostname = request.POST['hostname']
    username = request.POST['username']
    passwd = request.POST['passwd']

    p_ip = subprocess.Popen("sshpass -p '{0}' ssh -p 22 -o StrictHostKeyChecking=no {1}@{2} 'pwd'".format(passwd, username, ip), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    p_hostname = subprocess.Popen("sshpass -p '{0}' ssh -p 22 -o StrictHostKeyChecking=no {1}@{2} 'pwd'".format(passwd, username, hostname), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    if len(p_ip.stdout.readlines()) == 0:
        result["result"] = False
        result["msg"] = "Connect with IP failed!"

    if len(p_hostname.stdout.readlines()) == 0:
        result["result"] = False
        result["msg"] = "Connect with hostname failed!"

    return JsonResponse(result)


def check_slave_install_status(request):
    installing_slaves = Slave.objects.filter(policy='1', install_status='0', owner=request.user.id)
    failed_slaves = Slave.objects.filter(policy='1', install_status='2', owner=request.user.id)
    result = {}
    for slave in installing_slaves:
        p = subprocess.Popen("ssh -p 22 {0}@{1} 'cat ~/slave_status'".format(slave.user_name, slave.host_name), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        status = p.stdout.readlines()
        if len(status) > 0:
            if status[-1].split(",")[0] == "completed":
                slave.install_status = 1
                slave.save()
            elif status[-1].split(",")[0] == "failed":
                slave.install_status = 2
                slave.save()

            result[slave.id] = status[-1]
    for slave in failed_slaves:
        p = subprocess.Popen("ssh -p 22 {0}@{1} 'cat ~/slave_status'".format(slave.user_name, slave.host_name), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        status = p.stdout.readlines()
        if len(status) > 0:
            result[slave.id] = status[-1]
    return JsonResponse(result)


def update_slaveserver(request):
    slave_id = request.POST['slave_id']
    passwd = request.POST['passwd']
    slave = Slave.objects.get(id=slave_id)
    p_update = subprocess.Popen("ssh -t -p 22 {0}@{1} 'slavemanger -u -p {2}'".format(slave.user_name, slave.host_name, passwd), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    ret = 1 if len(p_update.stdout.readlines()) > 1000 else 0
    return JsonResponse({"result": ret})


def slave_status(request, slave_id, slave_ip):
    try:
        queue_tasks = []
        for task in Task.objects.filter(available=True, slave__id=slave_id):
            conf = json.load(open(os.path.join(os.path.dirname(__file__), 'data', 'test_configs', task.test_config)))
            queue_tasks.append({'project': conf['project_name'], 'slave_project': task.project.slave_project, 'target': conf['test_target'], 'build': conf['build'], 'cases': conf['case_name'], 'case_loops': conf['case_loop'], 'skip_flash': conf['skip_flash'], 'owner': '%s, %s' % (task.submitter.last_name, task.submitter.first_name)})

        req = requests.post('http://%s:9001/slave_stat/' % slave_ip, data={'queue_tasks': json.dumps(queue_tasks)},  timeout=0.5, verify=False)
        res = json.loads(req.text)
        res['status_code'] = 200
        return JsonResponse(res)
    except Exception as e:
        return JsonResponse({'error': repr(e), 'status_code': 404})


def get_test_template(request, id):
    return JsonResponse(ConfigTemplate.objects.get(id=id).serialize)

def convert_testdata(request):
    if request.method == 'POST':
        project = request.POST['project']
        collection_name = request.POST['collection']
        test_id = request.POST['testid']
        build = request.POST['build']
        db = db_client.get_database(project)
        logger.debug(collection_name)
        if not db.get_collection(collection_name).find({'test_id': test_id}).count():
            logger.debug('===='+collection_name)
            rawdatas = db.get_collection('raw').find({'test_id': test_id})
            if collection_name == 'bkc':
                cursors = list(rawdatas.sort('case_name'))
                cursord = groupby(cursors, lambda x:x['case_name'])
                for i in cursord:
                    testinfo = {'test_id':test_id, 'build':build, 'case_name':i[0]}
                    db.get_collection(collection_name).insert(testinfo)
                return HttpResponse('convert bkc success')
            if collection_name == 'daily':
                for j in rawdatas:
                    testinfo = {'test_id':test_id, 'build':build, 'case_name':j['case_name'], 'result':j['result']}
                    logger.debug(testinfo)
                    if db.get_collection(collection_name).find(testinfo).count() == 0:
                        db.get_collection(collection_name).insert(testinfo)
                return HttpResponse('convert daily success')
            return HttpResponse('error:convert failed!')
        else:
            return HttpResponse('error: data already exists!')

    return Http404()

def remove_convert_data(request):
    status = ''
    user = request.user
    project = request.POST['project']
    tag = request.POST['tag']
    build = request.POST['build']
    db = db_client.get_database(project)
    if db.get_collection(tag).find({'build': build}).count():
        db.get_collection(tag).remove({'build': build})
        status = 'user:{0} \n status:remove {1} success'.format(user, build)
    else:
        status = 'user:{0} \n status:remove {1} failed'.format(user, build)
    return HttpResponse(status)


def get_weekly_from_db(request):
    project = request.GET['project']
    tag = request.GET['tag']
    weekyear = request.GET['weekyear']
    weeknum = request.GET['weeknum']
    db = db_client.get_database(project)
    db_lists = db.get_collection(tag).find({'build':{'$regex':'^{0}\w+{1}$'.format(weekyear, weeknum)}})
    dbMsg = ''
    web_msg = []
    if db_lists.count():
        sort_db_list = list(db_lists.sort('build'))
        db_data_list = groupby(sort_db_list, lambda x:x['build'])
        for i in db_data_list:
            web_msg.append('<option>'+i[0]+'</option>')
        dbMsg = '\n'.join(web_msg)
    return JsonResponse({'selects': dbMsg})


