""" Module for PATH related items """

import numpy as np
import pandas
import datetime

from astropy.coordinates import SkyCoord

from YSE_App.common.utilities import getGalaxyname
from YSE_App.models import FRBGalaxy, GalaxyPhotData 
from YSE_App.models import GalaxyPhotometry, PhotometricBand
from YSE_App.models import FRBTransient, Path
from YSE_App.models import TransientStatus
from YSE_App.models.instrument_models import Instrument
from YSE_App.models.enum_models import ObservationGroup

from YSE_App import frb_utils
from YSE_App import frb_status

from IPython import embed

# ########################3
# PRIORS

chime_priors = {}
chime_priors['PU'] = 0.2
chime_priors['survey'] = 'Pan-STARRS'
chime_priors['scale'] = 0.5

def ingest_path_results(itransient:FRBTransient,
                        candidates:pandas.DataFrame,
                        Filter:str,
                        inst_name:str,
                        obs_group:str,
                        P_Ux:float, user,
                        bright_star:int=None,
                        remove_previous:bool=True):
    """ Method to ingest a table of PATH results into the DB

    The tables where entries are create/updated include:
      - FRBGalaxy: Each candidate is added
      - GalaxyPhotometry: Add PATH photometry for each candidate 
      - GalaxyPhotData: Added for each candidate 
      - FRBTransient: Add P_Ux

    Args:
        itransient (FRBTransient): FRBTansient object
        candidates (pandas.DataFrame): 
            Table of candidates from PATH
        Filter (str): Name of the filter
        inst_name (str): Name of the instrument
        obs_group (str): Name of the observation group
        P_Ux (float): PATH unseen probability P(U|x)
        bright_star (int, optional): 1=a bright star near the FRB 
            If not None, add to FRBTransient
        user (django user object): user 
        remove_previous (bool, optional): If True, remove any previous
            entries related to PATH from the DB. Defaults to True.

    Returns:
        str: DB name for the instrument (mainly used for testing)
    """

    # TODO -- move the following code to a utility module
    # Remove previous
    if remove_previous:
        for p in Path.objects.filter(transient=itransient):
            galaxy = FRBGalaxy.objects.get(name=p.galaxy.name)
            # Remove candidate
            itransient.candidates.remove(galaxy)
            # Remove galaxy altogether (likely)?
            delete_galaxy = True
            for t in FRBTransient.objects.all():
                if galaxy in t.candidates.all():
                    delete_galaxy = False
            if delete_galaxy:  # This also deletes the photometry
                galaxy.delete()
            # Delete from PATH table
            p.delete()

    # Add new ones to DB
    print('Looping on candidates')
    for ss in range(len(candidates)):
        icand = candidates.iloc[ss]
        print(f"ss: {ss}, ra: {icand.ra}, dec: {icand.dec}")
        # Add or grab the host candidates
        name = getGalaxyname(icand.ra, icand.dec)
        galaxy = frb_utils.add_or_grab_obj(
            FRBGalaxy, dict(name=name), dict(ra=icand.ra, dec=icand.dec, 
                       ang_size=icand.ang_size), user=user)

        # Add redshifts (these need not exist)
        if hasattr(icand, 'redshift_type') and icand.redshift_type == 'spectro-z':
            galaxy.redshift = icand.redshift
            galaxy.redshift_err = icand.redshift_err
            galaxy.redshift_source = icand.redshift_source
            galaxy.redshift_quality = 1
        elif hasattr(icand,'redshift_type') and icand.redshift_type == 'photo-z':
            galaxy.photoz = icand.redshift
            galaxy.photoz_err = icand.redshift_err
            galaxy.photoz_source = icand.redshift_source
        else:
            pass
        galaxy.save()


        # Photometry
        gp = frb_utils.add_or_grab_obj(
            GalaxyPhotometry, 
            dict(galaxy=galaxy, instrument=Instrument.objects.get(name=inst_name), 
                 obs_group=ObservationGroup.objects.get(name=obs_group)),
                 {}, user=user)
        band=PhotometricBand.objects.filter(instrument__name=inst_name).get(name=Filter)
        gpd = frb_utils.add_or_grab_obj(
            GalaxyPhotData, 
            dict(photometry=gp,
                 band=band),
            dict(mag=icand.mag, 
                 obs_date=datetime.datetime.now()),
            user=user)

        # Add to transient
        itransient.candidates.add(galaxy)

        # PATH
        ipath = Path(transient=itransient, 
                     galaxy=galaxy, P_Ox=icand.P_Ox,
                     created_by_id=user.id, modified_by_id=user.id)
        ipath.band = band
        ipath.save()

    print(f"Done with candidates.  Now P_Ux: {P_Ux}, {bright_star}")
    # PATH P(U|x)
    itransient.P_Ux = P_Ux

    # Bright star?
    print(f"Bright star")
    if bright_star is not None:
        itransient.bright_star = bool(bright_star)

    # Set host from highest P_Ox
    print(f"P_Ox")
    itransient.host = itransient.best_Path_galaxy

    # Set status
    print(f"Updating status")
    frb_status.set_status(itransient)


    # Return (mainly for testing)
    return str(gp.instrument)

