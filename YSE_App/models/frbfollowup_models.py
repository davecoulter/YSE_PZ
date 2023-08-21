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
from YSE_App import frb_targeting


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

    # Surveys to which this resource is applicable
    #  e.g. CHIME/FRB, CRAFT, etc.
    #  all is ok too
    frb_surveys = models.CharField(max_length=64)


    # Optional

    # Classical, ToO, Queue
    obs_type = models.CharField(max_length=64, null=True, blank=True)
    # PI
    PI = models.ForeignKey(PrincipalInvestigator, on_delete=models.CASCADE, null=True, blank=True)
    # Program name
    Program = models.CharField(max_length=64, null=True, blank=True)
    # Semester, period, etc.,  e.g. 2024A
    Period = models.CharField(max_length=64, null=True, blank=True)

    # Items for selecting targets
    min_POx = models.FloatField(null=True, blank=True)
    frb_tags = models.CharField(max_length=64, null=True, blank=True)
    frb_statuses = models.CharField(max_length=64, null=True, blank=True)

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

    def generate_targets(self):
        """ Generate a list of FRBTansients that are valid for this resource, 
        i.e. meet all the criteria including AM

        Returns:
            list: list of FRBTransient objects
        """

        # Cut down transients by selection criteria
        #  magnitude
        #  FRB Survey
        #  P(O|x)
        #  E(B-V)
        #  Bright star?
        gd_frbs = frb_targeting.targetfrbs_for_fu(self)

        # gd_frbs should be a query set
        #gd_frbs = FRBTransient.objects.all()
        nfrb = len(gd_frbs)

        # Caculate minimum airmasses during the Resource period
        min_AM = frb_targeting.calc_airmasses(self, gd_frbs)

        # Parse
        keep_frbs = []
        for ss in range(nfrb):
            if min_AM[ss] < self.max_AM:
                keep_frbs.append(gd_frbs[ss])
        #
        return keep_frbs