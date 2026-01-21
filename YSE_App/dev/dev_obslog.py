""" Scripts for developing FRBFollowUpObservation """
import os
from pkg_resources import resource_filename

from django.contrib import auth

from YSE_App.models.frbfollowup_models import FRBFollowUpObservation, FRBFollowUpResource
from YSE_App.models import FRBTransient
from YSE_App import data_utils

import pandas

from IPython import embed

def add_obslog():
    csv_file = os.path.join(
        resource_filename('YSE_App', 'dev'), 'observing_logs.csv')

    obslogs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Add it
    row = obslogs.iloc[0]
    embed(header='30 of dev_obslog.py')
    transient=FRBTransient.objects.get(name=row['TNS'])
    resource=FRBFollowUpResource.objects.get(name=row['Resource'])

    required = dict(transient=transient, resource=resource, mode=row['mode'],
            conditions=row['Conditions'], texp=row['texp'], date=pandas.Timestamp(row['date']),
            success=row['success'])
    obs = data_utils.add_or_grab_obj(FRBFollowUpObservation, required, {}, user)

    # Remove it
    obs.delete()