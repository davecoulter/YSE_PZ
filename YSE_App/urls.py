from django.conf.urls import url

from . import views

urlpatterns = [
	# ex: /yse/
	url(r'^$', views.index, name='index'),
	# ex: /yse/transient_detail/5/
	url(r'^transient_detail/(?P<transient_id>[0-9]+)/$', 
		views.transient_detail, name='transient_detail'),
]