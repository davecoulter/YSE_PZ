from django.conf.urls import url, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views
from . import api_views


# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r'users', api_views.UserViewSet)
# router.register(r'transient', api_views.TransientViewSet)


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
	# url(r'^api/', include(router.urls)),
	# url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

api_url_patterns = [
	url(r'^api/$', api_views.api_root),
	url(r'^api/users/$', api_views.UserList.as_view(), name='user-list'),
	url(r'^api/users/(?P<pk>[0-9]+)/$', api_views.UserDetail.as_view(), name='user-detail'),
	url(r'^api/transients/$', api_views.TransientList.as_view(), name='transient-list'),
	url(r'^api/transients/(?P<pk>[0-9]+)$', api_views.TransientDetail.as_view()),
	url(r'^api/transienthostranks/$', api_views.TransientHostRankList.as_view(), name='transienthostrank-list'),
	url(r'^api/statuses/$', api_views.StatusList.as_view(), name='status-list'),
	url(r'^api/observationgroups/$', api_views.ObservationGroupList.as_view(), name='observationgroup-list'),
	url(r'^api/sedtypes/$', api_views.SEDTypeList.as_view(), name='sedtype-list'),
	url(r'^api/hostmorphologies/$', api_views.HostMorphologyList.as_view(), name='hostmorphology-list'),
	url(r'^api/phases/$', api_views.PhaseList.as_view(), name='phase-list'),
	url(r'^api/transientclasses/$', api_views.TransientClassList.as_view(), name='transientclass-list'),
	url(r'^api/hostclasses/$', api_views.HostClassList.as_view(), name='hostclass-list'),
	url(r'^api/classicalnighttypes/$', api_views.ClassicalNightTypeList.as_view(), name='classicalnighttype-list'),
	url(r'^api/informationsources/$', api_views.InformationSourceList.as_view(), name='informationsource-list'),

	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

api_url_patterns = format_suffix_patterns(api_url_patterns)
urlpatterns += api_url_patterns
