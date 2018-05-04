from django.db import models
from YSE_App.models.base import *
from YSE_App.models.instrument_models import *

class PhotometricBand(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	lambda_eff = models.CharField(max_length=64, null=True, blank=True)
	throughput_file = models.CharField(max_length=512, null=True, blank=True)
	
	def __str__(self):
		return 'Band: %s - %s' % (self.instrument.name, self.name)

	def natural_key(self):
		return '%s - %s'% (self.instrument.name, self.name)
