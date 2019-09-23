from django.core.management.base import BaseCommand
import json
import time
from people.models import bxtp_m
from people.models import bxtp_o
from Patches import Patches
from people.models import bkc_m
from people.models import bkc_o
from data.models import Task


class Command(BaseCommand):

    def handle(self,*args, **options):
        while True:
            options_time = time.strftime("%Y-%m-%d %H:%M:%S")
            print "======================================="
            print "Now time is: {0}".format(str(options_time))
            self.checkdata()
            print "Please wait 30 seconds for next update "
            print "======================================="
            time.sleep(30)

    def checkdata(self):
        Bkc_m = bkc_m.objects.all()
        Bkc_o = bkc_o.objects.all()
        for i in Bkc_m:
            id = i.id
            if i.eb =='':
                tasks_id = i.task
                if tasks_id:
                    tasks = Task.objects.get(id=tasks_id)
                    config_id = str(tasks.test_config)
                    if (json.load(open("./data/data/test_configs/" + config_id)).has_key('base_build')):
                        new_eb = "https://buildbot.sh.intel.com/absp/builders/bxtp_ivi_m-engineering/builds/"+json.load(open("./data/data/test_configs/" + config_id))['build'][0]
                        print "update eblink({0}).subject to {1}".format(str(i.eb), new_eb)
                        bkc_m.objects.filter(id=id).update(eb=new_eb)

        for i in Bkc_o:
            id = i.id
            if i.eb =='':
                tasks_id = i.task
                if tasks_id:
                    tasks = Task.objects.get(id=tasks_id)
                    config_id = str(tasks.test_config)
                    if (json.load(open("./data/data/test_configs/" + config_id)).has_key('base_build')):
                        new_eb = "https://buildbot.sh.intel.com/absp/builders/master-engineering/builds/"+json.load(open("./data/data/test_configs/" + config_id))['build'][0]
                        print "update eblink({0}).subject to {1}".format(str(i.eb), new_eb)
                        bkc_o.objects.filter(id=id).update(eb=new_eb)

        all = bxtp_m.objects.all()
        for i in all:
            id = i.id
            data = i.patch.split("/")[5]
            p = Patches(data)
            if len(p.content):
                owner = str(p.owner)
                subject = str(p.subject)
                status = str(p.status)
                track = str(p.track_id)
                if i.owner != owner:
                    print "update patch({0}).owner to {1}".format(str(i.id),owner)
                    bxtp_m.objects.filter(id=id).update(owner=owner)
                if i.subject != subject:
                    print "update patch({0}).subject to {1}".format(str(i.id),subject)
                    bxtp_m.objects.filter(id=id).update(subject=subject)
                if i.status != status:
                    print "update patch({0}).status to {1}".format(str(i.id),status)
                    bxtp_m.objects.filter(id=id).update(status=status)
                if i.track != track:
                    print "update patch({0}).track to {1}".format(str(i.id),track)
                    bxtp_m.objects.filter(id=id).update(track=track)
            else:
                print 'Patch_M(%d) error' % id

            alls = bxtp_o.objects.all()
            for i in alls:
                id = i.id
                data = i.patch.split("/")[5]
                p = Patches(data)
                if len(p.content):
                    owner = str(p.owner)
                    subject = str(p.subject)
                    status = str(p.status)
                    track = str(p.track_id)
                    if i.owner != owner:
                        print "update patch({0}).owner to {1}".format(str(i.id),owner)
                        bxtp_o.objects.filter(id=id).update(owner=owner)
                    if i.subject != subject:
                        print "update patch({0}).subject to {1}".format(str(i.id),subject)
                        bxtp_o.objects.filter(id=id).update(subject=subject)
                    if i.status != status:
                        print "update patch({0}).status to {1}".format(str(i.id),status)
                        bxtp_o.objects.filter(id=id).update(status=status)
                    if i.track != track:
                        print "update patch({0}).track to {1}".format(str(i.id),track)
                        bxtp_o.objects.filter(id=id).update(track=track)
                else:
                    print 'Patch_O(%d) error' % id