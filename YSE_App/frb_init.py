""" Methods to init the DB """

from YSE_App.models import TransientStatus
from YSE_App.models import ObservationGroup
from YSE_App.frb_utils import add_or_grab_obj

from YSE_App import frb_status

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