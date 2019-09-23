import urllib
import urllib2
import requests
import json
import re
from requests.auth import HTTPDigestAuth


class Patches:
    def __init__(self,id):
        self.usr = 'xichen1x'
        self.pwd = '5vfZx5Gm3T3eElytlmzmQDIeMgLMWMhqPTR5jw5NVQ'
        self.id=str(id)
        self.content = self.getjson()
        self.current_revision = self.content['current_revision'] if 'current_revision' in self.content else None

    def getjson(self):
        try:
            url = 'https://android.intel.com/a/changes/{0}/detail?o=CURRENT_COMMIT&o=CURRENT_REVISION'.format(self.id)
            response = requests.get(url, auth=HTTPDigestAuth(self.usr,self.pwd)).text
            d = json.loads(response[5:])
            return d
        except Exception ,e:
            print e.message
            print "Patch %s not exists" %self.id
            return {}

    @property
    def owner(self):
        if not 'owner' in self.content:
            self.content = self.getjson()
            return self.content['owner']['name']
        else: 
            return self.content['owner']['name']
    @property
    def subject(self):
        return self.content['subject']
    @property
    def status(self):
        d=[]
        status=''
        values=''
        values1=''
        values2=''
        values3=''
        values4=''
        if self.content['status'] == "NEW":
            try:
                f=self.content['labels']['Code-Review']['all'][0:]
                for i in f:
                    d.append(i['name']+':'+str(i['value']))
                for i in d:
                    if i.find('-2')!=-1:
                        values=i
                    if i.find('-1')!=-1:
                        values1=i
                    if i.find('2')!=-1:
                        values2=i.split(':')[0]+':'+str('+2')
                    if i.find('1')!=-1:
                        values3=i.split(':')[0]+':'+str('+1')
                    if i.find('0')!=-1:
                        values4='Needs Code-Review'
                if values:
                    status = values
                if (not values) and values1:
                    status = values1
                if (not values and not values1) and values2:
                    status = values2
                if (not values and not values1) and not values2 and values3:
                    status = values3
                if (not values and not values1) and (not values2 and not values3) and values4:
                    status = values4
                return status
            except Exception,e:
                status='Needs Code-Review'
                return status                     
        else:
            return self.content['status']
    @property
    def track_id(self):
        urls = re.findall(r'Tracked-On: (.+)',self.content['revisions'][self.current_revision]['commit']['message'])
        if len(urls):
            return urls[0]
        else:
            return None
