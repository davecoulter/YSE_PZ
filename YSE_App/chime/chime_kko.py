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

    return

    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_kko_sep2023.csv')
    df_frbs = pandas.read_csv(csv_file)

    # Add CHIME Observation Group?
    survey_names = [survey.name for survey in FRBSurvey.objects.all()]
    for survey in ['CHIME/FRB']:
        if survey not in survey_names:
            obs = FRBSurvey(name=survey, created_by_id=user.id, modified_by_id=user.id)
            obs.save()

    # Add em 
    transients = ctu.add_df_to_db(df_frbs, user, 
                         delete_existing=False)

    # Set the KKO tag
    kko_tag = frb_utils.add_or_grab_obj(
            FRBTag, dict(name='CHIME-KKO'), {}, user)
    unkn_tag = frb_utils.add_or_grab_obj(
            FRBTag, dict(name='CHIME-Unknown'), {}, user)
    for transient in transients:
        # Drop unknown
        transient.frb_tags.remove(unkn_tag)
        #
        transient.frb_tags.add(kko_tag)
        # Update status (and save)
        frb_status.set_status(transient)