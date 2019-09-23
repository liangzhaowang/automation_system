# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from data.models import Project, BuildPath
from redis import Redis
import requests
import json
import re


MERGE_REQUEST_SITES = {
    'jf': 'https://jfstor001.jf.intel.com/artifactory/api/storage/cactus-absp-jf/{}-mergerequest?list&listFolders=1&deep=1',
    'sh': 'https://mcg-depot.intel.com/artifactory/api/storage/cactus-absp-sh/{}-mergerequest?list&listFolders=1&deep=1'
}


def save_to_cache(builder_name, site, images, targets):
    rds = Redis(host='localhost', port=6379)
    rds.delete('mq_images_{}_{}'.format(site, builder_name), 'mq_targets_{}_{}'.format(site, builder_name))
    print 'push', site, builder_name, len(images)
    if images:
        rds.lpush('mq_images_{}_{}'.format(site, builder_name), *images)
    if targets:
        rds.lpush('mq_targets_{}_{}'.format(site, builder_name), *targets)


def check_merge_request_build(builder_name):
    for site in MERGE_REQUEST_SITES:
        url = MERGE_REQUEST_SITES[site].format(builder_name)
        print 'fetching', url
        resp = requests.get(url, verify=False, auth=('chenc5x', '#EDC4rfv')).text
        resp_dict = json.loads(resp)
        if 'errors' in resp_dict:
            continue
        files = resp_dict['files']
        targets = []
        images = re.findall(r'cactus.+/(.+)\?', url)[0]
        images = []
        for file_info in files:
            file_list = re.findall(r'/(\d+)/(\w+)/userdebug/', file_info['uri'])
            if len(file_list):
                if file_list[0][1] not in targets:
                    targets.append(file_list[0][1])
                images.append(file_info['uri'])
        save_to_cache(builder_name, site, images, targets)
    return True


def get_builds(url, builder_name):
    if 'artifactory/cactus' in url:
        changed_url = url.replace('mcg-depot.intel.com', '10.223.98.82')
        api_url = re.sub('artifactory/cactus', 'artifactory/api/storage/cactus', changed_url) + '?list&listFolders=1&deep=1'
        builder_name = builder_name
        resp = requests.get(api_url, verify=False, auth=('chenc5x', '9ol.0p;/I')).text
        resp_dict = json.loads(resp)
        if 'created' in resp_dict:
            files = resp_dict['files']
            targets = []
            images = []
            for file_info in files:
                file_list = re.findall(r'/(.+)/(.+)/userdebug/.+\.zip', file_info['uri'])
                if len(file_list):
                    if file_list[0][1] not in targets:
                        targets.append(file_list[0][1])
                    if '/'.join(file_list[0]) not in images:
                        print file_list[0]
                        images.append('/'.join(file_list[0]))
            rds = Redis(host='localhost', port=6379)
            redis_image_key = url
            rds.delete(redis_image_key)
            print 'push', url, len(images), 'builds'
            if images:
                rds.lpush(redis_image_key, *images)


@shared_task
def cache_all_builds():
    all_build_path = BuildPath.objects.all()
    distinct = []
    for build_path in all_build_path:
        if build_path.url not in distinct:
            distinct.append(build_path.url)
            # todo
            get_builds(build_path.url, build_path.project.builder_name)
        


@shared_task
def fetch_build_lists():
    all_builders = Project.objects.values_list('builder_name', flat=True)
    builders = list(set(all_builders))
    for builder in builders:
        # merge_requests
        check_merge_request_build(builder)
    return ', '.join(builders)
