from django.db import models
from django.db.models import Q
from YSE_App.models.base import *
from YSE_App.models.transient_models import *
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

class GWCandidate(BaseModel):

	### Properties ###
	# Required
	field_name = models.CharField(max_length=64)
	candidate_id = models.CharField(max_length=64)
	name = models.CharField(max_length=64)
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)
	
	# Optional
	websniff_url = models.CharField(max_length=256, null=True, blank=True)

class GWCandidateImage(BaseModel):

	### Properties ###
	# Required
	obs_date = models.DateTimeField(null=True, blank=True)
	gw_candidate = models.ForeignKey(GWCandidate, on_delete=models.CASCADE)
	image_filename = models.CharField(max_length=256)
	image_filter = models.ForeignKey(PhotometricBand, on_delete=models.CASCADE)
	dophot_class = models.IntegerField(null=True, blank=True)
