""" Add CHIME test(s) for grabbing targets from the database """

import os
from pkg_resources import resource_filename
import numpy as np
import pandas

from django.contrib import auth
from django.db.models import ForeignKey
from django.http import HttpResponse,JsonResponse

from YSE_App.models import FRBFollowUpResource
#from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu

from YSE_App import frb_utils

from IPython import embed

def test_target_table():
    """ Run the test which will:

    This test requires the DB was populated using chime_test_db.build_chime_test_db()


    Args:
    """

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')

    # Grab the targets
    valid_frbs = frb_fu.valid_frbs()

    # Table
    tbl = frb_utils.target_table_from_frbs(valid_frbs)

    # Check
    embed(header='44 of chime_test_targets.py')
    #tmp = JsonResponse(tbl.to_json(), status=201, safe=False)
    tmp = JsonResponse(tbl.to_dict(), status=201)