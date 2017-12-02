from django.db import models
from YSE_App.models.base import *

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
		return 'Observatory: %s' % self.name