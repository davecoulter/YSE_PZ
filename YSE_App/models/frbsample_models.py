""" Models for FRB Samples (also known, unfortunately, as tags)"""

from django.db import models

import pandas

from YSE_App.models.base import BaseModel
from YSE_App.models.frbtransient_models import *


class FRBSampleCriteria(BaseModel):
    """ FRBSampleCriteria model

    Defines the data model for sample criteria for FRB follow-up
    """

    ### Entity relationships ###

    # #########################################################
    # Required
    name = models.CharField(max_length=64, unique=True)
    version = models.CharField(max_length=64)
    desc = models.CharField(max_length=256) # Description of the sample criteria
    frb_survey = models.ForeignKey(FRBSurvey, on_delete=models.CASCADE)

    # Weighting factor when selecting from many targets
    weight = models.FloatField()

    # min P(O|x) for selection
    min_POx = models.FloatField()

    # Consider top two when assessing P(O|x) criterion?
    use_top_two = models.BooleanField()

    # max E(B-V) for selection
    max_EBV = models.FloatField()

    # max mr (faint) for selection
    max_mr = models.FloatField()

    # Run Public PATH as the default?
    run_public_path = models.BooleanField()

    # Run Public PATH as the default?
    apply_bright_star = models.BooleanField(default=True)
    
    # #########################################################
    # Optional
    start_date = models.DateTimeField(null=True, blank=True) # Start of observing run (UT)
    stop_date = models.DateTimeField(null=True, blank=True) # End of observing run (UT)

    # max P(U|x) for selection
    max_PUx = models.FloatField(null=True, blank=True)

    # min DM; for highDM sample
    min_DM = models.FloatField(null=True, blank=True)

    # max DM; for low-z sample
    max_DM = models.FloatField(null=True, blank=True)

    # Localization
    max_a = models.FloatField(null=True, blank=True)

    # Skip NeedImage
    skip_need_image = models.BooleanField(null=True, blank=True)
    

    def __str__(self):
        return f'Name: {self.name} Survey: {self.frb_survey} Version: {self.version}' 

    def NameString(self):
        return self.name
