# Generated by Django 2.2.19 on 2022-06-09 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20220609_1738'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'get_latest_by': '+pub_date'},
        ),
    ]
