# Generated by Django 2.0.5 on 2018-06-05 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('state', models.SmallIntegerField()),
                ('user_id', models.IntegerField()),
                ('phone', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paycom_transaction_id', models.CharField(max_length=25)),
                ('paycom_time', models.CharField(max_length=13)),
                ('paycom_time_datetime', models.DateTimeField()),
                ('create_time', models.DateTimeField()),
                ('perfrom_time', models.DateTimeField(default=None, null=True)),
                ('cancel_time', models.DateTimeField(default=None, null=True)),
                ('amount', models.IntegerField()),
                ('state', models.SmallIntegerField()),
                ('reason', models.SmallIntegerField()),
                ('receivers', models.CharField(default=None, max_length=255, null=True)),
                ('order_id', models.IntegerField()),
            ],
        ),
    ]
