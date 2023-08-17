""" Scripts for developing follow-up """
from importlib import reload

import numpy as np

from YSE_App.models.frbfollowup_models import FRBFollowUpResource
from YSE_App.models import FRBTransient

from astroplan import Observer

from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord, EarthLocation
from astropy import units

from IPython import embed

#reload(FRBFollowUpResource)

def dev_targets():
    frbfup = FRBFollowUpResource.objects.all()[1]

    # Grab the telescope from its name
    tel = Observer.at_site('keck', timezone='US/Hawaii')
    '''
    telescope = frbfup.instrument.telescope
    location = EarthLocation.from_geodetic(
        telescope.longitude*units.deg,telescope.latitude*units.deg,
        telescope.elevation*units.m)
    tel = Observer(location=location, timezone="UTC")
    '''

    # Cut down transients by selection criteria
    #  magnitude
    #  FRB Survey
    #  P(O|x)
    #  E(B-V)
    #  Bright star?
    gd_frbs = FRBTransient.objects.all()
    nfrb = len(gd_frbs)
    ras = [frbt.ra for frbt in gd_frbs]
    decs = [frbt.dec for frbt in gd_frbs]
    frb_coords = SkyCoord(ra=ras, dec=decs, unit='deg')

    min_AM = [1e9]*nfrb

    # Loop on nights
    this_time = Time(frbfup.valid_start)
    end_time = Time(frbfup.valid_stop)
    
    # Loop on nights
    while(this_time < end_time):
        night_end = tel.twilight_morning_astronomical(this_time)
        this_obs_time = this_time.copy()


        # Loop on 30min intervals from 
        while(this_obs_time < min(end_time,night_end)):
            print(this_obs_time.datetime)

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

    return min_AM