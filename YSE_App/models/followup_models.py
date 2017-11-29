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
	status = models.ForeignKey(Status)

	# Optional
	too_resource = models.ForeignKey(ToOResource, null=True, blank=True)
	classical_resource = models.ForeignKey(ClassicalResource, null=True, blank=True)
	queued_resource = models.ForeignKey(QueuedResource, null=True, blank=True)

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
	transient = models.ForeignKey(Transient)

	def __str__(self):
		return "Transient Followup: [%s]; Valid: %s to %s" % (self.transient.name, self.valid_start[0], self.valid_stop[0])

class HostFollowup(Followup):
	### Entity relationships ###
	host = models.ForeignKey(Host)

	def __str__(self):
		ra_str, dec_str = GetSexigesimalString(self.host.ra, self.host.dec)
		entity_str = ""

		if self.host.name:
			entity_str = "Host Followup: [%s; (%s, %s)]; Valid: %s to %s" % (self.host.name, ra_str, dec_str, self.valid_start[0], self.valid_stop[0])
		else:
			entity_str = "Host Followup: [(%s, %s)]; Valid: %s to %s" % (ra_str, dec_str, self.valid_start[0], self.valid_stop[0])

		return entity_str