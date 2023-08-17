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
from astropy.coordinates import SkyCoord, EarthLocation
from astropy import units

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
        #frbfup = FRBFollowUpResource.objects.all()[1]

        # Grab the telescope 
        telescope = self.instrument.telescope
        location = EarthLocation.from_geodetic(
            telescope.longitude*units.deg,telescope.latitude*units.deg,
            telescope.elevation*units.m)
        tel = Observer(location=location, timezone="UTC")

        # Cut down transients by selection criteria
        #  magnitude
        #  FRB Survey
        #  P(O|x)
        #  E(B-V)
        #  Bright star?
        # This needs to be a query set
        gd_frbs = FRBTransient.objects.all()
        nfrb = len(gd_frbs)

        # Coords
        ras = [frbt.ra for frbt in gd_frbs]
        decs = [frbt.dec for frbt in gd_frbs]
        frb_coords = SkyCoord(ra=ras, dec=decs, unit='deg')

        min_AM = np.array([1e9]*nfrb)

        # Loop on nights
        this_time = Time(self.valid_start)
        end_time = Time(self.valid_stop)
        
        # Loop on nights
        while(this_time < end_time):
            night_end = tel.twilight_morning_astronomical(this_time)
            this_obs_time = this_time.copy()


            # Loop on 30min intervals from 
            while(this_obs_time < min(end_time,night_end)):
                #print(this_obs_time.datetime)

                # Calculate AM
                altaz = tel.altaz(this_obs_time, frb_coords)
                airmass = 1/np.cos((90.-altaz.alt.value)*np.pi/180.)
                # Below horizon
                airmass[altaz.alt.value < 0] = 1e9

                # Save
                min_AM = np.minimum(min_AM, airmass)

                # Increment in 30min
                this_obs_time = this_obs_time + TimeDelta(1800, format='sec')

            # Add a day
            this_time = this_time + TimeDelta(1, format='jd')
            this_time = tel.twilight_evening_astronomical(this_time, which='previous')

        # Parse
        keep_frbs = []
        for ss in range(nfrb):
            if min_AM[ss] < self.max_AM:
                keep_frbs.append(gd_frbs[ss])
        #
        return keep_frbs