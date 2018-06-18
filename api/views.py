from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from .forms import TestForm
from .auth import AuthData
from ast import literal_eval
from .models import Transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .decorators import basic_auth
import datetime
import time
import json

message_id = 0
# Главный класс для принятия запросов от PayMe
@method_decorator(csrf_exempt, 'dispatch')
@method_decorator(basic_auth, 'dispatch')
class PaymentAPI(View):

    methods = ('CheckPerformTransaction',
               'CreateTransaction',
               'PerformTransaction',
               'CancelTransaction',
               'CheckTransaction',
               'GetStatement',
               'ChangePassword'
               )

    def post(self, request):
        global message_id
        json_data = json.loads(request.body.decode('utf-8', 'ignore'))
        print(json_data)
        method = json_data['method']
        if 'id' in json_data:
            message_id = json_data['id']
        if method in self.methods:
            result = getattr(self, method)(self, json_data)
            return JsonResponse(result)
        response = Response.error('wrong_method')
        return JsonResponse(response)


    # Проверка возможности оплаты
    def CheckPerformTransaction(self, request, json, *args, **kwargs):
        method = self.CheckPerformTransaction.__name__

        if 'account' not in json['params']:
            return Response.error('field_error')
        if 'uid' not in json['params']['account']:
            return Response.error('field_error')

        uid = json['params']['account']['uid']
        result = OneCConnector().check_id(uid)

        if not result:
            # Ошибка, если невозможно осушествить оплату для данного UID
            return Response.error('uid_error')

        if 'amount' in json['params']:
            amount = json['params']['amount']
            # Ограничения на сумму
            if 2000000 <= amount <= 30000000:
                return Response.success(method, result)
            else:
                # Ошибка, если сумма неверна
                return Response.error('wrong_amount')

        return Response.error()

    # Создание транзакции
    def CreateTransaction(self, request, json, *args, **kwargs):
        method = self.CreateTransaction.__name__
        params = json['params']
        transaction, created = Transaction.objects.get_or_create(paycom_transaction_id=params['id'])
        transaction_id = transaction.id

        if created:
            check_perform = self.CheckPerformTransaction(request, json)
            if 'result' in check_perform:
                transaction.state = 1
                transaction.paycom_time = params['time']
                transaction.paycom_time_datetime = datetime_from_timestamp(params['time'])
                transaction.account = params['account']['uid']
                transaction.amount = params['amount'] / 100
                transaction.create_time = datetime.datetime.now()
                transaction.save()
                create_time_timestamp = timestamp_from_datetime(transaction.create_time)

                return Response.success(method,
                                        create_time=create_time_timestamp,
                                        transaction=transaction_id,
                                        state=transaction.state
                                        )

            return check_perform

        create_time = transaction.create_time
        create_time_timestamp = timestamp_from_datetime(create_time)

        if transaction.state != 1 or timeout(transaction):
            return Response.error('perform_error')

        if transaction.state == 1:
            return Response.success(
                method,
                create_time=create_time_timestamp,
                transaction=transaction_id,
                state=transaction.state
            )

        return Response.error()

    # Проведение транзакции. Зачисление средств и установка статуса "Оплачен"
    def PerformTransaction(self, request, json):
        method = self.PerformTransaction.__name__
        params = json['params']
        transaction = get_transaction(params['id'])

        if not transaction:
            return Response.error('not_found')

        if transaction.state != 1:
            if transaction.state == 2:
                perform_timestamp = timestamp_from_datetime(transaction.perform_time)

                return Response.success(
                    method,
                    state=transaction.state,
                    perform_time=perform_timestamp,
                    transaction=transaction.id,
                )

            return Response.error('perform_error')

        if timeout(transaction):
            return Response.error('perform_error')

        # perform!
        tr_id = OneCConnector().perform_transaction(transaction.account, transaction.amount)
        transaction.perform_time = datetime.datetime.now()
        perform_timestamp = timestamp_from_datetime(transaction.perform_time)
        transaction.state = 2
        transaction.base_transaction_id = tr_id
        transaction.save()

        return Response.success(
            method,
            state=transaction.state,
            perform_time=perform_timestamp,
            transaction=transaction.id,
        )

    # Отмена транзакции как созданной, так и проведенной
    def CancelTransaction(self, request, json):
        method = self.CancelTransaction.__name__
        params = json['params']
        transaction = get_transaction(params['id'])

        if 'reason' in params:
            reason = params['reason']
        else:
            return Response.error('field_error')

        if not transaction:
            return Response.error('not_found')

        state = transaction.state
        transaction_id = transaction.id
        cancel_time = datetime.datetime.now()
        cancel_timestamp = timestamp_from_datetime(cancel_time)
        uid = transaction.account
        amount = transaction.amount
        id_tr = transaction.base_transaction_id

        if state == 1 or state == 0:
            transaction.state = -1
            transaction.reason = reason
            transaction.cancel_time = cancel_time
            transaction.save()

            return Response.success(
                method,
                cancel_time=cancel_timestamp,
                state=transaction.state,
                transaction=transaction_id
            )

        if state != 2:
            cancel_time = transaction.cancel_time
            cancel_timestamp = timestamp_from_datetime(cancel_time)

            return Response.success(
                method,
                cancel_time=cancel_timestamp,
                state=transaction.state,
                transaction=transaction_id
            )

        if state == 2:
            if OneCConnector().check_balance(uid, amount):

                try:
                    OneCConnector().cancel_transaction(id_tr)
                except:
                    return Response.error()

                transaction.state = -2
                transaction.reason = reason
                transaction.cancel_time = cancel_time
                transaction.save()

                return Response.success(
                    method,
                    cancel_time=cancel_timestamp,
                    state=transaction.state,
                    transaction=transaction_id
                )

            return Response.error('cancel_error')

        return Response.error()

    # Проверка статусы транзакции
    def CheckTransaction(self, request, json):
        method = self.CheckTransaction.__name__
        params = json['params']
        transaction = get_transaction(params['id'])

        if not transaction:
            return Response.error('not_found')

        create_time = timestamp_from_datetime(transaction.create_time)
        perform_time = timestamp_from_datetime(transaction.perform_time)
        cancel_time = timestamp_from_datetime(transaction.cancel_time)
        transaction_id = transaction.id
        state = transaction.state
        reason = transaction.reason

        return Response.success(
            method,
            create_time=create_time,
            perform_time=perform_time,
            cancel_time=cancel_time,
            transaction=transaction_id,
            state=state,
            reason=reason,
        )

    # Сверка транзакций
    def GetStatement(self, request, json):
        method = self.GetStatement.__name__
        params = json['params']
        start = datetime_from_timestamp(params['from'])
        end = datetime_from_timestamp(params['to'])

        transactions = Transaction.objects.filter(paycom_time_datetime__range=(start, end))

        if transactions.__len__() == 0:
            return Response.success(method, transactions=[])

        transactions_list = [
            {
                'id': transaction.paycom_transaction_id,
                'time': transaction.paycom_time,
                'amount': transaction.amount*100,
                'account':{
                    'uid': transaction.account
                },
                'create_time': timestamp_from_datetime(transaction.create_time),
                'perform_time': timestamp_from_datetime(transaction.perform_time),
                'cancel_time': timestamp_from_datetime(transaction.cancel_time),
                'transaction': transaction.id,
                'state': transaction.state,
                'reason': transaction.reason,
            }
            for transaction in transactions
        ]

        return Response.success(method, transactions=transactions_list)

    # Смена пароля доступа к биллингу мерчанта
    def ChangePassword(self, request, json):
        method = self.ChangePassword.__name__
        return Response.error()


class Test(View):

    def get(self, request):
        template = 'api/test.html'
        form = TestForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, template, context)


class Response:

    @staticmethod
    def error(key='system_error', value=None, m_id=None):

        srv_errors = {
            'wrong_amount': {
                'code': -31001,
                'message': {
                    'ru': 'Неправильная сумма оплаты',
                    'uz': 'Notog\'ri tolov',
                    'en': 'Wrong amount'
                },
            },
            'not_found': {
                'code': -31003,
                'message': {
                    'ru': 'Транзакция не найдена',
                    'uz': 'Tranzakciya to\'pilmadi',
                    'en': 'Transaction not found'
                },
            },
            'cancel_error': {
                'code': -31007,
                'message': {
                    'ru': 'Отмена платежа невозможна',
                    'uz': 'Tolovlaringizi qaytarib bo\'lmaydi',
                    'en': 'Return payment denied'
                },
            },
            'perform_error': {
                'code': -31008,
                'message': {
                    'ru': 'Невозможно провести платеж',
                    'uz': '',
                    'en': 'Transaction perform error'
                },
            },
            'uid_error': {
                'code': -31050,
                'message': {
                    'ru': 'Абонент не найден',
                    'uz': '',
                    'en': 'Subscriber not found'
                },
            },
            'not_post': {
                'code': -32300,
                'message': {
                    'ru': 'Неправильный http метод',
                    'uz': '',
                    'en': 'Wrong http method'
                },
            },
            'json_parse_error': {
                'code': -32700,
                'message': {
                    'ru': 'Ошибка разбора JSON',
                    'uz': '',
                    'en': 'JSON parse error'
                },
            },
            'field_error':  {
                'code': -32600,
                'message': {
                    'ru': 'Указаны неправильные поля JSON',
                    'uz': '',
                    'en': 'JSON fields error'
                },
            },
            'wrong_method': {
                'code': -32601,
                'message': {
                    'ru': 'Неправильный метод',
                    'uz': '',
                    'en': 'Wrong method'
                },
            },
            'no_permissions': {
                'code': -32504,
                'message': {
                    'ru': 'Недостаточно прав для этого действия',
                    'uz': '',
                    'en': 'Permission denied'
                },
            },
            'system_error': {
                'code': -32400,
                'message': {
                    'ru': 'Системная ошибка',
                    'uz': '',
                    'en': 'System error'
                },
            },
        }

        key_value = srv_errors[key]

        error = {
            'error': {
                'code':key_value['code'],
                'id': message_id,
                'message': key_value['message']
            }
        }
        if m_id:
            error['error']['id'] = m_id

        if value:
            reverse_srv_errors = {x: y for y, x in srv_errors.items()}
            error['error']['code'] = reverse_srv_errors[value]

        return error

    @staticmethod
    def success(
            method, allow=True, create_time=None,
            transaction=None, state=0, perform_time=None,
            cancel_time=None, reason=None, transactions=None,
        ):
        transaction = str(transaction)
        success = {
            'CheckPerformTransaction': {'allow': allow},
            'CreateTransaction': {
                'create_time': create_time,
                'transaction': transaction,
                'state': state
            },
            'PerformTransaction': {
                'transaction': transaction,
                'perform_time': perform_time,
                'state': state
            },
            'CancelTransaction': {
                'transaction': transaction,
                'cancel_time': cancel_time,
                'state': state
            },
            'CheckTransaction': {
                'create_time': create_time,
                'perform_time': perform_time,
                'cancel_time': cancel_time,
                'transaction': transaction,
                'state': state,
                'reason': reason,
            },
            'GetStatement': {
                'transactions': transactions
            },
            'ChangePassword': {
                'success': allow
            },
        }

        result = {
            'result': success[method]
        }

        return result

class OneCConnector(AuthData):

    def check_id(self, uid):
        url = 'hs/payme/%s' % uid
        response = self.Connector(url)
        parse = literal_eval(response.content.decode())
        return parse

    def check_balance(self, uid, amount=0):
        url = 'hs/subjectinfo/%s' % uid
        response = self.Connector(url)
        parse = literal_eval(response.content.decode())
        balance = dict(parse)['Balance1']
        if balance == 'Нет данных':
            return False
        balance = int(balance)
        if balance > 0:
            return balance >= amount
        return False

    def perform_transaction(self, uid, amount):
        url = 'hs/payme/'
        data = {
            'uid': uid,
            'amount': int(amount)
        }
        r = self.ConnectorPOST(url, data)
        transaction_id = int(r.content)

        return transaction_id

    def cancel_transaction(self, id_tr):
        url = 'hs/payme/cancel'
        data = {
            'ID': id_tr
        }
        r = self.ConnectorPOST(url, data)
        result = (r.content)

        return result

def get_transaction(paycom_transaction_id=0):
    try:
        transaction = Transaction.objects.get(
            paycom_transaction_id=paycom_transaction_id
        )
        return transaction
    except:
        return False


def timeout(transaction):
    timestamp = transaction.paycom_time
    time_now = int(datetime.datetime.now().timestamp() * 1000)

    if time_now - timestamp >= 43200000:
        transaction.state = -1
        transaction.reason = 4
        transaction.save()
        return True

    return False


def timestamp_from_datetime(datetime):
    if datetime is None:
        return 0
    return int(datetime.replace(microsecond=0).timestamp() * 1000)

def datetime_from_timestamp(timestamp):
    result = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.gmtime(
                        timestamp/1000
                    )
            )

    return result
