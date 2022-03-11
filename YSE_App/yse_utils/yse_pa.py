import astropy.coordinates as cd
import astropy.units as u
import numpy as np
from YSE_App.models import *
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from YSE_App.common.utilities import GetSexigesimalString
from matplotlib.patches import Rectangle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
from YSE_App.table_utils import TransientTable, TransientFilter
from YSE_App.queries.yse_python_queries import *
from django_tables2 import RequestConfig
from django.shortcuts import redirect
import subprocess
from random import sample

from astropy.time import Time
from astroplan import Observer

tel = Observer.at_site("keck", timezone="US/Hawaii")

# goodcells = {}
# with open("/Users/David/Dropbox/research/YSE_FieldSelection/YSE_scheduler/findcells/good_cells.txt") as fin:
#    for line in fin:
#        goodcells[line.split()[0][:-1]] = line.split()[1:]


def yse_pa(msb_name, pa=None):
    print(msb_name)
    # every MSB on the same PA
    survey_field_msb = SurveyFieldMSB.objects.get(name=msb_name)

    transients_in_field_query = []
    for sf in survey_field_msb.survey_fields.all():
        # find the interesting transients in the field
        d = sf.dec_cen * np.pi / 180
        width_corr = 3.3 / np.abs(np.cos(d))
        # Define the tile offsets:
        ra_offset = cd.Angle(width_corr / 2.0, unit=u.deg)
        dec_offset = cd.Angle(3.3 / 2.0, unit=u.deg)
        transients_in_field_query += [
            Q(ra__gt=sf.ra_cen - ra_offset.degree)
            & Q(ra__lt=sf.ra_cen + ra_offset.degree)
            & Q(dec__gt=sf.dec_cen - dec_offset.degree)
            & Q(dec__lt=sf.dec_cen + dec_offset.degree)
            & Q(tags__name="YSE")
        ]
    query_full = transients_in_field_query[0]
    for q in transients_in_field_query[1:]:
        query_full = np.bitwise_or(query_full, q)
    transients_in_field = Transient.objects.filter(query_full)

    scf = SkyCoord(sf.ra_cen, sf.dec_cen, unit=u.deg)

    tg = TransientTag.objects.filter(name="YSE good cell")
    transients_best = transients_in_field.filter(tags__in=tg)
    transients_2best = transients_in_field.filter(
        Q(status__name="Interesting") & ~Q(tags__in=tg)
    )
    transients_3best = transients_in_field.filter(
        Q(status__name="FollowupRequested") & ~Q(tags__in=tg)
    )
    transients_4best = transients_in_field.filter(
        Q(status__name="Following") & ~Q(tags__in=tg)
    )

    # figure out the PA for today, best airmass
    t = Time.now()
    time_start = "05:00:00"
    time_end = "15:00:00"
    night_start = tel.twilight_evening_astronomical(t, which="previous")
    night_end = tel.twilight_morning_astronomical(t, which="previous")
    hourmin, hourmax = (
        int(night_start.iso.split()[-1].split(":")[0]),
        int(night_end.iso.split()[-1].split(":")[0]),
    )
    airmass, times = np.array([]), np.array([])
    for hour in range(hourmin, hourmax + 1):
        time_obs = "%s %02i:%s:00" % (t.iso.split()[0], hour, time_start.split(":")[1])
        time = Time(time_obs)
        altaz = tel.altaz(time, scf)
        if altaz.alt.value < 0:
            continue
        airmass = np.append(
            airmass, 1 / np.cos((90.0 - altaz.alt.value) * np.pi / 180.0)
        )
        times = np.append(times, time)
    time = times[airmass == np.min(airmass)]
    parallactic_angle = tel.parallactic_angle(time[0], scf)

    if pa is not None:
        rotator_angles = np.array([180 - pa + parallactic_angle.deg])
    else:
        rotator_angles = np.linspace(-44, -183, 30)
    len_good, list_full = [], []
    for rotator_angle in rotator_angles:
        good_list = []
        pa = 180 - (-parallactic_angle.deg + rotator_angle)
        for i, transient_list in enumerate(
            [transients_4best, transients_3best, transients_2best, transients_best]
        ):
            for transient in transient_list:
                cmd = (
                    "echo %.7f %.7f | /Users/David/Dropbox/research/YSE_FieldSelection/YSE_scheduler/findcells/pscoords in=sky out=cell ra=%.7f dec=%.7f pa=%.1f dx=0 dy=0 dpa=0 sc=38.856"
                    % (transient.ra, transient.dec, sf.ra_cen, sf.dec_cen, pa)
                )
                output = subprocess.check_output(cmd, shell=True)
                ota, cell, centerx, centery = output.split()
                if (
                    "OTA" + ota.decode("utf-8") in goodcells.keys()
                    and cell.decode("utf-8") in goodcells["OTA" + ota.decode("utf-8")]
                ):
                    if i < 3:
                        good_list += [transient.name]
                    else:
                        good_list += [transient.name] * 4
        len_good += [len(good_list)]
        list_full += [[t for t in np.unique(good_list)]]

    iGood = np.argsort(len_good)[::-1][0:5]
    best_idx = sample(iGood.tolist(), 1)
    best_rotator = rotator_angles[best_idx]  # [np.array(len_good) == np.max(len_good)]
    list_good = np.array(list_full)[best_idx][
        0
    ]  # [np.array(len_good) == np.max(len_good)]
    best_pa = 180 - (-parallactic_angle.deg + best_rotator[0])
    return best_pa, list_good

    # if len(best_rotator) == 1:
    #    best_pa = 180 - (-parallactic_angle.deg + best_rotator[0])
    #    print(list_good)
    #    return best_pa,list_good
    # else:
    #    best_rotator = best_rotator[np.abs(rotator_angles[np.array(len_good) == np.max(len_good)]+115) == \
    #                                np.min(np.abs(rotator_angles[np.array(len_good) == np.max(len_good)]+115))][0]
    #    list_good = list_good[np.abs(rotator_angles[np.array(len_good) == np.max(len_good)]+115) == \
    #                          np.min(np.abs(rotator_angles[np.array(len_good) == np.max(len_good)]+115))][0]
    #    best_pa = 180 - (-parallactic_angle.deg + best_rotator)
    #    print(list_good)
    #    return best_pa,list_good
