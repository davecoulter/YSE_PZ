from datetime import datetime

from django.db import models

# Create your models here.
class TransientHostRank(models.Model):
	rank = models.IntegerField()

	def __str__(self):
		return self.rank

class ObservationGroup(models.Model): # New
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class SEDType(models.Model):
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class HostMorphology(models.Model):
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class Phase(models.Model): # New
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class TransientClass(models.Model):
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class HostClass(models.Model): # New
	name = models.CharField(max_length=64)
	
	def __str__(self):
		return self.name

class Observatory(models.Model):
	name = models.CharField(max_length=64)
	latitude = models.FloatField() # New
	longitude = models.FloatField()
	altitude = models.FloatField()

	def __str__(self):
		return self.name

class Telescope(models.Model):
	name = models.CharField(max_length=64)
	observatory = models.ForeignKey(Observatory)
	too_hours = models.FloatField(null=True, blank=True)
	observing_nights = models.FloatField(null=True, blank=True)

	def __str__(self):
		return self.name

class ObservingNightDates(models.Model):
	observing_night = models.DateTimeField()
	telescope = models.ForeignKey(Telescope)

	def __str__(self):
		return datetime.strptime(self.observing_night, "%m/%d/%Y") 

class Instrument(models.Model):
	name = models.CharField(max_length=64)
	telescope = models.ForeignKey(Telescope)

	def __str__(self):
		return self.name

class PhotometricBand(models.Model):
	name = models.CharField(max_length=64)
	lambda_eff = models.CharField(max_length=64)
	throughput_file = models.TextField(null=True, blank=True)
	telescope = models.ForeignKey(Telescope)

	def __str__(self):
		return '%s - %s' % (self.telescope.name, self.name)

class Image(models.Model):
	band = models.ForeignKey(PhotometricBand)
	zero_point = models.FloatField(null=True, blank=True)
	zero_point_err = models.FloatField(null=True, blank=True)
	sky = models.FloatField(null=True, blank=True)
	sky_rms = models.FloatField(null=True, blank=True)
	img_file = models.TextField()
	dcmp_file = models.TextField(null=True, blank=True)

class Transient(models.Model):
	name = models.CharField(max_length=64)
	obs_group = models.ForeignKey(ObservationGroup)
	ra = models.FloatField()
	dec = models.FloatField()
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_source = models.CharField(max_length=64, null=True, blank=True)
	disc_date = models.DateTimeField()
	date_modified = models.DateTimeField(auto_now=True)
	best_spec_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	photo_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True)
	non_detect_date = models.DateTimeField(null=True, blank=True)
	non_detect_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	non_detect_limit = models.FloatField(null=True, blank=True)
	best_spectrum = models.ForeignKey('Spectrum', related_name='+', null=True, blank=True)
	best_host = models.ForeignKey('Host', related_name='+', null=True, blank=True)
	mw_ebv = models.FloatField(null=True, blank=True)
	abs_mag_peak = models.FloatField(null=True, blank=True)
	abs_mag_peak_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True)
	abs_mag_peak_date = models.DateTimeField(null=True, blank=True)
	postage_stamp_file = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name

class Host(models.Model):
	transient = models.ManyToManyField(Transient) # Different
	name = models.CharField(max_length=64, null=True)
	ra = models.FloatField()
	dec = models.FloatField()
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	host_morphology = models.ForeignKey(HostMorphology, null=True, blank=True)
	host_class = models.ForeignKey(HostClass, null=True, blank=True)
	r_a = models.FloatField(null=True, blank=True)
	r_b = models.FloatField(null=True, blank=True)
	theta = models.FloatField(null=True, blank=True)
	band_sextract = models.ForeignKey(PhotometricBand, null=True, blank=True)
	best_spec = models.ForeignKey('Spectrum', related_name='+', null=True, blank=True)
	eff_offset = models.FloatField(null=True, blank=True)
	photo_z = models.FloatField(null=True, blank=True)
	photo_z_err = models.FloatField(null=True, blank=True)
	photo_z_source = models.CharField(max_length=64)
	transient_host_rank = models.ForeignKey(TransientHostRank, null=True, blank=True) # Modified to enforce uniqueness

	def __str__(self):
		return self.name

class Spectrum(models.Model):
	instrument = models.ForeignKey(Instrument)
	spec_data_file = models.TextField()
	spec_plot_file = models.TextField(null=True, blank=True)
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_quality = models.NullBooleanField(blank=True)
	spec_phase = models.ForeignKey(Phase, null=True, blank=True) # New
	snid_plot_file = models.TextField(null=True, blank=True)
	transient = models.ForeignKey(Transient)
	obs_date = models.DateTimeField()
	ra = models.FloatField()
	dec = models.FloatField()
	obs_group = models.ForeignKey(ObservationGroup)
	tdr = models.FloatField(null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True) # Contains ref to Host.HostClass

class Photometry(models.Model): # Combined Host Photometry + Photometry
	band = models.ForeignKey(PhotometricBand)
	obs_date = models.DateTimeField()
	flux = models.FloatField(null=True, blank=True)
	flux_err = models.FloatField(null=True, blank=True)
	mag = models.FloatField(null=True, blank=True)
	mag_err = models.FloatField(null=True, blank=True)
	forced = models.NullBooleanField(null=True, blank=True)
	image = models.ForeignKey(Image, null=True, blank=True)
	transient = models.ForeignKey(Transient, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)
	obs_group = models.ForeignKey(ObservationGroup)
	dq = models.NullBooleanField(null=True, blank=True)

class FollowUp(models.Model):
	transient = models.ForeignKey(Transient, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True) # New
	spec_priority = models.IntegerField(null=True, blank=True)
	phot_priority = models.IntegerField(null=True, blank=True)
	offset_star_ra = models.FloatField(null=True, blank=True)
	offset_star_dec = models.FloatField(null=True, blank=True)
	offset_north = models.FloatField(null=True, blank=True)
	offset_east = models.FloatField(null=True, blank=True)

class InformationSource(models.Model):
	name = models.CharField(max_length=64)

class WebResource(models.Model):
	transient = models.ForeignKey(Transient)
	information_source = models.ForeignKey(InformationSource)
	url = models.CharField(max_length=64)
	date_modified = models.DateTimeField()
	# Classification => comment; handled in Log table

class Log(models.Model):
	comment = models.TextField()
	date_modified = models.DateTimeField()
	transient = models.ForeignKey(Transient, null=True, blank=True)
	host = models.ForeignKey(Host, null=True, blank=True)
	spectrum = models.ForeignKey(Spectrum, null=True, blank=True)
	photometry = models.ForeignKey(Photometry, null=True, blank=True) # New
	web_resource = models.ForeignKey(WebResource, null=True, blank=True) # New
	follow_up = models.ForeignKey(FollowUp, null=True, blank=True) # New

class AlternateTransientNames(models.Model):
	name = models.CharField(max_length=64)
	obs_group = models.ForeignKey(ObservationGroup)
	transient = models.ForeignKey(Transient, null=True, blank=True)


class SpecData(models.Model):
	wavelength = models.FloatField()
	wavelength_err = models.FloatField(null=True, blank=True) # New
	flux = models.FloatField()
	flux_err = models.FloatField() # New

# If this is one-to-one, why a new table?
# Does redshift need to be repeated?
class HostSED(models.Model):
	host = models.ForeignKey(Host)
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
	redshift = models.FloatField(null=True, blank=True) # Need this?
	redshift_err = models.FloatField(null=True, blank=True) # Need this?
	sed_type = models.ForeignKey(SEDType, null=True, blank=True)
	fit_chi2 = models.FloatField(null=True, blank=True)
	fit_n = models.IntegerField(null=True, blank=True)
	fit_plot_file = models.TextField(null=True, blank=True)















