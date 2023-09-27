""" Build up the Test DB (may be more than one option)"""

import datetime

from django.contrib import auth

import pandas

from YSE_App.models import *
from YSE_App.chime import chime_path_test
from YSE_App.data_utils import add_or_grab_obj
from YSE_App import frb_init
from YSE_App import frb_observing

def build_chime_test_db():
    """ Build the CHIME test DB from scratch """

    user = auth.authenticate(username='root', password='F4isthebest')

    # Clean first
    clean_all()

    # ##############################
    # Init the DB
    # Status
    frb_init.init_status(user)

    # Add objects

    # Set of FRBs and Path for one
    chime_path_test.run(delete_existing=True,
                        delete_all_galaxies=False,
                        delete_all_paths=False)

    # Add an FRB Resource                    
    instr = Instrument.objects.get(name='GMOS') # This will become GMOS-N eventually
    uni_fields = dict(name='Gemini-LP-2024A-99',
                  instrument=instr,
                  valid_start=datetime.datetime(2024, 3, 1, tzinfo=datetime.timezone.utc),
                  valid_stop=datetime.datetime(2024, 3, 7, tzinfo=datetime.timezone.utc),
                  num_targ_img=1,
                  num_targ_mask=4,
                  num_targ_longslit=4,
                  max_AM=1.5,
                  frb_surveys='CHIME/FRB',
    )
    extra_fields = dict(min_POx=0.9,
                  obs_type='Queue',
    )
    _ = add_or_grab_obj(FRBFollowUpResource,
                        uni_fields, extra_fields, user)

    # Modify status of 2 FRBs
    FRB='FRB20300714Z'
    transient=FRBTransient.objects.get(name=FRB)
    transient.status = TransientStatus.objects.get(name='Image')
    transient.save()
                
    FRB='FRB20300714Y'
    transient=FRBTransient.objects.get(name=FRB)
    transient.status = TransientStatus.objects.get(name='Spectrum')
    transient.save()

    # Add a FollowUp request
    row = dict(TNS=FRB,
               Resource='Gemini-LP-2024A-99',
               mode='longslit')
    obsplan = pandas.DataFrame([row])
    code, msg = frb_observing.ingest_obsplan(obsplan, user)


def clean_all():
    """ Wipe clean the DB """

    print("Removing Path objects")
    for ipath in Path.objects.all():
        ipath.delete()

    print("Removing FRBGalaxy objects")
    for galaxy in FRBGalaxy.objects.all():
        galaxy.delete()

    print("Removing FRBFollowUpResource objects")
    for frb_fu in FRBFollowUpResource.objects.all():
        frb_fu.delete()

    print("Removing FRBTransient objects")
    for itransient in FRBTransient.objects.all():
        itransient.delete()
