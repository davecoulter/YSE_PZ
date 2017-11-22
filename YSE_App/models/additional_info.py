from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enums import *
from YSE_App.models.transient_models import *
from YSE_App.models.host_models import *

class WebResource(BaseModel):
	### Entity relationships ###
	# Required
	information_source = models.ForeignKey(InformationSource)

	### Properties ###
	# Required 
	information_text = models.TextField()
	url = models.CharField(max_length=512)

class TransientWebResource(WebResource):
	### Entity relationships ###
	# Required
	transient = models.ForeignKey(Transient)

class HostWebResource(WebResource):
	### Entity relationships ###
	# Required
	host = models.ForeignKey(Host)