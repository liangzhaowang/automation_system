# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import time
import redis
from data.models import *
from cp0.lib import new_render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from home.views import new_test
from django.shortcuts import render_to_response
from django.http import StreamingHttpResponse
from people.models import *
from Patches import Patches
from data.attachment_views.bar_data import CSV_PARSE
from cp0.settings import BASE_DIR
import re
import json
import os
import requests
import logging
from getdata import Getbuild
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

rds = redis.Redis(host='localhost', port=6379)
logger = logging.getLogger('django')
vdates = time.strftime('%Y-%m-%d %H:%M:%S')
vdate = datetime.datetime.strptime(vdates, '%Y-%m-%d %H:%M:%S')
dayall = datetime.timedelta(days=vdate.isoweekday())
dayfrom = (vdate - dayall + datetime.timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
dayto = (vdate - dayall + datetime.timedelta(days=7)).strftime('%Y-%m-%d 23:59:59')
timefrom = datetime.datetime.strptime(dayfrom, '%Y-%m-%d %H:%M:%S')
timeto = datetime.datetime.strptime(dayto, '%Y-%m-%d %H:%M:%S')
buildsPath = os.path.join(os.path.join(BASE_DIR, 'people/builds'), 'builds.json')


def index_page(request, project):
    global timefrom
    global timeto
    build_list = ''
    index_html = 'index_{0}.html'.format(project)
    available_filter = patch.objects.filter(project=project).filter(available=True).order_by('-id').exclude(status='MERGED').exclude(status='ABANDONED')
    usrnames = str(request.user)
    counts = len(available_filter)
    clipboard = []
    if os.path.exists(buildsPath):
        build_list = json.load(open(buildsPath, 'r'))
    build_count = len(filter(lambda x:x['project']==project, build_list))
    for i in available_filter:
        i.data = i.track.split('/')[-1]
        i.fomartted_date = (i.patchtime + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        clipboard.append(i.fullpatch())
    all_filter = patch.objects.filter(project=project).order_by('-id')
    all_counts = str(len(all_filter))
    for l in all_filter:
        l.fomartted_date = (l.patchtime + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        l.data = l.track.split('/')[-1]
    return new_render(request, index_html,
                      {'str': available_filter, 'clipboard': '\r'.join(clipboard), 'counts': counts, 'All': patch.objects.filter(project=project),
                       'users': usrnames,
                       'ALL': all_filter, 'all_counts': all_counts, "project":project, 'Builds':build_list, 'build_count':build_count}, title='CP0', subtitle=(project.upper()))

def select_page(request,project):
    textdata = request.POST['selects']
    textdatas = textdata.encode('utf-8')
    f = textdatas.split('-')
    clipboard = []
    for s in f:
        if s != "":
            if patch.objects.filter(id=s).filter(project=project):
                clipboard.append(patch.objects.filter(project=project).get(id=s).patch)
            else:
                fs = 'https://android.intel.com/#/c/%s/' % s
                clipboard.append(fs)
    clipboards = list(set(clipboard))
    newdata = '\r'.join(clipboards)
    return HttpResponse(newdata)

def addmerge_page(request):
    textdata = request.POST['merged']
    textdatas = textdata.encode('utf-8')
    f = textdatas.split('-')
    clipboard = []
    for s in f:
        if s != "":
            clipboard.append(s)
    newdata = '\r'.join(clipboard)
    return HttpResponse(newdata)

def test_page(request, project):
    if request.method == "POST":
        usrnames = str(request.user)
        textarea = request.POST['content']
        cate = str(request.POST['cate'])
        comments = str(request.POST['comments'])
        patch_list = re.findall(r'/(\d+)', textarea)
        lists = []
        if patch_list:
            for i in patch_list:
                patchs = 'https://android.intel.com/#/c/%s/' % i
                if len(patch.objects.filter(project=project).filter(patch=patchs)) == 0:
                    patchtimes = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data = i
                    owner = str(Patches(data).owner)
                    subject = str(Patches(data).subject)
                    status = str(Patches(data).status)
                    track_id = str(Patches(data).track_id)
                    if status != '':
                        p = patch(name=usrnames, patch=patchs, patchtime=patchtimes, owner=owner, subject=subject,
                                      status=status, track=track_id, category=cate, comments=comments, project=project)
                        p.save()
                        lists.append('Success:\nAdd Patch {0} success '.format(i))

                    else:
                        lists.append('Add Fail:\nPatch {0} status is None'.format(i))

                else:
                    patch.objects.filter(project=project).filter(patch=patchs).update(available=True)
                    lists.append('Back to list:\nPatch {0} is already display now'.format(i))
            return HttpResponse('\n'.join(lists))
        else:
            return HttpResponse('Please input normal patches')

def del_page(request, project):
    a = request.POST['data']
    if project in ['demo_video', 'others', 'video']:
        if a != None:
            uploads.objects.filter(project=project).filter(id=a).update(available=False)
            return HttpResponse('success')
    else:
        a = request.POST['data']
        if a != None:
            patch.objects.filter(project=project).filter(id=a).update(available=False)
        return HttpResponse('success')

def calendar_page(request, project):
    all = patch.objects.filter(project=project)
    all_bkc = bkc.objects.filter(project=project)
    content = []
    for i in all:
        start = (i.patchtime + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        patches = i.patch
        patchs = str("<a href=\"" + patches + "\"target='_blank'>" + patches + "</a>")
        owner = i.owner
        title = str(i.subject) + ":" + str(i.patch)
        status = i.status
        track = i.track
        cate = i.category
        if track == "None":
            track = i.track
        else:
            track = str("<a href=\"" + i.track + "\"target='_blank'>" + i.track + "</a>")
        content.append({
            "patch": patchs,
            "title": title,
            "start": start,
            "owner": owner,
            "status": status,
            "track": track,
            "cate": cate
        })
    for i in all_bkc:
        list_bkc = []
        start = i.time.strftime("%Y-%-m-%d %H:%M:%S")
        patchs = i.patchlist
        patchs = patchs.encode("utf-8")
        patches = eval(patchs)
        for l in patches:
            s = l.split('|')
            data = "<tr><td style='text-align:center'>" + s[0] + "</td>" + "<td style='text-align:center'>" + s[
                1] + "</td>" + "<td style='text-align:center'>" + s[
                       2] + "</td>" + "<td style='text-align:center'>" + s[
                       3] + "</td>" + "<td style='text-align:center'>" + s[4] + "</td></tr>"
            list_bkc.append(data)
        datas = ''.join(list_bkc)
        patch_sum = "<table class='table'><tr><th  style='text-align:center'>ID</th><th  style='text-align:center'>SUBJECT</th>" + \
                    "<th  style='text-align:center'>STATUS</th><th  style='text-align:center'>TRACK</th>" + \
                    "<th  style='text-align:center'>CATEGORY</th></tr>" + datas + "</table>"
        owner = "JLF_BKC"
        title = i.sub
        status = "Record Success"
        track = str(i.eb)
        if track == '':
            id = i.id
            task_id = i.task
            if task_id:
                tasks = Task.objects.get(id=task_id)
                config_id = str(tasks.test_config)
                if (json.load(open("./data/data/test_configs/" + config_id)).has_key('base_build')):
                    new_eb = "https://buildbot.sh.intel.com/absp/builders/master-engineering/builds/" + \
                             json.load(open("./data/data/test_configs/" + config_id))['build']
                    bkc.objects.filter(project=project).filter(id=id).update(eb=new_eb)
                    track = str("<a href=\"" + new_eb + "\"target='_blank'>" + new_eb + "</a>")
                else:
                    track = str(i.eb)
        else:
            if track[-1] == "]":
                track = track[2:-1][1:-1]
                track = str("<a href=\"" + track + "\"target='_blank'>" + track + "</a>")
            else:
                track = str("<a href=\"" + track + "\"target='_blank'>" + track + "</a>")
        content.append({
            "patch": patch_sum,
            "title": title,
            "start": start,
            "owner": owner,
            "status": status,
            "track": track,
            "cate": "BKC"
        })
    return JsonResponse(content, safe=False)

def calendar_data_page(request, project):
    all = patch.objects.filter(project=project)
    all_week = bkc.objects.filter(project=project)
    content = []
    for i in all:
        start = (i.patchtime + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        title = str(i.subject) + ":" + str(i.patch)
        content.append({
            "title": title,
            "start": start
        })
    for i in all_week:
        start = i.time
        title = i.sub
        content.append({
            "title": title,
            "start": start
        })
    return JsonResponse(content, safe=False)

def week_page(request, project):
    sun = ((timeto - datetime.timedelta(days=7))).strftime('%Y-%m-%d %H:%M:%S')
    patches = []
    tips = []
    if request.method == "POST":
        data = json.loads(request.POST["data"])
        clips = data["patch"].split('\n')
        eb = data["display_build"]
        new_task = new_test(request)
        new_task = json.loads(new_task.content)
        tasks_id = new_task["task_id"]
        try:
            if tasks_id:
                tasks = Task.objects.get(id=tasks_id)
                config_id = tasks.test_config
                if (json.load(open("data/data/test_configs/" + config_id)).has_key('base_build')):
                    new_eb = json.load(open("./data/data/test_configs/" + config_id))['build']
                else:
                    new_eb = ''
            for i in clips:
                if i:
                    s = patch.objects.filter(project=project).get(patch=i)
                    if s:
                        datas = s.patch.split('/')[-2]
                        track = s.track
                        if track == "None":
                            track = s.track
                        else:
                            track = str(
                                "<a href=\"" + s.track + "\"target='_blank'>" + s.track.split('/')[-1] + "</a>")
                        data = "<a href=\"" + s.patch + "\"target='_blank'>" + datas + "</a>" + "|" + s.subject + "|" + s.status + "|" + track + "|" + s.category
                        patches.append(data)
            if not bkc.objects.filter(sub=eb):
                p = bkc(time=sun, sub=eb, eb=new_eb, patchlist=patches, task=str(tasks_id), project=project)
                p.save()
                if p:
                    tips.append('Generate BKC Record: {0} Success'.format(eb))
                else:
                    tips.append('Generate BKC Record: {0} Failed!!'.format(eb))
            else:
                bkc.objects.filter(sub=eb).update(time=sun, eb=new_eb, patchlist=patches, task=str(tasks_id), project=project)
                tips.append('Update BKC Record: {0} Success'.format(eb))
            return JsonResponse(tips, safe=False)
        except Exception as e:
            print e
            return HttpResponse('Error')

def Get_list(request):
    slists = {}
    optionAll = []
    slaveId = []
    projectAll = []
    project = request.GET["project"]
    slist = Getbuild(project).get_weekly()
    project_all = Project.objects.all()
    for i in slist:
        options = "<option value=%s>%s</option>" % (i, i)
        optionAll.append(options)
    slaves = Slave.objects.filter(policy=0)
    private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
    available_slaves = []
    for p_slave in private_slave:
        available_slaves.append({"id": p_slave.id, "name": p_slave.num, "comment": p_slave.comment})
    for slave in slaves:
        available_slaves.append({"id": slave.id, "name": slave.num, "comment": slave.comment})
    for j in available_slaves:
        options = "<option value=%s>%s</option>" % (j["id"], j["name"] + ":%s" % (j["comment"]))
        slaveId.append(options)
    for k in project_all:
        options = "<option value=%s>%s</option>" % (k.id, k.name)
        projectAll.append(options)
    slists["sli"] = '\n'.join(optionAll),
    slists["slave"] = '\n'.join(slaveId)
    slists["projects"] = '\n'.join(projectAll)
    return JsonResponse(slists, safe=False)

def generate_build(request, project):
    buildNum = 0
    patch_list = request.POST["patch_list"]
    project_name = request.POST["project_name"]
    acrnAuther = {'Authorization': 'Basic {}'.format(rds.get('auth_header'))}
    genetime = time.strftime("%Y%m%d_%H%M%S")
    build_url = 'https://buildbot.sh.intel.com/absp/builders/{0}-engineering/builds/'.format(project_name)
    manifest = 'manifests-generated.json'
    print 'checking', build_url
    if requests.get(build_url + 'manifests-generated.json', verify=False, headers=acrnAuther).status_code == 404:
        manifest = 'manifests-original.json'
    manifest_override_url = '{0}/{1}'.format(build_url, manifest)

    # project = Project.objects.get(id=12)
    post_url = 'https://buildbot.sh.intel.com/absp/builders/{0}-engineering/force'.format(
        "f_o_mr1_acrn_pnp")  # project.builder_name)
    data = {
        'forcescheduler': 'force_engineering_{0}'.format("f_o_mr1_acrn_pnp"),  # project.builder_name),
        'reason': genetime,
        'download_list_computation_mode': 'reorder without downloading other patches',
        'force_build_changeids': patch_list,
        'variant_list': 'userdebug',
        'target_products_to_build': 'gordon_peak_acrn',
        'customized_build_command': '',
        'preferred_site': 'sh',
        'branch_list': '',
        'manifest_override_url': ''
    }
    stateCode = requests.post(post_url, data=data, verify=False, headers=acrnAuther).status_code
    time.sleep(5)
    buildbot_link = "https://buildbot.sh.intel.com/absp/json/builders/f_o_mr1_acrn_pnp-engineering/"
    building_list = json.loads(requests.get(buildbot_link, verify=False).text)['currentBuilds']
    query_attrs = '&'.join(map(lambda x: 'select=' + str(x), building_list))
    building_info_url = buildbot_link + 'builds?' + query_attrs
    building_info = json.loads(requests.get(building_info_url, verify=False).content)
    for key, value in building_info.items():
        for item in value['properties']:
            if genetime in item:
                buildNum = key
    if stateCode == 200 and buildNum:
        buildNumurl = os.path.join(build_url, buildNum)
        if not os.path.exists(buildsPath):
            fp = open(buildsPath,'w')
            fp.write('[]')
            fp.close()
        Builds = json.load(open(buildsPath, "r"))
        tmpdict = {"time": genetime, "owner": str(request.user), "patch": patch_list, "Eburl": buildNumurl,
                   "Ebnum": buildNum, "project":project}
        Builds.append(tmpdict)
        try:
            Jason_File = open(buildsPath, "w")
            Jason_File.write(json.dumps(Builds))
            Jason_File.close()
        except Exception, e:
            print e
        return JsonResponse(buildNumurl, safe=False)
    else:
        return JsonResponse("Failed code:%s" % stateCode, safe=False)

def upload_file(request):
    cur_user = request.user
    all = uploads.objects.filter(available=True).order_by("-id")
    for i in all:
        i.fmattime = (i.create_time + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    return new_render(request, 'upload.html', {"all": all, "user":cur_user}, title='CP0', subtitle='UPLOAD_FILE')

def create_file(request):
    cui_dir= ''
    name = request.user
    create_dir = time.strftime('%Y%m%d_%H%M%S')
    create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if request.method == "POST":
        files = request.FILES.getlist('file')
        project = request.POST['projects']
        build = request.POST['builds']
        if project == 'demo_video' or project == 'video':
            cui_dir = os.path.join('./collect_static/video', build, create_dir, project)
        else:
            cui_dir = os.path.join('./data/data/upload/raw', build, create_dir, project)
        if not os.path.exists(cui_dir):
            os.makedirs(cui_dir)
        try:
            for i in files:
                dest = open(cui_dir + '/' + i.name, 'wb+')
                p = uploads(user=name, create_time=create_time, project=project, build=build,
                            url=str(cui_dir.replace('collect_static', 'static') + '/' + i.name))
                p.save()
                for chunk in i.chunks():
                    dest.write(chunk)
                dest.close()
        except Exception, e:
            print e
            return False
    return HttpResponseRedirect('/upload_file/')

def view_attach(request, data):
    Title = 'CP0'
    if 'mp4' in data:
        return new_render(request, "video_view.html", {"video_url":data}, title=Title,
                      subtitle='VIEW_VIDEOS')
    else:
        title = 'Chart View'
        all_data = CSV_PARSE(data).bar_total()
        return new_render(request, "charts_common.html", {'alldata': all_data, "title_name": title}, title=Title,
                      subtitle='VIEW_CHARTS')

def view_log(request, text):
    data = text.split('.')[-1]
    if data:
        text_log = open(text).read().decode('utf-8')
        return new_render(request, 'log_view.html', {'content': text_log})
    else:
        return render_to_response('500.html')

def file_iterator(data, chunk_size=512):
    with open(data) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break

def download_log(request, log_id):
    logs = uploads.objects.get(id=log_id).url
    if 'video' in logs:
        logs = logs.replace('static', 'collect_static')
    # print 'downurl', logs
    file_name = logs.split('/')[-1]
    response = StreamingHttpResponse(file_iterator(logs))
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)
    return response

def getpatches(request, project):
    tmpcontent = []
    patches = request.POST['patches']
    tmplist = re.findall('https://android.intel.com/#/c/\d+/', patches)
    contentall = ''
    for i in tmplist:
        f = patch.objects.filter(project=project).filter(patch=i)
        for allList in f:
            allList.fomartted_date = (allList.patchtime + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            content = "<tr><td style='text-align:center'><a href='%s'>"%allList.patch + re.findall('\d+', allList.patch)[
                0] + "</a></td>" + "<td style='text-align:left'>" + allList.fomartted_date + "</td>" +"<td style='text-align:left'>" + allList.subject + "</td>" + "<td style='text-align:center'>" + allList.status + "</td>" + "<td style='text-align:center'><a href='%s' target='_blank'>"%((lambda x:'#' if x=='None' else x)(allList.track)) + (lambda x:x if x=='None' else re.findall('OAM-\d+',x)[0])(allList.track) +"</a></td>" + \
                      "<td style='text-align:center'>" + allList.category + "</td>" + "<td style='text-align:center'>" + allList.comments + "</td></tr>"
            tmpcontent.append(content)
        contentall = "<table class='table'><tr><th style='text-align:center'>ID</th><th style='text-align:center'>TIME</th>" + \
                     "<th style='text-align:center'>SUBJECT</th><th style='text-align:center'>STATUS</th><th style='text-align:center'>TRACK</th>" + \
                     "<th style='text-align:center'>CATEGORY</th>" + "<th style='text-align:center'>COMMENT</th></tr>" +''.join(
            tmpcontent) + "</table>"
    return JsonResponse(contentall, safe=False)


