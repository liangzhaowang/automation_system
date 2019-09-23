from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from django.http import JsonResponse
from django.conf import settings
from cp0.lib import new_render
import os
import json


# http://127.0.0.1:8000/chart_data/usage_chart/aic/18ww08/20190315_190121/game_90/aic_game_0.json/
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
        'api': '/'.join(['chart_data', 'usage_chart_v2', project, build, test_id, case_name, attachment_name])
    }
    return new_render(request, 'usage_chart_v2.html', context=context, title='CP0', subtitle=None, wide=True)


def parse_raw_data(file_path):
    instance_list = []
    show_data = -1440
    cpu_dataset = [{
        'label': 'usage',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
        'yAxisID': 'y-axis-1',
        'pointRadius': 0
    },{
        'label': 'instance',
        'backgroundColor': "",
        'borderColor': "rgb(255, 99, 132)",
        'data': [],
        'fill': False,
        'yAxisID': 'y-axis-2',
        'pointBorderWidth': 1,
        'pointRadius': 0
    }]

    fps_dataset = [{
        'label': 'fps',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
        'pointBorderWidth': 1,
        'pointRadius': 0
    },{
        'label': 'instance',
        'backgroundColor': "",
        'borderColor': "rgb(255, 99, 132)",
        'data': [],
        'fill': False,
        'yAxisID': 'y-axis-2',
        'pointBorderWidth': 1,
        'pointRadius': 0
    }]

    available_mem_dataset = [{
        'label': 'usage',
        'backgroundColor': "",
        'borderColor': "rgb(54, 162, 235)",
        'data': [],
        'fill': False,
        'pointBorderWidth': 1,
        'pointRadius': 0
    },{
        'label': 'instance',
        'backgroundColor': "",
        'borderColor': "rgb(255, 99, 132)",
        'data': [],
        'fill': False,
        'yAxisID': 'y-axis-2',
        'pointBorderWidth': 1,
        'pointRadius': 0
    }]
    with open(file_path, 'r') as f:
        origin_dict = json.loads(f.read())
        if origin_dict.has_key('instance_results'):
            for instance in origin_dict['instance_results']:
                instance_list.extend(instance['list_time'])
                if 'cpu_usages' in instance:
                    cpu_dataset[0]['data'].extend(instance['cpu_usages'])
                    cpu_dataset[1]['data'].extend(len(instance['cpu_usages']) * [instance['instance_num']])

                if 'fps' in instance:
                    fps_dataset[0]['data'].extend(instance['fps'])
                    fps_dataset[1]['data'].extend(len(instance['fps']) * [instance['instance_num']])
                if 'mem' in instance:
                    available_mem_dataset[0]['data'].extend(instance['mem']['usages'])
                    available_mem_dataset[1]['data'].extend(len(instance['mem']['usages']) * [instance['instance_num']])
        else:
            cpu_dataset[0]['data'].extend(origin_dict['cpu_usages'][show_data:])
            cpu_dataset[1]['data'].extend(origin_dict['instance_num'][show_data:])
            fps_dataset[0]['data'].extend(origin_dict['fps'][show_data:])
            fps_dataset[1]['data'].extend(origin_dict['instance_num'][show_data:])

            available_mem_dataset[0]['data'].extend(origin_dict['mem']['usages'][show_data:])
            available_mem_dataset[1]['data'].extend(origin_dict['instance_num'][show_data:])
            instance_list.extend(origin_dict['list_time'][show_data:])
            #print len(instance_list)

    return {
        'mem_dataset': available_mem_dataset,
        'fps_dataset': fps_dataset,
        'cpu_dataset': cpu_dataset,
        'instances': instance_list
    }
