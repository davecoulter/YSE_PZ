""" Module for PATH related items """

import numpy as np

from astropy.coordinates import SkyCoord


from astropath import path
from astropath import catalogs

from IPython import embed

# ########################3
# PRIORS

chime_priors = {}
chime_priors['PU'] = 0.2
chime_priors['survey'] = 'Pan-STARRS'
chime_priors['scale'] = 0.5


def run_path_on_instance(instance, ssize:float=5., 
                         priors=None,
                         min_loc_err=0.2,
                         nmin=2, nmax=10):

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

    embed(header='path.py: 79')