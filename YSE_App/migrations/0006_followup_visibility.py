from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("YSE_App", "0005_log_visibility"),
    ]

    operations = [
        migrations.AddField(
            model_name="hostfollowup",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="hostfollowup",
            name="requested_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="transientfollowup",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="transientfollowup",
            name="requested_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="hostfollowup",
            name="groups",
            field=models.ManyToManyField(blank=True, to="auth.group"),
        ),
        migrations.AddField(
            model_name="transientfollowup",
            name="groups",
            field=models.ManyToManyField(blank=True, to="auth.group"),
        ),
    ]
