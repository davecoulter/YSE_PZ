""" Common methods for CHIME tests """

import pandas

from django.db.models import ForeignKey

from YSE_App.models import *

def add_df_to_db(df_frbs:pandas.DataFrame, user, delete_existing:bool=False):
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
                    import pdb; pdb.set_trace()

        # Build it
        dbtransient = FRBTransient(**transientdict)

        # Add to list
        dbtransients.append(dbtransient)

        # Save me!
        dbtransient.save()

    # Return
    return dbtransients

def clean_all(skip_resources:bool=False):
    """ Wipe clean the DB """

    print("Removing Path objects")
    for ipath in Path.objects.all():
        ipath.delete()

    print("Removing FRBGalaxy objects")
    for galaxy in FRBGalaxy.objects.all():
        galaxy.delete()

    # FRBFollowUpResource
    if not skip_resources:
        print("Removing FRBFollowUpResource objects")
        for frb_fu in FRBFollowUpResource.objects.all():
            frb_fu.delete()

    print("Removing FRBTransient objects")
    for itransient in FRBTransient.objects.all():
        itransient.delete()