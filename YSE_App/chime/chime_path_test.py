""" Add CHIME test for PATH analysis 
of an FRB added to the database """

import os
from pkg_resources import resource_filename
from importlib import reload
import numpy as np
import pandas

from django.contrib import auth
from django.db.models import ForeignKey

from YSE_App.models import FRBTransient
from YSE_App.models import FRBGalaxy, Path#, Candidate
from YSE_App.models import FRBSurvey
#from YSE_App.models.enum_models import ObservationGroup
from YSE_App.chime import chime_test_utils as ctu

from YSE_App.galaxies import path

from YSE_App.serializers import frbtransient_serializers 
from YSE_App.serializers import user_serializers

import pandas

from IPython import embed

def run(delete_existing:bool=True,
        delete_all_galaxies:bool=True,
        delete_all_paths:bool=True):
    """ Run the test which will:

    1. Add CHIME/FRB transients to the database, if needed
    2. Ingest the results for PATH for one of these (FRB20300714A)
    3. Test that the results are as expected
    4. Clean up, as requested

    Args:
        delete_existing (bool, optional): Delete the FRB Transients
            from the DB before re-adding them. Defaults to True.
        delete_all_galaxies (bool, optional): Clean up the FRBGalaxies table. Defaults to True.
        delete_all_paths (bool, optional): Clean up the Path table. Defaults to True.
    """
    # Load up the table
    csv_file = os.path.join(
        resource_filename('YSE_App', 'chime'), 'chime_tests.csv')
    df_frbs = pandas.read_csv(csv_file)

    user = auth.authenticate(username='root', password='F4isthebest')

    # Add CHIME Observation Group?
    survey_names = [survey.name for survey in FRBSurvey.objects.all()]
    for survey in ['CHIME/FRB', 'CRAFT']:
        if survey not in survey_names:
            obs = FRBSurvey(name=survey, created_by_id=user.id, modified_by_id=user.id)
            obs.save()

    # Add em (if necessary)
    _ = ctu.add_df_to_db(df_frbs, user, 
                         delete_existing=delete_existing)

    # Transient for PATH
    itransient = FRBTransient.objects.get(name='FRB20300714A')

    # Run PATH 
    #candidates, P_Ux, Path, mag_key, priors = ctu.run_path_on_instance(idbtransient)

    # Or us an input table
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
    #embed(header='66 of chime_path_test.py')
    photom_inst_name = path.ingest_path_results(
        itransient, candidates, 
        F, 'GPC1', 'Pan-STARRS1', P_Ux, user)

    # Test!
    assert max([ipath.P_Ox for ipath in Path.objects.filter(transient=itransient)]) >= 0.98
    photom = itransient.best_Path_galaxy.phot_dict
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
    
    if delete_all_galaxies:
        for galaxy in FRBGalaxy.objects.all():
            galaxy.delete()

    # Finish
    print(FRBTransient.objects.all())
    print("All clear!")

def test_galaxy_serialize():
    data = {'name': 'J123456.78+123456.7', 'ra': 123.5678, 'dec': 54.321, 'source': 'PS1'}

    # Create
    create = False
    if create:
        user = auth.authenticate(username='root', 
                                password='F4isthebest')

        #user_serialize = user_serializers.UserSerializer(user)
        # TODO -- figure out how to serialize the user
        data['created_by'] = "http://0.0.0.0:8000/api/users/189/"
        data['modified_by'] = "http://0.0.0.0:8000/api/users/189/"

        serializer = frbtransient_serializers.FRBGalaxySerializer(data=data)
        if serializer.is_valid():
            serializer.save()

    # Destroy
    destroy = True
    if destroy:
        galaxy = FRBGalaxy.objects.get(name=data['name'])
        galaxy.delete()