""" Common methods for CHIME tests """

import pandas

from django.db.models import ForeignKey

from YSE_App.models import Transient

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
    tns_names = [t.name for t in Transient.objects.all()]

    # Loop on me
    dbtransients = []
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]

        # Nearly all of the following was taken from add_transient() in data_utils.py
        transientkeys = transient.keys()

        if transient['name'] in tns_names:
            if delete_existing:
                t = Transient.objects.get(name=transient['name'])
                t.delete()
            else:
                print(f"Transient {transient['name']} already exists in the database")
                print("Skipping")
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

    # Return
    return dbtransients