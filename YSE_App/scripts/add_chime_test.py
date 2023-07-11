""" Add CHIME test FRBs to the database """
import os
from pkg_resources import resource_filename
from YSE_App.models import Transient
from YSE_App.models.enum_models import ObservationGroup

from django.contrib import auth
from django.db.models import ForeignKey

import pandas


def run():
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'test_files'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Add CHIME ObservatoniGroup?
    obs_names = [obs.name for obs in ObservationGroup.objects.all()]
    flag_CHIME = False
    if 'CHIME' not in obs_names:
        obs = ObservationGroup(name='CHIME', created_by_id=user.id, modified_by_id=user.id)
        obs.save()
        flag_CHIME = True

    # TNS names
    tns_names = [t.name for t in Transient.objects.all()]

    # Loop on me
    dbtransients = []
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]
        transientkeys = transient.keys()

        if transient['name'] in tns_names:
            raise IOError(f"Transient {transient['name']} already exists in the database")

        transientdict = {'created_by_id':user.id,
                         'modified_by_id':user.id}

        for transientkey in transientkeys:
            if transientkey == 'transientphotometry' or \
                transientkey == 'transientspectra' or \
                transientkey == 'host' or \
                transientkey == 'tags' or \
                transientkey == 'gw' or \
                transientkey == 'non_detect_instrument' or \
                transientkey == 'internal_names': continue
            if not isinstance(Transient._meta.get_field(transientkey), ForeignKey):
                if transient[transientkey] is not None: transientdict[transientkey] = transient[transientkey]
            else:
                fkmodel = Transient._meta.get_field(transientkey).remote_field.model
                fk = fkmodel.objects.filter(name=transient[transientkey])
                transientdict[transientkey] = fk[0]

        # Build it
        dbtransient = Transient(**transientdict)

        # Add to list
        dbtransients.append(dbtransient)

        # Save me!
        dbtransient.save()

    # Test them!

    # Break it down
    if flag_CHIME:
        obs.delete()

    for dbtransient in dbtransients:
        dbtransient.delete()