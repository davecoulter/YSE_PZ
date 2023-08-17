""" Models for FRB Followup Resources """
from autoslug import AutoSlugField
from auditlog.registry import auditlog

from django.db import models
from django.dispatch import receiver

import numpy as np

from YSE_App.models.base import BaseModel
from YSE_App.models.frbtransient_models import *
from YSE_App.models.instrument_models import *
from YSE_App.models.principal_investigator_models import *

from astroplan import Observer
from astropy.time import Time, TimeDelta

class FRBFollowUpResource(BaseModel):
    """ FRBFollowUpResource model

    Defines a follow-up resource for observing FRBs
    """

    ### Entity relationships ###
    # Required
    name = models.CharField(max_length=64, unique=True)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    valid_start = models.DateTimeField() # Start of observing run
    valid_stop = models.DateTimeField() # End of observing run

    # Number or targets
    num_targ_img = models.IntegerField()
    num_targ_mask = models.IntegerField()
    num_targ_longslit = models.IntegerField()

    # Maximum AM
    max_AM = models.FloatField()

    # Describes at what stage of follow-up an FRB is at

    # Optional

    # Classical, ToO, Queue
    obs_type = models.CharField(max_length=64, null=True, blank=True)
    PI = models.ForeignKey(PrincipalInvestigator, on_delete=models.CASCADE, null=True, blank=True)
    Program = models.CharField(max_length=64, null=True, blank=True)
    Period = models.CharField(max_length=64, null=True, blank=True)

    min_POx = models.FloatField(null=True, blank=True)

    slug = AutoSlugField(null=True, default=None, unique=True, populate_from='name')

    def __str__(self):
        return f'Name: {self.name} Instrument: {self.instrument.name}, start={self.valid_start}, stop={self.valid_stop}'

    def natural_key(self):
        return f'Instrument: {self.instrument.name}, start={self.valid_start}, stop={self.valid_stop}'

    def NameString(self):
        return self.name

    def InstrString(self):
        return self.instrument.name

    def StartString(self):
        return self.valid_start.strftime('%Y-%b-%d')

    def StopString(self):
        return self.valid_stop.strftime('%Y-%b-%d')

    def valid_transients(self):
        # Grab the telescope
        tel = Observer.at_site('keck', timezone='US/Hawaii')

        # Cut down transients by selection criteria
        gd_frbs = FRBTransient.objects.all()

        min_AM = np.array(len(gd_frbs))

        # Loop on nights
        this_time = Time(self.valid_start)
        end_time = Time(self.valid_stop)
        
        while(this_time < end_time):
            night_end = tel.twilight_evening_astronomical(this_time)
            this_obs_time = this_time

            while(this_obs_time < min(end_time,night_end)):

                # Loop over the remaining ones
                for ss, frbt in gd_frbs:
                    pass

                # Increment in 30min
                this_obs_time = this_obs_time + TimeDelta(1800, format='sec')

            # Add a day
            this_time = this_time + TimeDelta(1, format='jd')