from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("YSE_App", "0004_slackthreadlink"),
    ]

    operations = [
        migrations.AddField(
            model_name="log",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="log",
            name="groups",
            field=models.ManyToManyField(blank=True, to="auth.group"),
        ),
    ]
