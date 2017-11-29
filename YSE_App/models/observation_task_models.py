from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.instrument_models import *
from YSE_App.models.followup_models import *

class ObservationalTask(BaseModel):
	class Meta:
		abstract = True

	instrument_config = models.ForeignKey(InstrumentConfig)
	status = models.ForeignKey(Status)

	### Properties ###
	# Required
	exposure_time = models.FloatField()
	number_of_exposures = models.IntegerField()
	desired_obs_date = models.DateTimeField()

	# Optional
	actual_obs_date = models.DateTimeField(null=True, blank=True)
	description = models.TextField(null=True, blank=True)

class TransientObservationTask(ObservationalTask):
	### Entity relationships ###
	# Required
	followup = models.ForeignKey(TransientFollowup)
	
	def __str__(self):
		return "%s; %s; %s; %s to %s" % (self.followup.transient.name, 
							self.instrument_config.instrument.name,
							self.instrument_config.name,
							self.followup.valid_start[0],
							self.followup.valid_stop[0])

class HostObservationTask(ObservationalTask):
	### Entity relationships ###
	# Required
	followup = models.ForeignKey(HostFollowup)
	
	def __str__(self):
		return "%s; %s; %s; %s to %s" % (self.followup.host.name, 
							self.instrument_config.instrument.name,
							self.instrument_config.name,
							self.followup.valid_start[0],
							self.followup.valid_stop[0])