# Generated by Django 2.0.4 on 2020-04-13 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("YSE_App", "0053_canvasfov")]

    operations = [
        migrations.RemoveField(model_name="canvasfov", name="author"),
        migrations.AddField(
            model_name="surveyfield", name="active", field=models.NullBooleanField()
        ),
    ]
