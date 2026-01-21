from django.db import models
from YSE_App.models.base import *
from YSE_App.models.transient_models import *

class Tag(BaseModel):
    class Meta:
        abstract = True

    ### Entity relationships ###
    # Optional
    color = models.ForeignKey(WebAppColor, on_delete=models.CASCADE, null=True, blank=True)

    ### Properties ###
    # Required
    name = models.CharField(max_length=256)
    
class TransientTag(Tag):
    
    def __str__(self):
        return "Name: %s" % self.name

class FRBTag(Tag):
    
    def __str__(self):
        return "Name: %s" % self.name

