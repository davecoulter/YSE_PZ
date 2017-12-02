from django.db import models
from YSE_App.models.base import *
from YSE_App.models.spectra_models import *
from YSE_App.models.phot_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *
from YSE_App.models.additional_info_models import *
from YSE_App.models.followup_models import *
from YSE_App.models.observation_task_models import *

class Log(BaseModel):
	### Entity relationships ###
	# Optional
	transient = models.ForeignKey(Transient, null=True, blank=True, on_delete=models.CASCADE)
	host = models.ForeignKey(Host, null=True, blank=True, on_delete=models.CASCADE)
	host_sed = models.ForeignKey(HostSED, null=True, blank=True, on_delete=models.CASCADE)

	transient_image = models.ForeignKey(TransientImage, null=True, blank=True, on_delete=models.CASCADE)
	host_image = models.ForeignKey(HostImage, null=True, blank=True, on_delete=models.CASCADE)
	
	transient_spectrum = models.ForeignKey(TransientSpectrum, null=True, blank=True, on_delete=models.CASCADE)
	host_spectrum = models.ForeignKey(HostSpectrum, null=True, blank=True, on_delete=models.CASCADE)

	transient_photometry = models.ForeignKey(TransientPhotometry, null=True, blank=True, on_delete=models.CASCADE)
	host_photometry = models.ForeignKey(HostPhotometry, null=True, blank=True, on_delete=models.CASCADE)

	transient_web_resource = models.ForeignKey(TransientWebResource, null=True, blank=True, on_delete=models.CASCADE)
	host_web_resource = models.ForeignKey(HostWebResource, null=True, blank=True, on_delete=models.CASCADE)

	transient_observation_task = models.ForeignKey(TransientObservationTask, null=True, blank=True, on_delete=models.CASCADE)
	host_observation_task = models.ForeignKey(HostObservationTask, null=True, blank=True, on_delete=models.CASCADE)

	transient_followup = models.ForeignKey(TransientFollowup, null=True, blank=True, on_delete=models.CASCADE)
	host_followup = models.ForeignKey(HostFollowup, null=True, blank=True, on_delete=models.CASCADE)

	instrument = models.ForeignKey(Instrument, null=True, blank=True, on_delete=models.CASCADE)
	instrument_config = models.ForeignKey(InstrumentConfig, null=True, blank=True, on_delete=models.CASCADE)
	config_element = models.ForeignKey(ConfigElement, null=True, blank=True, on_delete=models.CASCADE)

	### Properties ###
	# Required
	comment = models.TextField()

	def __str__(self):
		limit = 20
		return (self.comment[:limit] + '...') if len(self.comment) > limit else self.comment