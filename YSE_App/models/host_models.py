from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.photometric_band_models import *
from YSE_App.common.utilities import *

class Host(BaseModel):
	### Entity relationships ###
	# Optional
	host_morphology = models.ForeignKey(HostMorphology, null=True, blank=True)
	host_class = models.ForeignKey(HostClass, null=True, blank=True)
	band_sextract = models.ForeignKey(PhotometricBand, null=True, blank=True)
	best_spec = models.ForeignKey('HostSpectrum', related_name='+', null=True, blank=True)
	transient_host_rank = models.ForeignKey(TransientHostRank, null=True, blank=True)

	### Properties ###
	# Required
	ra = models.FloatField()
	dec = models.FloatField()

	# Optional
	name = models.CharField(max_length=64, null=True, blank=True)
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	r_a = models.FloatField(null=True, blank=True)
	r_b = models.FloatField(null=True, blank=True)
	theta = models.FloatField(null=True, blank=True)
	eff_offset = models.FloatField(null=True, blank=True)
	photo_z = models.FloatField(null=True, blank=True)
	photo_z_err = models.FloatField(null=True, blank=True)
	photo_z_source = models.CharField(max_length=64, null=True, blank=True)

	def __str__(self):
		ra_str, dec_str = GetSexigesimalString(self.ra, self.dec)

		if self.name:
			return "Host: %s; (%s, %s)" % (self.name, ra_str, dec_str)
		else:
			return "Host: (%s, %s)" % (ra_str, dec_str)

class HostSED(BaseModel):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host)

	# Optional
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