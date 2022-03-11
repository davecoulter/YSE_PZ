from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.models import *

from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings
import datetime
import numpy as np
import pandas as pd
import os

import sys
import subprocess
from scipy import interpolate

from astropy.table import Table
import requests
from PIL import Image
from io import BytesIO
import pylab

from astropy.io import fits

import http
import urllib

from django.contrib.auth.models import User


user = User.objects.get(username="admin")  #!!!


def getimages(ra, dec, size=240, filters="grizy", type="stack"):

    """Query ps1filenames.py service to get a list of images

    ra, dec = position in degrees
    size = image size in pixels (0.25 arcsec/pixel)
    filters = string with filters to include
    Returns a table with the results
    """

    service = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
    url = (
        "{service}?ra={ra}&dec={dec}&size={size}&format=fits"
        "&filters={filters}&type={type}"
    ).format(**locals())
    table = Table.read(url, format="ascii")
    return table


def geturl(
    ra,
    dec,
    size=100,
    output_size=None,
    filters="grizy",
    format="jpg",
    color=False,
    type="stack",
):

    """Get URL for images in the table

    ra, dec = position in degrees
    size = extracted image size in pixels (0.25 arcsec/pixel)
    output_size = output (display) image size in pixels (default = size).
                  output_size has no effect for fits format images.
    filters = string with filters to include
    format = data format (options are "jpg", "png" or "fits")
    color = if True, creates a color image (only for jpg or png format).
            Default is return a list of URLs for single-filter grayscale images.
    Returns a string with the URL
    """

    if color and format == "fits":
        raise ValueError("color images are available only for jpg or png formats")
    if format not in ("jpg", "png", "fits"):
        raise ValueError("format must be one of jpg, png, fits")
    table = getimages(ra, dec, size=size, filters=filters, type=type)
    print(table)
    url = (
        "https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?"
        "ra={ra}&dec={dec}&size={size}&format={format}"
    ).format(**locals())
    if output_size:
        url = url + "&output_size={}".format(output_size)
    # sort filters from red to blue
    flist = ["yzirg".find(x) for x in table["filter"]]
    table = table[np.argsort(flist)]
    if color:
        if len(table) > 3:
            # pick 3 filters
            table = table[[0, len(table) // 2, len(table) - 1]]
        for i, param in enumerate(["red", "green", "blue"]):
            url = url + "&{}={}".format(param, table["filename"][i])
    else:
        urlbase = url + "&red="
        url = []
        for filename in table["filename"]:
            url.append(urlbase + filename)
    return url


class YSE(CronJobBase):

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.PS1_cutouts.YSE"

    def do(self, debug=True):

        try:
            nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
            from django.db.models import Q  # HAS To Remain Here, I dunno why

            print("Entered the PS cutout Cron")
            # save time b/c the other cron jobs print a time for completion

            transients = Transient.objects.filter(
                Q(host__isnull=False) & Q(host__dec__gt=-31)
            )  # & Q(something that prevents redownloading!)
            # we probably will have to run through the IDs and check what is currently available in th Cutouts folder

            counter = (
                0
            )  # for local testing don't grab too many or else i'll nuke my computer #!!!
            for T in transients:
                if T.host.ra and T.host.dec:  # and counter < 103: #!!!
                    ID = T.name
                    image = np.zeros((104, 104, 5))  # holds the final image
                    if os.path.isfile(
                        djangoSettings.STATIC_ROOT
                        + "/cutouts/cutout_{}_{}.npy".format(ID, "y")
                    ):
                        continue
                    try:
                        for i, F in enumerate(["g", "r", "i", "z", "y"]):
                            fitsurl = geturl(
                                ra=T.host.ra,
                                dec=T.host.dec,
                                size=104,
                                filters=F,
                                format="fits",
                            )
                            if not len(fitsurl):
                                continue
                            fh = fits.open(fitsurl[0])
                            image[:, :, i] = fh[0].data

                        number_nan_pixels = np.sum(np.isnan(image).astype(int))
                        if number_nan_pixels > 0:
                            for j in range(5):  # j is band information
                                if np.any(np.isnan(image[:, :, j])):
                                    backx = np.arange(0, image.shape[1])
                                    backy = np.arange(0, image.shape[0])
                                    backxx, backyy = np.meshgrid(backx, backy)
                                    array = np.ma.masked_invalid(image[:, :, j])
                                    x1 = backxx[np.logical_not(array.mask)]
                                    y1 = backyy[np.logical_not(array.mask)]
                                    newarr = array[np.logical_not(array.mask)]
                                    try:
                                        image[:, :, j] = interpolate.griddata(
                                            (x1, y1),
                                            newarr.ravel(),
                                            (backxx, backyy),
                                            method="cubic",
                                        )
                                    except:
                                        print(
                                            "whole image is NaN, this cutout may never work?"
                                        )
                                        print("keep track of my error: ", T.name)
                                        continue

                        image = (
                            image
                        ) / 10000.0  # everything in the same range as SDSS
                        image[image > 1] = 1  # now max 1 so everything in range -1, 1
                    except (urllib.error.HTTPError, http.client.IncompleteRead):
                        print("URL error, this cutout may never work?")
                        print("keep track of my error: ", T.name)
                        continue
                    except Exception as e:
                        continue
                    if np.any(
                        np.isnan(image)
                    ):  # quick last check that after interpolation something hasn't gone terribly wrong
                        continue
                    if np.all(
                        image == 0
                    ):  # quick check that the try loop failed to weed out missing files so my datarray was never updated
                        continue

                    # now save the final processed image as a numpy array, except in each band because thats how the image model works.
                    for i, F in enumerate(["g", "r", "i", "z", "y"]):
                        np.save(
                            djangoSettings.STATIC_ROOT
                            + "/cutouts/cutout_{}_{}.npy".format(ID, F),
                            image[:, :, i],
                        )  # save where? This has to be permanent, b/c link

                    h = T.host
                    for i, F in enumerate(["g", "r", "i", "z", "y"]):
                        hp = HostPhotometry(
                            host=h,
                            instrument=Instrument.objects.filter(name="GPC1")[0],
                            obs_group=ObservationGroup.objects.filter(
                                name="Pan-STARRS1"
                            )[0],
                            created_by=user,
                            modified_by=user,
                        )  # ,groups=???)#!!!
                        hp.save()

                        hpd = HostPhotData(
                            photometry=hp,
                            band=PhotometricBand.objects.filter(
                                instrument__name="GPC1"
                            ).filter(name=F)[0],
                            created_by=user,
                            modified_by=user,
                            obs_date=datetime.datetime.now(),
                        )  #!!! these are stack images, no one observing date...?
                        hpd.save()

                        hi = HostImage(
                            phot_data=hpd,
                            img_file=djangoSettings.STATIC_ROOT
                            + "/cutouts/cutout_{}_{}.npy".format(ID, F),
                            created_by=user,
                            modified_by=user,
                        )
                        hi.save()

                    h.save()
                    T.save()
                    counter += 1  #!!!
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(
                """PS1 Host cutout cron failed with error %s at line number %s"""
                % (e, exc_tb.tb_lineno)
            )
