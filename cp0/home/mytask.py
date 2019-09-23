from cp0.lib import new_render
from data.models import Task, Logger
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger


class CustomPaginator(Paginator):
    def __init__(self, page_tabs, object_list, per_page):
        Paginator.__init__(self, object_list, per_page)
        self.page_tabs = page_tabs

    def get_page_tabs(self):   
        return self.page_tabs


def mytask_view(request):
    return new_render(request, 'mytask.html')


def getmytask(request):
    try:
        p = int(request.GET.get('page'))
    except Exception as e:
        p = 1
    mytasks = Logger.objects.filter(~Q(description='mt'), user=request.user.id)[::-1]
    mytasks_paginator = CustomPaginator(10, mytasks, 7)
    try:
        posts = mytasks_paginator.page(p)
    except PageNotAnInteger:
        posts = mytasks_paginator.page(1)
    except EmptyPage:
        posts = mytasks_paginator.page(mytasks_paginator.num_pages)
    page_tabs = mytasks_paginator.get_page_tabs()
    start_page_tab = p - page_tabs // 2
    end_page_tab = p + page_tabs // 2
    middle_page_tab = int(page_tabs // 2)
    if p <= middle_page_tab:
        start_page_tab = 1
        end_page_tab = page_tabs
    if p > mytasks_paginator.num_pages - middle_page_tab:
        start_page_tab = mytasks_paginator.num_pages - page_tabs + 1
        end_page_tab = mytasks_paginator.num_pages
    page_html = ""
    for i in range(start_page_tab, end_page_tab + 3):
        if i < 1:
            continue
        if i > mytasks_paginator.num_pages:
            break
        per_page_html = '<button id="p_{0}" class="btn btn-white" onclick="getMytasks({0})">{0}</button>'.format(i)
        # per_page_html = '<li id="p_{0}"> <a onclick="getMytasks({0})">{0}</a></li>'.format(i)
        page_html += per_page_html
    return new_render(request, 'mytask_table.html', {"mytasks": posts, "page_html": page_html})


def getmyfavorites(request):
    try:
        p = int(request.GET.get('page'))
    except Exception as e:
        p = 1
    favoritesTasks = Task.objects.filter(favorites=request.user.id)
    myfavorites = Logger.objects.filter(task__in=favoritesTasks)[::-1]
    myfavo_paginator = CustomPaginator(10,myfavorites,7)
    try:
        myfavo_posts = myfavo_paginator.page(p)
    except PageNotAnInteger:
        myfavo_posts = myfavo_paginator.page(1)
    except EmptyPage:
        myfavo_posts = myfavo_paginator.page(myfavo_paginator.num_pages)
    page_tabs = myfavo_paginator.get_page_tabs()
    start_page_tab = p - page_tabs // 2
    end_page_tab = p + page_tabs // 2
    middle_page_tab = int(page_tabs // 2)
    if p <= middle_page_tab:
        start_page_tab = 1
        end_page_tab = page_tabs
    if p > myfavo_paginator.num_pages - middle_page_tab:
        start_page_tab = myfavo_paginator.num_pages - page_tabs + 1
        end_page_tab = myfavo_paginator.num_pages
    page_html = ""
    for i in range(start_page_tab, end_page_tab + 3):
        if i < 1:
            continue
        if i > myfavo_paginator.num_pages:
            break
        per_page_html = '<button id="pf_{0}" class="btn btn-white" onclick="getMyfavorites({0})">{0}</button>'.format(i)
        page_html += per_page_html
    return new_render(request, 'myfavorite_table.html', {"myfavorites": myfavo_posts, "page_html": page_html})


def getmymanualtasks(request):
    try:
        p = int(request.GET.get('page'))
    except Exception as e:
        p = 1
    mytasks = Logger.objects.filter(user=request.user.id, description='mt')[::-1]
    mytasks_paginator = CustomPaginator(10, mytasks, 7)
    try:
        posts = mytasks_paginator.page(p)
    except PageNotAnInteger:
        posts = mytasks_paginator.page(1)
    except EmptyPage:
        posts = mytasks_paginator.page(mytasks_paginator.num_pages)
    page_tabs = mytasks_paginator.get_page_tabs()
    start_page_tab = p - page_tabs // 2
    end_page_tab = p + page_tabs // 2
    middle_page_tab = int(page_tabs // 2)
    if p <= middle_page_tab:
        start_page_tab = 1
        end_page_tab = page_tabs
    if p > mytasks_paginator.num_pages - middle_page_tab:
        start_page_tab = mytasks_paginator.num_pages - page_tabs + 1
        end_page_tab = mytasks_paginator.num_pages
    page_html = ""
    for i in range(start_page_tab, end_page_tab + 3):
        if i < 1:
            continue
        if i > mytasks_paginator.num_pages:
            break
        per_page_html = '<button id="pm_{0}" class="btn btn-white" onclick="getMyManualtasks({0})">{0}</button>'.format(i)
        page_html += per_page_html
    return new_render(request, 'mytask_table.html', {"mytasks": posts, "page_html": page_html})


def mytask(request):
    p = int(request.GET.get('page')) if 'page' in request.GET else "1"
    tab = request.GET.get('tab') if 'tab' in request.GET else "1"
    uid = request.user.id
    return new_render(request, 'mytask.html', {"mytasks": getmytask(p, uid), "myfavorites": getmyfavorites(p, uid), "tab": tab})


def object2AttrDict(obj):
    res = {}
    for attr_name in dir(obj):
        try:
            attr = getattr(obj, attr_name)
            if callable(attr):
                # method
                continue
        except AttributeError:
            continue
        res[attr_name] = attr
    return res


def model2Json(obj):
    import json
    attrs = object2AttrDict(obj)
    res = {}
    for attr_name, attr in attrs.items():
        if str(attr_name).startswith("_") or attr_name == "pk":
            continue
        res[attr_name] = attr
    return json.dumps(res)

