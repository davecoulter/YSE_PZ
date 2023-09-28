""" Methods for dealing with FRB Observing """

from YSE_App.models import FRBFollowUpRequest
from YSE_App.models import FRBFollowUpResource
from YSE_App.models import FRBFollowUpObservation
from YSE_App.models import TransientStatus
from YSE_App.models import FRBTransient

from YSE_App import frb_utils
from YSE_App import frb_status

import pandas

def ingest_obsplan(obsplan:pandas.DataFrame, user,
                   scrub_previous_resource:bool=True):
    """ Ingest an observing plan into the DB

    This updates the transient status and adds to FRBFollowUpRequest

    Args:
        obsplan (pandas.DataFrame): _description_
        user (_type_): _description_
        scrub_previous_resource (bool, optional): If True, remove all 
        entries to the named resource from FRBFollowUpRequest.
          THIS OPTION IS NOT YET IMPLEMENTED

    Returns:
        tuple: (status, message) (int,str) 
    """

    # TODO
    # Scrub previous entries with the named resource?
    
    # Loop on rows
    for ss, row in obsplan.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['TNS'])
        except:
            return 401, f"FRB {row['TNS']} not in DB"

        # Check if the transient status is OK
        if row['mode'] in ['imaging']:
            if transient.status.name != 'NeedImage':
                return 402, f"FRB {row['TNS']} not in NeedImage status" 
        elif row['mode'] in ['longslit', 'mask']:
            if transient.status.name != 'NeedSpectrum':
                return 403, f"FRB {row['TNS']} not in NeedSpectrum status" 
        else:
            return 406, f"Mode {row['mode']} not allowed"

        # Grab the resource
        try:
            resource=FRBFollowUpResource.objects.get(name=row['Resource'])
        except:
            return 405, f"Resource {row['Resource']} not in DB"

        # Add to FRBFollowUpRequest if not already in there
        req = frb_utils.add_or_grab_obj(
            FRBFollowUpRequest,
            dict(transient=transient, resource=resource, mode=row['mode']),
            {}, user)
                                   
        # Update transient status
        frb_status.set_status(transient)
        '''
        if row['mode'] in ['imaging']:
            transient.status = TransientStatus.objects.get(name='ImagePending') 
        elif row['mode'] in ['longslit', 'mask']:
            transient.status = TransientStatus.objects.get(name='SpectrumPending') 

        # Save
        transient.save()
        '''

    return 200, "All good"
    
def ingest_obslog(obslog:pandas.DataFrame, user):
    """ Ingest an observing log into the DB

    This updates the transient status and adds to FRBFollowUpObservation

    Args:
        obslog (pandas.DataFrame): table of observations
            -- TNS (str)
            -- Resource (str)
            -- mode (str)
            -- Conditions (str)
            -- texp (float)
            -- date (timestamp)
            -- success (bool)
        user (_type_): _description_

    Returns:
        tuple: (status, message) (int,str) 
    """

    # TODO
    # Scrub previous entries with the named resource?
    
    # Loop on rows
    for ss, row in obslog.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['TNS'])
        except:
            return 401, f"FRB {row['TNS']} not in DB"

        # Check if the transient status is OK
        if row['mode'] in ['imaging']:
            if transient.status.name != 'PendingImage':
                return 402, f"FRB {row['TNS']} not in PendingImage status" 
        elif row['mode'] in ['longslit', 'mask']:
            if transient.status.name != 'PendingSpectrum':
                return 403, f"FRB {row['TNS']} not in PendingSpectrum status" 
        else:
            return 406, f"Mode {row['mode']} not allowed"

        # Grab the resource
        try:
            resource=FRBFollowUpResource.objects.get(name=row['Resource'])
        except:
            return 405, f"Resource {row['Resource']} not in DB"

        # Add to FRBFollowUpRequest if not already in there
        required = dict(
            transient=transient, 
            resource=resource, 
            mode=row['mode'],
            conditions=row['Conditions'], 
            texp=row['texp'], 
            date=pandas.Timestamp(row['date']),
            success=row['success'])
                                                                                  
        # Add to the table
        obs = frb_utils.add_or_grab_obj(
            FRBFollowUpObservation, required, {}, user)
                                   
        # Update transient status
        if row['mode'] in ['imaging']:
            transient.status = TransientStatus.objects.get(name='ObsImage') 
        elif row['mode'] in ['longslit', 'mask']:
            transient.status = TransientStatus.objects.get(name='ObsSpectrum') 


        # Save
        transient.save()

    return 200, "All good"
    