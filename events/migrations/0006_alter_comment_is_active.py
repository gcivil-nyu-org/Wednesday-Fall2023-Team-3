# Generated by Django 4.2.6 on 2023-11-13 14:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0005_comment_is_active"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
