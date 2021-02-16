# v1.00 2019-05-01: basic code
# v1.01 2019-09-20: updated to LCO API v3
# v1.02 2021-02-02: Modified to run on command line with examples

import requests, warnings, os, stat, json, shutil, sys, copy
from astropy.time import Time, TimeDelta
from astropy.io import ascii, fits
from astropy.coordinates import SkyCoord
from astropy import units as u
from dateutil.parser import parse
from datetime import datetime, timedelta
from django.conf import settings as djangoSettings
import numpy as np

class lcogt(object):
    def __init__(self, username, password, progid, telescop,
        start_date, end_date):

        uri_base = 'https://observe.lco.global/'
        archive_base = 'https://archive-api.lco.global/'
        self.params = {
            'uri': {
                'archive': {
                    'authorization': archive_base + 'api-token-auth/',
                    'frames': archive_base + 'frames/',
                    'token': None
                },
                'request': {
                    'authorization': uri_base + 'api/api-token-auth/',
                    'request': uri_base + 'api/requestgroups/',
                    'token': None
                }
            },
            'date_format': '%Y-%m-%d %H:%M:%S',
            'constraints': {
                'max_airmass': 2.5,
                'min_lunar_distance': 15
            },
            'strategy': {
                'default': {
                    'type': 'default',
                    'proposal': [
                    {'name':progid,'obstype':'NORMAL'},
                    ],
                    'filters': ['up', 'gp', 'rp', 'ip'],
                    'min_exposure': {'default':45, 'up':150},
                    'max_exposure': 540,
                    # SNR strategy are pairwise mag, snr values.
                    # If current source magnitude is < mag, then use given snr.
                    'snr': [[16,40],[18,20],[99,10]],
                    'cadence': 4,
                    'telescope_class': '1m0',
                    'instrument_type': '1M0-SCICAM-SINISTRO',
                    'acquisition_config': 'OFF',
                    'guiding_config': 'ON',
                    'window': 1.0,
                    'ipp': 1.0
                },
                'spectroscopy': {
                    'type': 'spectroscopy',
                    'proposal': [
                    {'name':progid,'obstype':'NORMAL'},
                    ],
                    'min_exposure': 300,
                    'max_exposure': 2400,
                    'telescope_class': '2m0',
                    'instrument_type': '2M0-FLOYDS-SCICAM',
                    'slit': 'slit_1.6as',
                    'acquisition_config': 'OFF',
                    'guiding_config': 'ON',
                    'window': 1.0,
                    'ipp': 1.0
                },
                'photometry': {
                    'type': 'photometry',
                    'proposal': [
                    {'name': progid,'obstype':'NORMAL'},
                    ],
                    'filters': ['up', 'gp', 'rp', 'ip'],
                    'min_exposure': {'default':45, 'up':150},
                    'max_exposure': 540,
                    # SNR strategy are pairwise mag, snr values.  first is mag
                    # and second is snr.  If mag_source < mag, then use snr.
                    'snr': [[16,40],[18,20],[99,10]],
                    'cadence': 4,
                    'telescope_class': '1m0',
                    'instrument_type': '1M0-SCICAM-SINISTRO',
                    'acquisition_config': 'OFF',
                    'guiding_config': 'ON',
                    'window': 1.0,
                    'ipp': 1.01
                }
            }
        }

        self.start_date = Time(start_date).datetime
        self.end_date = Time(end_date).datetime

        self.telescope = telescop
        if 'soar' in telescop:
            self.params['strategy']['spectroscopy']={
                    'type': 'spectroscopy',
                    'proposal': [
                    {'name':progid,'obstype':'NORMAL'},
                    ],
                    'min_exposure': 300,
                    'max_exposure': 2400,
                    'telescope_class': '4m0',
                    'instrument_type': 'SOAR_GHTS_REDCAM',
                    'slit': 'slit_1.0as',
                    'acquisition_config': 'OFF',
                    'guiding_config': 'ON',
                    'window': 6.0,
                    'ipp': 1.0
            }
            self.params['constraints']={
                'max_airmass': 1.7,
                'min_lunar_distance': 30
            }

        # List of all proposals to which I have access.  Some of these are old
        # proposals where the data are now public
        self.proposals = ['NOAO2019A-020','NOAO2017AB-012','NOAO2018A-005',
                'NOAO2019A-020-TC','NOAO2017AB-005','NOAO2018A-007',
                'NOAO2018B-022','NOAO2019A-001','NOAO2018B-022b',
                'NOAO2019B-008','NOAO2019B-004','KEY2017AB-001',
                'NOAO2019B-009','NAOC2017AB-001','LCO2018A-004',
                'FTPEPO2014A-004','ARI2017AB-002', progid]

        # These are relevant to SINISTRO on the 1m.  Will update with Spectral
        # and MuSCAT3 zeropoints
        self.constants = {
            'zpt': {
                'up': 20.5665,
                'gp': 23.2249,
                'rp': 23.1314,
                'ip': 22.8465
            }
        }

        self.username = username
        self.password = password

        self.format = {'token': 'Token {token}'}

    def get_username_password(self):
        if (self.username is not None and self.password is not None):
            return(self.username, self.password)
        else:
            # Get username password out of shibboleth
            return(None, None)

    def get_token_header(self, username, password, auth_type='archive'):

        # Check that we're getting the right token
        if auth_type not in self.params['uri'].keys():
            return(None)

        params = self.params['uri'][auth_type]

        # Check if header token has already been defined
        if params['token']:
            # Return the heade that we need
            fmt = self.format['token']
            header = {'Authorization': fmt.format(token=params['token'])}
            return(header)
        else:
            # Need to generate a new token
            data = {'username': username, 'password': password}
            uri = params['authorization']

            # Now run a request
            response = requests.post(uri, data=data).json()

            # Check that the request worked
            if 'token' in response.keys():
                self.params['uri'][auth_type]['token'] = response['token']
                fmt = self.format['token']
                header = {'Authorization': fmt.format(token=response['token'])}
                return(header)
            else:
                # There was some problem with authentication/connection
                return(None)

    # Download spectral calibration files for a specific telid and date
    def get_spectral_calibrations(self, date, telid, site, outrootdir='',
        funpack=True):

        # Get username and password
        username,password = self.get_username_password()

        # Get authorization token
        headers = self.get_token_header(username, password)

        params = {'limit': 100}
        results = []
        params['TELID'] = telid
        params['SITEID'] = site
        delta = TimeDelta(1, format='jd')
        params['start'] = (date-delta).datetime.strftime(self.params['date_format'])
        params['end'] = (date+delta).datetime.strftime(self.params['date_format'])

        # First check for LAMPFLATs
        params['OBSTYPE'] = 'LAMPFLAT'
        response = requests.get(self.params['uri']['archive']['frames'],
            params=params, headers=headers)

        if response.status_code != 200:
            print(response.text)
        else:
            data = response.json()
            results += data['results']

        # Now check for ARCs
        params['OBSTYPE'] = 'ARC'
        response = requests.get(self.params['uri']['archive']['frames'],
            params=params, headers=headers)

        if response.status_code != 200:
            print(response.text)
        else:
            data = response.json()
            results += data['results']

        # Now try to download the obslist
        self.download_obslist(results, outrootdir=outrootdir,
            use_basename=True, skip_header=True, funpack=funpack)

    # Get a json object with complete list of observations.  Optional to define
    # a program or date range to narrow search
    def get_obslist(self, propid=None, sdate=None, edate=None, telid=None,
        obstype=None, rlevel=None, obj=None, reqnum=None):

        # Get username and password
        username,password = self.get_username_password()

        # Get authorization token
        headers = self.get_token_header(username, password)

        # Get parameters for request
        params = {'limit': 5000}
        fmt=self.params['date_format']
        results = []
        propids = []
        if rlevel is not None:
            params['RLEVEL'] = rlevel
        else:
            params['RLEVEL'] = 91
        if propid is not None:
            propids = list(propid)
        if sdate is not None:
            params['start'] = sdate.datetime.strftime(fmt)
        if edate is not None:
            params['end'] = edate.datetime.strftime(fmt)
        if telid is not None:
            params['TELID'] = telid
        if obstype is not None:
            params['OBSTYPE'] = obstype
        if obj is not None:
            params['OBJECT'] = obj
        if reqnum is not None:
            params['REQNUM'] = reqnum

        for pid in propids:
            params['PROPID'] = pid

            # Now do request
            response = requests.get(self.params['uri']['archive']['frames'],
                params=params, headers=headers)

            if response.status_code != 200:
                print(response.text)
            else:
                data = response.json()
                results += data['results']

        return(results)

    # Get a set of standard star observation for spectrophotometric calibration
    def get_standardobs(self, sdate=None, telid=None, rlevel=None):

        # Get username and password
        username,password = self.get_username_password()

        # Get authorization token
        headers = self.get_token_header(username, password)

        # Get parameters for request
        params = {'OBSTYPE': 'SPECTRUM', 'public': True}

        delta = TimeDelta(14, format='jd')
        date = Time(datetime.now())
        start = (date-delta).datetime
        fmt=self.params['date_format']

        if not sdate: params['start']=start.strftime(fmt)
        else: params['start']=sdate.datetime.strftime(fmt)

        if not rlevel: params['RLEVEL']=0
        else: params['RLEVEL']=rlevel

        objs=['EGGR274','L745-46A','FEIGE110','HZ 44','BD+284211','GD71']

        results=[]
        for obj in objs:
            params['OBJECT']=obj
            response = requests.get(self.params['uri']['archive']['frames'],
                params=params, headers=headers)

            if response.status_code != 200:
                print(response.text)
            else:
                data = response.json()
                results += data['results']

        return(results)

    # Get recent observation requests for proposal ID, start date, end date,
    # observation type, and instrument type
    def get_requestgroups(self, propid=None, sdate=None, edate=None,
        obstype=None, itype=None):

        # Get username and password
        username, password = self.get_username_password()

        # Get authorization token
        headers = self.get_token_header(username, password, auth_type='request')

        params = {}
        results = []
        propids = []
        if propid is not None:
            propids = list(propid)
        if sdate is not None:
            start = sdate.datetime.strftime(self.params['date_format'])
            params['created_after'] = start
        if edate is not None:
            end = edate.datetime.strftime(self.params['date_format'])
            params['created_before'] = end

        for pid in propids:
            params['proposal'] = pid
            params['limit'] = 500

            # Now do request
            response = requests.get(self.params['uri']['request']['request'],
                params=params, headers=headers).json()

            # If instrument_type, remove values that do not conform
            if itype is not None:
                for r in copy.copy(response['results']):
                    test = r['requests'][0]['configurations'][0]['instrument_type']
                    if test != itype:
                        response['results'].remove(r)

            results += response['results']

        return(results)

    # Given an input obslist from the LCOGT archive, download the associated
    # files for each element
    def download_obslist(self, obslist, outrootdir='', use_basename=False,
        skip_header=False, funpack=True):

        for frame in obslist:
            filename = ''
            if use_basename:
                filename = frame['basename'] + '.fits.fz'
            else:
                target = frame['OBJECT']

                # Need to sanitize target, e.g., for spaces
                target = target.replace(' ','_')

                filt = frame['FILTER']
                idnum = str(frame['id'])
                date = Time(frame['DATE_OBS']).datetime.strftime('ut%y%m%d')
                filename = target + '.' + date + '.' +\
                    filt + '.' + idnum + '.fits.fz'
            fullfilename = outrootdir + '/' + filename
            if not os.path.exists(outrootdir):
                shutil.os.makedirs(outrootdir)
            if ((not os.path.exists(fullfilename)
                and not os.path.exists(fullfilename.strip('.fz')) and funpack)
                or (not os.path.exists(fullfilename))):
                message = 'Downloading LCOGT file: {file}'
                print(message.format(file=fullfilename))
                with open(fullfilename, 'wb') as f:
                    f.write(requests.get(frame['url']).content)
            else:
                message = 'LCOGT file: {file} already exists!'
                print(message.format(file=fullfilename))

            # funpack - requires cfitsio
            if not os.path.exists(fullfilename.strip('.fz')) and funpack:
                cmd = 'funpack {file}'
                os.system(cmd.format(file=fullfilename))
            if os.path.exists(fullfilename) and funpack:
                os.remove(fullfilename)

            # Remove extraneous extension
            if not skip_header:
                hdulist = fits.open(fullfilename.strip('.fz'))
                newhdu = fits.HDUList()
                hdu = hdulist['SCI']
                hdu.header['OBSTYPE'] = 'OBJECT'
                newhdu.append(hdu)
                newhdu.writeto(fullfilename.strip('.fz'), overwrite=True)

    # Make a location element with telescope class
    def make_location(self, telescope):
        return({'telescope_class': telescope})

    # Make an airmass/lunar distance constraint element
    def make_constraints(self):
        max_airmass = self.params['constraints']['max_airmass']
        min_lunar_distance = self.params['constraints']['min_lunar_distance']
        constraints = {
            'max_airmass': max_airmass,
            'min_lunar_distance': min_lunar_distance
        }
        return(constraints)

    # This sets up a target based on name, ra, dec
    def make_target(self, name, ra, dec):
        target = {
            'type': 'ICRS',
            'name': name,
            'ra': ra,
            'dec': dec,
            'proper_motion_ra': 0.0,
            'proper_motion_dec': 0.0,
            'parallax': 0.0,
            'epoch': 2000.0
        }
        return(target)

    # This sets up the instrument parameters for an obs
    # Imaging specific
    def make_instrument_configs(self, filt, exptime, strat):
        # This sets up an imaging observation for SINISTRO.  Need to update for
        # 2m imaging with Spectral and MuSCAT3
        if strat['type']=='default':
            configuration = {
                'instrument_name': '1M0-SCICAM-SINISTRO',
                'optical_elements': {'filter': filt},
                'mode': 'full_frame',
                'exposure_time': exptime,
                'exposure_count': 1,
                'bin_x': 1,
                'bin_y': 1,
                'extra_params': {'defocus': 0.0}
            }
        # This creates a spectroscopy observing element for FLOYDS
        elif strat['type']=='spectroscopy' and 'faulkes' in self.telescope:
            configuration = {
                "bin_x": 1,
                "bin_y": 1,
                "exposure_count": 1,
                "exposure_time": exptime,
                "mode": "default",
                "rotator_mode": "VFLOAT",
                "extra_params": {},
                "optical_elements": {
                    "slit": strat['slit']
                }
            }
        elif strat['type']=='spectroscopy' and 'soar' in self.telescope:
            configuration = {
                "bin_x": 2,
                "bin_y": 2,
                "exposure_count": 1,
                "exposure_time": exptime,
                "mode": "GHTS_R_400m1_2x2",
                "rotator_mode": "SKY",
                "extra_params": {"rotator_angle": 90},
                "optical_elements": {
                    "slit": strat['slit'],
                    "grating": "SYZY_400"
                }
            }
        return([configuration])

    # Make an acquisition element for FLOYDS spectroscopy (on coordinate vs.
    # acquire brightest object)
    def make_acquisition_config(self, strat, mode=None):
        if not mode:
            mode = strat['acquisition_config']
        return({'mode': mode})

    # Should guiding be on or off
    def make_guiding_config(self, strat, extra_params={}):
        mode = strat['guiding_config']
        config = {'mode': mode}
        for key in extra_params.keys():
            config[key]=extra_params[key]
        return(config)

    """
    Window object for LCOGT API v3.
    start time = earliest the obs can be executed
    duration = amount of time in which request can be executed
    """
    def make_window(self, start, duration):
        fmt = self.params['date_format']
        end = start + timedelta(days=duration)
        # Note that this is an override for YSE App
        window = [{
            'start': self.start_date.strftime(fmt),
            'end': self.end_date.strftime(fmt)
        }]
        return(window)

    # Post your observing request with requests.post
    def post_user_request(self, user_request):
        # Get username and password
        username, password = self.get_username_password()

        # Get authorization token
        header = self.get_token_header(username, password, auth_type='request')
        uri = self.params['uri']['request']['request']
        response = requests.post(uri, json=user_request, headers=header)
        return(response)

    # Guess the exposure time based on input magnitude of target
    def get_exposure_time(self, filt, mag, strat):
        # Get preferred snr given input magnitude
        # Handle 'spec' case
        if filt=='spec':
            if mag < 14:
                return(300)
            elif mag < 15:
                return(600)
            elif mag < 16:
                return(900)
            elif mag < 17:
                return(1500)
            elif mag < 17.5:
                return(1800)
            elif mag < 18.0:
                return(2100)
            elif mag < 18.5:
                return(2400)
            else:
                return(None)

        snr = 10.
        for pair in strat['snr']:
            if mag < pair[0]:
                snr = pair[1]
        term1 = 20. * snr**2
        term2 = 0.4 * (mag - self.constants['zpt'][filt])
        exptime = term1 * 10**term2
        print(filt,exptime)
        min_exposure = 45.0
        if filt in strat['min_exposure'].keys():
            min_exposure = strat['min_exposure'][filt]
        else:
            min_exposure = strat['min_exposure']['default']
        if exptime < min_exposure:
            exptime = min_exposure
        if exptime > strat['max_exposure']:
            return(None)

        return(exptime)

    """
    LCO API v3 configurations.
    configurations consist of constraints, instrument configuration, acquisition
    configuration, guiding configuration, target, instrument type, exposure
    type, and observation priority.  This method will construct a series of
    configurations for a single target.
    """
    def make_configurations(self, obj, ra, dec, exptime, strat):
        # Iterate over each filter and append to configurations list
        configurations = []

        # If default, construct configurations for photometry strategy
        if strat['type']=='default':
            for i,filt in enumerate(strat['filters']):
                constraints = self.make_constraints()

                # Get exposure time and make instrument_config
                instrument_configs = self.make_instrument_configs(filt, exptime, strat)

                # Make acquisition and guiding config with strat
                acquisition_config = self.make_acquisition_config(strat)
                guiding_config = self.make_guiding_config(strat)

                # Make a tar object
                target = self.make_target(obj, ra, dec)

                # Compile everything into configuration
                configuration = {
                    'constraints': constraints,
                    'instrument_configs': instrument_configs,
                    'acquisition_config': acquisition_config,
                    'guiding_config': guiding_config,
                    'target': target,
                    'instrument_type': strat['instrument_type'],
                    'type': 'EXPOSE',
                    'priority': i+1
                }
                configurations.append(configuration)

        elif strat['type']=='spectroscopy' and 'faulkes' in self.telescope:
            # Need to construct LAMP FLAT, ARC, SPECTRUM, ARC, LAMP FLAT
            for obstype in ['LAMP_FLAT', 'ARC', 'SPECTRUM', 'ARC', 'LAMP_FLAT']:

                # Use default constraint values
                constraints = self.make_constraints()

                if obstype=='LAMP_FLAT':
                    exptime = 50
                if obstype=='ARC':
                    exptime = 60

                # Make acquisition and guiding config with strat
                instrument_configs = self.make_instrument_configs('spec', exptime, strat)
                if obstype=='SPECTRUM':
                    acquisition_config = self.make_acquisition_config(strat, mode='WCS')
                else:
                    acquisition_config = self.make_acquisition_config(strat)
                guiding_config = self.make_guiding_config(strat)

                # Make a target object
                target = self.make_target(obj, ra, dec)

                # Compile everything into configuration
                configuration = {
                    'type': obstype,
                    'constraints': constraints,
                    'instrument_configs': instrument_configs,
                    'acquisition_config': acquisition_config,
                    'guiding_config': guiding_config,
                    'target': target,
                    'instrument_type': strat['instrument_type']
                }
                configurations.append(configuration)

        elif strat['type']=='spectroscopy' and 'soar' in self.telescope:
            for i,obstype in enumerate(['ARC', 'SPECTRUM']):
                # Use default constraint values
                constraints = self.make_constraints()

                if obstype=='ARC':
                    exptime = 0.5

                # Make acquisition and guiding config with strat
                instrument_configs = self.make_instrument_configs('spec', exptime, strat)
                if obstype=='SPECTRUM':
                    acquisition_config = self.make_acquisition_config(strat, mode='MANUAL')
                    guiding_config = self.make_guiding_config(strat,
                        extra_params={'optional': False,
                        "optical_elements": {},
                        "exposure_time": None,
                        "extra_params": {}})
                elif obstype=='ARC':
                    acquisition_config = self.make_acquisition_config(strat, mode='OFF')
                    guiding_config = self.make_guiding_config(strat,
                        extra_params={'optional': True,
                        "optical_elements": {},
                        "exposure_time": None,
                        "extra_params": {}})

                # Make a target object
                target = self.make_target(obj, ra, dec)

                # Compile everything into configuration
                configuration = {
                    'type': obstype,
                    'constraints': constraints,
                    'instrument_configs': instrument_configs,
                    'acquisition_config': acquisition_config,
                    'guiding_config': guiding_config,
                    'target': target,
                    'instrument_type': strat['instrument_type'],
                    'priority': i+1
                }
                configurations.append(configuration)

        return(configurations)


    """
    LCO API v3 request.
    requests is a list of requests each defined by a location, configuration,
    and a window.
    """
    def make_requests(self, obj, ra, dec, exptime, strat):
        location = self.make_location(strat['telescope_class'])
        window = self.make_window(datetime.now(), strat['window'])
        configurations = self.make_configurations(obj, ra, dec, exptime, strat)

        requests = [{
            'location': location,
            'windows': window,
            'configurations': configurations
        }]

        return(requests)

    """
    LCO API v3 observation request.
    Each method constructs one layer of the request.  Here we need to make the
    outermost obs request with name, proposal, ipp value, operator, observation
    type, and the individual requests.  Send the
    """
    def make_obs_request(self, obj, ra, dec, exptime, strategy = 'default',
        propidx=''):

        # Get params - strategy data
        strat = self.params['strategy'][strategy]

        proposal = propidx

        # Make the obs_request dictionary
        obs_request = {
            'name': obj,
            'proposal': propidx,
            'ipp_value': strat['ipp'],
            'operator': 'SINGLE',
            'observation_type': 'NORMAL'
        }

        # Iterate through the next level of request
        requests = self.make_requests(obj, ra, dec, exptime, strat)
        if not requests[0]['configurations']:
            return(None)
        else:
            obs_request['requests'] = requests
            print(obs_request)
            response = self.post_user_request(obs_request)
            print(response.content)
            response = response.json()
            return(response)

#
#
# HERE IS AN EXAMPLE TO DEMONSTRATE HOW THE CODE WORKS
#
#

def main(name, ra, dec, exptime, telescop, start_date, end_date):
    if 'faulkes' in telescop.lower():
        progid = 'NOAO2021A-001'
    elif 'soar' in telescop.lower():
        progid = 'SOAR2021A-003'
    else:
        print('Do not recognize telescope={0}'.format(telescop))
        sys.exit()

    lco = lcogt(djangoSettings.LCOGTUSER, djangoSettings.LCOGTPASS, progid, telescop, start_date,
        end_date)

    coord = SkyCoord(ra, dec, unit='deg')
    response = lco.make_obs_request(name, ra, dec, exptime,
        strategy='spectroscopy', propidx=progid)

if __name__ == "__main__":
    name = sys.argv[1]
    ra = sys.argv[2]
    dec = sys.argv[3]
    exptime = sys.argv[4]
    telescop = sys.argv[5]
    start_date = sys.argv[6]
    end_date = sys.argv[7]
    main(name, ra, dec, exptime, telescop, start_date, end_date)
