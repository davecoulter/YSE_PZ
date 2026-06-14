from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("YSE_App", "0003_surveyobservation_priority"),
    ]

    operations = [
        migrations.CreateModel(
            name="SlackThreadLink",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slack_channel_id", models.CharField(max_length=64)),
                ("slack_thread_ts", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "transient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slack_threads",
                        to="YSE_App.transient",
                    ),
                ),
            ],
            options={
                "unique_together": {("transient", "slack_channel_id")},
            },
        ),
    ]
