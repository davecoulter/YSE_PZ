# Generated by Django 2.0.4 on 2021-05-21 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("YSE_App", "0064_auto_20210206_2001")]

    operations = [
        migrations.AddField(
            model_name="host",
            name="panstarrs_objid",
            field=models.BigIntegerField(blank=True, null=True),
        )
    ]
