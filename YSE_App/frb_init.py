""" Methods to init the DB """

from YSE_App.models import TransientStatus
from YSE_App.data_utils import add_or_grab_obj

def init_status(user):

    # Delete all existing
    TransientStatus.objects.all().delete()

    # Create the FRB ones
    all_status = [\
        'New', # Just ingested, this may not be used 
        'PublicPATH', # Needs to be run through PATH with public data
        'Image', # Needs deeper imaging
        'Spectrum', # Needs spectroscopy for redshift
        'DeepPATH', # Needs PATH run on deeper imaging
        'PendingImage', # Pending deeper imaging with an FRBFollowUp
        'PendingSpectrum', # Pending spectroscopy with an FRBFollowUp
        'ObsImage', # Observed with imaging
        'ObsSpectrum', # Observed with spectroscopy
        'Complete', # Redshift measured or deemed impossible
    ]

    # Add into DB
    for status in all_status:
        _ = add_or_grab_obj(TransientStatus,
                        dict(name=status), {}, user)