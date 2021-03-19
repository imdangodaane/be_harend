# Generated by Django 2.2.6 on 2019-10-02 05:53

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20191002_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='login',
            name='access_token',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='login',
            name='code',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='login',
            name='refresh_token',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='token',
            name='expired_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2019, 10, 2, 6, 53, 58, 782580, tzinfo=utc), null=True),
        ),
    ]