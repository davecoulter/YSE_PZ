""" Utilities for FRB activities """

from YSE_App.models import *

import pandas

from astroplan import Observer
from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord, EarthLocation
from astropy import units

def calc_airmasses(frb_fu, gd_frbs,
                    debug:bool=False):
    """ Calulate the minimum AM for a set of FRBs
    tied to a FRBFollowupResource

    Moved here to speed up development.  Could be
    a method on FRBFollowupResource someday..

    Args:
        frb_fu (FRBFollowupResource): _description_
        gd_frbs (QuerySet of FRBTransient): _description_
        debug (bool, optional): _description_. Defaults to False.

    Returns:
        np.ndarray: Minimum airmass values for the input FRBs
            during the observing period
    """
                    
    # Grab the telescope 
    telescope = frb_fu.instrument.telescope
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
    this_time = Time(frb_fu.valid_start)
    end_time = Time(frb_fu.valid_stop)
    
    # Loop on nights
    while(this_time < end_time):
        night_end = tel.twilight_morning_astronomical(this_time)
        this_obs_time = this_time.copy()


        # Loop on 30min intervals from 
        while(this_obs_time < min(end_time,night_end)):
            if debug:
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

        # Add a day -- Add to night_end to avoid death loop
        this_time = night_end + TimeDelta(1, format='jd')
        this_time = tel.twilight_evening_astronomical(this_time, which='previous')

    return min_AM

def target_table_from_frbs(frbs:list):


    # Loop in FRBTansients
    rows = []
    for itransient in frbs:
        rdict = {}
        rdict['TNS'] = itransient.name
        rdict['FRB_RA'] = itransient.ra
        rdict['FRB_Dec'] = itransient.dec
        rdict['FRB_DM'] = itransient.DM

        # Host?
        if itransient.host:
            rdict['Host_name'] = itransient.host.name
            rdict['Host_RA'] = itransient.host.ra
            rdict['Host_Dec'] = itransient.host.dec
            rdict['Host_POx'] = itransient.host.P_Ox
            # Photometry
            ifilter, mag = itransient.host.FilterMagString()
            rdict['Host_mag'] = float(mag)
            rdict['Host_filter'] = ifilter
        #
        rows.append(rdict)

    # Table
    df = pandas.DataFrame(rows)

    # Return
    return df