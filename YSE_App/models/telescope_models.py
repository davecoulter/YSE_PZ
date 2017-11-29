from django.db import models
from YSE_App.models.base import *
from YSE_App.models.observatory_models import *

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