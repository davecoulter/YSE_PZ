from django.conf.urls import url, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from rest_framework import routers

from . import views
from . import api_views


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'transient', api_views.TransientViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
	# ex: /yse/
	url(r'^$', views.index, name='index'),
	url(r'^dashboard$', views.dashboard, name='dashboard'),
	url(r'^dashboard_example$', views.dashboard_example, name='dashboard_example'),

	url(r'^transient_edit/$', 
		views.transient_edit, name='transient_edit'),
	url(r'^transient_edit/(?P<transient_id>[0-9]+)/$', 
		views.transient_edit, name='transient_edit'),

	# ex: /yse/transient_detail/5/
	url(r'^transient_detail/(?P<transient_id>[0-9]+)/$', 
		views.transient_detail, name='transient_detail'),
	url(r'^login/$', views.auth_login, name='auth_login'),
	url(r'^logout/$', views.auth_logout, name='auth_logout'),
	# url(r"^airmassplot/(?P<transient_id>[0-9]+)/(?P<obs>[a-zA-Z0-9_-]+)/(?P<observatory>[a-zA-Z0-9]+)", 
	# 	views.airmassplot, name='airmassplot'),

	url(r'^api/', include(router.urls)),
	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

	url(r'^api/all_transients$', api_views.transient_list),
	url(r'^api/get_transient/(?P<pk>[0-9]+)/$', api_views.transient_detail),
	url(r'^api/all_transienthostrank$', api_views.transienthostrank_list),
	url(r'^api/all_status$', api_views.status_list),
	url(r'^api/all_observationgroup$', api_views.observationgroup_list),
	url(r'^api/all_sedtype$', api_views.sedtype_list),
	url(r'^api/all_hostmorphology$', api_views.hostmorphology_list),
	url(r'^api/all_phase$', api_views.phase_list),
	url(r'^api/all_transientclass$', api_views.transientclass_list),
	url(r'^api/all_hostclass$', api_views.hostclass_list),
	url(r'^api/all_classicalnighttype$', api_views.classicalnighttype_list),
	url(r'^api/all_informationsource$', api_views.informationsource_list),
]
