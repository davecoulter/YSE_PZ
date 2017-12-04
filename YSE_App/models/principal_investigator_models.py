from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *

class PrincipalInvestigator(BaseModel):
	### Entity relationships ###
	# Optional
	obs_group = models.ManyToManyField(ObservationGroup, blank=True)

	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	# Optional
	phone = models.CharField(max_length=64)
	email = models.EmailField()
	institution = models.CharField(max_length=64)
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name