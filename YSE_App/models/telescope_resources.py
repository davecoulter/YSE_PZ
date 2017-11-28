from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enums import *
from YSE_App.models.telescope_model import *

class ToOResource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start
	awarded_too_hours = models.FloatField()
	used_too_hours = models.FloatField()

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "ToO Resource: %s; Valid: %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class QueuedResource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start

	# Optional
	awarded_hours = models.FloatField(null=True, blank=True)
	used_hours = models.FloatField(null=True, blank=True)
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "Queued Resource: %s; Valid: %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class ClassicalResource(BaseModel):
	### Entity relationships ###
	# Required
	telescope = models.ForeignKey(Telescope)

	### Properites ###
	# Required
	begin_date_valid = models.DateTimeField() # i.e. the "semester" start
	end_date_valid = models.DateTimeField() # i.e. the "semester" start

	# Optional
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return "Classical Resource: %s; Valid: %s to %s" % (self.telescope.name, self.begin_date_valid[0], self.end_date_valid[0])

class ClassicalObservingDate(BaseModel):
	### Entity relationships ###
	# Required
	resource = models.ForeignKey(ClassicalResource)
	night_type = models.ForeignKey(ClassicalNightType)

	### Properties ###
	# Required
	obs_date = models.DateTimeField()
	
	def __str__(self):
		return "%s - %s" % (self.resource.telescope.name, self.observing_night[0])
	def happening_soon(self):
		now = timezone.now()
		return (now + datetime.timedelta(days=14) >= self.observing_night >= now)