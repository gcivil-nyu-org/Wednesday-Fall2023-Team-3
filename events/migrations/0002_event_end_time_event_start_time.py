# Generated by Django 4.2.5 on 2023-10-10 01:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='end_time',
            field=models.DateTimeField(default=(2023, 1, 1, 0, 0, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='start_time',
            field=models.DateTimeField(default=(2023, 1, 1, 0, 0, 0)),
            preserve_default=False,
        ),
    ]
