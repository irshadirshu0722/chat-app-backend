# Generated by Django 5.0.6 on 2024-09-12 10:29

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0002_remove_user_access_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='data_joined',
            new_name='date_joined',
        ),
        migrations.AddField(
            model_name='user',
            name='profile',
            field=cloudinary.models.CloudinaryField(blank=True, default='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRH8hYwgBA8dG12jg4YK5aJ4xqDd1VAB96FKg&s', max_length=255, null=True, verbose_name='image'),
        ),
    ]
