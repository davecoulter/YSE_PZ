""" Common methods for CHIME tests """

from YSE_App.models import Transient
from django.db.models import ForeignKey

def add_df_to_db(df_frbs, user, delete_existing:bool=False):

    # TNS names
    tns_names = [t.name for t in Transient.objects.all()]

    # Loop on me
    dbtransients = []
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]
        transientkeys = transient.keys()

        if transient['name'] in tns_names:
            if delete_existing:
                t = Transient.objects.get(name=transient['name'])
                t.delete()
            else:
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

    # Return
    return dbtransients