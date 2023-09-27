""" Scripts for developing follow-up """

from YSE_App.models.frbfollowup_models import FRBFollowUpResource
from YSE_App.models import FRBTransient
from YSE_App import frb_utils

from IPython import embed

def dev_airmass():
    frbfup = FRBFollowUpResource.objects.all()[2]
    gd_frbs = FRBTransient.objects.all()

    min_AM = frb_utils.calc_airmasses(frbfup, gd_frbs,
                                      debug=True)
    print(min_AM)