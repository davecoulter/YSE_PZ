""" Add CHIME test FRBs to the database 
and confirm they follow the Survey logic """

import os
from pkg_resources import resource_filename

from django.contrib import auth

from YSE_App.models import FRBTransient
from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu


import pandas

from IPython import embed

def run(delete_existing:bool=False):
    """ Test the CHIME FRB tags

    Args:
        delete_existing (bool, optional): If True, delete any
            existing FRBs with the same TNS first. Defaults to False.
    """
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    # Authenticate
    user = auth.authenticate(username='root', password='F4isthebest')

    # Add CHIME ObservatoniGroup?
    obs_names = [obs.name for obs in ObservationGroup.objects.all()]
    flag_CHIME = False
    if 'CHIME' not in obs_names:
        obs = ObservationGroup(name='CHIME', created_by_id=user.id, modified_by_id=user.id)
        obs.save()
        flag_CHIME = True

    # Add em
    dbtransients = ctu.add_df_to_db(df_frbs, user, 
                                    delete_existing=delete_existing)

    # Test them!
    for ss in range(len(df_frbs)):
        ifrb = df_frbs.iloc[ss]
        assert ifrb['name'] in [t.name for t in FRBTransient.objects.all()]
        # Tag
        if ifrb['name'] == 'FRB20300102B':
            t = FRBTransient.objects.get(name=ifrb['name'])
            assert 'CHIME-Blind' in [t.name for t in t.frb_tags.all()]

    # Break it all down
    if flag_CHIME:
        obs.delete()

    #for new_tag in new_tags:
    #    new_tag.delete()

    for dbtransient in dbtransients:
        dbtransient.delete()

    # Finish
    print(FRBTransient.objects.all())
    print("All clear!")