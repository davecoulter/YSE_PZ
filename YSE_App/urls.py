from django.conf.urls import url, include
from django.urls import path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from django.urls import path, re_path, include

from . import views, view_utils, data_utils, table_utils, yse_views
from . import api_views
from .form_views import *
from .yse_utils.yse_forms import MoveYSEFormView
from . import surveypages
from YSE_App.yse_utils import yse_pointings, yse_view_utils
from YSE_App.views import SearchResultsView

schema_view = get_schema_view(title='Young Supernova Experiment (YSE) API')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
	# ex: /yse/
    url(r'^$', views.index, name='index'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^yse_home/$', views.yse_home, name='yse_home'),
    url(r'^personaldashboard/$', views.personaldashboard, name='personaldashboard'),
    url(r'^calendar/$', views.calendar, name='calendar'),
    url(r'^followup/$', views.followup, name='followup'),
	url(r'^transient_tags/$', views.transient_tags, name='transient_tags'),
	url(r'^get_transient_tags/$', views.get_transient_tags, name='get_transient_tags'),

	# survey info
    url(r'^survey/$', surveypages.survey, name='survey'),
    url(r'^news/$', surveypages.news, name='news'),
    url(r'^team/$', surveypages.team, name='team'),
    url(r'^contact/$', surveypages.contact, name='contact'),
    url(r'^acknowledgements/$', surveypages.acknowledgements, name='acknowledgements'),
    
    url(r'^dashboard_example/$', views.dashboard_example, name='dashboard_example'),
    url(r'^transient_edit/$', views.transient_edit, name='transient_edit'),
    url(r'^transient_edit/(?P<transient_id>[0-9]+)/$', views.transient_edit, name='transient_edit'),
    url(r'^transient_detail/(?P<slug>.*)/$', views.transient_detail, name='transient_detail'),
    url(r'^transient_summary/(?P<status_or_query_name>.*)/$', views.transient_summary, name='transient_summary'),

    url(r'^observing_calendar/$', views.observing_calendar, name='observing_calendar'),
    url(r'^yse_observing_calendar/$', views.yse_observing_calendar, name='yse_observing_calendar'),
    url(r'^yse_planning/$', yse_views.yse_planning, name='yse_planning'),
    url(r'^yse_fields/(?P<ra_min_hour>.*)/(?P<ra_max_hour>.*)/(?P<min_mag>.*)/$', yse_views.yse_fields, name='yse_fields'),
    url(r'^yse_sky/$', yse_views.yse_sky, name='yse_sky'),
    url(r'^select_yse_fields/$', yse_views.select_yse_fields, name='select_yse_fields'),
	url(r'^move_yse_field/$', MoveYSEFormView.as_view(), name='move_yse_field'),
	url(r'^return_serialized_transients/$', yse_views.return_serialized_transients, name='return_serialized_transients'),
    url(r'^msb_detail/(?P<msb>.*)$', yse_views.msb_detail, name='msb_detail'),
    url(r'^delete_followup/(?P<followup_id>[0-9_-]+)/$', views.delete_followup, name='delete_followup'),

    re_path(r'^toggleTargetField/$', yse_view_utils.toggle_field, name='toggle_field'),
	re_path(r'^toggleFieldSet/$', yse_view_utils.toggle_fieldset, name='toggle_fieldset'),
	re_path(r'^getFieldVerts/$', yse_view_utils.get_field_verts, name='get_field_verts'),
	re_path(r'^getSNVerts/$', yse_view_utils.get_sn_verts, name='get_sn_verts'),
	re_path(r'^getFieldMSBVerts/$', yse_view_utils.get_fieldmsb_verts, name='get_fieldmsb_verts'),
    re_path(r'^initDrawFields/$', yse_view_utils.init_draw_fields, name='init_draw_fields'),
    re_path(r'^initDrawTransients/$', yse_view_utils.init_draw_transients, name='init_draw_transients'),
    re_path(r'^initDrawFieldsDetail/$', yse_view_utils.init_draw_fields_detail, name='init_draw_fields_detail'),
    re_path(r'^updateTargetFieldLocations/$', yse_view_utils.update_target_field_locations, name='update_target_field_locations'),

    #url(r'^yse_msb/$', yse_views.yse_msb, name='yse_msb'),
    url(r'^yse_pointings/(?P<field_name>.*)/(?P<snid>[a-zA-Z0-9_-]+)/$', yse_pointings.get_yse_pointings, name='yse_pointings'),
    url(r'^yse_pointings_plot/(?P<field_name>.*)/(?P<snid>[a-zA-Z0-9_-]+)/$', yse_pointings.yse_pointing_plot, name='yse_pointings_plot'),
    url(r'^adjust_yse_pointings/(?P<field_name>.*)/(?P<snid>[a-zA-Z0-9_-]+)/$', yse_pointings.adjust_yse_pointings, name='adjust_yse_pointings'),
    url(r'^adjust_yse_pointings_plot/(?P<field_name>.*)/(?P<snid>[a-zA-Z0-9_-]+)/$', yse_pointings.adjust_yse_pointings_plot, name='adjust_yse_pointings_plot'),
    url(r'^yse_msb_change/(?P<field_to_drop>.*)/(?P<field_to_add>.*)/(?P<snid>[a-zA-Z0-9_-]+)/(?P<ra_to_add>.*)/(?P<dec_to_add>.*)/$', 
		yse_views.yse_msb_change, name='yse_msb_change'),

    url(r'^yse_oncall_calendar/$', views.yse_oncall_calendar, name='yse_oncall_calendar'),
    url(r'^observing_night/(?P<telescope>.*)/(?P<obs_date>[a-zA-Z0-9_-]+)/(?P<pi_name>.*)$', views.observing_night, name='observing_night'),
    #url(r'^survey_observing_calendar/$', views.survey_observing_calendar, name='survey_observing_calendar'),
    url(r'^yse_observing_night/(?P<obs_date>[a-zA-Z0-9_-]+)/$', views.yse_observing_night, name='yse_observing_night'),
    url(r'^view_yse_fields/$', view_utils.view_yse_fields, name='view_yse_fields'),
	
	url(r'^get_transient/(?P<slug>.*)/$', data_utils.get_transient, name='get_transient'),
	url(r'^get_rising_transients/(?P<ndays>[a-zA-Z0-9_-]+)/$', data_utils.get_rising_transients, name='get_rising_transients'),
	url(r'^add_transient/', data_utils.add_transient, name='add_transient'),
	url(r'^add_yse_survey_obs/', data_utils.add_yse_survey_obs, name='add_yse_survey_obs'),
	url(r'^add_yse_survey_fields/', data_utils.add_yse_survey_fields, name='add_yse_survey_fields'),

	url(r'^add_gw_candidate/', data_utils.add_gw_candidate, name='add_gw_candidate'),
	url(r'^add_transient_phot/', data_utils.add_transient_phot, name='add_transient_phot'),
	url(r'^add_transient_spec/', data_utils.add_transient_spec, name='add_transient_spec'),
	url(r'^get_host/(?P<ra>\d+\.\d+)/(?P<dec>[+-]?\d+\.\d+)/(?P<sep>\d+\.?\d*)/$', data_utils.get_host, name='get_host'),
	url(r'^get_rising_transients_box/(?P<ra>\d+\.\d+)/(?P<dec>[+-]?\d+\.\d+)/(?P<ra_width>\d+\.?\d*)/(?P<dec_width>\d+\.?\d*)/$', 
		data_utils.get_rising_transients_box, name='get_rising_transients_box'),
	url(r'^get_new_transients_box/(?P<ra>\d+\.\d+)/(?P<dec>[+-]?\d+\.\d+)/(?P<ra_width>\d+\.?\d*)/(?P<dec_width>\d+\.?\d*)/$', 
		data_utils.get_new_transients_box, name='get_new_transients_box'),
	url(r'^box_search/(?P<ra>\d+\.\d+)/(?P<dec>[+-]?\d+\.\d+)/(?P<radius>\d+\.?\d*)/$', 
		data_utils.box_search, name='box_search'),
	url(r'^search/$', 
		SearchResultsView.as_view(), name='search'),

	url(r'^query_api/(?P<query_name>.*)/$',data_utils.query_api, name='query_api'),
	url(r'^change_status_for_query/(?P<query_id>[a-zA-Z0-9_-]+)/(?P<status_id>[a-zA-Z0-9_-]+)$', 
		views.change_status_for_query, name='change_status_for_query'),
	url(r'^download_data/(?P<slug>.*)/$', views.download_data, name='download_data'),
	url(r'^download_spectra/(?P<slug>.*)/$', views.download_spectra, name='download_spectra'),
	url(r'^download_photometry/(?P<slug>.*)/$', views.download_photometry, name='download_photometry'),
	url(r'^download_bulk_photometry/(?P<query_title>[a-zA-Z0-9_-]+)/$', views.download_bulk_photometry, name='download_bulk_photometry'),
	url(r'^download_target_list/(?P<telescope>[a-zA-Z0-9_-]+)/(?P<obs_date>[a-zA-Z0-9_-]+)/$', views.download_target_list, name='download_target_list'),
	url(r'^download_targets_and_finders/(?P<telescope>[a-zA-Z0-9_-]+)/(?P<obs_date>[a-zA-Z0-9_-]+)/$', views.download_targets_and_finders, name='download_targets_and_finders'),
	url(r'^upload_spectrum/', views.upload_spectrum, name='upload_spectrum'),
	
    url(r'^login/$', views.auth_login, name='auth_login'),
    url(r'^logout/$', views.auth_logout, name='auth_logout'),
    url(r"^airmassplot/(?P<transient_id>[a-zA-Z0-9_-]+)/(?P<obs_id>[a-zA-Z0-9_-]+)/(?P<telescope_id>[a-zA-Z0-9_-]+)", 
		view_utils.airmassplot, name='airmassplot'),
    url(r'^lightcurveplot_detail/(?P<transient_id>[0-9_-]+)/$', view_utils.lightcurveplot_detail, name='lightcurveplot_detail'),
    url(r'^lightcurveplot_flux/(?P<transient_id>[0-9_-]+)/$', view_utils.lightcurveplot_flux, name='lightcurveplot_flux'),
    url(r'^lightcurveplot_summary/(?P<transient_id>[0-9_-]+)/$', view_utils.lightcurveplot_summary, name='lightcurveplot_summary'),
    url(r'^salt2plot/(?P<transient_id>[0-9]+)/(?P<salt2fit>[0-1]+)/$', view_utils.salt2plot, name='salt2plot'),
    url(r'^salt2fluxplot/(?P<transient_id>[0-9]+)/(?P<salt2fit>[0-1]+)/$', view_utils.salt2fluxplot, name='salt2fluxplot'),
    url(r'^spectrumplot/(?P<transient_id>[0-9]+)/$', view_utils.spectrumplot, name='spectrumplot'),
    url(r'^spectrumplot_summary/(?P<transient_id>[0-9]+)/$', view_utils.spectrumplot_summary, name='spectrumplot_summary'),
    url(r'^spectrumplotsingle/(?P<transient_id>[a-zA-Z0-9_-]+)/(?P<spec_id>[a-zA-Z0-9_-]+)/$', view_utils.spectrumplotsingle, name='spectrumplotsingle'),
	url(r'^finderchart/(?P<transient_id>[0-9]+)/$', view_utils.finder().finderchart, name='finderchart'),
	url(r'^finderim/(?P<transient_id>[0-9]+)/$', view_utils.finder().finderim, name='finderim'),
	
	url(r'^add_transient_followup/', AddTransientFollowupFormView.as_view(), name='add_transient_followup'),
	url(r'^add_classical_resource/', AddClassicalResourceFormView.as_view(), name='add_classical_resource'),
	url(r'^add_too_resource/', AddToOResourceFormView.as_view(), name='add_too_resource'),
	url(r'^automated_spectrum_request/', AddAutomatedSpectrumRequestFormView.as_view(), name='automated_spectrum_request'),
    url(r'^add_transient_observation_task/', AddTransientObservationTaskFormView.as_view(), name='add_transient_observation_task'),
	url(r'^add_survey_field/', AddSurveyFieldFormView.as_view(), name='add_survey_field'),
	url(r'^add_survey_obs/', AddSurveyObsFormView.as_view(), name='add_survey_obs'),
	url(r'^add_oncall_observer/', AddOncallUserFormView.as_view(), name='add_oncall_observer'),
    url(r'^add_transient_comment/', AddTransientCommentFormView.as_view(), name='add_transient_comment'),
	url(r'^add_dashboard_query/', AddDashboardQueryFormView.as_view(), name='add_dashboard_query'),
	url(r'^remove_dashboard_query/(?P<pk>[0-9_-]+)/', RemoveDashboardQueryFormView.as_view(), name='remove_dashboard_query'),
	url(r'^add_followup_notice/', AddFollowupNoticeFormView.as_view(), name='add_followup_notice'),
	url(r'^remove_followup_notice/(?P<pk>[0-9_-]+)/', RemoveFollowupNoticeFormView.as_view(), name='remove_followup_notice'),
	url(r'^rise_time/(?P<transient_id>[0-9]+)/(?P<obs_id>[a-zA-Z0-9_-]+)',
		view_utils.rise_time, name='rise_time'),
	url(r'^set_time/(?P<transient_id>[0-9]+)/(?P<obs_id>[a-zA-Z0-9_-]+)',
		view_utils.set_time, name='set_time'),
	url(r'^moon_angle/(?P<transient_id>[0-9]+)/(?P<obs_id>[a-zA-Z0-9_-]+)',
		view_utils.moon_angle, name='moon_angle'),
	url(r'^tonight_rise_time/(?P<transient_id>[0-9]+)/(?P<too_id>[a-zA-Z0-9_-]+)',
		view_utils.tonight_rise_time, name='tonight_rise_time'),
	url(r'^tonight_set_time/(?P<transient_id>[0-9]+)/(?P<too_id>[a-zA-Z0-9_-]+)',
		view_utils.tonight_set_time, name='tonight_set_time'),
	url(r'^tonight_moon_angle/(?P<transient_id>[0-9]+)/(?P<too_id>[a-zA-Z0-9_-]+)',
		view_utils.tonight_moon_angle, name='tonight_moon_angle'),

	url(r'^delta_too_hours/(?P<too_id>[a-zA-Z0-9_-]+)',
		view_utils.delta_too_hours, name='delta_too_hours'),

	url(r'^get_ps1_image/(?P<transient_id>[0-9]+)',
		view_utils.get_ps1_image, name='get_ps1_image'),
	url(r'^get_hst_image/(?P<transient_id>[0-9]+)',
		view_utils.get_hst_image, name='get_hst_image'),
	url(r'^get_chandra_image/(?P<transient_id>[0-9]+)',
		view_utils.get_chandra_image, name='get_chandra_image'),
	url(r'^get_legacy_image/(?P<transient_id>[0-9]+)',
		view_utils.get_legacy_image, name='get_legacy_image'),

    path('accounts/', include('django.contrib.auth.urls')),
	url(r'^explorer/', include('explorer.urls')),
	#url(r'^silk/', include('silk.urls', namespace='silk')),
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
router.register(r'webappcolors', api_views.WebAppColorViewSet)
router.register(r'units', api_views.UnitViewSet)

router.register(r'dataquality', api_views.DataQualityViewSet)

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

router.register(r'surveyfields', api_views.SurveyFieldViewSet)
router.register(r'surveyfieldmsbs', api_views.SurveyFieldMSBViewSet)
router.register(r'surveyobservations', api_views.SurveyObservationViewSet)

router.register(r'transientphotometry', api_views.TransientPhotometryViewSet, base_name='transientphotometry')
router.register(r'hostphotometry', api_views.HostPhotometryViewSet, base_name='hostphotometry')
router.register(r'transientphotdata', api_views.TransientPhotDataViewSet, base_name='transientphotdata')
router.register(r'hostphotdata', api_views.HostPhotDataViewSet, base_name='hostphotdata')

router.register(r'transientimages', api_views.TransientImageViewSet)
router.register(r'hostimages', api_views.HostImageViewSet)
router.register(r'photometricbands', api_views.PhotometricBandViewSet)
router.register(r'principalinvestigators', api_views.PrincipalInvestigatorViewSet)
router.register(r'profiles', api_views.ProfileViewSet)

router.register(r'transientspectra', api_views.TransientSpectrumViewSet, base_name='transientspectrum')
router.register(r'hostspectra', api_views.HostSpectrumViewSet, base_name='hostspectrum')
router.register(r'transientspecdata', api_views.TransientSpecDataViewSet, base_name='transientspecdata')
router.register(r'hostspecdata', api_views.HostSpecDataViewSet, base_name='hostspecdata')

router.register(r'tooresources', api_views.ToOResourceViewSet, base_name='tooresource')
router.register(r'queuedresources', api_views.QueuedResourceViewSet, base_name='queuedresource')
router.register(r'classicalresources', api_views.ClassicalResourceViewSet, base_name='classicalresource')
router.register(r'classicalobservingdates', api_views.ClassicalObservingDateViewSet, base_name='classicalobservingdate')

router.register(r'telescopes', api_views.TelescopeViewSet)
router.register(r'transients', api_views.TransientViewSet)
router.register(r'alternatetransientnames', api_views.AlternateTransientNamesViewSet)
router.register(r'users', api_views.UserViewSet)
router.register(r'groups', api_views.GroupViewSet)
router.register(r'transienttags', api_views.TransientTagViewSet)

router.register(r'gwcandidates', api_views.GWCandidateViewSet)
router.register(r'gwcandidateimages', api_views.GWCandidateImageViewSet)

# Login/Logout
api_url_patterns = [url(r'^api/', include(router.urls)),
					url(r'^api/schema/$', schema_view),
					url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),]

urlpatterns += api_url_patterns
