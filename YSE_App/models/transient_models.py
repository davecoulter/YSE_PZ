from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.photometric_band_models import *
from YSE_App.models.host_models import *
from YSE_App.common.utilities import GetSexigesimalString
from YSE_App.common.alert import IsK2Pixel, SendTransientAlert
from django.dispatch import receiver

class Transient(BaseModel):
	### Entity relationships ###
	# Required
	status = models.ForeignKey(TransientStatus, models.SET(get_sentinel_transientstatus))
	obs_group = models.ForeignKey(ObservationGroup, on_delete=models.CASCADE)

	# Optional
	non_detect_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	best_spec_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	photo_class = models.ForeignKey(TransientClass, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	best_spectrum = models.ForeignKey('TransientSpectrum', related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	host = models.ForeignKey(Host, null=True, blank=True, on_delete=models.SET_NULL)
	abs_mag_peak_band = models.ForeignKey(PhotometricBand, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)
	antares_classification = models.ForeignKey(AntaresClassification, null=True, blank=True, on_delete=models.SET_NULL)
	internal_survey = models.ForeignKey(InternalSurvey, null=True, blank=True, on_delete=models.SET_NULL)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)
	ra = models.FloatField()
	dec = models.FloatField()

	# Optional
	disc_date = models.DateTimeField(null=True, blank=True)
	candidate_hosts = models.TextField(null=True, blank=True) # A string field to hold n hosts -- if we don't quite know which is the correct one
	redshift = models.FloatField(null=True, blank=True)
	redshift_err = models.FloatField(null=True, blank=True)
	redshift_source = models.CharField(max_length=64, null=True, blank=True)
	non_detect_date = models.DateTimeField(null=True, blank=True)
	non_detect_limit = models.FloatField(null=True, blank=True)
	mw_ebv = models.FloatField(null=True, blank=True)
	abs_mag_peak = models.FloatField(null=True, blank=True)
	abs_mag_peak_date = models.DateTimeField(null=True, blank=True)
	postage_stamp_file = models.CharField(max_length=512, null=True, blank=True)
	k2_validated = models.NullBooleanField(null=True, blank=True)

	def CoordString(self):
		return GetSexigesimalString(self.ra, self.dec)

	def Separation(self):
		host = Host.objects.get(pk=self.host_id)
		return '%.2f'%getSeparation(self.ra,self.dec,host.ra,host.dec)

	def __str__(self):
		return self.name

@receiver(models.signals.post_save, sender=Transient)
def execute_after_save(sender, instance, created, *args, **kwargs):
	if created:
		print("Transient Created: %s" % instance.name)
		print("Internal Survey: %s" % instance.internal_survey)

		sent_from_K2_TNS = True #(instance.internal_survey == 'K2')
		if sent_from_K2_TNS:

			print("Is sent from K2")

			is_k2_validated = IsK2Pixel(instance.ra, instance.dec)
			instance.k2_validated = is_k2_validated
			instance.save()

		if sent_from_K2_TNS:
			print('goodbye')
			SendTransientAlert()


# Alternate Host names?
class AlternateTransientNames(BaseModel):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)

	# Optional
	obs_group = models.ForeignKey(ObservationGroup, null=True, blank=True, on_delete=models.SET_NULL)
	
	### Properities ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name
