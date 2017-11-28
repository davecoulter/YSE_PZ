from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enums import *
from YSE_App.models.photometric_band import *
from YSE_App.models.host_models import *

class Transient(BaseModel):
	### Entity relationships ###
	# Required
	status = models.ForeignKey(Status)
	obs_group = models.ForeignKey(ObservationGroup)

	# Optional
	non_detect_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	best_spec_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	photo_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	best_spectrum = models.ForeignKey('TransientSpectrum', related_name='+', null=True, blank=True)
	best_host = models.ForeignKey('Host', related_name='+', null=True, blank=True)
	abs_mag_peak_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	host = models.ManyToManyField(Host, blank=True) # To hold n hosts -- if we don't quite know which is the correct one

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	ra = models.FloatField()
	dec = models.FloatField()
	disc_date = models.DateTimeField()

	# Optional
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_source = models.CharField(max_length=64, null=True, blank=True)
	non_detect_date = models.DateTimeField(null=True, blank=True)
	non_detect_limit = models.FloatField(null=True, blank=True)
	mw_ebv = models.FloatField(null=True, blank=True)
	abs_mag_peak = models.FloatField(null=True, blank=True)
	abs_mag_peak_date = models.DateTimeField(null=True, blank=True)
	postage_stamp_file = models.CharField(max_length=512, null=True, blank=True)

	def __str__(self):
		return self.name

# Alternate Host names?
class AlternateTransientNames(BaseModel):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)

	# Optional
	obs_group = models.ForeignKey(ObservationGroup, null=True, blank=True)
	
	### Properities ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	description = models.TextField(null=True, blank=True)