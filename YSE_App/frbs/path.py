""" Module for PATH related items """

import numpy as np

from astropy import units
from astropy.coordinates import SkyCoord


from astropath import path
from astropath import catalogs


chime_priors = {}
chime_priors['PU'] = 0.2
chime_priors['survey'] = 'Pan-STARRS'
chime_priors['scale'] = 0.5


def run_path_on_instance(instance, ssize:float, 
                         priors=None):

    if priors is None:
        priors = chime_priors

    # Lcalization
    # TODO -- All for PA
    eellipse = {'a': instance.dec_err, 
                'b': instance.ra_err, 
                'theta': 0.}

    # Load up the survey
    coord = SkyCoord(ra=instance.ra, dec=instance.dec, unit='deg')

    # Grab the catalog
    catalog, mag_key = catalogs.query_catalog(priors['survey'], 
                                              coord, 
                                              ssize)

    # Set boxsize accoring to the largest galaxy (arcsec)
    box_hwidth = max(30., 10.*np.max(catalog['ang_size']))

    # Turn into a cndidate table
    Path = path.PATH()

   # Set up localization
    Path.init_localization('eellipse', 
                           center_coord=coord, 
                           eellipse=eellipse)
    # Coords
    Path.init_candidates(catalog['ra'],
                         catalog['dec'],
                         catalog['ang_size'],
                         mag=catalog[mag_key])

    # Candidate prior
    Path.init_cand_prior('inverse', P_U=priors['PU'])

    # Offset prior
    Path.init_theta_prior('exp', 6., priors['scale'])

    # Priors
    p_O = Path.calc_priors()

    # Posterior
    P_Ox, P_Ux = Path.calc_posteriors('local', box_hwidth=box_hwidth, 
        max_radius=box_hwidth)

    # Finish
    Path.candidates.sort_values(by='P_Ox', ascending=False, inplace=True)

    # Print
    print(Path.candidates[['ra', 'dec', 'ang_size', 'mag', 'P_O', 'P_Ox']])
    print(f"P_Ux = {Path.candidates['P_Ux'][0]}")