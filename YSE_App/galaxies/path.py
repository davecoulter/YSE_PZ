""" Module for PATH related items """

import numpy as np
import pandas
import datetime

from astropy.coordinates import SkyCoord

from YSE_App.common.utilities import getGalaxyname
from YSE_App import data_utils
from YSE_App.models import Host, Path, HostPhotData 
from YSE_App.models import HostPhotometry, PhotometricBand
from YSE_App.models import Transient
from YSE_App.models.instrument_models import Instrument
from YSE_App.models.enum_models import ObservationGroup

from IPython import embed

# ########################3
# PRIORS

chime_priors = {}
chime_priors['PU'] = 0.2
chime_priors['survey'] = 'Pan-STARRS'
chime_priors['scale'] = 0.5

def ingest_path_results(itransient:Transient,
                        candidates:pandas.DataFrame, 
                        Filter:str,
                        inst_name:str,
                        obs_group:str,
                        P_Ux:float, user):

    # Add to DB
    for ss in range(len(candidates)):
        icand = candidates.iloc[ss]
        # Add or grab the host candidates
        name = getGalaxyname(icand.ra, icand.dec)
        host = data_utils.add_or_grab_obj(
            Host, dict(name=name), dict(ra=icand.ra, dec=icand.dec, 
                       ang_size=icand.ang_size), user=user)

        # Photometry
        hp = data_utils.add_or_grab_obj(
            HostPhotometry, 
            dict(host=host, instrument=Instrument.objects.get(name=inst_name), 
                 obs_group=ObservationGroup.objects.get(name=obs_group)),
                 {}, user=user)
        hpd = data_utils.add_or_grab_obj(
            HostPhotData, 
            dict(photometry=hp,
                 band=PhotometricBand.objects.filter(instrument__name=inst_name).get(name=Filter)),
            dict(mag=icand.mag, 
                 obs_date=datetime.datetime.now()),
            user=user)

        # Add to transient
        itransient.candidates.add(host)

        # PATH
        ipath = Path(transient_name=itransient.name, 
                     host_name=host.name, P_Ox=icand.P_Ox,
                     created_by_id=user.id, modified_by_id=user.id)
        ipath.save()

    # PATH P(U|x)
    itransient.P_Ux = P_Ux

    # Save
    itransient.save()

    # Return (mainly for testing)
    return hp.instrument


def run_path_on_instance(instance, ssize:float=5., 
                         priors:dict=None,
                         min_loc_err:float=0.2,
                         tot_posterior:float=0.999,
                         nmin:int=2, nmax:int=10):
    """ Run PATH on a single Transient instance or a pandas.Series

    For the current implementation, the instance must have the following attributes:
     - ra
     - dec
     - ra_err
     - dec_err
     
    and the code assumes it is an ellipse with PA=0deg (E from N)

    The PATH priors `dict` must inclue the following keys:
      - survey (str): Survey name (e.g. 'Pan-STARRS')
      - PU (float): Probability of a galaxy being unseen
      - scale (float): Scale factor for the galaxy size (e.g. 0.5)

    After the calculation is performed, the candidates are cut down to 
    represent the cumulative 99.9% poseterior, including P(U|x) with 
    a maximum of `nmax` candidates.

    Args:
        instance (): Transient or pandas.Series instance of a Transient
        ssize (float, optional): Radius for probing the survey (arcmin). Defaults to 5.
        priors (dict, optional): PATH priors. Defaults to None, in which 
            case the CHIME defaults are used.
        min_loc_err (float, optional): _description_. Defaults to 0.2.
        tot_posterior (float, optional): Total posterior probability to
            for the candidates (including P(U|x)). Defaults to 0.999.
        nmin (int, optional): Minimum number of objects to return, if this
            many canidates exist. Defaults to 2.
        nmax (int, optional): Maximum number of objects to return. Defaults to 10.

    Returns:
        tuple: pandas.DataFrame of the candidates, P(U|x) for the best candidate,
            PATH object
    """
    from astropath import path
    from astropath import catalogs


    if priors is None:
        priors = chime_priors

    # Lcalization
    # TODO -- Allow for PA
    eellipse = {'a': max(min_loc_err, instance.dec_err*3600), 
                'b': max(min_loc_err, instance.ra_err*np.cos(instance.dec*np.pi/180.)*3600), 
                'theta': 0.}

    # Load up the survey
    coord = SkyCoord(ra=instance.ra, dec=instance.dec, unit='deg')

    # Grab the catalog
    catalog, mag_key = catalogs.query_catalog(priors['survey'], 
                                              coord, 
                                              ssize)
    if len(catalog) == 0:
        return None, None

    # Set boxsize accoring to the largest galaxy (arcsec)
    box_hwidth = max(30., 10.*np.max(catalog['ang_size']))

    # Cut down the catalog based on box_hwidth
    Ddec_arcsec = np.abs(catalog['dec'].data - instance.dec)*3600.
    Dra_arcsec = np.abs(catalog['ra'].data - instance.ra)*3600.*np.cos(instance.dec*np.pi/180.)

    keep = (Ddec_arcsec < box_hwidth) & (Dra_arcsec < box_hwidth)
    cut_catalog = catalog[keep]

    # Turn into a cndidate table
    Path = path.PATH()

   # Set up localization
    Path.init_localization('eellipse', 
                           center_coord=coord, 
                           eellipse=eellipse)
    # Coords
    Path.init_candidates(cut_catalog['ra'],
                         cut_catalog['dec'],
                         cut_catalog['ang_size'],
                         mag=cut_catalog[mag_key])

    # Candidate prior
    Path.init_cand_prior('inverse', P_U=priors['PU'])

    # Offset prior
    Path.init_theta_prior('exp', 6., priors['scale'])

    # Priors
    p_O = Path.calc_priors()

    # Posterior
    P_Ox, P_Ux = Path.calc_posteriors('fixed', box_hwidth=box_hwidth, 
        max_radius=box_hwidth, step_size=eellipse['b']/3.)

    # Finish
    Path.candidates.sort_values(by='P_Ox', ascending=False, inplace=True)

    # Print
    print(Path.candidates[['ra', 'dec', 'ang_size', 'mag', 'P_O', 'P_Ox']])
    print(f"P_Ux = {Path.candidates['P_Ux'][0]}")

    # Cumulative posterior
    cum_post = np.cumsum(Path.candidates['P_Ox'])
    cut = np.where(cum_post+P_Ux < tot_posterior)[0]

    # Trim down 
    nobj = max(nmin, min(nmax, len(cut)+1))
    # Allow for not enough candidates
    nobj = min(nobj, len(Path.candidates))

    # Return
    return Path.candidates.iloc[:nobj], P_Ux, Path, mag_key, priors