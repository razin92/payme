from .auth import HTTPBasicAuth
from django.http import JsonResponse
import json

error = {'error': {
            'code': -32504,
            'id': 0,
            'message': {
                'ru': 'Недостаточно прав для этого действия',
                'uz': 'Deny',
                'en': 'Permission denied'
                },
        }
}

def basic_auth(func):
    def wrapped(request, *args, **kwargs):
        message_id = json.loads(request.body.decode('utf-8', 'ignore'))['id']
        error['error']['id'] = message_id
        if HTTPBasicAuth(request).check_user():
            return func(request, *args, **kwargs)
        return JsonResponse(error)
    return wrapped

