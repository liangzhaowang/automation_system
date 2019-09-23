import os
import time
import json
import requests
import datetime
import subprocess
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.conf import settings
from cp0.lib import new_render
from data.models import Slave
from data.models import SlaveForm
from django.forms import modelformset_factory, modelform_factory


def profile_view(request):
    private_slave = Slave.objects.filter(policy='1', owner=request.user.id)
    SlaveFormSet = modelformset_factory(Slave, form=SlaveForm, max_num=1)
    private_slave_stat = []
    for slave in private_slave:
        stat = slave.status()
        is_running = True if "atf_test_id" in stat and stat["atf_test_id"] != "None" else False
        private_slave_stat.append({"slave_id": slave.id, "is_running": is_running})

    context = {
        'slaves': private_slave,
        'formsets': [SlaveFormSet(queryset=Slave.objects.filter(id=slave.id)) for slave in private_slave],
        'newslavefrom': modelform_factory(Slave, form=SlaveForm)(),
        'private_slave_stat': private_slave_stat
    }
    return new_render(request, 'profile.html', context=context, subtitle='Profile')


def update_slave(request, slave_id):
    SlaveFormSet = modelformset_factory(Slave, form=SlaveForm, max_num=1)
    if request.method == 'POST':
        formset = SlaveFormSet(
            request.POST, request.FILES,
            queryset=Slave.objects.filter(id=int(slave_id)),
        )
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect('/dashboard/')
    return HttpResponseRedirect('/dashboard/')


def add_slave(request):
    if request.method == 'POST':
        slave = Slave()
        slave.owner = request.user
        slave.install_status = 0
        slave_f = SlaveForm(request.POST, instance=slave)
        if slave_f.is_valid():
            username = request.POST["user_name"]
            ip = request.POST["ip"]
            passwd = request.POST["passwd"]
            p = subprocess.Popen("expect ./scripts/autossh.sh {0} {1} {2}".format(username, ip, passwd), stdout=subprocess.PIPE, shell=True)
            start = datetime.datetime.now()
            timeout = 3
            while p.poll() is None:
                time.sleep(0.2)
                now = datetime.datetime.now()
                if (now - start).seconds > timeout:
                    p.terminate()
                    return HttpResponseRedirect('/dashboard/')
            p.stdout.readlines()
            ret = os.system("sshpass -p {0} scp {1}/install.sh {2}@{3}:/tmp/".format(passwd, settings.SCRIPT_PATH, username, ip))
            if ret == 0:
                slave_f.save()
                p_install = subprocess.Popen("sshpass -p {0} ssh -t {1}@{2} 'echo {0} | sudo -S cp /tmp/install.sh /usr/local/bin/slavemanger && slavemanger -c -g -i -p {0}'".format(passwd, username, ip), stdout=subprocess.PIPE, stderr=subprocess.PIPE ,shell=True)
            return HttpResponseRedirect('/dashboard/')
        else:
            private_slave = Slave.objects.filter(policy='1', owner=request.user.id)
            SlaveFormSet = modelformset_factory(Slave, form=SlaveForm, max_num=1)
            context = {
                'slaves': private_slave,
                'formsets': [SlaveFormSet(queryset=Slave.objects.filter(id=slave.id)) for slave in private_slave],
                'newslavefrom': slave_f
            }
            return new_render(request, 'profile.html', context=context, subtitle='Profile')
    return HttpResponseRedirect('/dashboard/')
