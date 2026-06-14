from django.apps import AppConfig


class YseAppConfig(AppConfig):
    name = 'YSE_App'

    def ready(self):
        import YSE_App.signals  # noqa: F401

