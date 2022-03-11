#!/usr/bin/env python
# D. Jones - 11/25/19

"""skycell utils.  Get image/tarball name for given candidates"""

from YSE_App.models.transient_models import *
from YSE_App.models.survey_models import *
import datetime
from astropy.coordinates import SkyCoord, Angle
import html
import requests
import re


def ZTF_TNS_YSE_matches():

    for a in AlternateTransientNames.objects.filter(name__startswith="ZTF"):
        image_id = get_recent_image_from_coord(a.transient.ra, a.transient.dec)
        skycell, xpos, ypos = getskycell(a.transient.ra, a.transient.dec)

        print(
            a.transient.name,
            a.transient.ra,
            a.transient.dec,
            a.transient.recent_mag(),
            image_id,
            skycell,
            xpos,
            ypos,
        )


def get_recent_image_from_coord(ra, dec, debug=False):

    sc = SkyCoord(ra, dec, unit=u.deg)

    recentmjd = date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(14))
    survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)

    for s in survey_obs:
        width_corr = 3.1 / np.abs(np.cos(s.survey_field.dec_cen))
        ra_offset = Angle(width_corr / 2.0, unit=u.deg)
        dec_offset = Angle(3.1 / 2.0, unit=u.deg)
        sc2 = SkyCoord(s.survey_field.ra_cen, s.survey_field.dec_cen, unit=u.deg)
        ra_min = sc2.ra - ra_offset
        ra_max = sc2.ra + ra_offset
        dec_min = sc2.dec - dec_offset
        dec_max = sc2.dec + dec_offset
        if sc.ra > ra_min and sc.ra < ra_max and sc.dec > dec_min and sc.dec < dec_max:
            return s.image_id
    return None


def getskycell(ra, dec):

    session = requests.Session()
    session.auth = ("ps1sc", "skysurveys")
    skycellurl = "http://pstamp.ipp.ifa.hawaii.edu/findskycell.php"

    # First login. Returns session cookie in response header. Even though status_code=401, it is ok
    page = session.post(skycellurl)

    info = {"ra": (None, ra), "dec": (None, dec)}
    page = session.post(skycellurl, data=info)

    skycell = page.text.split("<tr><td>RINGS.V3</td><td>skycell.")[-1].split("</td>")[0]
    xpos = (
        page.text.split("<tr><td>RINGS.V3</td><td>skycell.")[-1]
        .split("<td>")[1]
        .split("</td>")[0]
    )
    ypos = (
        page.text.split("<tr><td>RINGS.V3</td><td>skycell.")[-1]
        .split("<td>")[2]
        .split("</td>")[0]
    )

    # rings = "<tr><td>RINGS.V3</td><td>skycell.1241.019</td><td>2504.54</td><td>2868.85</td></tr>"

    return skycell, xpos, ypos
