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