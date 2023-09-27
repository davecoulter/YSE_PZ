""" Add CHIME test(s) for ingesting obs plan """

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

from YSE_App import frb_observing

from IPython import embed


def test_ingest_obsplan():
    """ Run the test on a fake obsplan table
    """
    user = auth.authenticate(username='root', password='F4isthebest')

    FRB='FRB20300714A'
    transient=FRBTransient.objects.get(name=FRB)
    sv_status = TransientStatus.objects.get(name=transient.status.name)

    # Generate a fake obsplan table
    row = dict(FRB=FRB,
               Resource='Gemini-LP-2024A-99',
               mode='longslit')
    obsplan = pandas.DataFrame([row])

    # Run
    code, msg = frb_observing.ingest_obsplan(obsplan, user)
    print(code, msg)
    assert code == 200

    # Test
    transient=FRBTransient.objects.get(name=FRB)
    assert transient.status.name == 'PendingSpectrum'

    # Reset status
    transient.status = sv_status
    transient.save()