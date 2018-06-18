from django.contrib import admin
from .models import Transaction, BasicAuth

# Register your models here.
admin.site.register(Transaction)
admin.site.register(BasicAuth)