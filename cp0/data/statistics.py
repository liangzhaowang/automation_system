from cp0.lib import new_render, JsonResponse
from data.models import Task, Slave, User, Project
from collections import OrderedDict
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from django.conf import settings
from pytz import timezone
import datetime
import json
import random


def get_summary(request):
    tasks = Task.objects.all()
    annotates = tasks.annotate(month=TruncMonth('create_time')).values('month').annotate(c=Count('id')).values('month', 'c')
    month_list = [annotate['month'].strftime("%Y-%m") for annotate in annotates]
    task_count_list = [annotate['c'] for annotate in annotates]
    res = {
        'task_count': tasks.count(),
        'project_count': Project.objects.all().count(),
        'slave_count': Slave.objects.all().count(),
        'user_count': User.objects.all().count(),
        'task_count_list': task_count_list,
        'month_list': month_list,
    }
    return JsonResponse(res)


def get_weekly_statistics(request, duration):
    duration = int(duration)
    settings_time_zone = timezone(settings.TIME_ZONE)
    now = datetime.datetime.now()
    start = now - datetime.timedelta(days=duration-1)
    queryset = Task.objects.filter(start_time__gt=start)
    public_slaves = Slave.objects.filter(policy=0)
    date_range = [(now - datetime.timedelta(days=i)) for i in range(duration)]
    
    res = OrderedDict()
    for task in queryset:
        if task.slave.num in res:
            i = (now - task.start_time.replace(tzinfo=None)).days
            res[task.slave.num][i] += (task.duration() / 60)
        else:
            res[task.slave.num] = [0] * duration

    datasets = []
    for k, v in res.items():
        datasets.append({
            'label': k,
            'backgroundColor': 'rgb({}, {}, {})'.format(*random_color()),
            'data': v
        })
    
    return JsonResponse({
        'labels': [dt.strftime('%Y-%m-%d') for dt in date_range],
        'datasets': datasets
    })


def random_color():
    rgb = []
    for i in range(3):
        color = random.randint(0, 255)
        rgb.append(color)
    return rgb

def get_statistics(request, duration):
    duration = int(duration)
    now = datetime.datetime.now()
    start = now - datetime.timedelta(days=duration)
    queryset = Task.objects.filter(start_time__gt=start)
    public_slaves = Slave.objects.filter(policy=0)
    total_execution = 0

    res = OrderedDict()
    for task in queryset:
        total_execution += task.duration() or 0
        if task.slave.id in res:
            res[task.slave.id]['tasks'].append(task.id)
            res[task.slave.id]['sum'] += task.duration()
        else:
            res[task.slave.id] = {
                'slave_info': {
                    'ip': task.slave.ip,
                    'number': task.slave.num
                },
                'tasks': [task.id],
                'sum': task.duration() or 0
            }

    # extend slaves with no task
    for slave in public_slaves:
        if slave.id not in res:
            res[slave.id] = {
                'slave_info': {
                    'ip': slave.ip,
                    'number': slave.num
                },
                'tasks': [],
                'sum': 0
            }
    res['total'] = {
        'hours': int(total_execution / 3000),
        'tasks': queryset.count()
    }
    return JsonResponse(res)


def index(request):
    context = {
    }
    return new_render(request, 'statistics.html', context=context, subtitle='Statistics')