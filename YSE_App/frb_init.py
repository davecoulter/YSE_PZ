""" Methods to init the DB """

from YSE_App.models import TransientStatus
from YSE_App.frb_utils import add_or_grab_obj

from YSE_App import frb_status

def init_statuses(user):

    # Delete all existing
    TransientStatus.objects.all().delete()

    # Add into DB
    for status in frb_status.all_status:
        _ = add_or_grab_obj(TransientStatus,
                        dict(name=status), {}, user)