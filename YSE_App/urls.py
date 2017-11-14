from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
	# ex: /yse/
	url(r'^$', views.index, name='index'),
	url(r'^index2$', views.index2, name='index2'),
	# ex: /yse/transient_detail/5/
	url(r'^transient_detail/(?P<transient_id>[0-9]+)/$', 
		views.transient_detail, name='transient_detail'),
]
