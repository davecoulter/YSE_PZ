from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.telescope_models import *
from explorer.models import *

class Profile(BaseModel):
	### Entity relationships ###
	# Required
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	### Properties ###
	# Required
	phone_country_code = models.CharField(max_length=16)
	phone_area = models.CharField(max_length=3)
	phone_first_three = models.CharField(max_length=3)
	phone_last_four = models.CharField(max_length=4)
	phone_provider_str = models.CharField(max_length=16)

	def __str__(self):
		return "User: %s; Phone: +%s %s-%s-%s; Provider: %s" % (self.user.username, 
			self.phone_country_code, self.phone_area, self.phone_first_three,
			self.phone_last_four, self.phone_provider_str)

class UserQuery(BaseModel):

	user = models.ForeignKey(User, on_delete=models.CASCADE)
	query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.CASCADE)

	def __str__(self):
		return '%s %s: %s'%(self.user.first_name,self.user.last_name,self.query.title)

class UserTelescopeToFollow(BaseModel):

	profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
	telescope = models.ForeignKey(Telescope, on_delete=models.CASCADE)

	def __str__(self):
		return '%s: %s'%(self.profile.user,self.telescope.name)
