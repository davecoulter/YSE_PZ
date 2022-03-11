import datetime
import json
import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pylab
import requests
import tensorflow as tf
from astropy.io import ascii
from astropy.table import Table
from django.conf import settings as djangoSettings
from django_cron import CronJobBase
from django_cron import Schedule
from tensorflow import keras

from photoz_helper import evaluate
from photoz_helper import get_common_constraints_columns
from photoz_helper import load_lupton_model
from photoz_helper import preprocess
from photoz_helper import serial_objID_search
from YSE_App.common.alert import sendemail
from YSE_App.models.transient_models import *

try:  # Python 3.x
    from urllib.parse import quote as urlencode
    from urllib.request import urlretrieve
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode
    from urllib import urlretrieve

try:  # Python 3.x
    import http.client as httplib
except ImportError:  # Python 2.x
    import httplib

import sfdmap  # https://github.com/kbarbary/sfdmap


class YSE(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.PS1_PhotoZ.YSE"

    def do(self):
        try:
            nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
            from django.db.models import Q  # HAS To Remain Here

            # save time b/c the other cron jobs print a time for completion

            transients = Transient.objects.filter(Q(host__isnull=False))
            mask = []
            objIDs = []
            key = {}
            for T in transients:
                if T.host.panstarrs_objid:
                    mask.append(True)
                    objIDs.append(T.host.panstarrs_objid)
                    key[T.host.panstarrs_objid] = T
                else:
                    mask.append(False)

            print("photoz len(objids): ", len(objIDs))
            if len(objIDs) == 0:
                # print('return nothing since nothing in objIDs')
                # since nothing in objIDs, no search, so we are done
                return
            constraints, columns = get_common_constraints_columns()
            DFs = serial_objID_search(objIDs, columns=columns, **constraints)

            DF = pd.concat(DFs)

            dust_PATH = os.path.join(djangoSettings.STATIC_ROOT, "sfddata-master/")
            model_PATH = os.path.join(djangoSettings.STATIC_ROOT, "MLP_lupton.hdf5")

            mymodel, range_z = load_lupton_model(model_PATH)

            X = preprocess(DF, dust_PATH)

            posteriors, point_estimates, errors = evaluate(X, mymodel, range_z)

            objids_returned = DF["objID"].values

            for j, objID in enumerate(objids_returned):
                T = key[int(objID)]
                T.host.photo_z_internal = point_estimates[j]
                T.host.photo_z_err_internal = errors[j]
                T.host.save()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(
                """PS Photo-z cron failed with error %s at line number %s"""
                % (e, exc_tb.tb_lineno)
            )
            # html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            # sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
