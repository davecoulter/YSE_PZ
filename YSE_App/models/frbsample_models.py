""" Models for FRB Samples (also known, unfortunately, as tags)"""

from django.db import models

import pandas

from YSE_App.models.base import BaseModel
from YSE_App.models.frbtransient_models import *
from YSE_App import frb_targeting


class FRBSampleCriteria(BaseModel):
    """ FRBSampleCriteria model

    Defines the data model for sample criteria for FRB follow-up
    """

    ### Entity relationships ###

    # #########################################################
    # Required
    name = models.CharField(max_length=64, unique=True)
    version = models.CharField(max_length=64)
    frb_survey = models.ForeignKey(FRBSurvey, on_delete=models.CASCADE)

    # Weighting factor when selecting from many targets
    weight = models.FloatField()

    # min P(O|x) for selection
    min_POx = models.FloatField()

    # max E(B-V) for selection
    max_EBV = models.FloatField()

    # max mr (faint) for selection
    max_mr = models.FloatField()

    # Run Public PATH as the default?
    run_public_path = models.BooleanField()
    
    # #########################################################
    # Optional
    start_date = models.DateTimeField(null=True, blank=True) # Start of observing run (UT)
    stop_date = models.DateTimeField(null=True, blank=True) # End of observing run (UT)

    # max P(U|x) for selection
    max_PUx = models.FloatField(null=True, blank=True)

    # min DM
    min_DM = models.FloatField(null=True, blank=True)


    def __str__(self):
        return f'Name: {self.name} Survey: {self.frb_survey} Version: {self.version}' 

    def NameString(self):
        return self.name

    def get_frbs_by_mode(self):
        """ Generate a dict of valid FRBs for targeting by observing mode

        calls frb_targeting.grab_targets_by_mode()

        Returns:
            dict: dict of FRBTransients by observing mode
        """
        # Cut down transients by selection criteria
        #  magnitude
        #  FRB Survey
        #  P(O|x)
        #  E(B-V)
        #  Bright star?
        gd_frbs = frb_targeting.targetfrbs_for_fu(self)

        # Caculate minimum airmasses during the Resource period
        min_AM = frb_targeting.calc_airmasses(self, gd_frbs)

        # Parse on AM
        keep_frbs = []
        for ss in range(len(gd_frbs)):
            if min_AM[ss] <= self.max_AM:
                keep_frbs.append(gd_frbs[ss].id)
        gd_frbs = gd_frbs.filter(id__in=keep_frbs)

        # Now the various modes!
        frbs_by_mode = frb_targeting.grab_targets_by_mode(self, gd_frbs)

        return frbs_by_mode

    def generate_target_table(self):
        """ Generate a table of FRBTransients that are valid for this resource, 
        i.e. meet all the criteria including AM

        Returns:
            pandas.DataFrame: table of FRBTransients for observing
        """
        # All FRBs by mode satisfying criteria
        frbs_by_mode = self.get_frbs_by_mode()

        # Cut down by number requested and priority
        final_targs_by_mode = frb_targeting.select_with_priority(self, frbs_by_mode)

        # Table me
        tbls = []
        for key in final_targs_by_mode.keys():
            tbls.append(frb_targeting.target_table_from_frbs(final_targs_by_mode[key], key))

        # Combine
        target_table = pandas.concat(tbls, ignore_index=True)

        # Add in the resource
        target_table['Resource'] = self.name

        return target_table
