""" Add CHIME test for PATH analysis 
of an FRB added to the database """

import os
from pkg_resources import resource_filename
from importlib import reload
import numpy as np
import pandas

from django.contrib import auth
from django.db.models import ForeignKey

from YSE_App.models import Transient
from YSE_App.models import Host, Path
from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu

from YSE_App.galaxies import path


import pandas

from IPython import embed

def run(delete_existing:bool=True,
        delete_all_hosts:bool=True,
        delete_all_paths:bool=True):
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Add CHIME Observation Group?
    obs_names = [obs.name for obs in ObservationGroup.objects.all()]
    flag_CHIME = False
    if 'CHIME' not in obs_names:
        obs = ObservationGroup(name='CHIME', created_by_id=user.id, modified_by_id=user.id)
        obs.save()
        flag_CHIME = True

    # Add em
    dbtransients = ctu.add_df_to_db(df_frbs, user, 
                                    delete_existing=delete_existing)

    # Run PATH on one
    ifrb = np.where(df_frbs.name == 'FRB20300714A')[0][0]
    itransient = dbtransients[ifrb]
    #candidates, P_Ux, Path, mag_key, priors = ctu.run_path_on_instance(idbtransient)

    # The following will come from PATH
    candidates = pandas.DataFrame()
    candidates['ra'] = [183.979572, 183.979442]
    candidates['dec'] = [-13.0213, -13.0201]
    candidates['ang_size'] = [0.5, 1.2] # arcsec
    candidates['mag'] = [18.5, 19.5]
    candidates['P_Ox'] = [0.98, 0.01]
    mag_key = 'Pan-STARRS_r'
    F = mag_key[-1]
    P_Ux = 0.01

    # Ingest
    photom_inst_name = path.ingest_path_results(
        itransient, candidates, 
        F, 'GPC1', 'Pan-STARRS1', P_Ux, user)

    embed(header='80 of chime_path_test.py')

    # Test!
    assert max([ipath.P_Ox for ipath in Path.objects.filter(transient_name=itransient.name)]) >= 0.98
    photom = itransient.best_Path_host.phot_dict
    assert np.isclose(photom[photom_inst_name][F], 
                      candidates.iloc[0].mag, rtol=1e-3)

    # Do it again

    # Break it all down
    #if flag_CHIME:
    #    obs.delete()

    #for dbtransient in dbtransients:
    #    dbtransient.delete()

    if delete_all_paths:
        for ipath in Path.objects.all():
            ipath.delete()
    
    if delete_all_hosts:
        for host in Host.objects.all():
            host.delete()

    # Finish
    print(Transient.objects.all())
    print("All clear!")