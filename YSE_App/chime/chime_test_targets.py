""" Add CHIME test(s) for grabbing targets from the database """

import os
from pkg_resources import resource_filename
import numpy as np
import pandas

from django.contrib import auth
from django.db.models import ForeignKey
from django.http import HttpResponse,JsonResponse

from YSE_App.models import FRBFollowUpResource
from YSE_App.models import FRBTransient
from YSE_App.models import FRBTag
from YSE_App.models import TransientStatus
#from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu

from YSE_App import frb_targeting

from IPython import embed


def test_target_table():
    """ Run the test to create an internal target table

    This test requires the DB was populated using chime_test_db.build_chime_test_db()


    Args:
    """

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')

    # Grab the targets
    tbl = frb_fu.generate_target_table()

    # Check
    tmp = JsonResponse(tbl.to_dict(), status=201)

def test_multi_surveys():

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')
    frb_fu.frb_surveys = 'CHIME/FRB,CRAFT'
    gd_frbs = frb_targeting.targetfrbs_for_fu(frb_fu)

    # Test
    assert len(gd_frbs.filter(name='FRB20300714X')) == 1

def test_tags():

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')
    frb_fu.frb_tags = 'CHIME-Blind'

    gd_frbs = frb_targeting.targetfrbs_for_fu(frb_fu)

    # Test
    tag = FRBTag.objects.get(name='CHIME-Blind')
    assert np.all([tag in frb.frb_tags.all() for frb in gd_frbs])

def test_modes():

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')
    gd_frbs = frb_targeting.targetfrbs_for_fu(frb_fu)


    targets_by_mode = frb_targeting.grab_targets_by_mode(frb_fu, gd_frbs)

    # Test
    assert len(targets_by_mode['longslit'].filter(name='FRB20300714A')) == 1

def test_status():

    # Resource
    frb_fu = FRBFollowUpResource.objects.get(name='Gemini-LP-2024A-99')
    itransient = FRBTransient.objects.get(name='FRB20300714A')
    status = TransientStatus.objects.get(name='FollowupRequested')
    itransient.status = status
    itransient.save()


    gd_frbs = frb_targeting.targetfrbs_for_fu(frb_fu)

    # Test
    assert len(gd_frbs.filter(name='FRB20300714A')) == 0

    # Revert
    status = TransientStatus.objects.get(name='New')
    itransient.status = status
    itransient.save()