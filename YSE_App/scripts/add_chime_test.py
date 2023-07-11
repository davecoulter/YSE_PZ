""" Add CHIME test FRBs to the database """
import os
from pkg_resources import resource_filename
from YSE_App.models import Transient

from django.contrib import auth

import pandas


def run():
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'tests'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Loop on me
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]
        transientdict = {'created_by_id':user.id,
                         'modified_by_id':user.id}

        for transientkey in transientkeys: