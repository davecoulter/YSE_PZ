import datetime

import astropy.units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon
from astropy.coordinates import SkyCoord
from astropy.time import Time
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone

from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.principal_investigator_models import *
from YSE_App.models.telescope_models import *


class TelescopeResource(BaseModel):
    class Meta:
        abstract = True

        ### Entity relationships ###
        # Required

    telescope = models.ForeignKey(Telescope, on_delete=models.CASCADE)
    # Optional
    principal_investigator = models.ForeignKey(
        PrincipalInvestigator, null=True, blank=True, on_delete=models.SET_NULL
    )
    groups = models.ManyToManyField(Group, blank=True)

    ### Properties ###
    # Required
    begin_date_valid = models.DateTimeField()  # i.e. the "semester" start
    end_date_valid = models.DateTimeField()  # i.e. the "semester" start

    # Optional
    description = models.TextField(null=True, blank=True)


class ToOResource(TelescopeResource):
    ### Properites ###
    # Required
    awarded_too_hours = models.FloatField(null=True, blank=True)
    used_too_hours = models.FloatField(null=True, blank=True)

    awarded_too_triggers = models.FloatField(null=True, blank=True)
    used_too_triggers = models.FloatField(null=True, blank=True)

    def __str__(self):
        return "ToO Resource: %s; Valid: %s to %s" % (
            self.telescope.name,
            self.begin_date_valid.strftime("%m/%d/%Y"),
            self.end_date_valid.strftime("%m/%d/%Y"),
        )


class QueuedResource(TelescopeResource):
    ### Properites ###
    # Optional
    awarded_hours = models.FloatField(null=True, blank=True)
    used_hours = models.FloatField(null=True, blank=True)

    def __str__(self):
        return "Queued Resource: %s; Valid: %s to %s" % (
            self.telescope.name,
            self.begin_date_valid.strftime("%m/%d/%Y"),
            self.end_date_valid.strftime("%m/%d/%Y"),
        )


class ClassicalResource(TelescopeResource):
    def __str__(self):
        if self.principal_investigator:
            return "Classical Resource: %s; PI: %s, Valid: %s to %s" % (
                self.telescope.name,
                self.principal_investigator.name,
                self.begin_date_valid.strftime("%m/%d/%Y"),
                self.end_date_valid.strftime("%m/%d/%Y"),
            )
        else:
            return "Classical Resource: %s; Valid: %s to %s" % (
                self.telescope.name,
                self.begin_date_valid.strftime("%m/%d/%Y"),
                self.end_date_valid.strftime("%m/%d/%Y"),
            )


class ClassicalObservingDate(BaseModel):
    ### Entity relationships ###
    # Required
    resource = models.ForeignKey(ClassicalResource, on_delete=models.CASCADE)
    night_type = models.ForeignKey(ClassicalNightType, on_delete=models.CASCADE)

    ### Properties ###
    # Required
    obs_date = models.DateTimeField()

    def happening_soon(self):
        now = timezone.now()
        return (
            now + datetime.timedelta(days=4)
            >= self.obs_date
            >= now - datetime.timedelta(days=2)
        )

    def __str__(self):
        return "%s - %s" % (
            self.resource.telescope.name,
            self.obs_date.strftime("%m/%d/%Y"),
        )
