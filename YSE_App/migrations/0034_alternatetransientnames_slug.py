# Generated by Django 2.0.4 on 2019-10-26 17:32

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("YSE_App", "0033_auto_20190925_2043")]

    operations = [
        migrations.AddField(
            model_name="alternatetransientnames",
            name="slug",
            field=autoslug.fields.AutoSlugField(
                default=None,
                editable=False,
                null=True,
                populate_from="name",
                unique=True,
            ),
        )
    ]
