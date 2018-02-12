from django.db import models
from django.forms import ModelForm
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
