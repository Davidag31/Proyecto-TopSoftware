# Generated by Django 5.1 on 2024-09-27 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_alter_userprofile_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='genre',
            field=models.CharField(default='Na', max_length=100),
        ),
    ]
