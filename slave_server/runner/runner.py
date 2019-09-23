import os
import re
import sys
import json
import logging
import getopt
import time
import yaml
import redis
import subprocess
import requests
import numpy as np
from operation_lib import utiliy
from conf import conf
from atf import TestLogger


ignore_keys = ['log']
rds = redis.Redis(host='localhost', port=6379)
logger = None


class SlaveInfo(object):
    def __init__(self):
        yaml_path = os.path.join(os.getcwd(), 'slave.yaml')
        self.data = yaml.load(open(yaml_path, 'r'))

    @property
    def server(self):
        return self.data['server']

    @property
    def config(self):
        return self.data['config']

    @property
    def target(self):
        return self.data['target']


class Runner(object):
    runner_path = os.path.dirname(os.path.abspath(__file__))
    slaveinfo = SlaveInfo()
    test_id_by_taskm = None
    flash = True
    project = None
    build = None
    upload = True
    url = ''
    cfg = None

    def __init__(self, args, slaveinfo=slaveinfo):
        self.args = args
        self.test_id = None
        self.config = None
        self.test_results_path = None
        self.task_id = None
        self.build_info = None
        self.project = None
        self.slave_project = None
        self.build = None
        self.build_type = None
        self.tag = None
        self.skip_flash = None
        self.test_type = []
        self.test_case = []
        self.test_tool = []
        self.test_loop = []
        self.scripts_path = None
        self.patches = []
        self.static_cmds = []
        self.dynamic_cmds = []
        self.server = slaveinfo.server
        self.configuration = slaveinfo.config
        self.build_target = slaveinfo.target
        self.reset()
        self.read_args()
        self.create_folders()
        self.parse_configs()

    @staticmethod
    def reset(reset_all=False):
        for k in rds.keys():
            if reset_all:
                pass
            elif k == 'pid':
                continue
            elif k == 'atf_task_id':
                continue
            if not k.startswith('est_'):
                rds.set(k, None)

    @staticmethod
    def test_finish():
        logging.debug('test finished')
        for k in rds.keys():
            if not k.startswith('est_'):
                rds.set(k, None)

    def create_folders(self):
        folder_lists = [
            'runner_logs',
            'test_results',
            'test_configs',
            'test_scripts',
            'test_src',
        ]

        for folder in folder_lists:
            if not os.path.exists(os.path.join(self.runner_path, folder)):
                os.makedirs(os.path.join(self.runner_path, folder))

        logger.debug('logs: {0}'.format(self.test_results_path))
        if not os.path.exists(self.test_results_path):
            os.makedirs(self.test_results_path)
        logger.debug('results: {0}'.format(self.test_results_path))

    def read_args(self):
        global logger
        try:
            opts, args = getopt.getopt(
                self.args, 't:c:i:', ['task=', 'config=', 'testid='])
            for name, value in opts:
                if name == '-t':
                    self.task_id = value
                    rds.set('atf_task_id', value)

                if name == '-c':
                    self.config = value

                if name == '-i':
                    self.test_id_by_taskm = value

                if self.test_id_by_taskm:
                    self.test_id = self.test_id_by_taskm
                else:
                    self.test_id = time.strftime('%Y%m%d_%H%M%S')

            rds.set('slave_root', self.runner_path)
            rds.set('atf_test_id', self.test_id)
            logger = TestLogger().get_logger("process")

            # set result and log path
            self.test_results_path = os.path.join(self.runner_path, 'test_results', self.test_id)

        except getopt.GetoptError as e:
            logger.error('get opt error', e.message)
            sys.exit(0)

        logger.debug('Test id: %s' % self.test_id)
        logger.debug('Task id: %s' % self.task_id)

        # update test id to server
        try:
            if self.test_id_by_taskm:
                logger.debug('skip update test id to server(%s)' % self.server)
            else:
                logger.debug('update test id to server(%s)' % self.server)

            response = requests.post('http://' + self.server + '/api/task/test_id/', data={"task_id": self.task_id, 'test_id': self.test_id}).content
            if response != 'success':
                logger.debug(response)
                sys.exit(0)
        except Exception as e:
            logger.error("can not connect to server", e.message)
            sys.exit(0)

    def parse_configs(self):
        case = json.loads(requests.get('/'.join(['http:/', self.server, 'api', 'config', self.config])).content)
        self.project = case['project_name']
        self.slave_project = case['slave_project']
        self.url = case['build_url']
        self.build = case['build']
        self.build_type = case['build_type']
        self.test_target = case['test_target']
        self.skip_flash = case['skip_flash']
        self.tag = case['tag']
        self.test_tag = case['test_tag']
        self.patches = re.findall(r'(https://.+)\s', case['patch'][0]) if len(case['patch']) else []
        logger.debug('project %s' % self.project)
        logger.debug('url %s' % self.url)
        logger.debug('patch length %s' % len(self.patches))
        logger.debug('tag %s' % self.tag)
        logger.debug('test_tag %s' % self.test_tag)
        logger.debug('build %s' % self.build)
        logger.debug('target %s' % self.build_target)
        logger.debug('config %s' % self.configuration)

        # test type
        if filter(lambda x: 'config_params' in x, case.keys()):
            self.test_type.append('optimize')
        if len(self.patches):
            self.test_type.append('patch')
        if len(self.test_type) == 0:
            self.test_type.append('general')
        elif len(self.test_type) > 1:
            self.test_type = 'error'
            logger.error('test type is error')
            sys.exit(0)
        self.test_type = self.test_type[0]
        logger.debug('test type %s' % self.test_type)
        self.scripts_path = os.path.join(self.runner_path, 'test_scripts', self.slave_project)

        # test cases
        self.test_case.extend(case['case_name'])
        self.test_loop.extend(case['case_loop'])
        self.test_tool.extend(case['case_tool'])

        for key in case:
            if 'case_' in key and key not in ('case_loop', 'case_name', 'case_tool'):
                if 'test_' + key.split('_')[1] not in self.__dict__:
                    self.__dict__['test_' + key.split('_')[1]] = case[key]
                else:
                    self.__dict__['test_' + key.split('_')[1]].extend(case[key])
        logger.debug('test cases length %d' % len(self.test_case))

        # preload commands
        if 'config_cmds' in case:
            for i in range(len(case['config_cmds'])):
                if not 'config_params[{0}][]'.format(str(i)) in case:
                    self.static_cmds.append(case['config_cmds'][i])
            logger.debug('preload commands length %d' % len(self.static_cmds))

    def execute_preload_commands(self):
        if self.test_type == 'general':
            if len(self.static_cmds):
                for cmd in self.static_cmds:
                    logger.debug('Execute: "%s"' % cmd)
                    subprocess.Popen(cmd, shell=True).wait()
                    time.sleep(2)
            else:
                logger.debug('No commands found, skip this step')

    def skip_wizard(self, gap=50):
        time.sleep(5)
        if self.project == 'bxtp_ivi_m':
            logger.debug('skip setupwizard')
            adb_cmds = "adb shell input tap "
            line = os.popen("adb shell dumpsys window displays |head -n 3").read()
            p = re.compile(r"cur=(?P<dspx>\d+)[xX]+(?P<dspy>\d+)")
            sobj = p.search(line, re.I)
            if sobj:
                dspx = int(sobj.group('dspx'))
                dspy = int(sobj.group('dspy'))
                os.system(adb_cmds + str(gap) + " " + str(gap))
                time.sleep(0.2)
                os.system(adb_cmds + str(dspx - gap) + " " + str(gap))
                time.sleep(0.2)
                os.system(adb_cmds + str(dspx - gap) + " " + str(dspy - gap))
                time.sleep(0.2)
                os.system(adb_cmds + str(gap) + " " + str(dspy - gap))
                time.sleep(5)
                os.system('adb shell input keyevent 4')
            else:
                logger.error('skip setupwizard is failed')
        elif self.project == 'bxtp_ivi_o':
            pass
        time.sleep(5)

    def image_dl_flash(self, retry=1):
        print "========================="
        print self.test_target
        print "========================="
        if retry < 0:
            return False
        start = time.time()
        if self.skip_flash:
            logger.debug('skip flash')
            return True
        elif "_acrn" in self.test_target:
            from flash.Acrn_flash import AcrnFlash
            AcrnFlash(self.build, self.build_type, self.url, self.test_target).flash_images()
            try:
                rds.lpush("est_" + self.slave_project + "_acrnflash", int(float(time.time()-start)))
            except Exception as e:
                print "rds error: " + repr(e)
            finally:
                return True
        elif "cel_" in self.test_target or "apl_" in self.test_target:
            print "----------------"
            print self.test_target
            print "----------------"
            from flash.flash_aia_v3 import Aia_flash
            Aia_flash(self.build, self.build_type, self.url, self.test_target).flash_aias()
            try:
                rds.lpush("est_" + self.slave_project + "_aiaflash", int(float(time.time()-start)))
            except Exception as e:
                print "rds error: " + repr(e)
            finally:
                return True
        else:
            args = [
                '-d', self.slave_project,
                '-b', self.build,
                '-u', self.url,
                '-i', self.test_target,
                '-c', self.configuration
            ]
            cmd = "python runner/flash/auto_flash_download.py %s" % (' '.join(args))
            p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, universal_newlines=True)
            p.wait()
            p_err = p.stderr.readlines()
            if len(p_err) > 0:
                logger.error("---------------------error------------------------")
                logger.error("  \n".join(p_err))
                logger.error("--------------------------------------------------")
            if len(p_err) > 0 and "image_flash_failed" in p_err[-1]:
                retry -= 1
                self.image_dl_flash(retry)
            else:
                try:
                    rds.lpush("est_" + self.slave_project + "_flash", int(float(time.time() - start)))
                except Exception as e:
                    logger.error("rds error: " + repr(e))
                finally:
                    return True

    def execute_test_scripts(self):
        case = json.loads(requests.get('/'.join(['http:/', self.server, 'api', 'config', self.config])).content)
        try:
            progress = 0
            loop_sum = sum([int(l) for l in self.test_loop])
            case_info = yaml.load(open(os.path.join(self.scripts_path, 'info.yaml')))
            cooldown_time = conf.case.cooldown_time
            for case_name in self.test_case:
                rds.rpush('est_cases', case_name)
            for case_loop in self.test_loop:
                rds.rpush('est_case_loops', case_loop)
            for script in self.test_case:
                logger.debug('=' * 70)
                rds.set('case_name', script)
                rds.set('atf_case_index', str(self.test_case.index(script)))
                script_infos = filter(lambda x: x['name'] == script, case_info['scripts'])
                tool_infos = []
                if len(script_infos) == 0:
                    logger.error('case: {0} is not defined in info.yaml'.format(script))
                    continue

                if 'case_tool' in case:
                    for tool in case['case_tool'][self.test_case.index(script)]:
                        case_tools = filter(lambda x: x['name'] == tool, case_info['tools'])
                        if len(case_tools) > 0:
                            tool_infos.append(case_tools[0])
                        else:
                            logger.error('tool: {0} is not defined in info.yaml'.format(tool))

                script_info = script_infos[0]
                script_path = os.path.join('runner', 'test_scripts', self.slave_project, script_info['script'])
                total_loop = int(self.test_loop[self.test_case.index(script)])
                time.sleep(cooldown_time)
                for loop in range(total_loop):
                    start = time.time()
                    rds.set('atf_loop_index', str(loop))
                    rds.set('atf_progress', str(round(float(progress * 100) / loop_sum, 1)))
                    rds.set('atf_current', '{0} ({1}/{2})'.format(script, loop + 1, total_loop))
                    cmd = ' '.join(['python', script_path, script_info["arg"]])
                    logger.debug(cmd)
                    subprocess_list = []

                    for tool_info in tool_infos:
                        tool_cmd = ' '.join(['python', tool_info['script'], tool_info['arg'], "-n", script_info["app_package"], "-d", self.test_id+"/"+script])
                        p2 = subprocess.Popen(tool_cmd, shell=True, close_fds=True, preexec_fn=os.setsid)
                        subprocess_list.append(p2)

                    p = subprocess.Popen(cmd, shell=True, universal_newlines=True)
                    logger.debug('({0}/{1}) {2} pid:{3}'.format(loop + 1, total_loop, script, p.pid))
                    p.wait()
                    time.sleep(2)
                    for p2 in subprocess_list:
                        os.kill(-p2.pid, 9)
                    time.sleep(2)
                    for tool_info in tool_infos:
                        if tool_info['name'] == 'Cpu':
                            out_dir = os.path.join("runner", "test_results", self.test_id, script, "tool", "cpu")
                            path = os.path.join(os.getcwd() +'/'+ out_dir)
                            ch_path = os.chdir(path)
                            files = os.listdir(path)
                            a = []
                            for fi in files:
                                fi = fi.encode('gbk')
                                c_fi = 'csv' in fi
                                p_fi = 'png' in fi
                                if c_fi or p_fi:
                                    a.append(fi.split('.')[0])
                                length = np.unique(a)
                                for i in length.tolist():
                                    os.system('./plot.sh '+ i+ '*.csv')
                            time.sleep(2)
                            os.chdir(self.runner_path)
                            os.chdir(os.path.abspath(os.path.dirname(self.runner_path)))
                    time.sleep(2)
                    self.upload_tool_log(script, loop)
                    logger.debug('-' * 70)
                    progress += 1
                    time.sleep(1)
                    utiliy.hard_reboot()
                    time.sleep(cooldown_time)
                    if p.returncode == 0:
                        rds.lpush("est_" + self.slave_project + "_" + script, time.time() - start)
        except Exception as e:
            print 'error', e, sys.exc_info()[2].tb_lineno

    @staticmethod
    def broadcast(server, task_id, test_id, msg=None):
        try:
            print 'task_id, test_id, msg', task_id, test_id, msg
            requests.post('http://' + server + '/api/broadcast/', data={"task_id": task_id, 'test_id': test_id, 'msg': msg})
        except requests.ConnectionError as e:
            print e

    def save_config(self):
        d = {}
        for k in self.__dict__:
            if k not in ignore_keys:
                d[k] = self.__dict__[k]
        rds.set('atf_config', self.config)
        with open(os.path.join(self.runner_path, 'test_configs', self.config), 'w') as f:
            f.write(json.dumps(d, indent=4))
            f.close()
        time.sleep(2)

    def upload_tool_log(self, casename, loop_index):
        tool_dir = os.path.join('runner', 'test_results', self.test_id, casename, 'tool')
        if os.path.exists(tool_dir):
            print "--------start upload tool log----------"
            utiliy.zip_file(tool_dir, tool_dir + ".zip")
            data = {
                "project": self.project,
                "test_id": self.test_id,
                "build": self.build,
                "config_name": self.config,
                "case_name": casename,
                "file_name": "tool.zip",
                "loop": loop_index
            }
            files = {'document': open(tool_dir + ".zip", 'rb')}
            requests.post('http://' + self.server + '/api/test_attachment', data=data, files=files)
            os.remove(tool_dir + ".zip")


if __name__ == '__main__':
    runner = Runner(sys.argv[1:])
    runner.save_config()
    if runner.image_dl_flash():
        runner.skip_wizard()
        runner.execute_preload_commands()
        runner.execute_test_scripts()
        Runner.broadcast(server=runner.server, task_id=runner.task_id, test_id=runner.test_id, msg='success')
        Runner.reset(reset_all=True)
        sys.stdout.write('test finished\n')
        logger.debug('test finished\n')
    else:
        Runner.broadcast(server=runner.server, task_id=runner.task_id, test_id=runner.test_id, msg='failed')
        requests.get('http://' + runner.server + '/api/test_failed/' + runner.task_id + '/ff')
        Runner.reset(reset_all=True)
        sys.stdout.write('flash image failed, please check it! \n')
        logger.debug('flash image failed, please check it! \n')
    sys.exit(0)
