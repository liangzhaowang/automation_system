import requests
import json
import time
import logging


BUILDBOT_API = {
    'builder': {
        'url': 'https://buildbot.sh.intel.com/absp/json/builders/{}',
    },
    'build': {
        'url': 'https://buildbot.sh.intel.com/absp/json/builders/{}/builds/{}?as_text=1'
    }
}


logger = logging.getLogger('django.request')


class Buildbot:
    builder = None

    def __init__(self, builder, auth=()):
        """Initialize a Buildbot instance
        
        Arguments:
            builder {str} -- example: master-engineering
        
        Keyword Arguments:
            auth {turple} -- Intel generic account and password (default: {None})
            example: ('chenc5x', 'pwd123456')
        """
        self.auth = auth
        self.builder = builder

    def get_current_builds(self):
        """Get a list of building builds
        
        Returns:
            list -- build numbers
        """
        url = BUILDBOT_API['builder']['url'].format(self.builder)
        resp = requests.get(url, auth=self.auth, verify=False).text
        print url
        return [str(x) for x in json.loads(resp)['currentBuilds']]
    
    def check_build_target(self, build):
        url = BUILDBOT_API['build']['url'].format(self.builder, build)
        logger.debug('url %s' % url)
        resp = requests.get(url, auth=self.auth, verify=False).text
        properties = json.loads(resp)['properties']
        for property in properties:
            if property[0] == 'target_products_to_build':
                return property[1]

    def check_build_status(self, build):
        url = BUILDBOT_API['build']['url'].format(self.builder, build)
        resp = requests.get(url, auth=self.auth, verify=False).text
        data = json.loads(resp)
        if 'text' in data:
            result_text = ' '.join(data['text'])
            if 'build successful' in result_text:
                return {
                    'finished': True,
                    'msg': result_text,
                    'status': 'success'
                }
            elif 'failed' in result_text:
                return {
                    'finished': True,
                    'msg': result_text,
                    'status': 'success'
                }
            elif 'exception' in result_text:
                return {
                    'finished': True,
                    'msg': result_text,
                    'status': 'exception'
                }
            elif 'build cancelled' in result_text:
                return {
                    'finished': True,
                    'msg': result_text,
                    'status': 'cancel'
                }
            return {
                'finished': True,
                'msg': result_text,
                'status': 'unknown'
            }
        else:
            return {
                'finished': False
            }
