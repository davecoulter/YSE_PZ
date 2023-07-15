""" Add CHIME test for PATH analysis 
of an FRB added to the database """

import os
from pkg_resources import resource_filename

from django.contrib import auth
from django.db.models import ForeignKey

from YSE_App.models import Transient
from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu


import pandas

from IPython import embed

def run(delete_existing:bool=False):
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Add CHIME Observation Group?
    obs_names = [obs.name for obs in ObservationGroup.objects.all()]
    flag_CHIME = False
    if 'CHIME' not in obs_names:
        obs = ObservationGroup(name='CHIME', created_by_id=user.id, modified_by_id=user.id)
        obs.save()
        flag_CHIME = True

    # Add em
    dbtransients = ctu.add_df_to_db(df_frbs, user, 
                                    delete_existing=delete_existing)

    # Run PATH on one
    embed(header='40 of chime_path_test.py')

    # Test them!

    # Break it all down
    if flag_CHIME:
        obs.delete()

    #for new_tag in new_tags:
    #    new_tag.delete()

    for dbtransient in dbtransients:
        dbtransient.delete()

    # Finish
    print(Transient.objects.all())
    print("All clear!")