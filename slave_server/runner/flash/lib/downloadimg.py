#!/usr/bin/env python
import sys
import json
import yaml
import os
import requests
from html_parse import output_download_url
requests.packages.urllib3.disable_warnings()


class downloadimage:
    def __init__(self, device_type, top_level_url, build_number):
        self.device_type = device_type
        self.top_level_url = top_level_url
        self.build_number = build_number
        slave_conf = yaml.load(open('slave.yaml', 'r'))
        try:
            self.headers = json.loads(requests.get('http://{server}/api/auth_header'.format(server=slave_conf['server'])).content)
        except Exception, e:
            print "get header error: ", e.message

    def checkNeedUnzip(self, imageName):
        if os.path.exists(imageName.replace(".zip", "") + "/flash.json"):
            confFile = file(imageName.replace(".zip", "") + "/flash.json")
            conf = json.load(confFile)
            confFile.close()
            print conf['flash']['version']
            if not conf['flash']['version'] == '':
                return False
        return True

    def unzipImage(self, imageName):
        if self.checkNeedUnzip(imageName):
            import zipfile
            if not os.path.exists(imageName):
                print "Image File : %s not exists." % (imageName)
                return
            print 'unzip %s ......'%(imageName)
            if not os.path.exists(imageName.replace(".zip", "")):
                os.mkdir(imageName.replace(".zip", ""))
            for flsFile in os.listdir(imageName.replace(".zip", "")):
                if os.path.isfile(flsFile):
                    try:
                        os.remove(flsFile)
                    except:
                        pass
            zfile = zipfile.ZipFile(imageName)
            for filename in zfile.namelist():
                zfile.extract(filename, imageName.replace(".zip", ""))

    def PrintMessage(msg):
        print >>sys.stdout, '\r',
        print >>sys.stdout, msg,

    def downloadbyurl(self, image_url, imageName, CallBackFunction=PrintMessage):
        print "downloading image..."
        try:
            response = requests.get(image_url, proxies={}, stream=True, verify=False, headers=self.headers)
            out_file = open(imageName, 'wb')
            size = 0
            print('Download image file to %s \r' % imageName)
            for chunk in response.iter_content(chunk_size=512):
                if chunk:
                    out_file.write(chunk)
                    size += len(chunk)
                    CallBackFunction('{0} MB'.format(size / 1024 / 1024))
            print "\n"
            return size
        except Exception as e:
            print 'download image error: ', str(e)


def down_load_image(device_type, build_number, top_level_url, cfg, build_info, force_flag=False, retry=1):
    if retry < 0:
        return ''
    downloadbyurl_flag = True
    dimg = downloadimage(device_type, top_level_url, build_number)
    if not os.path.exists('runner/flash/image'):
        os.mkdir('runner/flash/image/')
    image_url1 = output_download_url(dimg.headers, top_level_url, build_info, build_number)
    if image_url1:
        imageName1 = 'runner/flash/image/' + image_url1.split("/")[-1]
        imagePath = os.path.abspath(imageName1.replace(".zip", ""))
        if force_flag:
            if os.path.exists(imagePath):
                os.system('rm -rf '+imagePath)
            if os.path.exists(imageName1):
                os.remove(imageName1)

        if os.path.exists(imagePath+'/flash.json'):
            confFile = file(imagePath + "/flash.json")
            conf = json.load(confFile)
            confFile.close()
            print conf['flash']['version']
            if conf['flash']['version'] != '':
                downloadbyurl_flag = False

        if downloadbyurl_flag and (not os.path.exists(imageName1)):
            dimg.downloadbyurl(image_url1, imageName1)
        else:
            print "===================<<<WARNING>>>======================="
            print "%s is exist!!!" % imageName1
        try:
            dimg.unzipImage(imageName1)
        except Exception as e:
            print("unzip image error: " + repr(e))
            retry -= 1
            if os.path.exists(imageName1):
                os.remove(imageName1)
            down_load_image(device_type, build_number, top_level_url, cfg, build_info, True, retry)
        if os.path.exists(imageName1):
            os.remove(imageName1)
        print 'imagePath == ', imagePath
        return imagePath
    else:
        print 'image not found!'
        return ''
