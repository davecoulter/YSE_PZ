from django.db import models
from YSE_App.models.base import *
from YSE_App.models.spectra import *
from YSE_App.models.phot import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *
from YSE_App.models.additional_info import *
from YSE_App.models.followup_models import *
from YSE_App.models.observation_tasks import *

class Log(BaseModel):
	### Entity relationships ###
	# Optional
	transient = models.ForeignKey(Transient, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)
	host_sed = models.ForeignKey(HostSED, null=True, blank=True)

	transient_image = models.ForeignKey(TransientImage, null=True, blank=True)
	host_image = models.ForeignKey(HostImage, null=True, blank=True)
	
	transient_spectrum = models.ForeignKey(TransientSpectrum, null=True, blank=True)
	host_spectrum = models.ForeignKey(HostSpectrum, null=True, blank=True)

	transient_photometry = models.ForeignKey(TransientPhotometry, null=True, blank=True)
	host_photometry = models.ForeignKey(HostPhotometry, null=True, blank=True)

	transient_web_resource = models.ForeignKey(TransientWebResource, null=True, blank=True)
	host_web_resource = models.ForeignKey(HostWebResource, null=True, blank=True)

	transient_observation_task = models.ForeignKey(TransientObservationTask, null=True, blank=True)
	host_observation_task = models.ForeignKey(HostObservationTask, null=True, blank=True)

	transient_followup = models.ForeignKey(TransientFollowup, null=True, blank=True)
	host_followup = models.ForeignKey(HostFollowup, null=True, blank=True)

	instrument = models.ForeignKey(Instrument, null=True, blank=True)
	instrument_config = models.ForeignKey(InstrumentConfig, null=True, blank=True)
	config_element = models.ForeignKey(ConfigElement, null=True, blank=True)

	### Properties ###
	# Required
	comment = models.TextField()