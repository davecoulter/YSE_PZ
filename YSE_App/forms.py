from django.db import models
from django.forms import ModelForm
from django import forms
from YSE_App.models import *

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
	class Meta:
		model = TransientFollowup
		fields = [
			'status', 
			'too_resource',
			'classical_resource',
			'queued_resource',
			'valid_start',
			'valid_stop',
			'spec_priority',
			'phot_priority',
			'offset_star_ra',
			'offset_star_dec',
			'offset_north',
			'offset_east',
			'transient']

		
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
