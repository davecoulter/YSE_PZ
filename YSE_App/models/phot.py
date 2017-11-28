from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enums import *
from YSE_App.models.instrument_models import *
from YSE_App.models.followup_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *

class Photometry(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)
	obs_group = models.ForeignKey(ObservationGroup)

class TransientPhotometry(Photometry):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)

	# Optional
	host = models.ForeignKey(Host, null=True, blank=True)
	followup = models.ForeignKey(TransientFollowup, null=True, blank=True) # Can by null if data is from external source

class HostPhotometry(Photometry):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host)

	# Optional
	followup = models.ForeignKey(HostFollowup, null=True, blank=True) # Can by null if data is from external source

class PhotData(BaseModel):
	# Entity relationships ###
	# Required
	band = models.ForeignKey(PhotometricBand)

	### Properties ###
	# Required
	obs_date = models.DateTimeField()

	# Optional
	# Phot could be either flux or mag, so leaving both optional
	flux_zero_point = models.FloatField(null=True, blank=True)
	flux = models.FloatField(null=True, blank=True)
	flux_err = models.FloatField(null=True, blank=True)
	mag = models.FloatField(null=True, blank=True)
	mag_err = models.FloatField(null=True, blank=True)
	forced = models.NullBooleanField(null=True, blank=True)
	dq = models.NullBooleanField(null=True, blank=True)

class TransientPhotData(PhotData):
	# Entity relationships ###
	# Required
	photometry = models.ForeignKey(TransientPhotometry)

class HostPhotData(PhotData):
	# Entity relationships ###
	# Required
	photometry = models.ForeignKey(HostPhotometry)

class Image(BaseModel):
	### Properties ###
	# Optional
	img_file = models.CharField(max_length=512, null=True, blank=True)
	zero_point = models.FloatField(null=True, blank=True)
	zero_point_err = models.FloatField(null=True, blank=True)
	sky = models.FloatField(null=True, blank=True)
	sky_rms = models.FloatField(null=True, blank=True)
	dcmp_file = models.TextField(null=True, blank=True)

class TransientImage(Image):
	### Entity relationships ###
	# Required
	phot_data = models.ForeignKey(TransientPhotData)

class HostImage(Image):
	### Entity relationships ###
	# Required
	phot_data = models.ForeignKey(HostPhotData)