from django.forms import Form, CharField, TextInput

class TestForm(Form):
    request = CharField(
        max_length=500,
        widget=TextInput(attrs={
            'rows': '10'
        }),
        initial={
        'method' : 'CheckPerformTransaction',
        'params' : {
        'amount' : 500000,
        'account' : {
            'phone' : '903595731'
        }
    }
    }
    )