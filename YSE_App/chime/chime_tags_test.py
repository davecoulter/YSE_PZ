""" Add CHIME test FRBs to the database 
and confirm they follow the Survey logic """

import os
from pkg_resources import resource_filename

from django.contrib import auth
from django.db.models import ForeignKey

from YSE_App.models import Transient
from YSE_App.models.enum_models import ObservationGroup, TransientClass
from YSE_App.chime import tags as chime_tags
from YSE_App.models.tag_models import FRBTag


import pandas

from IPython import embed

def run():
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_tests.csv')
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

        # Tag (must come after saving)
        tags = chime_tags.set_from_instance(dbtransient)
        frb_tags = [ftag.name for ftag in FRBTag.objects.all()]
        new_tags = []
        for tag_name in tags:
            # Add?
            if tag_name not in frb_tags:
                new_tag = FRBTag(name=tag_name, created_by_id=user.id, modified_by_id=user.id)
                new_tag.save()
                new_tags.append(new_tag)
            # Use
            frb_tag = FRBTag.objects.get(name=tag_name)

            dbtransient.frb_tags.add(frb_tag)
        
        dbtransient.save()


    # Test them!
    embed(header='86 of chime_survey_test.py')

    # Break it all down
    if flag_CHIME:
        obs.delete()

    for new_tag in new_tags:
        new_tag.delete()

    for dbtransient in dbtransients:
        dbtransient.delete()

    # Finish
    print(Transient.objects.all())