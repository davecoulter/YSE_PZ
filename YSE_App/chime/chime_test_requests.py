""" Test requests via the API """

import os
import sys
import json
import pandas

import requests
from requests.auth import HTTPBasicAuth

from IPython import embed

def path_requests(delete:bool=False):

    # Need to delete the PATH entries first
    # And FRB Galaxies!

    # Test table
    # The following will come from PATH and read from a .csv file
    candidates = pandas.DataFrame()
    candidates['ra'] = [183.979572, 183.979442]
    candidates['dec'] = [-13.0213, -13.0201]
    candidates['ang_size'] = [0.5, 1.2] # arcsec
    candidates['mag'] = [18.5, 19.5]
    candidates['P_Ox'] = [0.98, 0.01]

    # Prep
    data = {}
    data['table'] = candidates.to_json()
    data['transient_name'] = 'FRB20300714A'
    data['mag_key'] = 'Pan-STARRS_r'
    data['F'] = data['mag_key'][-1] # Filter
    data['P_Ux'] = 0.01

    # These must be in the DB already (or we need to add code to add them)
    data['instrument'] = 'GPC1'
    data['obs_group'] = 'Pan-STARRS1'

    url = 'http://0.0.0.0:8000/ingest_path/'
    try:
        rt = requests.put(url=url,
            data=json.dumps(data),
                auth=HTTPBasicAuth(
                    os.getenv('FFFF_PZ_USER'),
                    os.getenv('FFFF_PZ_PASS')),
                timeout=60)
    except Exception as e:
        print("Error: %s"%e)

def sandbox():
    # Grab Transients in PATH table
    url = 'http://0.0.0.0:8000/api/paths/'
    r = requests.get(url=url, 
                auth=HTTPBasicAuth(
                    os.getenv('FFFF_PZ_USER'),
                    os.getenv('FFFF_PZ_PASS')))
    # Parse                     
    names = []
    for item in r.json()['results']:
        rt = requests.get(url=item['transient'], 
                auth=HTTPBasicAuth(
                    os.getenv('FFFF_PZ_USER'),
                    os.getenv('FFFF_PZ_PASS')))
        names.append(rt.json()['name'])
    uni_names = list(set(names))

    # Grab the User?
    url = 'http://0.0.0.0:8000/api/users/'

    # Create the galaxy first 
    new_galaxy = {}
    new_galaxy['name'] = 'J123456.78+123456.7'
    new_galaxy['ra'] = 123.5678
    new_galaxy['dec'] = 54.321
    new_galaxy['source'] = 'PS1'
    # Should do this in add_frb_galaxy
    #  This is a hack for now
    new_galaxy['created_by'] = "http://0.0.0.0:8000/api/users/189/"
    new_galaxy['modified_by'] = "http://0.0.0.0:8000/api/users/189/"
    # We are ignoring angular size and magnitude for now
    url = 'http://0.0.0.0:8000/add_frb_galaxy/'
    try:
        rt = requests.put(url=url,
            data=json.dumps(new_galaxy),
                auth=HTTPBasicAuth(
                    os.getenv('FFFF_PZ_USER'),
                    os.getenv('FFFF_PZ_PASS')),
                timeout=60)
    except Exception as e:
        print("Error: %s"%e)
    
    #embed(header='chime_path_test.py: 49')
    # Add a new PATH entry

    new_path = {}
    new_path['transient_name'] = 'FRB20300102B'
    new_path['galaxy_name'] = new_galaxy['name']
    new_path['P_Ox'] = 0.95
    new_path['vetted'] = True

    #  This is a hack for now
    new_path['created_by'] = "http://0.0.0.0:8000/api/users/189/"
    new_path['modified_by'] = "http://0.0.0.0:8000/api/users/189/"

    # #######################################
    # Clean up

    # Remove galaxy
    url = 'http://0.0.0.0:8000/rm_frb_galaxy/'
    try:
        rd = requests.put(url=url,
            data=json.dumps(new_galaxy),
                auth=HTTPBasicAuth(
                    os.getenv('FFFF_PZ_USER'),
                    os.getenv('FFFF_PZ_PASS')),
                timeout=60)
    except Exception as e:
        print("Error: %s"%e)

if __name__ == '__main__':
    path_requests()