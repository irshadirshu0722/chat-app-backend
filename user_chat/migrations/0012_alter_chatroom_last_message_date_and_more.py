# Generated by Django 5.0.6 on 2024-09-04 09:07

import datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_chat', '0011_alter_chatroom_last_message_date_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroom',
            name='last_message_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 4, 14, 37, 54, 163425)),
        ),
        migrations.AlterField(
            model_name='chatroom',
            name='room_id',
            field=models.CharField(default='P0src_EPN5u2zX8E2l4Hhg', editable=False, max_length=22, unique=True),
        ),
        migrations.AlterField(
            model_name='groupconf',
            name='admins',
            field=models.ManyToManyField(blank=True, related_name='admin_groups', to=settings.AUTH_USER_MODEL),
        ),
    ]
