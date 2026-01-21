""" Methods to init the DB """

import pandas

from YSE_App.models import TransientStatus
from YSE_App.models import ObservationGroup
from YSE_App.models import FRBSurvey
from YSE_App.frb_utils import add_or_grab_obj
from django.db.models import ForeignKey

from YSE_App import frb_status
from YSE_App import frb_utils
from YSE_App.models import FRBTransient
from YSE_App import frb_tags
from YSE_App.models import FRBSampleCriteria

from YSE_App.serializers import FRBSampleCriteriaSerializer


def init_obsgroups(user):
    """ Initialize the transient status table

    Args:
        user (): user
    """

    # Add into DB
    for obsgroup in ['DECaLS']:
        _ = add_or_grab_obj(ObservationGroup,
                        dict(name=obsgroup), {}, user)

def init_statuses(user):
    """ Initialize the transient status table

    Args:
        user (): user
    """

    # Delete all existing
    TransientStatus.objects.all().delete()

    # Add into DB
    for status in frb_status.all_status:
        _ = add_or_grab_obj(TransientStatus,
                        dict(name=status), {}, user)

def init_surveys(user):
    """ Initialize the FRBSurvey table 

    Args:
        user (): user
    """

    # Delete all existing
    FRBSurvey.objects.all().delete()

    # Add into DB
    for survey in ['CHIME/FRB']:
        _ = add_or_grab_obj(FRBSurvey,
                        dict(name=survey), {}, user)


def add_df_to_db(df_frbs:pandas.DataFrame, user, 
                 delete_existing:bool=False):
    """ Add a pandas DataFrame of FRBs to the database

    Args:
        df_frbs (pandas.DataFrame): pandas DataFrame of FRBs
        user (_type_): autheticated user
        delete_existing (bool, optional): If True, delete any
            existing FRBs with the same TNS first. Defaults to False.

    Raises:
        IOError: _description_

    Returns:
        list: list of the Transient objects added to the database
    """

    # TNS names
    tns_names = [t.name for t in FRBTransient.objects.all()]

    # Loop on me
    dbtransients = []
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]

        # Nearly all of the following was taken from add_transient() in data_utils.py
        transientkeys = transient.keys()

        if transient['name'] in tns_names:
            t = FRBTransient.objects.get(name=transient['name'])
            if delete_existing:
                t.delete()
            else:
                print(f"FRBTransient {transient['name']} already exists in the database")
                print("Skipping")
                dbtransients.append(t)
                continue

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
            if not isinstance(FRBTransient._meta.get_field(transientkey), ForeignKey):
                if transient[transientkey] is not None: transientdict[transientkey] = transient[transientkey]
            else:
                fkmodel = FRBTransient._meta.get_field(transientkey).remote_field.model
                fk = fkmodel.objects.filter(name=transient[transientkey])
                try:
                    transientdict[transientkey] = fk[0]
                except:
                    print(f'Bad key: {transientkey}')

        # Build it
        dbtransient = FRBTransient(**transientdict)

        # Set null status
        dbtransient.status = TransientStatus.objects.get(name='Unassigned')

        # Save me!
        dbtransient.save()

        # Tags
        if hasattr(transient, 'tags'):
            frb_tags.add_frb_tags(dbtransient, transient['tags'], user)

        # Add to list
        dbtransients.append(dbtransient)


    # Return
    return 200, 'All clear!'

