""" Models for FRB Followup Resources """
from autoslug import AutoSlugField
from auditlog.registry import auditlog

from django.db import models
from django.dispatch import receiver

import numpy as np

from YSE_App.models.base import BaseModel
from YSE_App.models import *  # Avoids circular import
from YSE_App.models.enum_models import *
from YSE_App.models.tag_models import *
from YSE_App.chime import tags as chime_tags
from YSE_App.common.utilities import GetSexigesimalString, getSeparation
from YSE_App.models.frbgalaxy_models import FRBGalaxy

class FRBFollowUpResource(BaseModel):
    """ FRBFollowUpResource model

    Defines a follow-up resource for observing FRBs
    """

    ### Entity relationships ###
    # Required
	instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
	valid_start = models.DateTimeField() # Start of observing run
	valid_stop = models.DateTimeField() # End of observing run

    # Number or targets
	num_targ_img = models.IntegerField()
    num_targ_mask = models.IntegerField()
    num_targ_longslit = models.IntegerField()

    # Maximum AM
	max_AM = models.FloatField(null=True, blank=True)

    # Describes at what stage of follow-up an FRB is at

    # Optional

    # Classical, ToO, Queue
    obs_type = models.CharField(max_length=64, null=True, blank=True)
    PI = models.CharField(max_length=64, null=True, blank=True)
    Program = models.CharField(max_length=64, null=True, blank=True)
    Period = models.CharField(max_length=64, null=True, blank=True)

    slug = AutoSlugField(null=True, default=None, unique=True, populate_from='name')


    def __str__(self):
        return f'Instrument: {self.instrument.name}, start={self.valid_start}, stop={self.valid_stop}'

    def natural_key(self):
        return f'Instrument: {self.instrument.name}, start={self.valid_start}, stop={self.valid_stop}'


auditlog.register(FRBTransient)

@receiver(models.signals.post_save, sender=FRBTransient)
def execute_after_save(sender, instance, created, *args, **kwargs):

    if created:

        # CHIME FRB items
        if instance.frb_survey.name == 'CHIME/FRB':

            # Add tags
            tags = chime_tags.set_from_instance(instance)
            frb_tags = [ftag.name for ftag in FRBTag.objects.all()]
            for tag_name in tags:
                # Add the tag if it doesn't exist
                if tag_name not in frb_tags:
                    new_tag = FRBTag(name=tag_name, 
                                     created_by_id=instance.created_by_id,
                                     modified_by_id=instance.modified_by_id)
                    new_tag.save()
                # Record
                frb_tag = FRBTag.objects.get(name=tag_name)
                instance.frb_tags.add(frb_tag)
                print(f"Added FRB tag: {tag_name}")
            
        instance.save()

class Path(BaseModel):
    """ django model for PATH table

    Each PATH posterior value P(O|x) is for an FRB-Galaxy pairing
    which are required properties

    Requires an FRBTansient and FRBGalaxy pairing

    """

    ### Properties ###
    # Required 

    # Transient 
    transient = models.ForeignKey(FRBTransient, on_delete=models.CASCADE)
    # PATH P(O|x) value
    P_Ox = models.FloatField()
    # Candidate name
    galaxy = models.ForeignKey(FRBGalaxy, on_delete=models.CASCADE)

    # Optional

    # Vetted? If true, a human has confirmed the results are valid
    vetted = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f'Path: {self.transient.name}, {self.galaxy.name}, {self.P_Ox}, {self.vetted}'   
