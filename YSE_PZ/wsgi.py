"""
WSGI config for YSE_PZ project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from configparser import RawConfigParser

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
configFile = os.path.join(__location__, 'settings.ini')

config = RawConfigParser()
config.read(configFile)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "YSE_PZ.settings")
os.environ["DJANGO_SETTINGS_MODULE"] = config.get('site_settings', 'LOCAL_APP_SETTINGS')

application = get_wsgi_application()
