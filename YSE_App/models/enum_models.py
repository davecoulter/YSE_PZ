from django.db import models
from YSE_App.models.base import *

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_transientstatus():
	return TransientStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]

class TransientStatus(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_followupstatus():
	return FollowupStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]

class FollowupStatus(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_taskstatus():
	return TaskStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]

class TaskStatus(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class AntaresClassification(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class InternalSurvey(BaseModel):
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

	def __str__(self):
		return self.name

class WebAppColor(BaseModel):
	### Properties ###
	# Required
	color = models.CharField(max_length=64)

	def __str__(self):
		return self.color