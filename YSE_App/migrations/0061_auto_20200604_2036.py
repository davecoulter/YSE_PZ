# Generated by Django 2.0.4 on 2020-06-04 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("YSE_App", "0060_auto_20200508_1919")]

    operations = [
        migrations.AddField(
            model_name="host",
            name="photo_z_err_internal",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="host",
            name="photo_z_internal",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
