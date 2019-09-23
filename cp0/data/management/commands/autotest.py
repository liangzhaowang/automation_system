import time
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

due_build = []
while True:
    hour = int(time.strftime("%H", time.localtime(time.time())))
    if 8 < hour < 20:
        for i in range(20 - hour):
            print "sleep an hour..."
            time.sleep(3600)
        continue
    try:
        url = "https://mcg-depot.intel.com/artifactory/cactus-absp-jf/pmr0_bxtp_ivi_stable-latest/"
        header = {'Authorization': 'Basic {}'.format("c2hhbnN4OlNoMTIzNDU2IQ==")}
        res = requests.get(url, verify=False, headers=header)
        str_data = time.strftime('%d-%b-%Y', time.localtime(time.time()))
        all_builds = [int(item) for item in re.findall('>(.+)/</a>.+', res.content)]
        cur_day_builds = re.findall('>(.+)/</a>.+ ' + str_data + '\s(0[0-6]|1[5-9]|2[0-4]):', res.content)
        avl_builds = [build for build in cur_day_builds if (hour-int(build[1])) < 8]
        start_build = int(avl_builds[0][0]) if len(avl_builds) > 0 else ''
        test_builds = [str(item) for item in all_builds if (start_build != '' and item >= start_build)]
        print test_builds
        for build in test_builds:
            if build in due_build:
                continue
            due_build.append(build)
            print "add task for build: " + build
            res_1 = requests.post("http://cubep.sh.intel.com:8000/api/autotest/", data={'build': build, 'template_name': 'daily_8G01'})
            print '8G01: ', res_1.content
            time.sleep(120)

            res_2 = requests.post("http://cubep.sh.intel.com:8000/api/autotest/", data={'build': build, 'template_name': 'daily_2G01'})
            print '2G01: ', res_2.content
            time.sleep(60)
    except Exception as e:
        print repr(e)

    time.sleep(600)
