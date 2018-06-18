from django.db import models

# Create your models here.
class Transaction(models.Model):
    paycom_transaction_id = models.CharField(max_length=25, unique=True)
    paycom_time = models.BigIntegerField(default=0)
    paycom_time_datetime = models.DateTimeField(blank=True, null=True, default=None)
    create_time = models.DateTimeField(auto_now=True)
    perform_time = models.DateTimeField(blank=True, null=True, default=None)
    cancel_time = models.DateTimeField(blank=True, null=True, default=None)
    amount = models.DecimalField(default=0.00, max_digits=9, decimal_places=2)
    state = models.SmallIntegerField(default=0)
    reason = models.SmallIntegerField(null=True, default=None)
    account = models.PositiveIntegerField(default=0)
    base_transaction_id = models.PositiveIntegerField(default=0)
