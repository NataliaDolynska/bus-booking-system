# Generated by Django 4.2.9 on 2024-11-13 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_profile_address_remove_profile_city_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='email',
        ),
    ]
