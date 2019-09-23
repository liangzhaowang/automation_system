import os
import signal
import yaml
import json
import traceback
import redis
from subprocess import Popen
from atf import Device, TestResult, TestLogger
from django.http import JsonResponse, HttpResponse
import sys
reload(sys)
sys.setdefaultencoding('utf8')

rds = redis.Redis(host='localhost', port=6379)
RUNNER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'runner'))


def hello(request):
    return HttpResponse('My lord')


def progress(request):
    return JsonResponse({'progress': str(rds.get('atf_progress'))})


def update_slave(request):
    result = False
    os.system('cd ~/back/cp0 ; git pull origin master')
    f = os.popen('cd ~/back/cp0 ; git pull origin master').readlines()
    if 'Already up-to-date' in f[0]:
        result = True
    print result
    return JsonResponse({'result': result})


def test_cases(request, project_name=None):
    if project_name in os.listdir(os.path.join(RUNNER_PATH, 'test_scripts')):
        info_path = os.path.join(RUNNER_PATH, 'test_scripts', project_name, 'info.yaml')
        if os.path.exists(info_path):
            info_data = yaml.load(open(info_path, 'r'))
            return JsonResponse(info_data)
        else:
            return JsonResponse({'error': 'Cannot find file info.yaml'}, )
    elif not project_name:
        return HttpResponse('Missing project name in URL:\r http://')
    else:
        return JsonResponse({'error': 'Slave has no tests for {0}'.format(project_name)})


def test(request):
    try:
        task_id = request.POST['task_id']
        test_config = request.POST['test_config']
        cmd = ' '.join(['python', 'runner/runner.py', '-c', test_config, '-t', task_id])
        if 'test_id' in request.POST:
            cmd += ' -i {0}'.format(request.POST['test_id'])
        print "test cmd:" + cmd
        sp = Popen(cmd, shell=True, close_fds=True, preexec_fn=os.setsid)
        print('main pid %d' % sp.pid)
        rds.set('pid', str(sp.pid))
        return HttpResponse('Aye Sir')
    except Exception as e:
        print 'error', e
        print traceback.format_exc()
        return HttpResponse('error')


def status(request):
    d = {}
    try:
        for k in rds.keys():
            if not k.startswith('est_'):
                d[k] = rds.get(k)
    except Exception as e:
        print 'None', e
    return JsonResponse(d)


def slave_stat(request):
    stat = {'queue_tasks': [], 'testing_tasks': [], 'total_est': 0}
    queue_tasks = json.loads(request.POST['queue_tasks'])
    for task in queue_tasks:
        result = {'build': task['build'], 'owner': task['owner'], 'status': 'queue', 'est': 0}

        if task['skip_flash'] == str(False):
            if '_acrn' in task['target']:
                tmp_est_flash = rds.lrange('est_' + task['slave_project'] + '_acrnflash', 0, 9)
            else:
                tmp_est_flash = rds.lrange('est_' + task['slave_project'] + '_flash', 0, 9)
            if len(tmp_est_flash) > 0:
                result['est'] += sum([int(float(x)) for x in tmp_est_flash]) / len(tmp_est_flash)
            else:
                if '_acrn' in task['target']:
                    result['est'] += 900
                else:
                    result['est'] += 1500
        for i, case in enumerate(task['cases']):
            est_list = rds.lrange('est_' + task['slave_project'] + '_' + case, 0, 9)
            if len(est_list) > 0:
                result['est'] += (sum([int(float(x)) for x in est_list]) / len(est_list)) * (int(task['case_loops'][i]))
            else:
                result['est'] += 180 * (int(task['case_loops'][i]))
        stat['queue_tasks'].append(result)
        stat['total_est'] += result['est']

    if rds.get('atf_task_id') != 'None' and os.path.exists(os.path.join(RUNNER_PATH, 'test_configs', rds.get('atf_config'))):
        conf = json.load(open(os.path.join(RUNNER_PATH, 'test_configs', rds.get('atf_config'))))
        result = {'build': conf['build'], 'owner': '', 'status': 'testing', 'est': 0}
        if rds.get('atf_current') == 'None' and not conf['skip_flash']:
            if '_acrn' in conf['test_target']:
                tmp_est_flash = rds.lrange('est_' + conf['slave_project'] + '_acrnflash', 0, 9)
            else:
                tmp_est_flash = rds.lrange('est_' + conf['slave_project'] + '_flash', 0, 9)
            if len(tmp_est_flash) > 0:
                result['est'] += sum([int(float(x)) for x in tmp_est_flash]) / len(tmp_est_flash)
            else:
                if '_acrn' in conf['test_target']:
                    result['est'] += 900
                else:
                    result['est'] += 1500

        case_index = -1 if rds.get("atf_case_index") == 'None' else int(rds.get("atf_case_index"))
        loop_index = 0 if rds.get('atf_loop_index') == 'None' else int(rds.get('atf_loop_index'))
        for i, case in enumerate(conf['test_case']):
            if i < case_index:
                continue
            loop_index = loop_index if i == case_index else 0
            est_list = rds.lrange('est_' + conf['slave_project'] + '_' + case, 0, 9)

            if len(est_list) > 0:
                result['est'] += (sum([int(float(x)) for x in est_list]) / len(est_list)) * (int(conf['test_loop'][i]) - loop_index)
            else:
                result['est'] += 180 * (int(conf['test_loop'][i]) - loop_index)
        stat['testing_tasks'].append(result)
        stat['total_est'] += result['est']
    stat['atf_task_id'] = rds.get('atf_task_id')

    return JsonResponse(stat)


def get_testing_task_total_est(request):
    result = {'result': 0}
    if rds.get('atf_task_id') != 'None' and os.path.exists(os.path.join(RUNNER_PATH, 'test_configs', rds.get('atf_config'))):
        conf = json.load(open(os.path.join(RUNNER_PATH, 'test_configs', rds.get('atf_config'))))
        if rds.get('atf_current') == 'None' and not conf['skip_flash']:
            if '_acrn' in conf['test_target']:
                tmp_est_flash = rds.lrange('est_' + conf['slave_project'] + '_acrnflash', 0, 9)
            else:
                tmp_est_flash = rds.lrange('est_' + conf['slave_project'] + '_flash', 0, 9)
            if len(tmp_est_flash) > 0:
                result['result'] += sum([int(float(x)) for x in tmp_est_flash]) / len(tmp_est_flash)
            else:
                if '_acrn' in conf['test_target']:
                    result['result'] += 900
                else:
                    result['result'] += 1500
        for i, case in enumerate(conf['test_case']):
            est_list = rds.lrange('est_' + conf['slave_project'] + '_' + case, 0, 9)
            if len(est_list) > 0:
                result['result'] += (sum([int(float(x)) for x in est_list]) / len(est_list)) * int(conf['test_loop'][i])
            else:
                result['result'] += 180 * int(conf['test_loop'][i])
    return JsonResponse(result)


def add_case(request):
    result = {'result': 0}
    project = request.POST['project']
    case_name = request.POST['case_name']
    code_str = request.POST['case_info']
    print '====', project, case_name
    with open(os.path.join(RUNNER_PATH, 'test_scripts', project, 'script', case_name + ".py"), "w+") as f:
        f.write(code_str)

    info_path = os.path.join(RUNNER_PATH, "test_scripts", project, "info.yaml")
    fo_info = open(info_path, 'r')
    info = fo_info.read()
    group_index = len(info)
    fo_info.close()
    with open(info_path, "a") as w_f:
        infos = """  - name: %s
    group: { id: %s, name: '%s' }
    loop: 1
    arg: ''
    unit: ''
    script: script/benchmark/%s.py"""%(case_name, group_index, case_name, case_name)
        w_f.write(infos)
    return JsonResponse(result)


def reset(request):
    if rds.get('pid') != 'None':
        logger = TestLogger().get_logger("process")
        if logger:
            logger.info('kill %d' % int(rds.get('pid')))
        try:
            os.killpg(os.getpgid(int(rds.get('pid'))), signal.SIGUSR1)
        except OSError, e:
            logger.info('Error message: ' + e.strerror)
        finally:
            if rds.get('atf_task_id') != 'None' and rds.get('atf_test_id') != 'None' and rds.get('atf_config') != 'None':
                tr = TestResult()
                tr.result("Cancel")
                if rds.get('case_name') == "stability_resume":
                    tr.add_attachment(os.path.join(tr.result_dir, 'USB2_ttylog.txt'))
                    tr.add_attachment(os.path.join(tr.result_dir, 'USB3_ttylog.txt'))
                    os.system("echo 123456 | sudo -S kill -9 `ps -ef | grep ttyUSB2 | grep -v color | cut -c 9-15`")
                    os.system("echo 123456 | sudo -S kill -9 `ps -ef | grep ttyUSB3 | grep -v color | cut -c 9-15`")
                tr.save()
            func_reset()
            dev = Device()
            dev.soft_reboot()
    else:
        print "already canceled!"

    return HttpResponse('1')


def func_reset():
    try:
        for k in rds.keys():
            if not k.startswith('est_'):
                rds.set(k, None)
        return True
    except Exception as e:
        print 'reset failed', e.message
        return False
