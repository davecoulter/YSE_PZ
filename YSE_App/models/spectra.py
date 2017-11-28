from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enums import *
from YSE_App.models.instrument_models import *
from YSE_App.models.followup_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *

class Spectrum(BaseModel):
	class Meta:
		abstract = True

	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)
	obs_group = models.ForeignKey(ObservationGroup)

	### Properties ###
	# Required
	ra = models.FloatField()
	dec = models.FloatField()
	obs_date = models.DateTimeField()

	# Optional
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_quality = models.NullBooleanField(blank=True)
	tdr = models.FloatField(null=True, blank=True)
	spec_plot_file = models.CharField(max_length=512, null=True, blank=True)
	spec_data_file = models.CharField(max_length=512, null=True, blank=True)
	spectrum_notes = models.TextField(null=True, blank=True)

class TransientSpectrum(Spectrum):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)

	# Optional
	followup = models.ForeignKey(TransientFollowup, null=True, blank=True) # Can by null if data is from external source
	spec_phase = models.ForeignKey(Phase, null=True, blank=True)
	snid_plot_file = models.CharField(max_length=512, null=True, blank=True)

class HostSpectrum(Spectrum):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host)

	# Optional
	followup = models.ForeignKey(HostFollowup, null=True, blank=True) # Can by null if data is from external source

class SpecData(BaseModel):
	### Properties ###
	# Required
	wavelength = models.FloatField()
	flux = models.FloatField()

	# Optional
	wavelength_err = models.FloatField(null=True, blank=True)
	flux_err = models.FloatField(null=True, blank=True)

class TransientSpecData(SpecData):
	### Entity relationships ###
	# Required
	spectrum = models.ForeignKey(TransientSpectrum)

class HostSpecData(SpecData):
	### Entity relationships ###
	# Required
	spectrum = models.ForeignKey(HostSpectrum)