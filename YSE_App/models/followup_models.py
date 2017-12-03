from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.telescope_resource_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *

class Followup(BaseModel):

	class Meta:
		abstract = True

	### Entity relationships ###
	# Required
	status = models.ForeignKey(FollowupStatus, on_delete=models.SET(get_sentinel_followupstatus))

	# Optional
	too_resource = models.ForeignKey(ToOResource, null=True, blank=True, on_delete=models.SET_NULL)
	classical_resource = models.ForeignKey(ClassicalResource, null=True, blank=True, on_delete=models.SET_NULL)
	queued_resource = models.ForeignKey(QueuedResource, null=True, blank=True, on_delete=models.SET_NULL)

	### Properties ###
	# Required
	valid_start = models.DateTimeField()
	valid_stop = models.DateTimeField()

	# Optional
	spec_priority = models.IntegerField(null=True, blank=True)
	phot_priority = models.IntegerField(null=True, blank=True)
	offset_star_ra = models.FloatField(null=True, blank=True)
	offset_star_dec = models.FloatField(null=True, blank=True)
	offset_north = models.FloatField(null=True, blank=True)
	offset_east = models.FloatField(null=True, blank=True)

class TransientFollowup(Followup):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)

	def __str__(self):
		return "Transient Followup: [%s]; Valid: %s to %s" % (self.transient.name, self.valid_start, self.valid_stop)

class HostFollowup(Followup):
	### Entity relationships ###
	host = models.ForeignKey(Host, on_delete=models.CASCADE)

	def __str__(self):
		return "Host Followup: [%s]; Valid: %s to %s" % (self.host.HostString(), self.valid_start, self.valid_stop)
