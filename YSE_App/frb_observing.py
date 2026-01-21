""" Methods for dealing with FRB Observing """

from django.utils import timezone as du_timezone

from YSE_App.models import FRBFollowUpRequest
from YSE_App.models import FRBFollowUpResource
from YSE_App.models import FRBFollowUpObservation
from YSE_App.models import FRBGalaxy
from YSE_App.models import TransientStatus
from YSE_App.models import FRBTransient

from YSE_App import frb_utils
from YSE_App import frb_status


import pandas

def ingest_obsplan(obsplan:pandas.DataFrame, user,
                   iresource:str,
                   override:bool=False):
    """ Ingest an observing plan into the DB

    It will first remove all pending observations for the
    named resource.  Then it will add the new ones.

    This updates the transient status and adds to FRBFollowUpRequest

    Args:
        obsplan (pandas.DataFrame): _description_
        user (_type_): User who is ingesting the plan
        iresource (str): Name of the FRB Followup Resource
        override (bool, optional): If True, allow several of the
            checks to be over-ridden.

    Returns:
        tuple: (status, message) (int,str) 
    """

    # Scrub previous entries with the same named resource
    try:
        resource=FRBFollowUpResource.objects.get(name=iresource)
    except:
        return 409, f"Resource {obsplan['Resource'].values[0]} not in DB"
    all_pending = FRBFollowUpRequest.objects.filter(
        resource=resource)
    for pending in all_pending:
        transient = pending.transient
        # Delete
        pending.delete()
        # Update status
        frb_status.set_status(transient)
    
    # Loop on rows to add
    if len(obsplan) == 0:
        return 200, "All good"
        
    for _, row in obsplan.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['TNS'])
        except:
            return 401, f"FRB {row['TNS']} not in DB"

        # Check if the transient status is OK
        if row['mode'] in ['imaging']:
            if transient.status.name != 'NeedImage' and not override:
                return 402, f"FRB {row['TNS']} not in NeedImage status" 
        elif row['mode'] in ['longslit', 'mask']:
            if transient.status.name != 'NeedSpectrum' and not override:
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

    return 200, "All good"
    
def ingest_obslog(obslog:pandas.DataFrame, user, override:bool=False,
                  keep_pending:bool=False):
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
        override (bool, optional): If True, allow several of the
            checks to be over-ridden.  
        keep_pending (bool, optional): If True, keep any
            FRBs not provided but in the Resource in the pending list.
            Defaults to False.

    Returns:
        tuple: (status, message) (int,str) 
    """
    # Loop on rows
    for _, row in obslog.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['TNS'])
        except:
            return 401, f"FRB {row['TNS']} not in DB"

        # Check if the transient status is OK
        if row['mode'] in ['imaging']:
            if transient.status.name != 'ImagePending' and not override:
                return 402, f"FRB {row['TNS']} not in PendingImage status" 
        elif row['mode'] in ['longslit', 'mask']:
            if transient.status.name != 'SpectrumPending' and not override:
                return 403, f"FRB {row['TNS']} not in PendingSpectrum status" 
        else:
            return 406, f"Mode {row['mode']} not allowed"

        # Grab the resource
        try:
            resource=FRBFollowUpResource.objects.get(name=row['Resource'])
        except:
            return 405, f"Resource {row['Resource']} not in DB"

        # Check we are after the stop date
        if resource.valid_stop > du_timezone.now() and not keep_pending:
            return 410, "This cannot be executed until after the valid_stop date!"

        # Add to FRBFollowUpObservation if not already in there
        required = dict(
            transient=transient,
            resource=resource,
            mode=row['mode'],
            date=pandas.Timestamp(row['date']))
        extras = dict(
            conditions=row['Conditions'],
            texp=row['texp'],
            success=row['success'])

        # Find any matches to the required fields
        existing=FRBFollowUpObservation.objects.filter(**required)
        # Delete these
        for obj in existing:
            obj.delete()
                                                                                  
        # Add to the table
        obs = frb_utils.add_or_grab_obj(
            FRBFollowUpObservation, required, extras, user)

        # Remove this FRB from Pending`
        any_pending = FRBFollowUpRequest.objects.filter(
            resource=resource, transient=transient)
        for pending in any_pending:
            pending.delete()

        # Update transient status
        frb_status.set_status(transient)

    # Remove the rest in the Resource from Pending`
    if not keep_pending:
        all_pending = FRBFollowUpRequest.objects.filter(
            resource=resource)
        for pending in all_pending:
            transient = pending.transient
            # Delete
            pending.delete()
            # Update status
            frb_status.set_status(transient)

    return 200, "All good"
    
def ingest_z(z_tbl:pandas.DataFrame):
    """ Ingest a table of redshifts into FFFF-PZ

    The values are added to the FRBGalaxy object(s)

    This also updates the FRBTransient status 

    Args:
        z_tbl (pandas.DataFrame): table of redshifts
            TNS (str) -- TNS of the FRB that has this galaxy as its preferred host
            Galaxy (str) -- JNAME *matching* that in FFFF-PZ
            Resource (str) -- Name of the FRB Followup Resource
            Redshift (float) -- Redshift of the galaxy (float)
            Quality (int) -- Quality of the redshift (int)

    Returns:
        tuple: (status, message) (int,str) 
    """

    # TODO -- Scrub previous entries with the named resource?
    
    # Loop on rows
    for _, row in z_tbl.iterrows():

        # Grab the transient
        try:
            transient=FRBTransient.objects.get(name=row['TNS'])
        except:
            return 401, f"FRB {row['TNS']} not in DB"

        # Grab the galaxy
        try:
            galaxy=FRBGalaxy.objects.get(name=row['Galaxy'])
        except:
            return 401, f"Galaxy {row['Galaxy']} not in DB"

        # Grab the resource
        try:
            resource=FRBFollowUpResource.objects.get(name=row['Resource'])
        except:
            # For public redshifts, we didn't use our own Resource
            if row['Resource'][:4] != 'FFFF':
                return 405, f"Resource {row['Resource']} not in DB"

        # Check the FRB was observed by this Resource (if not public)
        if row['Resource'][:4] != 'FFFF':
            obs = FRBFollowUpObservation.objects.filter(
                resource=resource, transient=transient)
            if len(obs) == 0:
                return 406, f"FRB {row['TNS']} not observed by {row['Resource']}"

        # Update the Galaxy
        galaxy.redshift = row['Redshift']
        galaxy.redshift_quality = row['Quality']
        galaxy.redshift_source = row['Resource']
        galaxy.save()

        # Update transient status
        frb_status.set_status(transient)

    return 200, "All good"
    