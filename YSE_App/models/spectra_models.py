from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.instrument_models import *
from YSE_App.models.followup_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *
from django.contrib.auth.models import Group

class Spectrum(BaseModel):
	class Meta:
		abstract = True

	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
	obs_group = models.ForeignKey(ObservationGroup, on_delete=models.CASCADE)

	# Optional
	unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.CASCADE)
	data_quality = models.ForeignKey(DataQuality, null=True, blank=True, on_delete=models.CASCADE)
	
	### Properties ###
	# Required
	ra = models.FloatField()
	dec = models.FloatField()
	obs_date = models.DateTimeField()
	# Optional
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_quality = models.NullBooleanField(blank=True)
	spec_plot_file = models.CharField(max_length=512, null=True, blank=True)
	spec_data_file = models.CharField(max_length=512, null=True, blank=True)
	spectrum_notes = models.TextField(null=True, blank=True)

	groups = models.ManyToManyField(Group, blank=True)

class TransientSpectrum(Spectrum):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)
	# Optional
	followup = models.ForeignKey(TransientFollowup, null=True, blank=True, on_delete=models.SET_NULL) # Can by null if data is from external source
	spec_phase = models.FloatField(null=True, blank=True)

	### Properties ###
	# Optional
	rlap = models.FloatField(null=True, blank=True)
	snid_plot_file = models.CharField(max_length=512, null=True, blank=True)

	def __str__(self):
		return 'Spectrum: %s - %s' % (self.transient.name, self.obs_date.strftime('%m/%d/%Y'))

class HostSpectrum(Spectrum):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host, on_delete=models.CASCADE)
	# Optional
	followup = models.ForeignKey(HostFollowup, null=True, blank=True, on_delete=models.SET_NULL) # Can by null if data is from external source

	### Properties ###
	# Optional
	tdr = models.FloatField(null=True, blank=True)

	def __str__(self):
		return 'Spectrum: %s - %s' % (self.host.HostString(), self.obs_date.strftime('%m/%d/%Y'))


class SpecData(BaseModel):
	class Meta:
		abstract = True
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
	spectrum = models.ForeignKey(TransientSpectrum, on_delete=models.CASCADE)

	def __str__(self):
		return '%s - %s' % (self.wavelength, self.flux)

class HostSpecData(SpecData):
	### Entity relationships ###
	# Required
	spectrum = models.ForeignKey(HostSpectrum, on_delete=models.CASCADE)

	def __str__(self):
		return '%s - %s' % (self.wavelength, self.flux)
