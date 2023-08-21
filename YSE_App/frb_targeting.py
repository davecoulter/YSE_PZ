""" Methods for FRB targeting """

from YSE_App.models import *

import pandas

from astroplan import Observer
from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord, EarthLocation
from astropy import units

from IPython import embed

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

def target_table_from_frbs(frbs, ttype:str):
    """ Generate a pandas table from a list or QuerySet of FRBs

    Args:
        frbs (QuerySet): List of FRBTransient objects

    Returns:
        pandas.DataFrame: table of FRBTransient properties
    """


    # Loop in FRBTansients
    rows = []
    for itransient in frbs.all():
        rdict = {}
        rdict['TNS'] = itransient.name
        rdict['FRB_RA'] = itransient.ra
        rdict['FRB_Dec'] = itransient.dec
        rdict['FRB_DM'] = itransient.DM
        rdict['FRB_Survey'] = itransient.FRBSurveyString()
        rdict['FRB_tags'] = itransient.FRBTagsString()

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
    if len(df) > 0:
        df['Target_type'] = ttype

    # Return
    return df

def targetfrbs_for_fu(frb_fu):
    """ Provided an FRBFollowupResource, return the
    QuerySet of FRBTransient objects that are acceptible

    This may be moved as a method to FRBFollowupResource

    Returns:
        QuerySet of FRBTransient:  _description_
    """
    # 
    # Check Surveys
    if frb_fu.frb_surveys == 'all':
        gd_frbs = FRBTransient.objects.all()
    else:
        gd_frbs = FRBTransient.objects.filter(frb_survey__in=FRBSurvey.objects.filter(
            name__in=frb_fu.frb_surveys.split(',')))

    # Status
    if frb_fu.frb_statuses:
        gd_frbs = gd_frbs.filter(status__in=TransientStatus.objects.filter(
            name__in=frb_fu.frb_statuses.split(',')))
    else:
        gd_frbs = gd_frbs.filter(status=TransientStatus.objects.get(name='New'))

    # Tags?
    if frb_fu.frb_tags:
        gd_frbs = gd_frbs.filter(frb_tags__in=FRBTag.objects.filter(name__in=frb_fu.frb_tags.split(',')))
    
    return gd_frbs

def grab_targets_by_mode(frb_fu, frbs):

    # Imaging
    if frb_fu.num_targ_img > 0:
        imaging_frbs = frbs.filter(host__isnull=True)
    else:
        imaging_frbs = FRBTransient.objects.none()


    # Longslit
    if frb_fu.num_targ_longslit > 0:
        longslit_frbs = frbs.filter(host__isnull=False)
        if frb_fu.min_POx:
            gd_ids = []
            for frb in longslit_frbs:
                if frb.host.P_Ox is not None and frb.host.P_Ox > frb_fu.min_POx:
                    gd_ids.append(frb.id)
            longslit_frbs = longslit_frbs.filter(id__in=gd_ids)

    # Mask -- Not yet implemented
    mask_frbs = FRBTransient.objects.none()

    # Populate
    targets_by_mode = {}
    targets_by_mode['imaging'] = imaging_frbs
    targets_by_mode['longslit'] = longslit_frbs
    targets_by_mode['mask'] = mask_frbs

    # Return
    return targets_by_mode
