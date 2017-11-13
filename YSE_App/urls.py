from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
	# ex: /yse/
	url(r'^$', views.index, name='index'),
	# ex: /yse/transient_detail/5/
	url(r'^%stransient_detail/(?P<transient_id>[0-9]+)/$' % settings.VIRTUAL_DIR, 
		views.transient_detail, name='transient_detail'),
]