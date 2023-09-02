""" Methods for dealing with FRB Observing """

from YSE_App.models import FRBFollowUpRequest
from YSE_App.models import FRBFollowUpResource
from YSE_App.models import TransientStatus
from YSE_App.models import FRBTransient

from YSE_App import data_utils

import pandas


def ingest_obsplan(obsplan:pandas.DataFrame, user):

    # Loop on rows
    for ss, row in obsplan.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['FRB'])
        except:
            return 202, f"FRB {row['FRB']} not in DB"

        # Check if the transient status is OK
        if row['mode'] in ['image']:
            if transient.status.name != 'Image':
                return 203, f"FRB {row['FRB']} not in Image status" 
        elif row['mode'] in ['longslit', 'mask']:
            if transient.status.name != 'Spectrum':
                return 203, f"FRB {row['FRB']} not in Spectrum status" 
        else:
            return 203, f"Mode {row['mode']} not allowed"

        # Grab the resource
        try:
            resource=FRBFollowUpResource.objects.get(name=row['Resource'])
        except:
            return 202, f"Resource {row['Resource']} not in DB"

        # Add if not already in there
        req = data_utils.add_or_grab_obj(
            FRBFollowUpRequest,
            dict(transient=transient, resource=resource, mode=row['mode']),
            {}, user)
                                   
        # Update transient status
        if row['mode'] in ['image']:
            transient.status = TransientStatus.objects.get(name='PendingImage') 
        elif row['mode'] in ['longslit', 'mask']:
            transient.status = TransientStatus.objects.get(name='PendingSpectrum') 

        # Save
        transient.save()

    return 200, "All good"
    