import datetime
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from data.models import Project, ReportCSV
from django.contrib.auth.models import User
from django.contrib import auth
from django.template.response import TemplateResponse
from django.conf import settings
import urlparse
import os
import redis
import collections
import time
import logging

logger = logging.getLogger('django.request')

rds = redis.Redis(host='localhost', port=6379)


def auth_header():
    return {'Authorization': 'Basic {}'.format(rds.get('auth_header'))}


def login():
    sso_url = 'https://cubep.sh.intel.com/sso'
    windows_auth_url = 'https://iamws-i.intel.com/api/v1/Windows/Auth'
    redirect_url = windows_auth_url + '?redirecturl=' + sso_url + '&appId=17807'
    return HttpResponseRedirect(redirect_url)


def new_render(request, template_name, context={}, title='CP0', subtitle=None, wide=False):
    now = datetime.datetime.now()
    if 'username' in request.session and 'wwid' in request.session:
        logger.debug('start ' + request.session['username'] + ', ' + request.session['wwid'])
    cmp_list = request.session.get("cmp", None)
    if settings.DEBUG:
        wwid = '00000000'
        user_name = 'admin'
    else:
        print 'Deploy Mode'
        if 'username' in request.session and 'wwid' in request.session:
            if request.session['wwid'] == '':
                logger.debug('wwid is null')
                sso_url = 'https://cubep.sh.intel.com/sso'
                windows_auth_url = 'https://iamws-i.intel.com/api/v1/Windows/Auth'
                redirect_url = windows_auth_url + '?redirecturl=' + sso_url + '&appId=17807'
                return HttpResponseRedirect(redirect_url)
 
            user_name = request.session['username']
            wwid = request.session['wwid']
            logger.debug(user_name + ', ' + wwid)
        else:
            logger.debug('goto sso')
            sso_url = 'https://cubep.sh.intel.com/sso'
            windows_auth_url = 'https://iamws-i.intel.com/api/v1/Windows/Auth'
            redirect_url = windows_auth_url + '?redirecturl=' + sso_url + '&appId=17807'
            return HttpResponseRedirect(redirect_url)

    user = User.objects.get(usercpz__wwid=wwid)

    if not request.user.is_authenticated():
        auth.login(request, user)

    # comparision sessions
    if cmp_list:
        context['cmp_list'] = map(lambda x: ReportCSV(x), cmp_list)
    else:
        context['cmp_list'] = None
        request.session['cmp'] = []
        cmp_list = []

    context['cmp_length'] = len(cmp_list)
    context['container'] = '' if wide else 'container'
    context['projects'] = Project.objects.order_by('-id')
    context['title'] = title
    context['subtitle'] = subtitle
    context['username'] = user.username
    context['wwid'] = wwid
    context['footer'] = (now.isocalendar()[1], now.strftime('%b %d, %Y'))
    return TemplateResponse(request, template_name, context)


def dict_utf8_to_string(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(dict_utf8_to_string, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(dict_utf8_to_string, data))
    else:
        return data


def test_config(name):
    try:
        return json.load(os.path.join(settings.BASE_DIR, 'data', 'test_configs', name))
    except:
        return None
