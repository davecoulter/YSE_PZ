from django.contrib.auth.models import Group
from django.db import models

from YSE_App.models import Photometry, PhotData

class GalaxyPhotometry(Photometry):

    # Required
    galaxy = models.ForeignKey(FRBGalaxy, on_delete=models.CASCADE)

    # Optional
    #followup = models.ForeignKey(HostFollowup, null=True, blank=True, on_delete=models.SET_NULL) # Can by null if data is from external source

    class Meta:
        unique_together = ['galaxy', 'instrument', 'obs_group']

    def __str__(self):
        return 'Galaxy Phot: %s ' % (self.galaxy.HostString())

    def natural_key(self):
        return '%s - %s' % (self.obs_group.name,self.instrument.name)


class GalaxyPhotData(PhotData):
    # Entity relationships ###
    # Required
    photometry = models.ForeignKey(GalaxyPhotometry, on_delete=models.CASCADE)

    def __str__(self):
        return '%s - %s - %s' % (
            self.photometry.galaxy.GalaxyString(), 
            self.band.name, 
            self.obs_date.strftime('%m/%d/%Y'))
