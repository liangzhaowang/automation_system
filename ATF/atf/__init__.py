import json
import os
import sys
import urllib
import urllib2
import base64
import yaml
import redis
import requests
import argparse
import logging
import subprocess
import time
import serial
import re

logging.basicConfig(format='%(asctime)s [%(funcName)s] [%(levelname)s] %(message)s', level=logging.DEBUG)
rds = redis.Redis(host='localhost', port=6379)
__version__ = '0.24'
DESCPRIPTION = 'Dev tool for slave'


class TestConfig(object):
    def __init__(self):
        self.project = None
        self.slave_project = None
        self.build = None
        self.tag = None

class TestLogger(object):
    logger = {}
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TestLogger, cls).__new__(cls)
        return cls.instance

    def get_logger(self, log_type, logfile=None):
        if rds.get('atf_test_id') == "None" or rds.get('slave_root') == "None":
            return self.logger

        if not logfile:
            logfile = os.path.join(rds.get('slave_root'), 'test_results', rds.get('atf_test_id'), 'process.log')

        if log_type in self.logger and self.logger[log_type]:
            return self.logger[log_type]
        else:
            self.logger[log_type] = logging.getLogger(log_type)
            if not  os.path.exists(os.path.dirname(logfile)):
                os.makedirs(os.path.dirname(logfile))

            fh = logging.FileHandler(logfile, mode='a')
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")
            fh.setFormatter(formatter)
            self.logger[log_type].addHandler(fh)
            return self.logger[log_type]

class TestResult(object):
    def __init__(self, casename=""):
        self.test_result = None
        self.config_name = rds.get('atf_config')
        self.case_index = int(rds.get('atf_case_index')) if rds.get('atf_case_index').isdigit() else 0
        self.loop_index = int(rds.get('atf_loop_index')) if rds.get('atf_loop_index').isdigit() else 0
        self.task_id = int(rds.get('atf_task_id')) if rds.get('atf_task_id').isdigit() else 0
        self.test_id = rds.get('atf_test_id')
        self.case = rds.get('case_name')
        self.config = self.get_config()
        self.result_dir = os.path.join(rds.get('slave_root'), 'test_results', self.test_id, self.case)
        self.cases_info = yaml.load(open(os.path.join('runner', 'test_scripts', self.config.slave_project, 'info.yaml'), 'r'))
        self.case_info = None
        for case_info in self.cases_info["scripts"]:
            for k, v in case_info.items():
                if v == self.case:
                    self.case_info = case_info
                    break
            if self.case_info:
                break
        self.case_name = self.case_info['name'] if self.case_info else ""
        self.unit = self.case_info['unit'] if self.case_info else ""
        self.result_file_name =  '_'.join([self.case_info['name'], str(self.loop_index)]) if self.case_info else ""
        self.attachments = []
        self.log = TestLogger().get_logger('process')
        self.result_dict = {'test_id': self.test_id,
                            'sub_score_names': [],
                            'sub_score_scores': [],
                            'sub_score_columns': [],
                            'unit': self.unit,
                            'loop': self.loop_index,
                            'project': self.config.project,
                            'build': self.config.build,
                            'tag': self.config.tag,
                            'task_id': self.task_id,
                            'test_tag': self.config.test_tag
                            }

    def get_config(self):
        cfg = TestConfig()
        config_dict = json.load(open(os.path.join('runner', 'test_configs', self.config_name)))
        for key in config_dict:
            if 'test_' in key:
                if type(config_dict[key]) == list:
                    cfg.__dict__[key.split('_')[1]] = config_dict[key][self.case_index]
        cfg.project = config_dict['project']
        cfg.slave_project = config_dict['slave_project']
        cfg.build = config_dict['build']
        cfg.tag = config_dict['tag']
        cfg.test_tag = config_dict['test_tag']
        return cfg

    def result(self, result):
        self.test_result = str(result)
        self.result_dict['result'] = self.test_result

    def sub_score(self, name, score, add_to_column=False):
        self.result_dict['sub_score_names'].append(name)
        self.result_dict['sub_score_scores'].append(score)
        self.result_dict['sub_score_columns'].append(add_to_column)

    def add_attachment(self, file_abs_path, post_to=None):
        self.attachments.append(file_abs_path)

    def save(self):
        if self.case_info:
            if not os.path.exists(os.path.join('runner', 'test_results', self.test_id, self.case)):
                os.makedirs(os.path.join('runner', 'test_results', self.test_id, self.case))

        server = yaml.load(open('slave.yaml', 'r'))['server']

        # upload test result
        url = '/'.join(['http:/', server, 'api', 'test_result'])
        data = self.result_dict
        data['result_file_name'] = self.result_file_name
        data['case_name'] = self.case_name
        data['tag'] = self.config.tag
        data['config_name'] = self.config_name
        req = urllib2.Request(url)
        post_data = urllib.urlencode({'data': json.dumps(data)})
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, post_data)

        # upload test attachment
        url2 = '/'.join(['http:/', server, 'api', 'test_attachment'])
        if os.path.exists(os.path.join('runner', 'test_results', self.test_id, 'process.log')):
            self.attachments.append(os.path.join('runner', 'test_results', self.test_id, 'process.log'))
            self.log.info("process log at: {p_log}".format(p_log=os.path.join('runner', 'test_results', self.test_id, 'process.log')))

        for attachment in self.attachments:
            if not os.path.exists(attachment):
                self.log.info("file: {f_name} not exists!".format(f_name=attachment))
                continue
            data['file_name'] = attachment.split('/')[-1]
            files = {'document': open(attachment, 'rb')}
            requests.post(url2, data=data, files=files, )


class Device(object):
    def __init__(self):
        self.serial_no = self.connect(show_log=False)
        self.relay = Relay('Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller')

    @staticmethod
    def connect(timeout=60, show_log=True):
        logging.debug('waiting for device')
        t_out = timeout
        while t_out:
            p = subprocess.Popen(['adb', 'get-serialno'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out = p.communicate()
            if out[1]:
                if show_log:
                    logging.error(out[1].strip())
                    t_out += -1
                time.sleep(1)
            else:
                logging.debug('device {} connected via adb'.format(out[0].strip()))
                return out[0].strip()
        logging.critical('can not connect device in {} secs'.format(timeout))
        sys.exit(0)

    def adb(self, cmd):
        if self.serial_no:
            cmds = ['adb']
            cmds.extend(cmd.split())
            p = subprocess.Popen(cmds, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            p.wait()
            out = p.communicate()
            if out[0]:
                return out[0].rstrip()
            else:
                return out[1]

    def hard_reboot(self, wait_boot_up=True, timeout=60):
        """
        Reboot device by relay.
        :return:
        """
        self.relay.on_off(3)
        time.sleep(1)
        self.connect(show_log=False, timeout=timeout)
        if wait_boot_up:
            logging.debug('waiting for boot complete')
            while timeout:
                if self.status:
                    logging.debug('reboot complete')
                    return True
                timeout += -1
                time.sleep(1)

    def soft_reboot(self, wait_boot_up=True, timeout=60):
        """
        Reboot device by adb.
        :param wait_boot_up, bool
        :param timeout
        :return:
        """
        logging.info('wait for boot complete: {}'.format(wait_boot_up))
        self.adb('reboot')
        time.sleep(1)
        self.connect(show_log=False, timeout=timeout)
        if wait_boot_up:
            logging.debug('waiting for boot complete')
            while timeout:
                if self.status:
                    logging.debug('reboot complete')
                    return True
                timeout += -1
                time.sleep(1)

    @property
    def status(self):
        complete = self.property('sys.boot_completed')
        # print('complete[{}]'.format(complete))
        if complete == '':
            # key 'sys.boot_completed' not exist
            return False
        elif complete == '1':
            return True
        elif complete == '0':
            return False
        else:
            return False

    def push(self, src_path, dst_path, media_scan=False):
        pass

    def pull(self, dst_path, src_path):
        pass

    def property(self, key=None, value=None):
        if value:
            self.adb('shell setprop {0} {1}'.format(key, value))
        elif key:
            return self.adb('shell getprop {}'.format(key))
        else:
            return self.adb('shell getprop')

    def suspend(self):
        self.relay.on_off(1)

    def install(self):
        pass

    def list_packages(self):
        ret = self.adb('shell pm list package')
        return map(lambda x: x[8:], ret.split('\n'))

    def activity(self):
        ret = self.adb('shell dumpsys window windows | grep -E \'mFocusedApp\'')
        return re.search(r'{\w+ \w+ (.+) \w+}', ret).group(1)

    def start_activity(self, activity):
        self.adb('shell am start -n {}'.format(activity))


class Slave(object):
    def __init__(self):
        pass

    @staticmethod
    def get_resource(name):
        path = os.path.join(rds.get('slave_root'), 'test_src', name)
        if os.path.exists(path):
            if path.endswith('.apk'):
                return APK(path)
            return Resource(path)
        else:
            logging.error('{} not exist'.format(name))
            return None


class Resource(object):
    def __init__(self, path):
        self.path = path
        if os.path.isfile(path):
            self.dir, self.file_name = os.path.split(path)
            self.ext = self.file_name.split('.')[-1]


class APK(Resource):
    def __init__(self, path):
        Resource.__init__(self, path)
        badge_info = self.badge()
        self.package_name = re.search(r'package: name=\'(.*?)\'', badge_info).group(1)
        self.package_version = re.search(r'versionName=\'(.*?)\'', badge_info).group(1)
        self.package_activity = re.search(r'launchable-activity: name=\'(.*?)\'', badge_info).group(1)
        self.package_launch_activity = self.package_name + '/' + self.package_activity

    def badge(self):
        cmd = ['aapt', 'dump', 'badging', self.path]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        badge_info = p.communicate()[0]
        return badge_info


class Relay(object):
    ON = 100
    OFF = 110

    def __init__(self, name):
        self.name = name
        self.comport = '/dev/' + self.usb_dev()

    def on(self, port_id):
        ser = serial.Serial(self.comport, 19200, 8, serial.PARITY_NONE, serial.STOPBITS_TWO)
        cmd_str = chr(self.ON + port_id)
        ser.write(cmd_str)
        ser.close()

    def off(self, port_id):
        ser = serial.Serial(self.comport, 19200, 8, serial.PARITY_NONE, serial.STOPBITS_TWO)
        cmd_str = chr(self.OFF + port_id)
        ser.write(cmd_str)
        ser.close()

    def on_off(self, port_id, timeout=0.5):
        ser = serial.Serial(self.comport, 19200, 8, serial.PARITY_NONE, serial.STOPBITS_TWO)
        ser.write(chr(self.ON+port_id))
        time.sleep(timeout)
        ser.write(chr(self.OFF + port_id))
        ser.close()

    def usb_dev(self):
        for root, dirs, files in os.walk('/sys/bus/usb/devices', topdown=False):
            for name in dirs:
                if name.startswith('usb'):
                    usb = os.path.realpath(os.path.join(root, name))
                    for root2, dirs2, files2 in os.walk(usb, topdown=False):
                        for file2 in files2:
                            if file2 == 'dev' and 'ttyUSB' in root2:
                                p = subprocess.Popen(
                                    ['udevadm', 'info', '-q', 'property', '-p', root2],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                )
                                if self.name in re.search(r'ID_SERIAL=(.+)\n', p.communicate()[0]).group(1):
                                    return os.path.split(root2)[-1]


def main():
    if not os.path.exists(rds.get('slave_root')):
        logging.critical('slave server is not exist')
        sys.exit(0)

    parser = argparse.ArgumentParser(description='{0} {1}'.format(DESCPRIPTION, __version__), prog='atf')
    parser.add_argument('-f', '--find', nargs='*', help='find sources in test_src')
    parser.add_argument('-a', '--activity', action='store_true', help='get current activity')
    parser.add_argument('-s', '--sync', action='store_true', help='sync resources')

    args = parser.parse_args()

    if args.activity:
        print(Device().activity())
    elif args.find:
        os.path.walk(os.path.join(rds.get('slave_root'), 'test_src'), visit, args.find[0])
    elif args.sync:
        pass
    else:
        parser.print_help()


def visit(arg, dir_name, names):
    for path in names:
        dst_path = os.path.join(dir_name, path)
        if arg in dst_path:
            print('slave.get_source(\'{}\')'.format(dst_path.split(os.path.join(rds.get('slave_root'), 'test_src'))[1]))


if __name__ == '__main__':
    main()
