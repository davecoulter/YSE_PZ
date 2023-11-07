""" Build up the Test DB (may be more than one option)"""

import datetime
import os
from pkg_resources import resource_filename

from django.contrib import auth

import pandas

from YSE_App.models import *
from YSE_App.chime import chime_test_utils as ctu
from YSE_App import frb_init
from YSE_App import frb_status
from YSE_App import frb_utils

def init_kko(clean:bool=True):
    """ Build the CHIME KKO DB from scratch """

    user = auth.authenticate(username='root', password='F4isthebest')

    # Clean first
    ctu.clean_all(skip_resources=True)

    # ##############################
    # Init the DB
    # Status
    frb_init.init_statuses(user)

    # Observing Groups
    frb_init.init_obsgroups(user)

    # Surveys
    frb_init.init_surveys(user)


    return


def init_DMISM():
    """ Stop gap to add DM_ISM to the KKO objects """

    for frb in FRBTransient.objects.all():
        if frb.DM_ISM is None:
            print(f'Working on: {frb.name}')
            # 
            frb.DM_ISM = frb.calc_DM_ISM()
            # Set status
            frb_status.set_status(frb)

            # Save
            frb.save()