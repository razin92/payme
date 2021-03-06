from django.test import TestCase
from .views import PaymentAPI, Response
from random import randrange, choice
import requests
import datetime
import string
import time
import json

# Create your tests here.

class DataTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(DataTest, self).__init__(*args, **kwargs)
        self.request = {}
        self.methods = ('CheckPerformTransaction', 'CreateTransaction', 'PerformTransaction',
                        'CancelTransaction', 'CheckTransaction', 'GetStatement', 'ChangePassword',
                        'asdasd', 'ererwe', 'erwerw')

    def check(self):
        #model = PaymentAPI
        #response = PaymentAPI.post(model, request=self.request)
        #result = str(response.content, encoding='utf-8')
        #self.assertJSONEqual(result, {'method': 'PerformTransaction'})
        pass

    def test(self):
        for x in range(1):
            data = {
                'method': self.methods[2],
                'params': {
                    'id': 'dal84do9ejwt9wde9g2e3l75',
                    'time': datetime.datetime.now().timestamp() * 1000,
                    'amount': randrange(2000000, 4000000),
                    'account': {
                        'uid': 7445,
                    },
                },
                'id': 2032
            }
            search = {
                'method': self.methods[5],
                'params': {
                    'from': 1528295411328,
                    'to': 1538295411328,
                }
            }
            cancel = {
                "jsonrpc": "2.0",
                "id": 36061,
                "method": "CancelTransaction",
                "params": {
                    "id": "dal84do9ejwt9wde9g2e3l75",
                    "reason": 5
                }
            }
            #self.request = json.dumps(data)
            login = 'payme'
            password = 'password'
            server = 'http://192.168.1.113:8443/'
            server2 = 'http://127.0.0.1:8000/'
            r = requests.post(server2, json=cancel,  auth=(login, password))
            print('sum: %s\nid: %s' % (data['params']['amount'], data['params']['account']['uid']))
            print(r.status_code)
            print(r.headers)
            print(r.content)
            print('--------------------------------------------')