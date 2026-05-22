import numpy as np
from pathlib import Path
from django.conf import settings as djangoSettings

CATALOG_PATH = Path(djangoSettings.STATIC_ROOT) / "YSE_App" / "tags" / "thacher.csv"


def _load_catalog():
    # The Thacher tag is optional; missing catalog data should not crash app startup.
    if not CATALOG_PATH.exists():
        return np.array([]), np.array([])

    try:
        return np.loadtxt(CATALOG_PATH, unpack=True, usecols=(1, 2), delimiter=",")
    except (OSError, ValueError):
        return np.array([]), np.array([])


ra_cat, dec_cat = _load_catalog()


def thacher_transient_search(ra, dec, fov=21, file='thacher.csv'):

    # Default input fov is arcmin
    fov = fov / 60.0

    # For input ra,dec, basically just need to check
    # if coords land inside fov from ra0,dec0 for all
    # ra0,dec0 in ra_cat,dec_cat
    if not len(ra_cat):
        return False

    if any([ra > ra0 - fov / (2. * np.cos(dec0 * np.pi / 180)) and ra < ra0 + fov / (2. * np.cos(dec0 * np.pi / 180))
        and dec < dec0 + fov / 2. and dec > dec0 - fov / 2. for ra0, dec0 in zip(ra_cat, dec_cat)]):
        return True
    else:
        return False
