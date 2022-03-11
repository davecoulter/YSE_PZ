import numpy as np
from django.conf import settings as djangoSettings

# read csv file
# format=NAME,RA,DEC,DIST,BMAG,JMAG,KMAG,TYPE,EXTINCTION(A_V)
usecols = (1, 2)
ra_cat, dec_cat = np.loadtxt(
    "%sYSE_App/tags/thacher.csv" % djangoSettings.STATIC_ROOT,
    unpack=True,
    usecols=usecols,
    delimiter=",",
)


def thacher_transient_search(ra, dec, fov=21, file="thacher.csv"):

    # Default input fov is arcmin
    fov = fov / 60.0

    # For input ra,dec, basically just need to check
    # if coords land inside fov from ra0,dec0 for all
    # ra0,dec0 in ra_cat,dec_cat
    if any(
        [
            ra > ra0 - fov / (2.0 * np.cos(dec0 * np.pi / 180))
            and ra < ra0 + fov / (2.0 * np.cos(dec0 * np.pi / 180))
            and dec < dec0 + fov / 2.0
            and dec > dec0 - fov / 2.0
            for ra0, dec0 in zip(ra_cat, dec_cat)
        ]
    ):
        return True
    else:
        return False
