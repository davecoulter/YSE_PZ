from django.db import models
from django.forms import ModelForm
from django import forms
from YSE_App.models import *
from YSE_App import view_utils
from django.utils import timezone
from datetime import timedelta

class TransientForm(ModelForm):
	class Meta:
		model = Transient
		fields = [
			'status', 
			'obs_group', 
			'non_detect_band',
			'best_spec_class',
			'best_spectrum',
			'host',
			'abs_mag_peak_band',
			'host',
			'name',
			'ra',
			'dec',
			'disc_date',
			'candidate_hosts',
			'redshift',
			'redshift_err',
			'redshift_source',
			'non_detect_date',
			'non_detect_limit',
			'mw_ebv',
			'abs_mag_peak',
			'abs_mag_peak_date',
			'postage_stamp_file']

class TransientFollowupForm(ModelForm):
	status = forms.ModelChoiceField(
		FollowupStatus.objects.all(),
		initial=FollowupStatus.objects.filter(name='Requested')[0])
	qs = ClassicalResource.objects.filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('end_date_valid').select_related()
	if len(qs):
		classical_resource = forms.ModelChoiceField(
			queryset=qs,
			initial=qs[0],
			required=False)
		valid_start = forms.DateTimeField(initial=qs[0].begin_date_valid)
		valid_stop = forms.DateTimeField(initial=qs[0].end_date_valid)
	else:
		classical_resource = forms.ModelChoiceField(
			queryset=qs,
			required=False)
		valid_start = forms.DateTimeField()
		valid_stop = forms.DateTimeField()
	comment = forms.CharField(required=False)

	class Meta:
		model = TransientFollowup
		fields = [
			'status', 
			'too_resource',
			'classical_resource',
			'queued_resource',
			'comment',
			'valid_start',
			'valid_stop',
			'spec_priority',
			'phot_priority',
			'offset_star_ra',
			'offset_star_dec',
			'offset_north',
			'offset_east',
			'transient']

class ClassicalResourceForm(ModelForm):

	observing_date = forms.DateTimeField()
	
	class Meta:
		model = ClassicalResource
		fields = [
			'telescope',
			'principal_investigator']

class ToOResourceForm(ModelForm):

	awarded_too_hours = forms.FloatField(initial=0)
	used_too_hours = forms.FloatField(initial=0)
	awarded_too_triggers = forms.FloatField(initial=0)
	used_too_triggers = forms.FloatField(initial=0)
	
	class Meta:
		model = ToOResource
		fields = [
			'telescope',
			'principal_investigator',
			'begin_date_valid',
			'end_date_valid',
			'awarded_too_hours',
			'used_too_hours',
			'awarded_too_triggers',
			'used_too_triggers']
		
class SurveyFieldForm(ModelForm):

	valid_start = forms.DateTimeField()
	valid_stop = forms.DateTimeField()
	coord = forms.CharField()
	qs = Instrument.objects.filter(name__startswith = 'GPC').select_related()
	if len(qs):
		instrument = forms.ModelChoiceField(
			queryset=qs,
			initial=qs[0],
			required=False)
	
	class Meta:
		model = SurveyField
		fields = ['field_id',
				  'cadence',
				  'ztf_field_id',
				  'instrument']
		
class SurveyObsForm(ModelForm):

	survey_obs_date = forms.DateTimeField()
	#import pdb; pdb.set_trace()
	qs = [(i['ztf_field_id'], i['ztf_field_id']) for i in SurveyField.objects.all().values('ztf_field_id').distinct().order_by('ztf_field_id')]

	if len(qs):
		ztf_field_id = forms.MultipleChoiceField(
			choices=qs,
			initial=qs[0],
			required=True)
	else:
		ztf_field_id = forms.MultipleChoiceField(
			choices=[],
			required=True)

	class Meta:
		model = SurveyObservation
		fields = ['survey_obs_date','ztf_field_id']

		
class OncallForm(ModelForm):

	valid_start = forms.DateTimeField()
	valid_stop = forms.DateTimeField()
	qs = User.objects.all().filter(groups__name='YSE').filter(~Q(username='admin')).order_by('username')
	if len(qs):
		user = forms.ModelChoiceField(
			queryset=qs,
			initial=qs[0],
			required=False)
	
	class Meta:
		model = YSEOnCallDate
		fields = [] #['field_id',
		#		  'cadence',
		#		  'ztf_field_id',
		#		  'instrument']

		
		
class TransientCommentForm(ModelForm):
	class Meta:
		model = Log
		fields = [
			'comment',
			'transient']

		
class TransientObservationTaskForm(ModelForm):
	class Meta:
		model = TransientObservationTask
		fields = [
			'status',
			'instrument_config',
			'exposure_time',
			'number_of_exposures',
			'desired_obs_date',
			'actual_obs_date',
			'description',
			'followup']

class QueryModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.__unicode__

class AddDashboardQueryForm(ModelForm):
	query = QueryModelChoiceField(Query.objects.all())

	class Meta:
		model = UserQuery
		fields = [
			'query']

class RemoveDashboardQueryForm(ModelForm):
	query = QueryModelChoiceField(Query.objects.all())

	class Meta:
		model = UserQuery
		fields = [
			'id']

class AddFollowupNoticeForm(ModelForm):
	telescope = QueryModelChoiceField(Telescope.objects.all())
	#import pdb; pdb.set_trace()
	class Meta:
		model = UserTelescopeToFollow
		fields = ['telescope']
	#		'id']

class RemoveFollowupNoticeForm(ModelForm):
	telescope = QueryModelChoiceField(Telescope.objects.all())

	class Meta:
		model = UserTelescopeToFollow
		fields = [
			'id']

		
class SpectrumUploadForm(ModelForm):
	filename = forms.FileField()
	obs_date = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'])
	obs_group = forms.ModelChoiceField(
		ObservationGroup.objects.filter(Q(name='SSS') | Q(name='Foundation') |
										Q(name='TESS') | Q(name='YSE') |
										Q(name='UCSC') |
										Q(name='Other')))
	spec_instruments = [
		'SED-Machine','P200-TSPEC',
		'LFC','DBSP','lay - MIKE','lay - LDSS-3',
		'aade - MagE','aade - Boller & Chivens',
		'WFC3','STIS','IRS','B&C-Asi-1.22m',
		'aade - IMACS','lay - LDSS-2','AFOSC',
		'uPont - Mod-spec','uPont - B&C-duPont',
		'uPont - WFCCD','V-grism','UV-grism',
		'T2 - X-Shooter','.2m - EFOSC-2.2','TT - Sofi',
		'TT - EFOSC2-NTT','TT - EMMI','.6m - EFOSC2-3.6',
		'OSIRIS','FLOYDS-N','FLOYDS-S','NIRC2',
		'NIRSPEC','NIRES','KCWI','ESI',
		'DEIMOS','OSIRIS','MOSFIRE','LRIS',
		'HIRES','GMOS','Goodman','KAST','WiFeS']
	instrument = forms.ModelChoiceField(Instrument.objects.filter(Q(name__in=spec_instruments)))
	#import pdb; pdb.set_trace()
	class Meta:
		model = TransientSpectrum
		fields = ('transient','ra',
				  'dec','spec_phase')#,'obs_group','instrument')
