""" Build up the Test DB (may be more than one option)"""

import datetime

from django.contrib import auth

from YSE_App.models import *
from YSE_App.chime import chime_path_test
from YSE_App.data_utils import add_or_grab_obj

def build_chime_test_db():

    user = auth.authenticate(username='root', password='F4isthebest')

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

def clean_all():

    for ipath in Path.objects.all():
        ipath.delete()
    for galaxy in FRBGalaxy.objects.all():
        galaxy.delete()
    for frb_fu in FRBFollowUpResource.objects.all():
        frb_fu.delete()
    for itransient in FRBTransient.objects.all():
        itransient.delete()
