""" Module for PATH related items """

import numpy as np
import pandas
import datetime

from astropy.coordinates import SkyCoord

from YSE_App.common.utilities import getGalaxyname
from YSE_App import data_utils
from YSE_App.models import FRBGalaxy, GalaxyPhotData 
from YSE_App.models import GalaxyPhotometry, PhotometricBand
from YSE_App.models import FRBTransient, Path
from YSE_App.models import TransientStatus
from YSE_App.models.instrument_models import Instrument
from YSE_App.models.enum_models import ObservationGroup

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
                        deeper:bool,
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
        user (django user object): user 
        deeper (bool): If True, request deeper photometry
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
        galaxy = data_utils.add_or_grab_obj(
            FRBGalaxy, dict(name=name), dict(ra=icand.ra, dec=icand.dec, 
                       ang_size=icand.ang_size), user=user)

        # Photometry
        gp = data_utils.add_or_grab_obj(
            GalaxyPhotometry, 
            dict(galaxy=galaxy, instrument=Instrument.objects.get(name=inst_name), 
                 obs_group=ObservationGroup.objects.get(name=obs_group)),
                 {}, user=user)
        gpd = data_utils.add_or_grab_obj(
            GalaxyPhotData, 
            dict(photometry=gp,
                 band=PhotometricBand.objects.filter(instrument__name=inst_name).get(name=Filter)),
            dict(mag=icand.mag, 
                 obs_date=datetime.datetime.now()),
            user=user)

        # Add to transient
        itransient.candidates.add(galaxy)

        # PATH
        ipath = Path(transient=itransient, 
                     galaxy=galaxy, P_Ox=icand.P_Ox,
                     created_by_id=user.id, modified_by_id=user.id)
        ipath.save()

    # PATH P(U|x)
    itransient.P_Ux = P_Ux

    # Set host from highest P_Ox
    itransient.host = itransient.best_Path_galaxy

    # Set status
    if deeper:
        itransient.status = TransientStatus.objects.get(name='Image')
    else:
        itransient.status = TransientStatus.objects.get(name='Spectrum')

    # Save to DB
    itransient.save()

    # Return (mainly for testing)
    return str(gp.instrument)

