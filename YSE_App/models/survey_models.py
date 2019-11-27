from django.db import models
from django.db.models import Q
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.photometric_band_models import *
from YSE_App.models.host_models import *
from YSE_App.models.tag_models import *
from YSE_App.common.utilities import GetSexigesimalString
from YSE_App.common.alert import IsK2Pixel, SendTransientAlert
from YSE_App.common.thacher_transient_search import thacher_transient_search
from YSE_App.common.tess_obs import tess_obs
from YSE_App.common.utilities import date_to_mjd
from YSE_App import models as yse_models
from django.dispatch import receiver
from pytz import timezone

class SurveyField(BaseModel):

	obs_group = models.ForeignKey(ObservationGroup, on_delete=models.CASCADE)
	field_id = models.CharField(max_length=64)
	#first_mjd = models.FloatField(null=True, blank=True)
	#last_mjd = models.FloatField(null=True, blank=True)
	cadence = models.FloatField(null=True, blank=True)
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
	ztf_field_id = models.CharField(max_length=64,null=True,blank=True)
	
	# field center
	ra_cen = models.FloatField()
	dec_cen = models.FloatField()

	# width, height
	width_deg = models.FloatField()
	height_deg = models.FloatField()

	def __str__(self):
		return self.field_id

	def CoordString(self):
		return GetSexigesimalString(self.ra_cen, self.dec_cen)
	
class SurveyObservation(BaseModel):

	mjd_requested = models.FloatField(null=True,blank=True)
	obs_mjd = models.FloatField(null=True, blank=True)
	survey_field = models.ForeignKey(SurveyField, on_delete=models.CASCADE)
	status = models.ForeignKey(TaskStatus, models.SET(get_sentinel_taskstatus))
	#requested_exposure_time = models.FloatField()
	#requested_photometric_band = models.ForeignKey(PhotometricBand, on_delete=models.CASCADE)
	#status = models.ForeignKey(TaskStatus, models.SET(get_sentinel_taskstatus))
	#instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
	exposure_time = models.FloatField()
	photometric_band = models.ForeignKey(PhotometricBand, on_delete=models.CASCADE)
	pos_angle_deg = models.FloatField(null=True, blank=True)
	fwhm_major = models.FloatField(null=True, blank=True)
	eccentricity = models.FloatField(null=True, blank=True)
	airmass = models.FloatField(null=True, blank=True)
	image_id = models.CharField(max_length=128,null=True,blank=True)
	mag_lim = models.FloatField(null=True, blank=True)
	zpt_obs = models.FloatField(null=True, blank=True)
	quality = models.IntegerField(null=True, blank=True)
	n_good_skycell = models.IntegerField(null=True, blank=True)
	
	def __str__(self):
		if self.obs_mjd:
			return '%s: %s'%(
				self.survey_field.field_id,self.obs_mjd)
		else:
			return '%s: %s'%(
				self.survey_field.field_id,self.mjd_requested)

#class SurveyObservation(BaseModel):

#	obs_mjd = models.FloatField(null=True, blank=True)
#	survey_observation_task = models.ForeignKey(SurveyObservationTask, on_delete=models.CASCADE)
#	status = models.ForeignKey(TaskStatus, models.SET(get_sentinel_taskstatus))
#	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
#	exposure_time = models.FloatField()
#	photometric_band = models.ForeignKey(PhotometricBand, on_delete=models.CASCADE)
#	pos_angle_deg = models.FloatField()
#	fwhm = models.FloatField(null=True, blank=True)
#	eccentricity = models.FloatField(null=True, blank=True)
#	airmass = models.FloatField(null=True, blank=True)
#	image_id = models.BigIntegerField()
	
#	def __str__(self):
#		return '%s: %s - %s'%(
#			self.survey_observation_task,self.obs_mjd)
