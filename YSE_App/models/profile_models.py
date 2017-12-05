from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *

class Profile(BaseModel):
	### Entity relationships ###
	# Required
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	### Properties ###
	# Required
	phone_country_code = models.CharField(max_length=16)
	phone_area = models.IntegerField()
	phone_first_three = models.IntegerField()
	phone_last_four = models.IntegerField()
	phone_provider_str = models.CharField(max_length=64)

	def __str__(self):
		return "User: %s; Phone: +%s %s-%s-%s; Provider: %s" % (self.user.username, 
			self.phone_country_code, self.phone_area, self.phone_first_three,
			self.phone_last_four, self.phone_provider_str)