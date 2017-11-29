from django.db import models
from YSE_App.models.base import *

class TransientHostRank(BaseModel):
	### Properties ###
	# Required
	rank = models.IntegerField()

	def __str__(self):
		return str(self.rank)

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

class ClassicalNightType(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

# Where did we get it? e.g. ATel, TNS, PS1, etc
class InformationSource(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)