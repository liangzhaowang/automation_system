from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib.auth.models import User, Group
from cp0.lib import new_render
from cp0.lib import auth_header
from data.models import Slave, Task, Project, Logger, ConfigTemplate
from django.contrib import auth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.auth import HTTPBasicAuth
from home.models import UserCPZ
from home.tasks import Testing
from data.views import get_config
from datetime import datetime, timedelta
from itertools import chain
import time
import random
import string
import os
import json
import logging
import urlparse
import requests
import re
import redis


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logger = logging.getLogger('django.request')
authorization = {'Authorization': 'Basic Y2hlbmM1eDpIRTdRZ2sjaA=='}
rds = redis.Redis(host='localhost', port=6379)
VIEWS = [('daily', 'Daily'), ('bkc', 'Weekly & BKC'), ('history', 'History')]

# Create your views here.


def page_not_found(request):
    return render_to_response('404.html')


def page_error(request):
    return render_to_response('500.html')


def releases(request):
    context = {

    }
    return new_render(request, 'releases.html', context)


def token():
    payload = {
        'grant_type': 'client_credentials',
        'scope': 'Token_WindowsAuth'
    }
    token = requests.post(
        'https://iamws-i.intel.com/api/v1/Token', 
        data=payload,
        auth=HTTPBasicAuth('lab_cpzero', '3edc4rfv%TGB'),
        verify=False
    )
    content = token.content
    logger.debug(content)
    return content


def windows_auth(user_token, access_token):
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    payload = {
        'token': user_token,
        'appId': '17807'
    }
    response = requests.post(
        'https://iamws-i.intel.com/api/v1/Windows/Auth',
        data=payload,
        verify=False,
        headers=headers
    )
    return response
    

def sso(request):
    try:
        user_token = request.GET['token']
        get_token = json.loads(token())
        logger.debug(get_token)
        access_token = get_token['access_token']
        expires_in = get_token['expires_in']
        _data = json.loads(windows_auth(user_token, access_token).content)
        user_data = _data['IntelUserExtension']
        request.session['username'] = user_data['displayName']
        request.session['wwid'] = user_data['id']
        users = User.objects.filter(username=user_data['externalId'])
        if users.exists():
            user = users[0]
            user.last_name = user_data['name']['familyName']
            if 'givenName' in user_data['name']:
                user.first_name = user_data['name']['givenName']
            else:
                user.first_name = ''
            user.email = user_data['emails'][0]['value']
            user.save()
            ucpz = UserCPZ.objects.get(user=user.id)
            ucpz.wwid = user_data['id']
            ucpz.save()
        else:
            user = User()
            user.last_name = user_data['name']['familyName']
            if 'givenName' in user_data['name']:
                user.first_name = user_data['name']['givenName']
            else:
                user.first_name = ''
            user.email = user_data['emails'][0]['value']
            user.username = user_data['externalId']
            user.save()
            ucpz = UserCPZ(user=user)
            ucpz.wwid = user_data['id']
            ucpz.save()
    except ValueError:
        print 'error'
    return HttpResponseRedirect('/')


def index(request):
    private_slaves = OrderedDict()
    public_slaves = OrderedDict()
    tasks_estimate = []
    tmp_slave_est = {}
    slave_estimate = []
    slaves = Slave.objects.all().order_by('-ram')
    
    for slave in slaves:
        if slave.policy == 0:
            if slave.ram in public_slaves:
                public_slaves[slave.ram].append(slave.__dict__)
            else:
                public_slaves[slave.ram] = [slave.__dict__]
        elif slave.policy == 1:
            if slave.ram in private_slaves:
                private_slaves[slave.ram].append(slave.__dict__)
            else:
                private_slaves[slave.ram] = [slave.__dict__]

    for slave_id in tmp_slave_est.keys():
        tmp_slave_min = (tmp_slave_est[slave_id]) / 60
        tmp_slave_sec = (tmp_slave_est[slave_id]) % 60
        slave_estimate.append({"id": slave_id, "value": tmp_slave_min, "result": str(tmp_slave_min)+' m '+str(tmp_slave_sec)+' s '})

    context = {
        'title': 'CP0',
        'private_slaves': private_slaves,
        'public_slaves': public_slaves,
        'tasks_estimate': tasks_estimate,
        "slave_estimate": slave_estimate,
    }
    return new_render(request, 'index.html', context, subtitle='Home')


@login_required
def new_test(request):
    if request.method == 'POST':
        content = json.loads(request.POST['data'])
        content['building'] = 'building' in content['build']
        content['build'] = content['build'].split()[0]
        if content['project_id'] == 'null':
            return JsonResponse({'success': False, 'msg': 'Project is not defined'})
        elif content['slave_id'] == 'null' and content['patch_method'] != "mt":
            return JsonResponse({'success': False, 'msg': 'Slave is not defined'})
        slave = None if content['slave_id'] == 'null' else Slave.objects.get(id=int(content['slave_id']))
        user = request.user if ('tester' not in content or content['tester'] == 'null') else User.objects.get(id=int(content['tester']))
        event = 'nt'
        try:
            test_config_name = generate_file_name()
            if not os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs')):
                os.mkdir(os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs'))
            test_config_path = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', test_config_name)
            fw = open(test_config_path, 'w')

            # post to buildbot
            # manifests-original.json
            # manifests-generated.json preferred
            if content['patch_method'] == 'bap':
                build_url = content['build_url'] + content['build']
                manifest = 'manifests-generated.json'
                if requests.get(build_url + '/manifests-generated.json', verify=False, headers=auth_header()).status_code == 404:
                    manifest = 'manifests-original.json'
                manifest_override_url = '{0}/{1}'.format(build_url, manifest)

                project = Project.objects.get(id=int(content['project_id']))
                products = content['test_target']
                post_url = 'https://buildbot.sh.intel.com/absp/builders/{0}-engineering/force'.format(project.builder_name)
                data = {
                    'forcescheduler': 'force_engineering_{0}'.format(project.builder_name),
                    'reason': test_config_name,
                    'download_list_computation_mode': 'reorder without downloading other patches',
                    'force_build_changeids': content['patch'],
                    'variant_list': 'userdebug',
                    'target_products_to_build': products,
                    'customized_build_command': '',
                    'preferred_site': 'sh',
                    'branch_list': '',
                    'manifest_override_url': manifest_override_url
                }
                response = requests.post(post_url, data=data, verify=False, headers=auth_header())
            elif content['patch_method'] == 'bep':
                pass
            elif content['patch_method'] == 'td':
                buildbot_link = urlparse.urljoin(content['build_url'], content['build'] + '/buildbot_link.htm')
                response = requests.get(buildbot_link, verify=False, headers=auth_header())
                if response.status_code == 200:
                    content['buildbot_link'] = re.search('<a href="(.+)">redirect</a>', response.content).group(1)
            elif content['patch_method'] == 'mt':
                event = 'mt'

            fw.write(json.dumps(content, indent=4))
            fw.close()
            new_task = Task(
                test_config=test_config_name,
                project=Project.objects.get(id=int(content['project_id'])),
                slave=slave,
                submitter=user,
                comment=content['test_comment']
            )
            if 'upload_result' in content and content['upload_result']:
                new_task.available = False
                new_task.test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_task.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_task.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            while len(Task.objects.filter(test_id=new_task.test_id)) > 0:
                new_task.test_id = (datetime.now()+timedelta(seconds=1)).strftime('%Y%m%d_%H%M%S')
            new_task.save()

            if event == 'mt':
                new_task.favorites.add(request.user)

            try:
                with open(os.path.join(settings.BASE_DIR, 'logs', str(new_task.id) + '.html')) as fbb:
                    fbb.write(response.text)
                    fbb.close()
            except:
                print 'fbb fail'

            new_logger = Logger(
                project=new_task.project,
                slave=new_task.slave,
                description=event,
                user=user,
                build=content['build'],
                test_config=test_config_name,
                task=new_task
            )
            new_logger.save()
            return JsonResponse({'success': True, 'task_id': str(new_task.id), 'test_id': new_task.test_id, 'test_config': new_task.test_config})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': repr(e)})

    elif request.method == 'GET':
        slaves = Slave.objects.filter(policy=0)
        private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
        available_slaves = []
        for p_slave in private_slave:
            available_slaves.append(p_slave)
        for slave in slaves:
            slave.sn = "*".join([pro.name for pro in slave.projects.all()])
            available_slaves.append(slave)

        context = {
            'available_slaves': available_slaves,
            'templates': list(chain(
                ConfigTemplate.objects.filter(user=request.user, public=False),
                ConfigTemplate.objects.filter(public=True)
            )),
            'manual_tester': Group.objects.get(id=1).user_set.values(),
            'test_owner': Group.objects.get(id=2).user_set.values(),
            'warning': rds.get('new')
        }
        return new_render(request, 'new_test.html', context, title='CP0', subtitle='New Test')


def copy_test(request, config_name):
    slaves = Slave.objects.filter(policy=0)
    private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
    available_slaves = []
    for p_slave in private_slave:
        available_slaves.append(p_slave)
    for slave in slaves:
        slave.sn = "*".join([pro.name for pro in slave.projects.all()])
        available_slaves.append(slave)

    context = {
        'available_slaves': available_slaves,
        'manual_tester': Group.objects.get(id=1).user_set.values(),
        'config_name': config_name,
        'warning': rds.get('new')
    }
    return new_render(request, 'new_test.html', context, title='CP0', subtitle='New Test')


def add_test(request, slave_id):
    slaves = Slave.objects.filter(policy=0)
    private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
    available_slaves = []
    for p_slave in private_slave:
        available_slaves.append(p_slave)
    for slave in slaves:
        slave.sn = "*".join([pro.name for pro in slave.projects.all()])
        available_slaves.append(slave)
    context = {
        'available_slaves': available_slaves,
        'manual_tester': Group.objects.get(id=1).user_set.values(),
        'slave_id': slave_id,
        'warning': rds.get('new')
    }
    return new_render(request, 'new_test.html', context, title='CP0', subtitle='New Test')


def history(request, project_name):
    active_user = []
    tasks = Task.objects.all().order_by('-id')[:100]
    for task in tasks:
        if task.submitter not in active_user:
            active_user.append(task.submitter)
    context = {
        'tag': 'history',
        'views': VIEWS,
        'title': 'CP0',
        'subtitle': 'History',
        'project_name': project_name,
        # 'server': settings.IP,
        'active_user': active_user,
    }
    return new_render(request, 'history.html', context)


def generate_file_name():
    while True:
        test_config_name = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        test_config_path = os.path.join(settings.BASE_DIR, 'data', 'data', 'test_configs', test_config_name)
        if not os.path.exists(test_config_path):
            return test_config_name


def login_view(request):
    if request.method == 'GET':
        content = {}
        if 'next' in request.GET:
            content['next'] = request.GET['next']
        return new_render(request, 'login.html', content)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        next_url = request.POST['next']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                if next_url == '':
                    return HttpResponseRedirect('/')
                else:
                    return HttpResponseRedirect(next_url)
            else:
                return HttpResponse('error')
        else:
            # Return an 'invalid login' error message.
            return HttpResponse('error')


def register_view(request):
    return new_render(request, 'register.html', {})


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')


@login_required
def profile_view(request):
    private_slave = Slave.objects.filter(policy='1', owner=request.user.id)
    return new_render(request, 'profile.html', {"slaves": private_slave}, wide=True)


def add_case(request):
    return new_render(request, 'add_case.html')

def case_demo(request):
    return new_render(request, 'Add_case.html')

def get_slaveProject(request):
    slaveId = []
    projectAll = []
    project_all = Project.objects.all()
    if request.method == 'GET':
        slaves = Slave.objects.filter(policy=0)
        private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
        available_slaves = []
        for p_slave in private_slave:
            available_slaves.append({"id": p_slave.id, "name": p_slave.num, "comment": p_slave.comment, "ip": p_slave.ip})
        for slave in slaves:
            available_slaves.append({"id": slave.id, "name": slave.num, "comment": slave.comment, "ip": slave.ip})
        for j in available_slaves:
            options = "<option value=%s>%s</option>" % (j["ip"], j["name"] + ":%s" % (j["comment"]))
            slaveId.append(options)
        for k in project_all:
            options = "<option value=%s>%s</option>" % (k.name, k.name)
            projectAll.append(options)
        return JsonResponse({"slave_info":slaveId, "projectall":projectAll}, safe=False)

def save_case(request):
    if request.method == 'POST':
        case_name = request.POST['case_name']
        slave_ip = request.POST['slave_ip']
        case_info = request.POST['case_info']
        project_name = request.POST['project']
        print "===", slave_ip, case_name, project_name
        status = requests.post("http://" + slave_ip + ":9001/add_case/", {"case_name":case_name, "case_info":case_info, "project":project_name}).status_code


    return HttpResponse(status)
