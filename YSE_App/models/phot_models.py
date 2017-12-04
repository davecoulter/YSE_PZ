from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.instrument_models import *
from YSE_App.models.followup_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *

class Photometry(BaseModel):

	class Meta:
		abstract = True

	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
	obs_group = models.ForeignKey(ObservationGroup, on_delete=models.CASCADE)

class TransientPhotometry(Photometry):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)

	# Optional
	host = models.ForeignKey(Host, null=True, blank=True, on_delete=models.SET_NULL)
	followup = models.ForeignKey(TransientFollowup, null=True, blank=True, on_delete=models.SET_NULL) # Can by null if data is from external source

	def __str__(self):
		return 'Transient Phot: %s' % (self.transient.name)

class HostPhotometry(Photometry):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host, on_delete=models.CASCADE)

	# Optional
	followup = models.ForeignKey(HostFollowup, null=True, blank=True, on_delete=models.SET_NULL) # Can by null if data is from external source

	def __str__(self):
		return 'Host Phot: %s ' % (self.host.HostString())

class PhotData(BaseModel):

	class Meta:
		abstract = True

	# Entity relationships ###
	# Required
	band = models.ForeignKey(PhotometricBand, on_delete=models.CASCADE)

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
	photometry = models.ForeignKey(TransientPhotometry, on_delete=models.CASCADE)

	def __str__(self):
		return '%s - %s - %s' % (self.photometry.transient.name, self.band.name, self.obs_date)

class HostPhotData(PhotData):
	# Entity relationships ###
	# Required
	photometry = models.ForeignKey(HostPhotometry, on_delete=models.CASCADE)

	def __str__(self):
		return '%s - %s - %s' % (self.photometry.host.HostString(), self.band.name, self.obs_date.strftime('%m/%d/%Y'))

class Image(BaseModel):
	class Meta:
		abstract = True

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
	phot_data = models.ForeignKey(TransientPhotData, on_delete=models.CASCADE)

	def __str__(self):
		return 'Img: %s - %s' % (self.phot_data.photometry.transient.name, self.phot_data.obs_date.strftime('%m/%d/%Y'))

class HostImage(Image):
	### Entity relationships ###
	# Required
	phot_data = models.ForeignKey(HostPhotData, on_delete=models.CASCADE)

	def __str__(self):
		return 'Img: %s - %s' % (self.phot_data.photometry.host.HostString(), self.phot_data.obs_date.strftime('%m/%d/%Y'))
