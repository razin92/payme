# Generated by Django 2.0.5 on 2018-06-06 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20180605_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='paycom_time',
            field=models.BigIntegerField(default=0),
        ),
    ]
