from django.contrib.auth.models import User
from django.shortcuts import HttpResponseRedirect
from django.http import JsonResponse
from cp0.lib import new_render
from data.models import Project, Slave


def index(request):
    owner = None if request.user.is_superuser else request.user
    slaves = Slave.objects.filter(owner=owner)
    context = {
        'joined_projects': [p.serialize for p in Project.objects.all()],
        'slaves': [slave.serialize for slave in slaves[:5]],
        'public_cases': [
            {
                'name': 'boot_analyze_2_0.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'Acrn_BTM.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'boottime.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'bootanalyze.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'boot_analyze_2_0.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'adb_rlbench.py',
                'owner': 'Liang, YuxiangX'
            },
            {
                'name': 'adb_gfx_gl4.py',
                'owner': 'Liang, YuxiangX'
            }
        ],
        'private_cases': [
            {
                'name': 'cp0_master_smoke_test.py',
                'owner': 'Chen, ChenX'
            },
            {
                'name': 'cp0_slave_smoke_test.py',
                'owner': 'Liang, YuxiangX'
            }
        ]
    }
    return new_render(request, 'workspace.html', context=context, title='CP0', subtitle='My Workspace')


def slave(request, slave_id):
    context = {

    }
    return new_render(request, 'workspace.slave.html', context=context, title='CP0', subtitle='My Workspace')


def create_project(request):
    if request.method == 'GET':
        context = {
            'users': ['%s, %s' % (u.last_name, u.first_name)
            for u in User.objects.exclude(last_name__exact='')],
            'slaves': [slave.serialize for slave in Slave.objects.all()]
        }
        return new_render(request, 'workspace.createproject.html', context=context, title='CP0', subtitle='Create project')
    elif request.method == 'POST':
        print('save project')
        return HttpResponseRedirect('/')


def get_contributors(request):
    return JsonResponse({
        'users': 'Yang WeiyunX, Shan ShanX, Chen ChenX, Jiang LinfengX'
    })