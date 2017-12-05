from django.conf.urls import url, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from . import views
from . import api_views

schema_view = get_schema_view(title='Young Supernova Experiment (YSE) API')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
	# ex: /yse/
	url(r'^$', views.index, name='index'),
	url(r'^dashboard$', views.dashboard, name='dashboard'),
	url(r'^dashboard_example$', views.dashboard_example, name='dashboard_example'),
	url(r'^transient_edit/$', views.transient_edit, name='transient_edit'),
	url(r'^transient_edit/(?P<transient_id>[0-9]+)/$', views.transient_edit, name='transient_edit'),
	# ex: /yse/transient_detail/5/
	url(r'^transient_detail/(?P<transient_id>[0-9]+)/$', views.transient_detail, name='transient_detail'),
	url(r'^login/$', views.auth_login, name='auth_login'),
	url(r'^logout/$', views.auth_logout, name='auth_logout'),
	# url(r"^airmassplot/(?P<transient_id>[0-9]+)/(?P<obs>[a-zA-Z0-9_-]+)/(?P<observatory>[a-zA-Z0-9]+)", 
	# 	views.airmassplot, name='airmassplot'),
]

router = DefaultRouter()
router.register(r'transientwebresources', api_views.TransientWebResourceViewSet)
router.register(r'hostwebresources', api_views.HostWebResourceViewSet)
router.register(r'transientstatuses', api_views.TransientStatusViewSet)
router.register(r'followupstatuses', api_views.FollowupStatusViewSet)
router.register(r'taskstatuses', api_views.TaskStatusViewSet)
router.register(r'antaresclassifications', api_views.AntaresClassificationViewSet)
router.register(r'internalsurveys', api_views.InternalSurveyViewSet)
router.register(r'observationgroups', api_views.ObservationGroupViewSet)
router.register(r'sedtypes', api_views.SEDTypeViewSet)
router.register(r'hostmorphologies', api_views.HostMorphologyViewSet)
router.register(r'phases', api_views.PhaseViewSet)
router.register(r'transientclasses', api_views.TransientClassViewSet)
router.register(r'classicalnighttypes', api_views.ClassicalNightTypeViewSet)
router.register(r'informationsources', api_views.InformationSourceViewSet)
router.register(r'transientfollowups', api_views.TransientFollowupViewSet)
router.register(r'hostfollowups', api_views.HostFollowupViewSet)
router.register(r'hosts', api_views.HostViewSet)
router.register(r'hostseds', api_views.HostSEDViewSet)
router.register(r'instruments', api_views.InstrumentViewSet)
router.register(r'instrumentconfigs', api_views.InstrumentConfigViewSet)
router.register(r'configelements', api_views.ConfigElementViewSet)
router.register(r'logs', api_views.LogViewSet)
router.register(r'transientobservationtasks', api_views.TransientObservationTaskViewSet)
router.register(r'hostobservationtasks', api_views.HostObservationTaskViewSet)
router.register(r'observatories', api_views.ObservatoryViewSet)
router.register(r'oncalldates', api_views.OnCallDateViewSet)
router.register(r'transientphotometry', api_views.TransientPhotometryViewSet)
router.register(r'hostphotometry', api_views.HostPhotometryViewSet)
router.register(r'transientphotdata', api_views.TransientPhotDataViewSet)
router.register(r'hostphotdata', api_views.HostPhotDataViewSet)
router.register(r'transientimages', api_views.TransientImageViewSet)
router.register(r'hostimages', api_views.HostImageViewSet)
router.register(r'photometricbands', api_views.PhotometricBandViewSet)
router.register(r'principalinvestigators', api_views.PrincipalInvestigatorViewSet)
router.register(r'profiles', api_views.ProfileViewSet)
router.register(r'transientspectra', api_views.TransientSpectrumViewSet)
router.register(r'hostspectra', api_views.HostSpectrumViewSet)
router.register(r'transientspectdata', api_views.TransientSpecDataViewSet)
router.register(r'hostspectdata', api_views.HostSpecDataViewSet)
router.register(r'tooresources', api_views.ToOResourceViewSet)
router.register(r'queuedresources', api_views.QueuedResourceViewSet)
router.register(r'classicalresources', api_views.ClassicalResourceViewSet)
router.register(r'classicalobservingdates', api_views.ClassicalObservingDateViewSet)
router.register(r'telescopes', api_views.TelescopeViewSet)
router.register(r'transients', api_views.TransientViewSet)
router.register(r'alternatetransientnames', api_views.AlternateTransientNamesViewSet)
router.register(r'users', api_views.UserViewSet)

# Login/Logout
api_url_patterns = [url(r'^api/', include(router.urls)), 
					url(r'^api/schema/$', schema_view),
					url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),]

urlpatterns += api_url_patterns
