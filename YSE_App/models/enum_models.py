""" Models that have multiple entries """

from django.db import models
from YSE_App.models.base import *

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_transientstatus():
	return TransientStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]


class TransientStatus(BaseModel):
	"""
	A general type of status for a transient in YSE_PZ.
	
	Examples of usage are, a transinet status could be New, FollowupRequested, or Interesting.
	
	Attributes:
		name (CharField): name of the status to be displayed.
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_followupstatus():
	return FollowupStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]

class FollowupStatus(BaseModel):
	"""
	A followup status of a transient in YSE_PZ
	
	Examples of usage are, a transinet could have had a Sucessful, Inprogress, Requested or Failed followup.
	
	Attributes:
		name (CharField): name of the followup status to be displayed.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

# If a status gets accidentally deleted, create a proxy status created/modified by `admin` superuser (will always be user.id == 1)
def get_sentinel_taskstatus():
	return TaskStatus.objects.get_or_create(name='StatusDeleted', created_by_id='1', modified_by_id='1')[0]

class TaskStatus(BaseModel):
	"""
	The status of a compute task in YSE_PZ
	
	Examples of usage are, a task could be Sucessful, Failed, Requested, or InProgress.
	
	Attributes:
		name (CharField): name of the followup status to be displayed.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class AntaresClassification(BaseModel):
	"""
	The Antares broker classification of a transient in YSE_PZ
	
	Attributes:
		name (CharField): name of the Antares classification.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class InternalSurvey(BaseModel):
	"""
	A way to add a tag to data designating its source.
	
	Attributes:
		name (CharField): name of the source of the data.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class ObservationGroup(BaseModel):
	"""
	A way to add a tag to data designating its external source.
	
	Attributes:
		name (CharField): name of the source of the data.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class SEDType(BaseModel):
	"""
	Type of Spectral Energry Distrubtion of a transient.
	
	Attributes:
		name (CharField): name of the Spectral Energry Distrubtion type.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class HostMorphology(BaseModel):
	"""
	Morphological type of the transient host galaxy.
	
	Attributes:
		name (CharField): Morphological type.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class Phase(BaseModel):
	"""
	Phase of the transient.
	
	Example usage, PreExplosiona and PostExplosion.
	
	Attributes:
		name (CharField): Name of the phase of the transient
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class TransientClass(BaseModel):
	"""
	Class of a transient.
	
	Example usage, SN, SN I, SN IB.
	
	Attributes:
		name (CharField): Name of the transient class.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class ClassicalNightType(BaseModel):
	"""
	Describes the observation mode of a transient on a classically scheduled night.
	
	Example usage, FirstHalf, SecondHalf, Full or Queue.
	
	Attributes:
		name (CharField): name of the classical night type.
	
	"""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

# Where did we get it? e.g. ATel, TNS, PS1, etc
class InformationSource(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class WebAppColor(BaseModel):
	### Properties ###
	# Required
	color = models.CharField(max_length=64)

	def __str__(self):
		return self.color

	def natural_key(self):
		return self.name

class Unit(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=128)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class DataQuality(BaseModel):
	### Properties ###
	# Required
	name = models.CharField(max_length=128)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name

class MagSystem(BaseModel):

	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

	def natural_key(self):
		return self.name
