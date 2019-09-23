from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from django.http import JsonResponse
from django.conf import settings
from cp0.lib import new_render
import os
import json


# http://127.0.0.1:8000/chart_data/usage_chart/aic/build001/20190311_012941/mem_usage/raw_1.json/
def api(request, project, build, test_id, case_name, attachment_name):
    file_path = os.path.join(
        settings.BASE_DIR,
        'data',
        'data',
        project, #aic
        'raw',
        build,
        test_id,
        case_name,
        attachment_name
    )
    # /chart_data/usage_chart/aic/build001/20190311_012941/mem_usage/raw_1.json/
    return JsonResponse({
        'data': 'data',
        'file_path': file_path,
        'datasets': parse_raw_data(file_path)
    })


# http://cubep.sh.intel.com/chart/usage_chart/aic/build001/20190311_012941/mem_usage/raw_1.json/
def view(request, project, build, test_id, case_name, attachment_name):
    context = {
        'api': '/'.join(['chart_data', 'usage_chart', project, build, test_id, case_name, attachment_name])
    }
    return new_render(request, 'usage.html', context=context, title='CP0', subtitle=None, wide=True)


def parse_raw_data(file_path):
    instance_list = []

    cpu_dataset = [{
        'label': 'usage',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
    }]

    fps_dataset = [{
        'label': 'fps',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
    }]

    available_mem_dataset = [{
        'label': 'available',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
    }]

    free_mem_dataset = [{
        'label': 'free',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
    }]

    time = []

    with open(file_path, 'r') as f:
        origin_dict = json.loads(f.read())

    for instance in origin_dict['instance_results']:
        instance_list.append(instance['instance_num'])
        if 'cpu_usages' in instance:
            # cpu_dataset[0]['data'].append(round(sum(instance['cpu_usages']) / len(instance['cpu_usages']), 2))
            cpu_dataset[0]['data'] = instance['cpu_usages']
        if 'fps' in instance:
            # fps_dataset[0]['data'].append(round(sum(instance['fps']) / len(instance['fps']), 2))
            fps_dataset[0]['data'] = instance['fps']
        if 'mem' in instance:
            for label, data in instance['mem'].items():
                if label == 'usages':
                    available_mem_dataset[0]['data'] = data
        if 'list_time' in instance:
            time = instance['list_time']

    return {
        'mem_dataset': available_mem_dataset,
        'fps_dataset': fps_dataset,
        'cpu_dataset': cpu_dataset,
        'time': time
    }
