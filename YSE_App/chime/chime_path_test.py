""" Add CHIME test for PATH analysis 
of an FRB added to the database """

import os
from pkg_resources import resource_filename
from importlib import reload
import numpy as np
import pandas
import datetime

from django.contrib import auth
from django.db.models import ForeignKey
from django.db import IntegrityError

from YSE_App.models import Transient
from YSE_App.models import Host, Path
from YSE_App.models.enum_models import ObservationGroup
from YSE_App.models.phot_models import HostPhotData, HostPhotometry, PhotometricBand
from YSE_App.models.instrument_models import Instrument
from YSE_App.chime import chime_test_utils as ctu
from YSE_App.common.utilities import getGalaxyname

from YSE_App import data_utils


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
    priors = dict(survey='Pan-STARRS')

    # Add to DB
    new_hosts = []
    new_Paths = []
    for ss in range(len(candidates)):
        icand = candidates.iloc[ss]
        # Add
        name = getGalaxyname(icand.ra, icand.dec)
        host = data_utils.add_or_grab_obj(
            Host, dict(name=name), dict(ra=icand.ra, dec=icand.dec, 
                       ang_size=icand.ang_size), user=user)
        '''
        if Host.objects.filter(name=name).count() == 1:
            print(f"Host {name} already exists! Using the existing one")
            host = Host.objects.get(name=name)
        elif Host.objects.filter(name=name).count() == 0:
            # Create
            host = Host(name=name, ra=icand.ra, dec=icand.dec, 
                        ang_size=icand.ang_size,
                        created_by_id=user.id, modified_by_id=user.id)
            # Save
            host.save()
        else:
            # How should we handle errors for real?
            raise IOError("Bad host count")
        '''
        new_hosts.append(host)

        # Add Photometry
        if priors['survey'] == 'Pan-STARRS':
            inst_name = 'GPC1'
            obs_group = 'Pan-STARRS1'
            photom_inst_name = 'Instrument: Pan-STARRS1 - GPC1'
        else:
            raise IOError("Bad survey")
        hp = data_utils.add_or_grab_obj(
            HostPhotometry, 
            dict(host=host, instrument=Instrument.objects.get(name=inst_name), 
                 obs_group=ObservationGroup.objects.get(name=obs_group)),
                 {}, user=user)
        hpd = data_utils.add_or_grab_obj(
            HostPhotData, 
            dict(photometry=hp,
                 band=PhotometricBand.objects.filter(instrument__name=inst_name).get(name=F)),
            dict(mag=icand.mag, 
                 obs_date=datetime.datetime.now()),
            user=user)

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
    assert max([ipath.P_Ox for ipath in Path.objects.filter(transient_name=itransient.name)]) >= 0.98
    photom = itransient.best_Path_host.phot_dict
    assert np.isclose(photom[photom_inst_name][F], candidates.iloc[0].mag, rtol=1e-3)


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