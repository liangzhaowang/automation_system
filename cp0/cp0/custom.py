import time

from data.models import Task, Project, Logger, Slave


class TimeMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.time_tracking = None

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        self.time_tracking = time.time()

    def process_template_response(self, request, response):
        delta = time.time() - self.time_tracking
        response['X-total-time'] = int(delta * 1000)
        return response

class PersonalDataMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass

    def process_template_response(self, request, response):
        # favorites
        fav = Task.objects.filter(favorites=request.user.id).order_by('-id')[:10]
        myfavorites = Logger.objects.filter(task__in=fav)[::-1]
        slaves = Slave.objects.filter(policy=0)
        private_slave = Slave.objects.filter(policy=1, owner=request.user.id)
        available_slaves = []
        for p_slave in private_slave:
            available_slaves.append(p_slave)
        for slave in slaves:
            available_slaves.append(slave)
        response.context_data['favorites'] = myfavorites
        response.context_data['active_projects'] = Project.objects.filter(active=True)
        response.context_data['inactive_projects'] = Project.objects.filter(active=False)
        response.context_data['upload_available_slaves'] = available_slaves
        return response
