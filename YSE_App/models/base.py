from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class BaseModel(models.Model):

	class Meta:
		abstract = True

	# Audit fields
	created_by = models.ForeignKey(User, related_name='%(class)s_created_by', on_delete=models.PROTECT)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_by = models.ForeignKey(User, related_name='%(class)s_modified_by', on_delete=models.PROTECT)
	modified_date = models.DateTimeField(auto_now=True)