from .auth import HTTPBasicAuth
from django.http import JsonResponse
from api import views
import json


def basic_auth(func):
    def wrapped(request, *args, **kwargs):
        message_id = json.loads(request.body.decode('utf-8', 'ignore'))['id']
        if HTTPBasicAuth(request).check_user():
            return func(request, *args, **kwargs)
        return JsonResponse(views.Response().error('no_permissions', m_id=message_id))
    return wrapped

