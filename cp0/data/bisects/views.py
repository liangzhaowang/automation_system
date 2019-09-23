from cp0.lib import new_render, test_config
from django.http import JsonResponse
from data import api
from data.models import BuildPath, Project, Slave, Task, Logger
import requests
import json
import logging
import os
from pymongo import MongoClient
from redis import Redis
from data.tasks import MERGE_REQUEST_SITES
from home.views import generate_file_name
from django.conf import settings
from pymongo import MongoClient
from collections import OrderedDict


logger = logging.getLogger('django.request')


LATEST_BASE_URL = 'https://buildbot.sh.intel.com/absp/json/builders/{}-latest/builds/{}?as_text=1'
MERGE_REQUEST_URL = 'https://buildbot.sh.intel.com/absp/json/builders/{}-mergerequest/builds?as_text=1&{}'
MERGE_REQUEST = 'https://buildbot.sh.intel.com/absp/builders/{}-mergerequest/builds/{}/'
MERGE_REQUEST_REPO = 'https://mcg-depot.intel.com/artifactory/cactus-absp-{}/master-mergerequest/{}/{}/'


def index(request, project_name, build):
    cases = request.POST.getlist('cb_case[]')
    origin_build = build.split('_')[1] if '_' in build else build
    builds = api.build_list(project_name, 'daily')
    prev_build = builds[builds.index(build) + 1]
    prev_origin_build = prev_build.split('_')[1] if '_' in prev_build else prev_build
    project = Project.objects.get(name=project_name)
    merge_req = get_mergerequest(project_name, origin_build)
    prev_merge_req_num = get_mergerequest(project_name, prev_origin_build).split('/')[1]
    branch_name, merge_req_num = merge_req.split('/')

    rds = Redis(host='localhost', port=6379)
    filter_target = 'gordon_peak_acrn'

    filtered_mq_list = []
    for site in MERGE_REQUEST_SITES:
        logger.debug('searching %s', site)
        logger.debug('mq_images_{}_{}'.format(site, project.builder_name))
        for mq in rds.lrange('mq_images_{}_{}'.format(site, project.builder_name), 0, -1):
            _, build, target = mq.split('/')[:3]
            if int(build) < int(merge_req_num) and int(build) > int(prev_merge_req_num) and target == filter_target:
                if (build, site, MERGE_REQUEST_REPO.format(site, build, target)) not in filtered_mq_list:
                    filtered_mq_list.append((build, site, MERGE_REQUEST_REPO.format(site, build, target)))
    
    
    context = {
        'project_name': project.name,
        'project_id': project.id,
        'current_build': origin_build,
        'current_mq': merge_req_num,
        'prev_build': prev_origin_build,
        'prev_mq': prev_merge_req_num,
        'count': len(filtered_mq_list), 
        'cases': cases,
        'slaves': Slave.objects.all(),
        'filtered_mq_list': filtered_mq_list,
        'builder_name': project.builder_name,
    }
    return new_render(request, 'bisects.html', context=context)


def get_config_id(project, build):
    db_client = MongoClient(host='localhost', port=27017, username='cp0_admin', password='Pw$g09e3')
    config_ids = db_client.get_database(project).get_collection('daily').find({'build': build}).distinct('test_id')
    return config_ids


def get_mergerequest(project, build):
    builder = Project.objects.get(name=project).builder_name
    url = LATEST_BASE_URL.format(builder, build)
    print '{} links to {}'.format(build, url)
    try:
        resp = requests.get(url, verify=False)
        if resp.status_code < 300:
            properties = json.loads(resp.text)['properties']
            for prop in properties: 
                if prop[0] == 'inherit':
                    return prop[1]
        else:
            return False
    except Exception as e:
        return False


def create_test(content, user):
    test_config_name = generate_file_name()
    if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs')):
        os.mkdir(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs'))
    test_config_path = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', test_config_name)
    fw = open(test_config_path, 'w')
    fw.write(json.dumps(content, indent=4))
    fw.close()
    print 'create config', test_config_path
    new_task = Task(
        test_config=test_config_name,
        project=Project.objects.get(id=int(content['project_id'])),
        slave=Slave.objects.get(id=int(content['slave_id'])),
        submitter=user,
        comment=content['test_comment']
    )
    new_task.save()
    print 'create task', new_task.id

    Logger(
        project=new_task.project,
        slave=new_task.slave,
        description='nt',
        user=user,
        build=content['build'],
        test_config=test_config_name,
        task=new_task  
    ).save()


def view(requests, project, daily_build):
    db_client = MongoClient(host='localhost', port=27017, username='cp0_admin', password='Pw$g09e3')
    coll = db_client.get_database(project).get_collection('raw')
    entries = coll.find({'test_set': "mq_%s" % daily_build})

    results = OrderedDict()
    case_length = 0
    all_case_name= []
    caseresult=OrderedDict()
    
    for entry in entries:
        if entry['case_name'] not in all_case_name:
            all_case_name.append(entry['case_name'])
        if entry['build'] not in results:
            
            results[entry['build']] = {
                entry['case_name']: {
                    'tests': [
                        {
                            'test_id': entry['test_id'], 
                            'result': entry['result'],
                        }
                    ]
                }
            }
        else:
            if entry['case_name'] not in results[entry['build']]:
                results[entry['build']][entry['case_name']] = {
                    'tests': [
                        {
                            'test_id': entry['test_id'], 
                            'result': entry['result'],
                        } 
                    ]
                }
                
                case_length += 1
            else:
                results[entry['build']][entry['case_name']]['tests'].append(
                    {
                        'test_id': entry['test_id'], 
                        'result': entry['result'],
                    }
                )
    a= len(results.items())    
    for i in range(a):
        k=  results.items()[i][1]
        for CaseAllname in all_case_name:
            CaseAllname=CaseAllname.encode("utf-8")
            if CaseAllname not in k.keys():
                k[CaseAllname]={
                'tests':[
                        {
                            'test_id': "NA", 
                            'result': "NA",
                        }]} 
                        
    for CaseAllname in all_case_name:
        for i in range(a) :
            if results.items()[i][0] not in caseresult:
                caseresult[results.items()[i][0]] = { CaseAllname : results.items()[i][1][CaseAllname]}                
            else:
                caseresult[results.items()[i][0]][CaseAllname]= results.items()[i][1][CaseAllname]

    mq_base_url = 'https://buildbot.sh.intel.com/absp/builders/{}-mergerequest/builds/'
    context = {
        'caseresult': caseresult,
        'allcase': all_case_name,
        'results': results,
        'project': project,
        'build': daily_build,
        'mq_url': mq_base_url.format(Project.objects.get(name=project).builder_name)
    }


    return new_render(requests, 'bisect_results.html', context=context, wide=True)


def create(requests, project, daily_build):
    project = Project.objects.get(name=project)
    prev_mq = requests.POST.get('prev_mq')
    current_mq = requests.POST.get('current_mq')
    case_loop = requests.POST.getlist('case_loop[]')
    case_name = requests.POST.getlist('case_name[]')
    filter_target = 'gordon_peak_acrn'
    logger.debug('project %s,' % project.name)
    rds = Redis(host='localhost', port=6379)

    filtered_mq_list = []
    for site in MERGE_REQUEST_SITES:
        for mq in rds.lrange('mq_images_{}_{}'.format(site, project.builder_name), 0, -1):
            _, build, target = mq.split('/')[:3]
            logger.debug('from %s to %s', (current_mq, prev_mq))
            if int(build) < int(current_mq) and int(build) > int(prev_mq) and target == filter_target:
                if (build, site, MERGE_REQUEST_REPO.format(site, build, target)) not in filtered_mq_list:
                    filtered_mq_list.append((build, site, MERGE_REQUEST_REPO.format(site, build, target)))
                    content = {
                        "config_cmds": [],
                        "case_loop": case_loop,
                        "case_name": case_name,
                        "build_url": "https://mcg-depot.intel.com/artifactory/cactus-absp-{}/{}-mergerequest/".format(site, project.builder_name),
                        "tag": "normal",
                        "test_tag": "",
                        "test_comment": "",
                        "test_set": "mq_%s" % daily_build,
                        "slave_project": project.slave_project,
                        "case_tool": [[]] * len(case_name),
                        "case_weight": [""] * len(case_name),
                        "build_type_id": "3",
                        "build": build,
                        "patch_method": "td",
                        "project_id": str(project.id),
                        "project_name": project.name,
                        "case_name": case_name,
                        "slave_id": requests.POST.get('slave'),
                        "skip_flash": False,
                        "build_type": "merge request",
                        "display_build": "",
                        "buildbot_link": "https://buildbot.sh.intel.com/absp/builders/{}-mergerequest/builds/{}/".format(project.builder_name, build),
                        "config_params": [],
                        "patch": "",
                        "test_target": 'gordon_peak_acrn',
                        "building": False
                    }
                    create_test(content, requests.user)
                    logger.debug('creat test %s', build)
        
    return JsonResponse({'status_code': '200'})
