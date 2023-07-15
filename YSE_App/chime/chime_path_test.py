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
from YSE_App.common.utilities import getGalaxyname


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
    #candidates, P_Ux, Path = ctu.run_path_on_instance(idbtransient)

    # The following will come from PATH
    candidates = pandas.DataFrame()
    candidates['ra'] = [183.979572, 183.979442]
    candidates['dec'] = [-13.0213, -13.0201]
    candidates['P_Ox'] = [0.98, 0.01]
    P_Ux = 0.01

    # Add to DB
    new_hosts = []
    new_Paths = []
    for ss in range(len(candidates)):
        icand = candidates.iloc[ss]
        # Add
        name = getGalaxyname(icand.ra, icand.dec)
        if Host.objects.filter(name=name).count() == 1:
            print(f"Host {name} already exists! Using the existing one")
            host = Host.objects.get(name=name)
        elif Host.objects.filter(name=name).count() == 0:
            # Create
            host = Host(name=name, ra=icand.ra, dec=icand.dec, 
                        created_by_id=user.id, modified_by_id=user.id)
            # Save
            host.save()
        else:
            # How should we handle errors for real?
            raise IOError("Bad host count")
        new_hosts.append(host)
        # Add to transient
        itransient.candidates.add(host)

        # PATH
        ipath = Path(transient_name=itransient.name, 
                     host_name=host.name, P_Ox=icand.P_Ox,
                     created_by_id=user.id, modified_by_id=user.id)
        ipath.save()
        new_Paths.append(ipath)

    # Save PATH values
    itransient.P_Ux = P_Ux

    # Save
    itransient.save()

    # Test them!
    embed(header='81 of chime_path_test.py')

    # Break it all down
    if flag_CHIME:
        obs.delete()

    for dbtransient in dbtransients:
        dbtransient.delete()

    if delete_all_paths:
        for ipath in Path.objects.all():
            ipath.delete()
    else:
        for new_Path in new_Paths:
            new_Path.delete()
    
    if delete_all_hosts:
        for host in Host.objects.all():
            host.delete()
    else:
        for new_host in new_hosts:
            new_host.delete()

    # Finish
    print(Transient.objects.all())
    print("All clear!")