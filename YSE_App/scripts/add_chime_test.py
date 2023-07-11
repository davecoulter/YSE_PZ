""" Add CHIME test FRBs to the database """
import os
from pkg_resources import resource_filename
from YSE_App.models import Transient

from django.contrib import auth
from django.db.models import ForeignKey

import pandas


def run():
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'test_files'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Loop on me
    dbtransients = []
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]
        transientkeys = transient.keys()

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

        # Build it
        dbtransient = Transient(**transientdict)
        dbtransients.append(dbtransient)

            # Save me!