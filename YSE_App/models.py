import datetime
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class BaseModel(models.Model):

	class Meta:
		abstract = True

	# Audit fields
	created_by = models.ForeignKey(User, related_name='%(class)s_created_by')
	created_date = models.DateTimeField(auto_now_add=True)
	modified_by = models.ForeignKey(User, related_name='%(class)s_modified_by')
	modified_date = models.DateTimeField(auto_now=True)

class TransientHostRank(BaseModel):
	### Properties ###
	# Required
	rank = models.IntegerField()

	def __str__(self):
		return self.rank

class Status(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class ObservationGroup(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class SEDType(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class HostMorphology(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class Phase(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class TransientClass(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class HostClass(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	
	def __str__(self):
		return self.name

class Observatory(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	utc_offset = models.IntegerField()
	tz_name = models.CharField(max_length=64)

	# Optional
	DLS_utc_offset = models.IntegerField(null=True, blank=True)
	DLS_tz_name = models.CharField(max_length=64, null=True, blank=True)
	DLS_start = models.DateTimeField(null=True, blank=True)
	DLS_end = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return self.name

class Telescope(BaseModel):
	### Entity relationships ###
	# Required
	observatory = models.ForeignKey(Observatory)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	latitude = models.FloatField()
	longitude = models.FloatField()
	elevation = models.FloatField()

	def __str__(self):
		return self.name

class Instrument(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return "%s - %s" % (self.telescope.name, self.name)

class ToO_Resource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start
	awarded_too_hours = models.FloatField()
	current_too_hours = models.FloatField()

	# Optional
	description = models.FloatField(null=True, blank=True)

	def __str__(self):
		return "ToO: %s; Active - %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class Classical_Resource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start

	# Optional
	awarded_hours = models.FloatField(null=True, blank=True)
	current_hours = models.FloatField(null=True, blank=True)
	description = models.FloatField(null=True, blank=True)

	def __str__(self):
		return "ToO: %s; Active - %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class Queued_Resource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start

	# Optional
	awarded_hours = models.FloatField(null=True, blank=True)
	current_hours = models.FloatField(null=True, blank=True)
	description = models.FloatField(null=True, blank=True)

	def __str__(self):
		return "ToO: %s; Active - %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class ClassicalObservingDate(BaseModel):
	### Entity relationships ###
	# Required
	resource = models.ForeignKey(Classical_Resource)

	### Properties ###
	# Required
	observing_night = models.DateTimeField()
	
	def __str__(self):
		return "%s - %s" % (self.resource.telescope.name, self.observing_night[0])
	def happening_soon(self):
		now = timezone.now()
		return (now + datetime.timedelta(days=14) >= self.observing_night >= now)

class QueuedObservingDate(BaseModel):
	### Entity relationships ###
	# Required
	resource = models.ForeignKey(Queued_Resource)

	### Properties ###
	# Required
	observing_night = models.DateTimeField()
	
	def __str__(self):
		return "%s - %s" % (resource.telescope.name, observing_night[0])
	def happening_soon(self):
		now = timezone.now()
		return (now + datetime.timedelta(days=14) >= self.observing_night >= now)

class InstrumentConfig(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return "%s - %s" % (self.instrument.name, self.name)

class ConfigElement(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)

	# Optional
	instrument_config = models.ManyToManyField(InstrumentConfig, null=True, blank=True)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "%s - %s" % (self.instrument.name, self.name)

class PhotometricBand(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	lambda_eff = models.CharField(max_length=64)

	# Optional
	throughput_file = models.CharField(max_length=512, null=True, blank=True)
	
	def __str__(self):
		return '%s - %s' % (self.instrument.name, self.name)

class Host(BaseModel):
	### Entity relationships ###
	# Optional
	host_morphology = models.ForeignKey(HostMorphology, null=True, blank=True)
	host_class = models.ForeignKey(HostClass, null=True, blank=True)
	band_sextract = models.ForeignKey(PhotometricBand, null=True, blank=True)
	best_spec = models.ForeignKey('Spectrum', related_name='+', null=True, blank=True)
	transient_host_rank = models.ForeignKey(TransientHostRank, null=True, blank=True)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	ra = models.FloatField()
	dec = models.FloatField()

	# Optional
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	r_a = models.FloatField(null=True, blank=True)
	r_b = models.FloatField(null=True, blank=True)
	theta = models.FloatField(null=True, blank=True)
	eff_offset = models.FloatField(null=True, blank=True)
	photo_z = models.FloatField(null=True, blank=True)
	photo_z_err = models.FloatField(null=True, blank=True)
	photo_z_source = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class Transient(BaseModel):
	### Entity relationships ###
	# Required
	status = models.ForeignKey(Status)
	obs_group = models.ForeignKey(ObservationGroup)

	# Optional
	non_detect_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	best_spec_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	photo_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	best_spectrum = models.ForeignKey('Spectrum', related_name='+', null=True, blank=True)
	best_host = models.ForeignKey('Host', related_name='+', null=True, blank=True)
	abs_mag_peak_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	host = models.ManyToManyField(Host, null=True, blank=True) # To hold n hosts -- if we don't quite know which is the correct one

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	ra = models.FloatField()
	dec = models.FloatField()
	disc_date = models.DateTimeField()

	# Optional
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_source = models.CharField(max_length=64, null=True, blank=True)
	non_detect_date = models.DateTimeField(null=True, blank=True)
	non_detect_limit = models.FloatField(null=True, blank=True)
	mw_ebv = models.FloatField(null=True, blank=True)
	abs_mag_peak = models.FloatField(null=True, blank=True)
	abs_mag_peak_date = models.DateTimeField(null=True, blank=True)
	postage_stamp_file = models.CharField(max_length=512, null=True, blank=True)

	def __str__(self):
		return self.name

class Followup(BaseModel):
	### Entity relationships ###
	# Required; Followup can be for a transient or a host, so these are nullable even though at least one is required
	status = models.ForeignKey(Status)
	transient = models.ForeignKey(Transient, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)

	# Optional
	too_resource = models.ForeignKey(ToO_Resource, null=True, blank=True)
	classical_resource = models.ForeignKey(Classical_Resource, null=True, blank=True)
	queued_resource = models.ForeignKey(Queued_Resource, null=True, blank=True)

	### Properties ###
	# Required
	valid_start = models.DateTimeField()
	valid_stop = models.DateTimeField()

	# Optional
	spec_priority = models.IntegerField(null=True, blank=True)
	phot_priority = models.IntegerField(null=True, blank=True)
	offset_star_ra = models.FloatField(null=True, blank=True)
	offset_star_dec = models.FloatField(null=True, blank=True)
	offset_north = models.FloatField(null=True, blank=True)
	offset_east = models.FloatField(null=True, blank=True)

	def __str__(self):
		return self.name

class ObservationTask(BaseModel):
	### Entity relationships ###
	# Required
	followup = models.ForeignKey(Followup)
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

	def __str__(self):
		return "%s - %s - %s - %s" % (self.followup.transient.name, 
							self.instrument_config.instrument.name,
							self.instrument_config.name,
							self.obs_window_start.strftime('%Y/%m/%d'))

class Spectrum(BaseModel):
	### Entity relationships ###
	# Required
	instrument = models.ForeignKey(Instrument)
	transient = models.ForeignKey(Transient)
	obs_group = models.ForeignKey(ObservationGroup)

	# Optional
	spec_phase = models.ForeignKey(Phase, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)
	followup = models.ForeignKey(Followup, null=True, blank=True) # Can by null if data is from external source

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
	snid_plot_file = models.CharField(max_length=512, null=True, blank=True)
	spec_plot_file = models.CharField(max_length=512, null=True, blank=True)
	spec_data_file = models.CharField(max_length=512, null=True, blank=True)

class Photometry(BaseModel):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)
	instrument = models.ForeignKey(Instrument)
	obs_group = models.ForeignKey(ObservationGroup)

	# Optional
	host = models.ForeignKey(Host, null=True, blank=True)
	followup = models.ForeignKey(Followup, null=True, blank=True) # Can by null if data is from external source

# Where did we get it? e.g. ATel, TNS, PS1, etc
class InformationSource(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

class WebResource(BaseModel):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)
	information_source = models.ForeignKey(InformationSource)

	### Properties ###
	# Required 
	information_text = models.TextField()
	url = models.CharField(max_length=512)

class AlternateTransientNames(BaseModel):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)
	obs_group = models.ForeignKey(ObservationGroup)
	
	### Properities ###
	# Required
	name = models.CharField(max_length=64)

class SpecData(BaseModel):
	### Entity relationships ###
	# Required
	spectrum = models.ForeignKey(Spectrum)

	### Properties ###
	# Required
	wavelength = models.FloatField()
	flux = models.FloatField()
	flux_err = models.FloatField()

	# Optional
	wavelength_err = models.FloatField(null=True, blank=True)

class PhotData(BaseModel):
	# Entity relationships ###
	# Required
	photometry = models.ForeignKey(Photometry)
	band = models.ForeignKey(PhotometricBand)

	### Properties ###
	# Required
	obs_date = models.DateTimeField()

	# Optional
	# Phot could be either flux or mag, so leaving both optional
	flux = models.FloatField(null=True, blank=True)
	flux_err = models.FloatField(null=True, blank=True)
	mag = models.FloatField(null=True, blank=True)
	mag_err = models.FloatField(null=True, blank=True)
	forced = models.NullBooleanField(null=True, blank=True)
	dq = models.NullBooleanField(null=True, blank=True)

class Image(BaseModel):
	### Entity relationships ###
	# Required
	phot_data = models.ForeignKey(PhotData)

	### Properties ###
	# Required
	img_file = models.CharField(max_length=512)

	# Optional
	zero_point = models.FloatField(null=True, blank=True)
	zero_point_err = models.FloatField(null=True, blank=True)
	sky = models.FloatField(null=True, blank=True)
	sky_rms = models.FloatField(null=True, blank=True)
	dcmp_file = models.TextField(null=True, blank=True)

class HostSED(BaseModel):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host)
	sed_type = models.ForeignKey(SEDType)

	### Properties ###
	# Optional
	metalicity = models.FloatField(null=True, blank=True)
	metalicity_err = models.FloatField(null=True, blank=True)
	log_SFR = models.FloatField(null=True, blank=True)
	log_SFR_err = models.FloatField(null=True, blank=True)
	log_sSFR = models.FloatField(null=True, blank=True)
	log_sSFR_err = models.FloatField(null=True, blank=True)
	log_mass = models.FloatField(null=True, blank=True)
	log_mass_err = models.FloatField(null=True, blank=True)
	ebv = models.FloatField(null=True, blank=True)
	ebv_err = models.FloatField(null=True, blank=True)
	log_age = models.FloatField(null=True, blank=True)
	log_age_err = models.FloatField(null=True, blank=True)
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	fit_chi2 = models.FloatField(null=True, blank=True)
	fit_n = models.IntegerField(null=True, blank=True)
	fit_plot_file = models.TextField(null=True, blank=True)

class Log(BaseModel):
	### Entity relationships ###
	# Optional
	transient = models.ForeignKey(Transient, null=True, blank=True)
	image = models.ForeignKey(Image, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)
	host_sed = models.ForeignKey(HostSED, null=True, blank=True)
	spectrum = models.ForeignKey(Spectrum, null=True, blank=True)
	photometry = models.ForeignKey(Photometry, null=True, blank=True)
	web_resource = models.ForeignKey(WebResource, null=True, blank=True)
	observation_task = models.ForeignKey(ObservationTask, null=True, blank=True)
	followup = models.ForeignKey(Followup, null=True, blank=True)
	instrument = models.ForeignKey(Instrument, null=True, blank=True)
	instrument_config = models.ForeignKey(InstrumentConfig, null=True, blank=True)
	config_element = models.ForeignKey(ConfigElement, null=True, blank=True)

	### Properties ###
	# Required
	comment = models.TextField()