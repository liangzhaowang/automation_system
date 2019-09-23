from django.http.response import HttpResponseServerError, HttpResponse
import importlib


def get_chart_func(chart_name, function_name):
    try:
        chart_module = importlib.import_module('.'.join(['data', 'attachment_views', chart_name]))
        func = getattr(chart_module, function_name)
        return func
    except ImportError as e:
        return e.message
    except AttributeError as e:
        return e.message


def chart(request, chart_name, project, build, test_id, case_name, attachment_name):
    func = get_chart_func(chart_name, 'view')
    if func.__class__ is str:
        return HttpResponseServerError(content=func)
    return func(request, project, build, test_id, case_name, attachment_name)


def chart_data(request, chart_name, project, build, test_id, case_name, attachment_name):
    func = get_chart_func(chart_name, 'api')
    if func.__class__ is str:
        return HttpResponseServerError(content=func)
    return func(request, project, build, test_id, case_name, attachment_name)
