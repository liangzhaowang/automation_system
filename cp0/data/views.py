from django.contrib.auth.models import Group
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from cp0.lib import new_render, test_config
from itertools import groupby
from collections import OrderedDict
from django.conf import settings
import logging
import api
import urllib2
import urlparse
import os
import base64
import re
import json
from models import *
from general_compare import GeneralTestResultCompare
from home.models import Message
from redis import Redis

# Create your views here.

data_path = os.path.join(os.path.dirname(__file__), 'data')
httpHandler = urllib2.HTTPHandler(debuglevel=1)
null_proxy_handler = urllib2.ProxyHandler({})
opener = urllib2.build_opener(httpHandler, null_proxy_handler)
urllib2.install_opener(opener)
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.0 Chrome/30.0.1599.101 Safari/537.36',
    'Connection': 'keep-alive'
}
logger = logging.getLogger('django.request')
VIEWS = [('daily', 'Daily'), ('bkc', 'Weekly & BKC'), ('history', 'History')]


class Test(object):
    task_id = None
    user = None
    comment = None

    def __init__(self, test_id):
        self.test_id = test_id
        self.query_task()

    def query_task(self):
        tasks = Task.objects.filter(test_id=self.test_id)
        print len(tasks)
        if tasks.count():
            self.task_id = tasks[0].id
            self.user = tasks[0].submitter
            self.comment = tasks[0].comment


def upload(request):
    return HttpResponse('success')


def page_not_found(request):
    return render_to_response('404.html')


def page_error(request):
    return render_to_response('500.html')


def null_content(request):
    return new_render(request, 'empty.html', {})

def result_compare(request): 
    table_data = GeneralTestResultCompare(request.session['cmp'])
    context = {
        'data': table_data.result(),
        'header': table_data.header(),
        'case': request.session['cmp'][0].split('/')[3]
    }
    return new_render(request, 'general_compare.html', context=context, title='CP0', subtitle='Compare')

def compare(request):
    cmp_type = ""
    cmp_types = [i.split('/')[-1] for i in request.session['cmp']]
    if len(cmp_types) == 0:
        return HttpResponse('compare container is empty!')
    elif '' in cmp_types and ''.join(cmp_types) == '':
        return daily_weekly_eb_compare(request)
    elif '' not in cmp_types:
        return result_compare(request)
    else:
        return HttpResponse('can not compare!')


def daily_weekly_eb_compare(request):
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
            raw_data = {}
            for j in range(len(raw_build)):
                entries = api.raw_data(project, raw_build[j], test_id) if raw_build[j] else []
                data = get_raw(entries, raw_data=False, med_and_avg=True, max_and_min=True)
                tmp_data = {}
                for item in data:
                    if item.case_name not in all_casename:
                        all_casename.append(item.case_name)
                        case_unit.append(item.unit)
                    tmp_data[item.case_name] = item.average or item.median
                raw_data = { raw_build[j] : data }
            # result_dic["case_data"].append(tmp_data)
            result_dic["build"].append(build)
            result_dic["test_id"].append(test_id)
            result_dic["data"].append(raw_data)    
        else:
            tem_data = {}
            build = i.split("/")[1]
            result_dic["build"].append(build)
            if 'W' in build:
                tem_data = { build: api.get_result_by_tag(project, 'bkc', build, include_raw=True) }
            else:
                tem_data = { build: api.get_result_by_tag(project, 'daily', build, include_raw=True)}
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
        rate = '%.2f %s' % ((abs(flu))/e*100, "%") if e!= 0 else "-"
        row.append(str(flu))
        if flu * reverse > 0:
            row.append("<font class='text-better'>" + str(rate) + "</font>")
        else:
            row.append("<font class='text-worth'>-" + str(rate) + "</font>")
        data_table.append(row)

    context = {
        'views': VIEWS,
        'cases': all_casename,
        'project': project,
        'tests': result_dic["build"],
        'data_table': data_table,
        'cmp': result_dic["build"][-1]
    }
    
    return new_render(request, 'daily_weekly_eb_compare.html', context=context, title='CP0', subtitle='Compare')


def get_config(request, config_name):
    config_path = os.path.join(data_path, 'test_configs', config_name)
    if os.path.exists(config_path):
        config_path_file = json.load(open(config_path, 'r'))
        target = config_path_file['patch_method']
        case_name = config_path_file['case_name']
        case_loop = config_path_file['case_loop']
        case_tool = config_path_file['case_tool']
        cases = ""
        for i in range(len(case_name)):
            if len(case_tool[i]) > 0:
                case = '{0} * {1} * {2}'.format(case_name[i], case_loop[i],','.join(case_tool[i]))
            else:
                case = '{0} * {1}'.format(case_name[i], case_loop[i])
            cases += case + '</br>'
        config_path_file['case_names'] = cases
        if target == 'bap':
            # config_path_file['patch_method'].append('build with patches')
            config_path_file['patches'] = '</br>'.join(re.findall(r'(http.+)', config_path_file['patch']))
            build_type = config_path_file['build_type']
            project = config_path_file['project_name']
            url = BuildPath.objects.filter(build_type=[item[0] for item in BUILD_TYPE_CHOICES if item[1] == build_type][0], project__name=project)[0].url
            if 'base_build' in config_path_file:
                base_build = config_path_file['base_build']
                based_on = urlparse.urljoin(url, base_build)
            else:
                based_on = ''
            config_path_file['based_link'] = based_on
        # else:
        #     config_path_file['patch_method'].append('no patch')
        return JsonResponse(config_path_file, safe=False)
    else:
        return JsonResponse({'error': 'config not exist'})


def test_cases(request, slave_id, project_id):
    project = Project.objects.get(id=project_id)
    slave = Slave.objects.get(id=slave_id)
    cases = urllib2.urlopen('http://' + slave.ip + ':9001/test_cases/' + project.slave_project + '/')
    trs = []
    caseList = json.load(cases)['scripts']
    caseGroup = {}
    for case in caseList:
        gid = str(case['group']['id'])
        if gid not in caseGroup:
            caseGroup[gid] = [case]
        else:
            caseGroup[gid].append(case)

    tmp_id = 0
    for k,v in caseGroup.items():
        display = "table-row"
        g = ""
        if len(v) > 1:
            g = '<div class="i-checks igroup" group={0} style="margin-bottom:-5px;" onclick="select_case(this)"><label><input name="case_group" type="checkbox" aria-name="{1}"></label></div>'.format(k, v[0]['group']['name'])
            td = "<td>{0}</td><td group={1} onclick='extend_case(this)' colspan=4>{2}<div class='caret'></div></td>".format(g,v[0]['group']['id'], v[0]['group']['name'])
            tr = '<tr style="display:{0}">{1}</tr>'.format(display,td)
            display = "none"
            trs.append(tr)
        
        for i, case_dict in enumerate(v):
            c = '<div class="i-checks"><label><input name="case" type="checkbox" id="{0}" aria-name="{1}"></label></div>'
            l = '<input style="width: 60px" name="loop" id="l{0}" type="number" min="1" value="{1}">'
            w = '<input style="width: 60px" name="weight" id="w{0}" type="number">'
            t ='<div class="form-group toolarea"><select id="t{0}" data-placeholder="Choose a tool..." class="chosen-select toolslt" multiple tabindex="4"><option value="Systrace">Systrace</option><option value="Memory">Memory</option><option value="Cpu">CPU</option></select></div>'
            checkbox = c.format(tmp_id, case_dict['name'])
            loop = l.format(tmp_id, case_dict['loop'])
            weight = w.format(tmp_id)
            tool =t.format(tmp_id)
            # {0}: checkbox
            # {1}: case name
            # {2}: loop
            # {3}: weight
            if display == "none":
                td_tag = '<td></td><td>{0}<font class="subCaseText">{1}</font></td><td>{4}</td><td>{2}</td><td>{3}</td>'
            else:
                td_tag = '<td>{0}</td><td><font>{1}</font></td><td>{4}</td><td>{2}</td><td>{3}</td>'
            td = td_tag.format(checkbox, case_dict['name'], loop, weight, tool)
            tr = '<tr style="display:{0}" group={1}>{2}</tr>'.format(display,v[0]['group']['id'], td)
            tmp_id += 1
            trs.append(tr)

    return JsonResponse({'trs': trs})


def add_test_tag(request):
    if request.method == 'POST':
        try:
            project = request.POST.get('project')
            project = project.encode('utf-8') if isinstance(project,unicode) else project
            tag = request.POST.get("tag")
            tag = tag.encode('utf-8') if isinstance(tag, unicode) else tag
            currentbuild = request.POST.get("currentbuild")
            currentbuild = currentbuild.encode('utf-8') if isinstance(currentbuild, unicode) else currentbuild
            subdata = request.POST.get("subdata")
            subdata = subdata.encode('utf-8') if isinstance(subdata, unicode) else subdata
            subdata_list = map(lambda x:x.split(":"),subdata.strip("|").split("|"))

            if api.set_current_build_test_tag(project,tag,currentbuild,subdata_list):
                return JsonResponse({'success': True})

        except Exception, e:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def attachments(request, project, build, test_id, case_name, attachment_name):
    file_path = os.path.join(data_path, project, 'raw', build, test_id, case_name, attachment_name)
    file_ext = attachment_name.split('.')[-1]
    if os.path.exists(file_path):
        print 'file_ext', file_ext
        if file_ext == 'png' or file_ext == 'jpg':
            template = 'pic_viewer.html'
            return new_render(request, 'pic_viewer.html', {
                'content': 'data:image/' + file_ext + ';base64,' + base64.b64encode(open(file_path, 'r').read())})
        elif file_ext == 'h5':
            fs = open(file_path, 'r')
            content = fs.read()
            fs.close()
            return HttpResponse(content)
        elif file_ext in ['zip', 'gz', 'tgz'] or attachment_name.startswith('logcat'):
            response = StreamingHttpResponse(file_iterator(file_path))
            response['Content-Type'] = 'text/plain'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(attachment_name)
            return response
        else:
            try:
                fs = open(file_path, 'r')
                template = 'text_viewer.html'
                content = {'content': fs.read().decode('utf-8')}
                return new_render(request, template, content, title='Log Viewer', subtitle=attachment_name)
            except UnicodeDecodeError:
                response = StreamingHttpResponse(file_iterator(file_path))
                response['Content-Type'] = 'text/plain'
                response['Content-Disposition'] = 'attachment;filename="{0}"'.format(attachment_name)
                return response
    else:
        return render_to_response('500.html')


def download_attachment(request, project, build, test_id, case_name, attachment_name):
    file_path = os.path.join(data_path, project, 'raw', build, test_id, case_name, attachment_name)
    file_ext = attachment_name.split('.')[1]
    response = StreamingHttpResponse(file_iterator(file_path))
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(attachment_name)
    return response


def bkc(request, project_name, yr=None, wk=None):
    show_delete = False
    if request.user.get_username() in [user['username'] for user in Group.objects.get(id=3).user_set.values()]:
        show_delete = True
    current_week = (yr, wk)
    builds = api.weekly_data(project_name).distinct('build')
    weeks = []
    weekly_builds = api.weekly_data(project_name).distinct('build')
    for build in weekly_builds:
        try:
            year, week = re.split(r'_.W', build)
            if (year, week) not in weeks:
                weeks.append((year, week))
        except ValueError:
            continue

    sorted(weeks, key=lambda x: int(x[0]) * 12 + int(x[1][:2]))

    if len(weeks):
        if not wk or not yr:
            current_week = weeks[-1]

        if current_week[0] + '_WW' + current_week[1] in builds:
            prev_build = current_week[0] + '_WW' + current_week[1]
        elif current_week[0] + '_WW' + current_week[1] + '_B' in builds:
            prev_build = current_week[0] + '_WW' + current_week[1] + '_B'
        elif current_week[0] + '_WW' + current_week[1] + '_C' in builds:
            prev_build = current_week[0] + '_WW' + current_week[1] + '_C'
        else:
            prev_build = None

        if current_week[0] + '_BW' + current_week[1] in builds:
            current_build = current_week[0] + '_BW' + current_week[1]
        else:
            current_build = prev_build
            prev_build = None
        data = api.get_result_by_tag(project_name, 'bkc', current_build, include_raw=True)
        prev_data = api.get_result_by_tag(project_name, 'bkc', prev_build, include_raw=True)
        summary = {}
        for d in data:
            pd = [pd for pd in prev_data if pd.case_name == d.case_name]
            reverse = -1 if d.raw[0]['unit'] in ('sec', 'ms', 'msec') else 1
            result = d.result if is_number(d.result) else False
            prev_result = pd[0].result if len(pd) else False
            fluc = float(result) - float(prev_result) if is_number(prev_result) and is_number(result) else False
            rate = round((fluc / float(prev_result) * 100), 2) if fluc and prev_result else False

            summary[d.case_name] = {
                'unit': d.raw[0]['unit'],
                'prev': prev_result,
                'result': d.result,
                'fluc': fluc,
                'rate': rate,
                'down': rate * reverse < 0
            }
        
        context = {
            'show_del': show_delete,
            'views': VIEWS,
            'tag': 'bkc',
            'project_name': project_name,
            'builds': builds,
            'current_week': current_week,
            'weeks': sorted(weeks, key=lambda x: (int(x[0]) * 100) + int(x[1][:2]), reverse=True),
            'current_build': current_build,
            'prev_build': prev_build,
            'data': data,
            'prev_data': prev_data,
            'summary': summary
        }
        return new_render(request, 'bkc.html', context=context, title='Weekly & BKC', subtitle=project_name)
    else:
        return null_content(request)


def daily(request, project_name, build_name=None):
    show_delete = False
    if request.user.get_username() in [user['username'] for user in Group.objects.get(id=3).user_set.values()]:
        show_delete = True
    logger.debug(project_name + "  " +  str(build_name))
    builds = api.build_list(project_name, 'daily')
    if not len(builds):
       return null_content(request)
    current_build = build_name if build_name else builds[0]
    data = list(api.get_result_by_tag(project_name, 'daily', current_build, include_raw=True))
    current_build_index = builds.index(current_build)
    prev_build = builds[current_build_index + 1] if len(builds) > current_build_index + 1 else None
    prev_data = api.get_result_by_tag(project_name, 'daily', prev_build) if prev_build else []
    summary = OrderedDict()
    data = sorted(data, key=lambda x: [x.case_name in ['full boot']], reverse=True)
    
    for d in data:
        pd = [pd for pd in prev_data if pd.case_name == d.case_name]
        reverse = -1 if d.raw[0]['unit'] in ('sec', 'ms', 'msec') else 1
        result = d.result
        prev_result = pd[0].result if len(pd) else False
        if is_number(result) and is_number(prev_result):
            rate = round(((float(result) - float(prev_result)) / float(prev_result) * 100), 2) if prev_result and result else False
            fluc = float(result) - float(prev_result) if prev_result and result else False
            prev =  round(prev_result, 2)
            result = round(result, 2)
        else:
            rate = False
            fluc = False

        summary[d.case_name] = {
            'unit': d.raw[0]['unit'],
            'prev': prev_result,
            'result': result,
            'fluc': round(fluc, 2),
            'rate': abs(rate),
            'down': rate * reverse < 0
        }


    context = {
        'show_del':show_delete,
        'views': VIEWS,
        'tag': 'daily',
        'project_name': project_name,
        'builds': builds,
        'current_build': current_build,
        'prev_build': prev_build,
        'data': data,
        'summary': summary
    }

    return new_render(request, 'daily.html', context, title='Daily', subtitle=project_name)


def customize(request, tag, project, build=None):
    customize_dir = os.path.join(data_path, project, tag)
    if not os.path.exists(customize_dir):
        return page_not_found(request)
    current_build = build
    if project in os.listdir(data_path):
        builds = filter(lambda x: os.path.isdir(os.path.join(customize_dir, x)), os.listdir(customize_dir))
        builds.sort()
        if len(builds):
            if not current_build:
                current_build = builds[-1]
            prev_build = builds[builds.index(current_build) - 1]

            # SUMMARY
            summary = TagSummary(tag_name=tag, build=current_build, prev_build=prev_build, project_name=project)

            # DETAIL
            raw_data = []
            test_results = summary.get_test_result()
            for test in test_results:
                test_id, file_name = test
                raw_data.append(RawData2(project, current_build, test_id, file_name))

            context = {
                'tag': tag,
                'project': project,
                'builds': builds,
                'current_build': current_build,
                'prev_build': prev_build,
                'summary': summary.result,
                'raw_data': sorted(raw_data, key=lambda x: (x.case_name, x.loop)),
                'attachment_url': '/'.join(['attachment', project, current_build])
            }
            return new_render(request, 'daily.html', context, title=tag, subtitle=project)
        else:
            return null_content(request)
    else:
        return null_content(request)


def raw(request, project_name, build_name, *args):
    logger.debug('project_name ' + project_name)
    show_delete = False
    if request.user.get_username() in [user['username'] for user in Group.objects.get(id=3).user_set.values()]:
        show_delete = True
    cursors = list(api.raw_data(project_name, build_name))
    test_id_list = []
    task_id = 0
    for tid, group in groupby(cursors, key=lambda x: x['test_id']):
        gp = list(group)
        task_id = gp[0]['task_id']
        tasks = Task.objects.filter(id=task_id)
        test_id_list.append(
            {
                'test_id': tid,
                'test_count': len(gp),
                'task': tasks[0] if len(tasks) else None,
                'mt_comment': json.loads(tasks[0].comment) if (gp[0]['test_tag'] == 'mt' and len(tasks)) else {},
                'color': '#007500' if gp[0]['test_tag'] == 'mt' else ''
            }
        )

    if args:
        get_entries = filter(lambda x: x['test_id'] == args[0], cursors)
    else:
        get_entries = cursors

    if len(get_entries) > 0:
        task_id = get_entries[0]['task_id']
        test_id = get_entries[0]['test_id']
    else:
        task_id = task_id
        test_id = args[0]
    data = get_raw(get_entries, raw_data=True, med_and_avg=True, max_and_min=True) if len(get_entries) > 0 else {}
    tasks = Task.objects.filter(id=task_id)
    context = {
        'show_del': show_delete,
        'data': data,
        'attachment_url': '/'.join(['attachment', project_name, build_name, test_id]),
        'message': Message.objects.filter(title='task_id', parent_id=task_id),
        'task': tasks[0] if tasks else {},
        'build': build_name,
        'current_build': build_name,
        'test_id_list': test_id_list,
        'project_name': project_name,
        'test_id': test_id,
        'config': test_config(tasks[0].test_config) if tasks else ''
    }
    return new_render(request, 'raw.html', context, title=project_name.upper(), subtitle=build_name)


def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


def view_project(request, project_name):
    # [input[i:i+n] for i in range(0, len(input), n)]
    rds = Redis(host='localhost')
    projects = Project.objects.filter(name=project_name)
    if len(projects):
        proj = projects[0]

    context = {
        'project': proj,
        'products': ', '.join(rds.lrange('products_%s' % proj.builder_name, 0, -1)),
        'db_info': api.db_info(project_name)
    }
    return new_render(request, 'project.html', context=context, title=project_name, subtitle='Overview')


def production_index(request, production_name):
    templates = {
        'gp21': 'project_index_2_1.html',
        'gp2': 'project_index.html',
        'kbl': 'project_index_kbl.html',
        'aic': 'project_index_aic.html'
    }

    filtered_projects = Project.objects.filter(production__short_name=production_name)

    context = {
        'views': VIEWS,
        'tag': 'daily',
        'filtered_projects': filtered_projects
    }
    print(filtered_projects)
    return new_render(request, templates[production_name], context=context)


def first_set_up():
    if not os.path.exists(data_path):
        os.mkdir(data_path)


def test_template_index(request):
    templates = ConfigTemplate.objects.filter(user=request.user)
    splited = [templates[i:i + 3] for i in xrange(0, len(templates), 2)]
    return new_render(request, 'test_template_index.html', context={'templates': splited})


def upload_aicData(request):
    if request.method == "POST":
        files = request.FILES.getlist('file')
        cui_dir = './data/data/aic/raw/aic_status/logs/instance_ins'
        if not os.path.exists(cui_dir):
            os.makedirs(cui_dir)
        try:
            for i in files:
                dest = open(cui_dir + '/' + i.name, 'wb+')
                for chunk in i.chunks():
                    dest.write(chunk)
                dest.close()
                return HttpResponse('success')
        except Exception, e:
            return HttpResponse('failure')
