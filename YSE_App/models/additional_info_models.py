from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *
from YSE_App.common.utilities import *
from YSE_App.models.frbtransient_models import *

class WebResource(BaseModel):

	class Meta:
		abstract = True
	### Entity relationships ###
	# Required
	information_source = models.ForeignKey(InformationSource, on_delete=models.CASCADE)

	### Properties ###
	# Required 
	information_text = models.TextField()
	resource_url = models.CharField(max_length=512)

class TransientWebResource(WebResource):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient, on_delete=models.CASCADE)

	def __str__(self):
		return "%s - %s" % (self.transient.name, self.information_source.name)

class HostWebResource(WebResource):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host, on_delete=models.CASCADE)

	def __str__(self):
		return "%s - %s" % (self.host.HostString(), self.information_source.name)

class FRBTransientWebResource(WebResource):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(FRBTransient, on_delete=models.CASCADE)

	def __str__(self):
		return "%s - %s" % (self.transient.name, self.information_source.name)