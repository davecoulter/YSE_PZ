from django.db import models
from django.db.models import Q
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.photometric_band_models import *
from YSE_App.models.host_models import *
from YSE_App.models.tag_models import *
from YSE_App.common.utilities import GetSexigesimalString
from YSE_App.common.alert import IsK2Pixel, SendTransientAlert
from YSE_App.common.thacher_transient_search import thacher_transient_search
from YSE_App.common.tess_obs import tess_obs
from YSE_App.common.utilities import date_to_mjd
from YSE_App import models as yse_models
from django.dispatch import receiver
from pytz import timezone
from django.utils.text import slugify
from autoslug import AutoSlugField

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
	tags = models.ManyToManyField(TransientTag, blank=True)

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
	k2_msg = models.TextField(null=True, blank=True)
	TNS_spec_class = models.CharField(max_length=64, null=True, blank=True) # To hold the TNS classiciation in case we don't have a matching enum

	slug = AutoSlugField(null=True, default=None, unique=True, populate_from='name')
	
	def CoordString(self):
		return GetSexigesimalString(self.ra, self.dec)

	def RADecimalString(self):
		return '%.7f'%(self.ra)

	def DecDecimalString(self):
		return '%.7f'%(self.dec)

	def Separation(self):
		host = Host.objects.get(pk=self.host_id)
		return '%.2f'%getSeparation(self.ra,self.dec,host.ra,host.dec)

	def modified_date_pacific(self):
		date_format = '%m/%d/%Y %H:%M:%S %Z'
		mod_date = self.modified_date.astimezone(timezone('US/Pacific'))
		return mod_date.strftime(date_format)

	def disc_date_string(self):
		date_format = '%m/%d/%Y'
		return self.disc_date.strftime(date_format)

	def disc_mag(self):

		transient_query = Q(transient=self.id)
		all_phot = yse_models.TransientPhotometry.objects.filter(transient_query)
		phot_ids = all_phot.values('id')
		phot_data_query = Q(photometry__id__in=phot_ids)
		disc_query = Q(discovery_point = 1)
		disc_mag = yse_models.TransientPhotData.objects.exclude(data_quality__isnull=False).filter(phot_data_query & disc_query)
		if len(disc_mag):
			return disc_mag[0].mag
		else:
			return None

	def recent_mag(self):
		date_format = '%m/%d/%Y'

		transient_query = Q(transient=self.id)
		all_phot = yse_models.TransientPhotometry.objects.filter(transient_query)
		phot_ids = all_phot.values('id')
		phot_data_query = Q(photometry__id__in=phot_ids)
		recent_mag = yse_models.TransientPhotData.objects.exclude(data_quality__isnull=False).filter(phot_data_query).order_by('-obs_date')

		if len(recent_mag):
			return '%.2f'%(recent_mag[0].mag)
		else:
			return None

	def recent_magdate(self):
		date_format = '%m/%d/%Y'

		transient_query = Q(transient=self.id)
		all_phot = yse_models.TransientPhotometry.objects.filter(transient_query)
		phot_ids = all_phot.values('id')
		phot_data_query = Q(photometry__id__in=phot_ids)
		recent_mag = yse_models.TransientPhotData.objects.exclude(data_quality__isnull=False).filter(phot_data_query).order_by('-obs_date')

		if len(recent_mag):
			return '%s'%(recent_mag[0].obs_date.strftime(date_format))
		else:
			return None

	def z_or_hostz(self):
		if self.redshift:
			return self.redshift
		elif self.host and self.host.redshift:
			return self.host.redshift
		else: return None

	def name_table_sort(self):
		if len(self.name) > 4:
			addnums = 7-len(self.name)
			sortname = "".join([self.name[:4],"".join(['1']*addnums),self.name[4:]])

			return sortname
		else:
			return None

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name
	
@receiver(models.signals.post_save, sender=Transient)
def execute_after_save(sender, instance, created, *args, **kwargs):

	if created:
		print("Transient Created: %s" % instance.name)
		print("Internal Survey: %s" % instance.internal_survey)

		is_k2_C16_validated, C16_msg = IsK2Pixel(instance.ra, instance.dec, "16")
		is_k2_C17_validated, C17_msg = IsK2Pixel(instance.ra, instance.dec, "17")
		is_k2_C19_validated, C19_msg = IsK2Pixel(instance.ra, instance.dec, "19")

		print("K2 C16 Val: %s; K2 Val Msg: %s" % (is_k2_C16_validated, C16_msg))
		print("K2 C17 Val: %s; K2 Val Msg: %s" % (is_k2_C17_validated, C17_msg))
		print("K2 C19 Val: %s; K2 Val Msg: %s" % (is_k2_C19_validated, C19_msg))

		if is_k2_C16_validated:
			k2c16tag = TransientTag.objects.get(name='K2 C16')
			instance.k2_validated = True
			instance.k2_msg = C16_msg
			instance.tags.add(k2c16tag)
			
		elif is_k2_C17_validated:
			k2c17tag = TransientTag.objects.get(name='K2 C17')
			instance.k2_validated = True
			instance.k2_msg = C17_msg
			instance.tags.add(k2c17tag)

		elif is_k2_C19_validated:
			k2c19tag = TransientTag.objects.get(name='K2 C19')
			instance.k2_validated = True
			instance.k2_msg = C19_msg
			instance.tags.add(k2c19tag)

		print('Checking TESS')
		if instance.disc_date:
			if tess_obs(instance.ra,instance.dec,date_to_mjd(instance.disc_date)+2400000.5):
				try:
					tesstag = TransientTag.objects.get(name='TESS')
					instance.tags.add(tesstag)
				except: pass
		else:
			if tess_obs(instance.ra,instance.dec,date_to_mjd(instance.modified_date)+2400000.5):
				try:
					tesstag = TransientTag.objects.get(name='TESS')
					instance.tags.add(tesstag)
				except: pass

		print('Checking Thacher')
		if thacher_transient_search(instance.ra,instance.dec):
			try:
				thachertag = TransientTag.objects.get(name='Thacher')
				instance.tags.add(thachertag)
			except: pass
			
		instance.save()
		#if is_k2_C19_validated:
		#	coord_string = GetSexigesimalString(instance.ra, instance.dec)
		#	coord_string = instance.CoordString()
		#	SendTransientAlert(instance.id, instance.name, coord_string[0], coord_string[1])

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
