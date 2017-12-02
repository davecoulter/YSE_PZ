from django.db import models
from YSE_App.models.base import *
from YSE_App.models.telescope_models import *

class Instrument(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope, on_delete=models.CASCADE)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "Instrument: %s - %s" % (self.telescope.name, self.name)

class InstrumentConfig(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return "Config: %s - %s" % (self.instrument.name, self.name)

class ConfigElement(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

	# Optional
	instrument_config = models.ManyToManyField(InstrumentConfig, blank=True)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "Element: %s - %s" % (self.instrument.name, self.name)