""" Build up the Test DB (may be more than one option)"""

import datetime
import os
from pkg_resources import resource_filename

from django.contrib import auth

import pandas

from YSE_App.models import *
from YSE_App.chime import chime_test_utils as ctu
from YSE_App import frb_init

def init_kko(clean:bool=True):
    """ Build the CHIME KKO DB from scratch """

    user = auth.authenticate(username='root', password='F4isthebest')

    # Clean first
    ctu.clean_all()

    # ##############################
    # Init the DB
    # Status
    frb_init.init_status(user)

    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_kko_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    # Add CHIME Observation Group?
    survey_names = [survey.name for survey in FRBSurvey.objects.all()]
    for survey in ['CHIME/FRB']:
        if survey not in survey_names:
            obs = FRBSurvey(name=survey, created_by_id=user.id, modified_by_id=user.id)
            obs.save()

    # Add em 
    _ = ctu.add_df_to_db(df_frbs, user, 
                         delete_existing=False)