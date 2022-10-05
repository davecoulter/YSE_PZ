import requests
import time
import imaplib
import socket
import ssl
import getpass
import pprint
import email
import re
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from enum import Enum
from astroquery.ned import Ned
Ned.TIMEOUT = 5
import astropy.units as u
from astropy import coordinates
import numpy as np
from astroquery.irsa_dust import IrsaDust
from datetime import timedelta
import json
import os
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS, Galactic, FK4, FK5
from astropy.time import Time
import coreapi
from urllib.parse import quote,unquote
import requests
from requests.auth import HTTPBasicAuth
import struct
import threading
import queue
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from collections import OrderedDict
from YSE_App.util.TNS_Synopsis import mastrequests
from astropy.io import ascii
from itertools import islice
from astropy.cosmology import FlatLambdaCDM
import sys
from YSE_App.common import mast_query,chandra_query,spitzer_query
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
import argparse, configparser
import signal
from astro_ghost.ghostHelperFunctions import *
try:
    from astro_ghost.photoz_helper import calc_photoz
    is_photoz = True
except:
    print('warning: can\'t import tensorflow')
    is_photoz = False
    pass
import os
from tendo import singleton

reg_obj = "https://www.wis-tns.org/object/(\w+)"
reg_ra = "\>\sRA[\=\*a-zA-Z\<\>\" ]+(\d{2}:\d{2}:\d{2}\.\d+)"
reg_dec = "DEC[\=\*a-zA-Z\<\>\" ]+((?:\+|\-)\d{2}:\d{2}:\d{2}\.\d+)\<\/em\>\,"

try:
    from dustmaps.sfd import SFDQuery
    sfd = SFDQuery()
except:
    pass

def get_ps_score(RA, DEC):
    '''Get ps1 star/galaxy score from MAST. Provide RA and DEC in degrees.
    Returns an empty string if no match is found witing 3 arcsec.
    '''
    # get the WSID and password if not already defined
    # get your WSID by going to https://mastweb.stsci.edu/ps1casjobs/changedetails.aspx after you login to Casjobs.

    os.environ['CASJOBS_WSID'] = str(1862226089)
    os.environ['CASJOBS_PW'] = 'tr4nsientsP!z'
    query = """select top 1 p.ps_score
    from pointsource_magnitudes_view as p
    inner join fGetNearbyObjEq(%.5f, %.5f, 0.05) nb on p.objid=nb.objid
    """ %(RA, DEC)

    jobs = mastrequests.MastCasJobs(context="HLSP_PS1_PSC")
    results = jobs.quick(query, task_name="python cross-match")

    output = results.split('\n')[1]
    if not output:
        output = None
    else:
        output = round(float(output), 3)
        print('PS_SCORE: %.3f' %output)

    return output
    
class processTNS:
    
    def __init__(self):
        self.verbose = None
        
    def add_options(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_argument('--clobber', default=False, action="store_true",
                            help='clobber output file')
        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('--status', default='New', type=str,
                            help='transient status to enter in YS_PZ')
        parser.add_argument('--noupdatestatus', default=False, action="store_true",
                            help='if set, don\'t promote ignore -> new when uploading')
        parser.add_argument('--update', default=False, action="store_true",
                            help='if set, scrape TNS pages to update events already in YSE_PZ')
        parser.add_argument('--updatefromZTF', default=False, action="store_true",
                            help='if set, update photometry from ZTF')
        parser.add_argument('--redohost', default=False, action="store_true",
                            help='if set, repeat search to find host matches (slow-ish)')
        parser.add_argument('--nedradius', default=5, type=float,
                            help='NED search radius, in arcmin')
        parser.add_argument('--ndays', default=None, type=int,
                            help='number of days before today update events')

        if config:
            parser.add_argument('--login', default=config.get('main','login'), type=str,
                                help='gmail login (default=%default)')
            parser.add_argument('--password', default=config.get('main','password'), type=str,
                                help='gmail password (default=%default)')
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                                help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                                help='database login, if post=True (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                                help='database password, if post=True (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                                help='database password, if post=True (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                                help='URL to POST transients to a database (default=%default)')
            parser.add_argument('--tnsapi', default=config.get('main','tnsapi'), type=str,
                                help='TNS API URL (default=%default)')
            parser.add_argument('--tnsapikey', default=config.get('main','tnsapikey'), type=str,
                                help='TNS API key (default=%default)')
            parser.add_argument('--tns_bot_id', default=config.get('main','tns_bot_id'), type=str,
                                help='TNS API key (default=%default)')
            parser.add_argument('--tns_bot_name', default=config.get('main','tns_bot_name'), type=str,
                                help='TNS API key (default=%default)')

            parser.add_argument('--tns_recent_ndays', default=config.get('main','tns_recent_ndays'), type=str,
                                help='time interval for grabbing recent TNS events (default=%default)')
            parser.add_argument('--tns_fastupdates_nminutes', default=config.get('main','tns_fastupdates_nminutes'), type=str,
                                help='time interval for grabbing very recent TNS events (default=%default)')
            parser.add_argument('--hostmatchrad', default=config.get('main','hostmatchrad'), type=float,
                                help='matching radius for hosts (arcmin) (default=%default)')
            parser.add_argument('--ghost_path', default=config.get('main','ghost_path'), type=str,
                                help='GHOST data directory (default=%default)')

            parser.add_argument('--ztfurl', default=config.get('ztf','ztfurl'), type=str,
                                help='ZTF URL (default=%default)')

            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                                help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                                help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                                help='SMTP port (default=%default)')

        else:
            parser.add_argument('--login', default="", type=str,
                                help='gmail login (default=%default)')
            parser.add_argument('--password', default="", type=str,
                                help='gmail password (default=%default)')
            parser.add_argument('--dblogin', default="", type=str,
                                help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemail', default="", type=str,
                                help='database login, if post=True (default=%default)')
            parser.add_argument('--dbpassword', default="", type=str,
                                help='database password, if post=True (default=%default)')
            parser.add_argument('--dbemailpassword', default="", type=str,
                                help='database password, if post=True (default=%default)')
            parser.add_argument('--url', default="", type=str,
                                help='URL to POST transients to a database (default=%default)')
            parser.add_argument('--hostmatchrad', default=0.001, type=float,
                                help='matching radius for hosts (arcmin) (default=%default)')
            parser.add_argument('--tnsapi', default="", type=str,
                                help='TNS API URL (default=%default)')
            parser.add_argument('--tnsapikey', default="", type=str,
                                help='TNS API key (default=%default)')
            parser.add_argument('--ztfurl', default="", type=str,
                                help='ZTF URL (default=%default)')
            parser.add_argument('--ghost_path', default="", type=str,
                                help='GHOST data directory (default=%default)')
            
            parser.add_argument('--SMTP_LOGIN', default='', type=str,
                                help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default='', type=str,
                                help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default='', type=str,
                                help='SMTP port (default=%default)')
            

        return(parser)

    def getTNSData(self,jd,obj,sc,ebv):

        if obj.startswith('2016'):
            status = 'Ignore'
        else:
            status = self.status

        try:
            ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
        except:
            ps_prob = None

        # get space archival data
        try:
            hst=mast_query.hstImages(sc.ra.deg,sc.dec.deg,'Object')
            hst.getObstable()
            if hst.Nimages > 0:
                has_hst = True
            else:
                has_hst = False
        except: has_hst = None
        try:
            chr=chandra_query.chandraImages(sc.ra.deg,sc.dec.deg,'Object')
            chr.search_chandra_database()
            if chr.n_obsid > 0:
                has_chandra = True
            else:
                has_chandra = False
        except: has_chandra = None
        try:
            if spitzer_query.get_bool_from_coord(t.ra,t.dec):
                has_spitzer = True
            else:
                has_spitzer = False
        except:
            has_spitzer = None

        TransientDict = {'name':obj,
                         'slug':obj,
                         'ra':sc.ra.deg,
                         'dec':sc.dec.deg,
                         'obs_group':'Unknown',
                         'mw_ebv':ebv,
                         'status':status,
                         'point_source_probability':ps_prob,
                         'has_hst':has_hst,
                         'has_chandra':has_chandra,
                         'has_spitzer':has_spitzer,
                         'tags':[]}

        if jd:
            TransientDict['disc_date'] = jd['discoverydate']
            TransientDict['obs_group'] = jd['reporting_group']['group_name']
            #jd['discovery_data_source']['group_name']

            if not TransientDict['obs_group']:
                TransientDict['obs_group'] = 'Unknown'
            z = jd['redshift']
            if z: TransientDict['redshift'] = float(z)
            evt_type = jd['object_type']['name']
            if evt_type:
                TransientDict['best_spec_class'] = evt_type
                TransientDict['TNS_spec_class'] = evt_type

            if jd['internal_names']:
                TransientDict['internal_names'] = jd['internal_names']
                
        return TransientDict

    def getZTFPhotometry(self,sc):
        ztfurl = '%s/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(
            self.ztfurl,sc.ra.deg,sc.dec.deg)
        client = coreapi.Client()
        schema = client.get(ztfurl)
        if 'results' in schema.keys():
            PhotUploadAll = {"mjdmatchmin":0.01,
                             "clobber":self.clobber}
            photometrydict = {'instrument':'ZTF-Cam',
                              'obs_group':'ZTF',
                              'photdata':{}}

            for i in range(len(schema['results'])):
                phot = schema['results'][i]['candidate']
                if phot['isdiffpos'] == 'f':
                    continue
                PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
                                  'band':'%s-ZTF'%phot['filter'],
                                  'groups':[]}
                PhotUploadDict['mag'] = phot['magpsf']
                PhotUploadDict['mag_err'] = phot['sigmapsf']
                PhotUploadDict['flux'] = None
                PhotUploadDict['flux_err'] = None
                PhotUploadDict['data_quality'] = 0
                PhotUploadDict['forced'] = None
                PhotUploadDict['flux_zero_point'] = None
                PhotUploadDict['discovery_point'] = 0
                PhotUploadDict['diffim'] = 1

                photometrydict['photdata']['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict
            PhotUploadAll['ZTF'] = photometrydict
            return PhotUploadAll

        else: return None

    def get_PS_DR2_data(self, sc):
        """
        Returns a dictionary of photometric data
        {'instrument': 'GPC1', 'obs_group': 'Pan-STARRS1', 'photdata': photdata}
        photdata = {{"2019-05-09T04:35:52.002_1": {'obs_data': '2019-05-09T04:35:52.002',
                                                   'band': 'g', 'groups': [], 'mag': float,
                                                   'mag_err': float, 'flux': None, 'flux_err': None,
                                                   'forced': None, 'discovery_point': 0,
                                                   'flux_zero_point': None, } }}
        """

        #radius is in arcmin
        radius = 3./60
        ra, dec = sc.ra.deg, sc.dec.deg
        query_obj_id = """select m.objid, m.gMeanPSFMag, m.rMeanPSFMag, m.iMeanPSFMag, m.zMeanPSFMag, m.yMeanPSFMag
        from fGetNearestObjEq(%.5f,%.5f,%.5f) nb
        inner join MeanObject m on m.objid=nb.objid
        """ %(ra,dec,radius)

        jobs = mastrequests.MastCasJobs(context="PanSTARRS_DR2")
        results = jobs.quick(query_obj_id, task_name="PS1_DR2 objid search")
        results = results.split('\n')
        if results[1]:
            objid = results[1].split(',')[0]
            query = "select objID, detectID, filter=f.filterType, obsTime, ra, dec, psfFlux, psfFluxErr, "
            query += "infoFlag, infoFlag2, infoFlag3 "
            query += "from (select * from Detection where objID=%s) d " %objid
            query += "join Filter f on d.filterID=f.filterID order by d.filterID, obsTime"
            results = jobs.quick(query, task_name="PS1 DR2 detections")

            photdata = {}
            for row in ascii.read(results):
                tobj = Time(row[3], format='mjd')
                obstime = datetime.strftime(tobj.to_datetime(), "%Y-%m-%dT%H:%M:%S.%f")[:-3]
                photdata[obstime] = {}
                photdata[obstime]['obs_date'] = obstime
                photdata[obstime]['band'] = row[2]
                photdata[obstime]['mag'] = -2.5*np.log10(row[6]) + 8.90
                photdata[obstime]['mag_err'] = 2.5/np.log(10)* (row[7]/row[6])
                photdata[obstime]['forced'] = None
                photdata[obstime]['flux_zero_point'] = None
                photdata[obstime]['data_quality'] = 0
                photdata[obstime]['flux'] = None
                photdata[obstime]['flux_err'] = None
                photdata[obstime]['discovery_point'] = 0
                photdata[obstime]['groups'] = []
                photdata[obstime]['diffim'] = None
            transientphot = {'instrument': 'GPC1', 'obs_group': 'Pan-STARRS1', 'photdata': photdata}
            return transientphot
        else:
            return None

    def getTNSPhotometry(self,jd,PhotUploadAll=None):

        if not PhotUploadAll:
            PhotUploadAll = {"mjdmatchmin":0.01,
                             "clobber":self.clobber}

        tmag,tmagerr,tfilt,tinst,tobsdate,obsgroups,mjd =\
            np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([])

        nondetectmaglim,nondetectdate,nondetectfilt,nondetectins = "","","",""
        for p in jd['photometry']:
            if p['instrument']['name'] == 'CFH12k':
                p['filters']['name'] = '%s-PTF'%p['filters']['name']
            elif p['instrument']['name'] == 'ZTF-Cam':
                p['filters']['name'] = '%s-ZTF'%p['filters']['name']

            if 'mag' in p['flux_unit']['name'].lower():
                tmag = np.append(tmag,p['flux'])
                tmagerr = np.append(tmagerr,p['fluxerr'])
                if not p['flux']:
                    nondetectmaglim = p['limflux']
                    nondetectdate = p['obsdate']
                    nondetectfilt = p['filters']['name']
                    nondetectins = p['instrument']['name']
            else:
                tmag = np.append(tmag,-99)
                tmagerr = np.append(tmagerr,-99)

            tobsdate = np.append(tobsdate,p['obsdate'])
            mjd = np.append(mjd,date_to_mjd(p['obsdate']))
            obsgroups = np.append(obsgroups,p['observer'])
            tinst = np.append(tinst,p['instrument']['name'])
            tfilt = np.append(tfilt,p['filters']['name'])

        disc_flag = np.zeros(len(tmag))
        iMag = np.where((tmag != -99) & (tmag != None))[0]
        indx = np.where((mjd[iMag] == np.min(mjd[iMag])))[0]
        disc_flag[iMag[indx]] = 1

        photometrycount = 0
        for ins in np.unique(tinst):

            if np.array(obsgroups)[np.array(tinst) == ins][0] is None:
                obsgroup = None
            else:
                obsgroup = re.sub(r'[^\x00-\x7f]',r'',np.array(obsgroups)[np.array(tinst) == ins][0])
            
            photometrydict = {'instrument':ins,
                              'obs_group':obsgroup,
                              'photdata':{}}

            for f,k in zip(np.unique(tfilt),range(len(np.unique(tfilt)))):
                # put in the photometry
                for m,me,od,df in zip(tmag[(f == tfilt) & (ins == tinst)],
                                             tmagerr[(f == tfilt) & (ins == tinst)],
                                             tobsdate[(f == tfilt) & (ins == tinst)],
                                             disc_flag[(f == tfilt) & (ins == tinst)]):
                    if not m and not me: continue #and not flx and not fe: continue
                    PhotUploadDict = {'obs_date':od.replace(' ','T'),
                                      'band':f,
                                      'groups':[]}
                    if m: PhotUploadDict['mag'] = m
                    else: PhotUploadDict['mag'] = None
                    if me: PhotUploadDict['mag_err'] = me
                    else: PhotUploadDict['mag_err'] = None
                    PhotUploadDict['flux'] = None
                    PhotUploadDict['flux_err'] = None
                    if df: PhotUploadDict['discovery_point'] = 1
                    else: PhotUploadDict['discovery_point'] = 0
                    PhotUploadDict['data_quality'] = 0
                    PhotUploadDict['forced'] = None
                    PhotUploadDict['flux_zero_point'] = None
                    PhotUploadDict['diffim'] = None

                    photometrydict['photdata']['%s_%i'%(od.replace(' ','T'),k)] = PhotUploadDict
            PhotUploadAll[photometrycount] = photometrydict
            photometrycount += 1

        if nondetectdate: nondetectdate = nondetectdate.replace(' ','T')
        return PhotUploadAll,nondetectdate,nondetectmaglim,nondetectfilt,nondetectins

    def getTNSSpectra(self,jd,sc):
        specinst,specobsdate,specobsgroup,specfiles = \
            np.array([]),np.array([]),np.array([]),np.array([])

        SpecDictAll = {'clobber':self.clobber}
        keyslist = ['ra','dec','instrument','rlap','obs_date','redshift',
                    'redshift_err','redshift_quality','spectrum_notes',
                    'obs_group','groups','spec_phase','snid','data_quality']
        requiredkeyslist = ['ra','dec','instrument','obs_date','obs_group','snid']

        for i in range(len(jd['spectra'])):
            spec = jd['spectra'][i]
            specinst = np.append(specinst,spec['instrument']['name'])
            specobsdate = np.append(specobsdate,spec['obsdate'])
            if 'source_group_name' in spec.keys():
                specobsgroup = np.append(specobsgroup,spec['source_group_name'])
            elif 'source_group' in spec.keys():
                specobsgroup = np.append(specobsgroup,spec['source_group']['name'])
            else:
                specobsgroup = np.append(specobsgroup,'Unknown')
            specfiles = np.append(specfiles,spec['asciifile'])
        
        for s,si,so,sog in zip(specfiles,specinst,specobsdate,specobsgroup):
            Spectrum = {}
            SpecData = {}
            os.system('rm spec_tns_upload.txt')

            try:
                dlfileresp = get_file(s,self.tnsapikey,self.tns_bot_id,self.tns_bot_name)
                if dlfileresp.status_code == 429:
                    print('TNS request failed.  Waiting 60 seconds to try again...')
                    time.sleep(60)
                    dlfileresp = get_file(s,self.tnsapikey,self.tns_bot_id,self.tns_bot_name)
                dlfile = dlfileresp.text
            except:
                continue

            with open('spec_tns_upload.txt','w') as fout:
                print('# wavelength flux',file=fout)
                print('# instrument %s'%si,file=fout)
                print('# obs_date %s'%so.replace(' ','T'),file=fout)
                print('# obs_group %s'%sog,file=fout)
                print('# ra %s'%sc.ra.deg,file=fout)
                print('# dec %s'%sc.dec.deg,file=fout)
                for line in dlfile.split('\n'):
                    if ':' in line or '=' in line or line.isspace() or 'END' in line or 'GROUPS' in line or 'SNID ' in line: continue
                    print(line.replace('\n',''),file=fout)

            fin = open('spec_tns_upload.txt')
            count = 0
            for line in fin:
                line = line.replace('\n','')
                if not count: header = np.array(line.replace('# ','').split())
                for key in keyslist:
                    if line.lower().startswith('# %s '%key) and key not in Spectrum.keys():
                        Spectrum[key] = line.split()[-1].replace("'","").replace('"','')
                count += 1
            fin.close()
            if ':' in Spectrum['ra']:
                scspec = SkyCoord(Spectrum['ra'],Spectrum['dec'],FK5,unit=(u.hourangle,u.deg))
                Spectrum['ra'] = scspec.ra.deg
                Spectrum['dec'] = scspec.dec.deg
            if 'wavelength' not in header or 'flux' not in header:
                raise RuntimeError("""Error : incorrect file format.
                The header should be # wavelength flux fluxerr, with fluxerr optional.""")

            try:
                spc = {}
                spc['wavelength'] = np.loadtxt('spec_tns_upload.txt',unpack=True,usecols=[np.where(header == 'wavelength')[0][0]])
                spc['flux'] = np.loadtxt('spec_tns_upload.txt',unpack=True,usecols=[np.where(header == 'flux')[0][0]])
            except:
                raise RuntimeError("""Error : incorrect file format.
                The header should be # wavelength flux fluxerr, with fluxerr optional.""")

            if 'fluxerr' in header:
                spc['fluxerr'] = np.loadtxt(self.options.inputfile,unpack=True,usecols=[np.where(header == 'fluxerr')[0][0]])
            for key in keyslist:
                if key not in Spectrum.keys():
                    print('Warning: %s not in spectrum header'%key)

            if 'fluxerr' in spc.keys():
                for w,f,df in zip(spc['wavelength'],spc['flux'],spc['fluxerr']):
                    if f == f:
                        SpecDict = {'wavelength':w,
                                    'flux':f,
                                    'flux_err':df}
                        SpecData[w] = SpecDict
            else:
                for w,f in zip(spc['wavelength'],spc['flux']):
                    if f == f:
                        SpecDict = {'wavelength':w,
                                    'flux':f,
                                    'flux_err':None}
                        SpecData[w] = SpecDict

            #os.system('rm spec_tns_upload.txt')
            Spectrum['specdata'] = SpecData
            Spectrum['instrument'] = si
            Spectrum['obs_date'] = so
            Spectrum['obs_group'] = re.sub(r'[^\x00-\x7f]',r'',sog)
            SpecDictAll[s] = Spectrum

        return SpecDictAll

    def getGHOSTData(self,jd,sc,ghost_host):
        hostdict = {}; hostcoords = ''
        hostdict = {'name':str(ghost_host['objName'].to_numpy()[0]),
                    'ra':ghost_host['raMean'].to_numpy()[0],
                    'dec':ghost_host['decMean'].to_numpy()[0]}

        hostcoords = f"ra={hostdict['ra']:.7f}, dec={hostdict['dec']:.7f}\n"
        if 'photo_z' in ghost_host.keys():
            hostdict['photo_z_internal'] = ghost_host['photo_z'].to_numpy()[0]
        if 'NED_redshift' in ghost_host.keys() and ghost_host['NED_redshift'].to_numpy()[0] == ghost_host['NED_redshift'].to_numpy()[0]:
            hostdict['redshift'] = ghost_host['NED_redshift'].to_numpy()[0]

        if 'photo_z_internal' in hostdict.keys():
            if hostdict['photo_z_internal'] != hostdict['photo_z_internal']:
                hostdict['photo_z_internal'] = None

        return hostdict,hostcoords
        
    def getNEDData(self,jd,sc,ned_table):

        gal_candidates = 0
        radius = 5
        while (radius < 11 and gal_candidates < 21):
            try:
                print("Radius: %s" % radius)
                gal_candidates = len(ned_table)
                radius += 1
                print("Result length: %s" % gal_candidates)
            except Exception as e:
                radius += 1
                print("NED exception: %s" % e.args)

        galaxy_names,noz_galaxy_names = [],[]
        galaxy_zs,noz_galaxy_zs = [],[]
        galaxy_seps,noz_galaxy_seps = [],[]
        galaxies_with_z,noz_galaxies_with_z = [],[]
        galaxy_ras,noz_galaxy_ras = [],[]
        galaxy_decs,noz_galaxy_decs = [],[]
        galaxy_mags,noz_galaxy_mags = [],[]
        if ned_table is not None:
            print("NED Matches: %s" % len(ned_table))

            galaxy_candidates = np.asarray([entry.decode("utf-8") for entry in ned_table["Type"]])
            galaxies_indices = np.where(galaxy_candidates == 'G')
            galaxies = ned_table[galaxies_indices]

            print("Galaxy Candidates: %s" % len(galaxies))

            # Get Galaxy name, z, separation for each galaxy with z
            for l in range(len(galaxies)):
                if isinstance(galaxies[l]["Redshift"], float):
                    galaxies_with_z.append(galaxies[l])
                    galaxy_names.append(galaxies[l]["Object Name"])
                    galaxy_zs.append(galaxies[l]["Redshift"])
                    galaxy_seps.append(galaxies[l]["Separation"])
                    galaxy_ras.append(galaxies[l]["RA"])
                    galaxy_decs.append(galaxies[l]["DEC"])
                    galaxy_mags.append(galaxies[l]["Magnitude and Filter"])

                noz_galaxies_with_z.append(galaxies[l])
                noz_galaxy_names.append(galaxies[l]["Object Name"])
                noz_galaxy_zs.append(galaxies[l]["Redshift"])
                noz_galaxy_seps.append(galaxies[l]["Separation"])
                noz_galaxy_ras.append(galaxies[l]["RA"])
                noz_galaxy_decs.append(galaxies[l]["DEC"])
                noz_galaxy_mags.append(galaxies[l]["Magnitude and Filter"])

            print("Galaxies with z: %s" % len(galaxies_with_z))
            # Get Dust in LoS for each galaxy with z
            if len(galaxies_with_z) > 0:
                for l in range(len(galaxies_with_z)):
                    co_l = coordinates.SkyCoord(ra=galaxies_with_z[l]["RA"],
                                                dec=galaxies_with_z[l]["DEC"],
                                                unit=(u.deg, u.deg), frame='fk4', equinox='J2000.0')

            else:
                print("No NED Galaxy hosts with z")

        # put in the hosts
        hostcoords = ''; hosturl = ''; ned_mag = ''
        galaxy_z_times_seps = np.array(galaxy_seps)*np.array(np.abs(galaxy_zs))
        hostdict = {}
        for z,name,ra,dec,sep,mag,gzs in zip(galaxy_zs,galaxy_names,galaxy_ras,
                                             galaxy_decs,galaxy_seps,galaxy_mags,
                                             galaxy_z_times_seps):
            if gzs == np.min(galaxy_z_times_seps):
                cosmo = FlatLambdaCDM(70,0.3)
                if sep*60/cosmo.arcsec_per_kpc_proper(z).value < 100:
                    hostdict = {'name':name,'ra':ra,'dec':dec,'redshift':z}
            hostcoords += f'ra={ra:.7f}, dec={dec:.7f}\n'

        # if this didn't work, let's get the nearest potential host
        if 'name' not in hostdict.keys():
            for z,name,ra,dec,sep,mag in zip(noz_galaxy_zs,noz_galaxy_names,noz_galaxy_ras,
                                             noz_galaxy_decs,noz_galaxy_seps,noz_galaxy_mags):
                if sep == np.min(noz_galaxy_seps):
                    hostdict = {'name':name,'ra':ra,'dec':dec,'redshift':None}
            
        return hostdict,hostcoords

    def UpdateFromTNS(self,ndays=None,allowed_statuses=['New','Following','Watch','FollowupRequested','Interesting'],doTNS=True):

        if ndays:
            date_format = '%Y-%m-%d'
            datemin = (datetime.now() - timedelta(days=ndays)).strftime(date_format)
            argstring = 'created_date_gte=%s'%datemin
        else:
            argstring = 'status_in={}'.format(','.join(allowed_statuses))
        offsetcount = 0

        auth = coreapi.auth.BasicAuthentication(
            username=self.dblogin,
            password=self.dbpassword,
        )
        client = coreapi.Client(auth=auth)
        transienturl = '%stransients?limit=1000&format=json&%s&offset=%i'%(self.dburl,argstring,offsetcount)
        print(transienturl)
        schema = client.get(transienturl)

        objs,ras,decs = [],[],[]

        for transient in schema['results']:
            objs.append(transient['name'])
            ras.append(transient['ra'])
            decs.append(transient['dec'])
        
        while len(schema['results']) == 1000:
            offsetcount += 1000
            transienturl = '%stransients?limit=1000&format=json&%s&offset=%i'%(self.dburl,argstring,offsetcount)
            print(transienturl)
            schema = client.get(transienturl)
            for transient in schema['results']:
                objs.append(transient['name'])
                ras.append(transient['ra'])
                decs.append(transient['dec'])
        if self.redohost: nsn = self.GetAndUploadAllData(objs,ras,decs,doGHOST=True,doEBV=True,doTNS=doTNS)
        else: nsn = self.GetAndUploadAllData(objs,ras,decs,doGHOST=False,doEBV=False,doTNS=doTNS)
        return nsn

    def GetRecentEvents(self,ndays=None,doTNS=True):
        #date_format = '%Y-%m-%d'
        datemin = (datetime.now() - timedelta(days=ndays)).isoformat() #strftime(date_format)
        search_obj=[("ra",""), ("dec",""), ("radius",""), ("units",""),
                    ("objname",""), ("internal_name",""),("public_timestamp",datemin)]
        
        response=search(self.tnsapi, search_obj, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
        count = 0
        while response.status_code == 429 and count < 5:
            print('TNS request failed.  Waiting 60 seconds to try again...')
            time.sleep(60)
            response=search(self.tnsapi, search_obj, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
            count += 1
        json_data = format_to_json(response.text)

        objs,ras,decs = [],[],[]
        for jd in json_data['data']['reply']:
            TNSGetSingle = [("objname",jd['objname']),
                            ("photometry","0"),
                            ("spectra","0")]

            response_single=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
            while response_single.status_code == 429:
                print('TNS request failed.  Waiting 60 seconds to try again...')
                time.sleep(60)
                response_single=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)

            json_data_single = format_to_json(response_single.text)

            objs.append(json_data_single['data']['reply']['objname'])
            ras.append(json_data_single['data']['reply']['ra'])
            decs.append(json_data_single['data']['reply']['dec'])
        if len(objs): nsn = self.GetAndUploadAllData(objs,ras,decs,doGHOST=self.redohost,doEBV=self.redohost,doTNS=doTNS)
        else: nsn = 0
        return nsn

    def GetRecentMissingEvents(self,ndays=None,doTNS=True):
        from YSE_App.models import Transient
        #date_format = '%Y-%m-%d'
        datemin = (datetime.now() - timedelta(days=ndays)).isoformat() #strftime(date_format)
        search_obj=[("ra",""), ("dec",""), ("radius",""), ("units",""),
                    ("objname",""), ("internal_name",""),("public_timestamp",datemin)]
        response=search(self.tnsapi, search_obj, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
        if response.status_code == 429:
            print('TNS request failed.  Waiting 60 seconds to try again...')
            time.sleep(60)
            response=search(self.tnsapi, search_obj, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
        json_data = format_to_json(response.text)

        objs,ras,decs = [],[],[]
        for jd in json_data['data']['reply']:
            if len(Transient.objects.filter(name=jd['objname'])): continue
            TNSGetSingle = [("objname",jd['objname']),
                             ("photometry","1"),
                             ("spectra","0")]

            
            response_single=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
            if response_single.status_code == 429:
                print('TNS request failed.  Waiting 60 seconds to try again...')
                time.sleep(60)
                response_single=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)

            json_data_single = format_to_json(response_single.text)
            objs.append(json_data_single['data']['reply']['objname'])
            ras.append(json_data_single['data']['reply']['ra'])
            decs.append(json_data_single['data']['reply']['dec'])

        if len(objs): nsn = self.GetAndUploadAllData(objs,ras,decs,doGHOST=self.redohost,doEBV=self.redohost,doTNS=doTNS)
        else: nsn = 0
        return nsn

    
    def ProcessTNSEmails(self):
        body = ""
        html = ""
        tns_objs = []

        ########################################################
        # Get All Email
        ########################################################
        mail =  imaplib.IMAP4_SSL('imap.gmail.com', 993) #, ssl_context=ctx

        ## NOTE: This is not the way to do this. You will want to implement an industry-standard login step ##
        mail.login(self.login, self.password)
        mail.select('TNS', readonly=False)
        retcode, msg_ids_bytes = mail.search(None, '(UNSEEN)')
        msg_ids = msg_ids_bytes[0].decode("utf-8").split(" ")

        try:
            if retcode != "OK" or msg_ids[0] == "":
                raise ValueError("No messages")

        except ValueError as err:
            print("%s. Exiting..." % err.args)
            mail.close()
            mail.logout()
            del mail
            print("Process done.")
            return 0

        objs,ras,decs = [],[],[]
        print('length of msg_ids %s' %len(msg_ids))
        for i in range(len(msg_ids)):
            if i%10 == 0:
              print("Processing emails %d/%d" %(i, len(msg_ids)))
            ########################################################
            # Iterate Over Email
            ########################################################
            typ, data = mail.fetch(msg_ids[i],'(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            if 'AstroNotes' in msg['Subject']: continue
            # Mark messages as "Unseen"
            # result, wdata = mail.store(msg_ids[i], '-FLAGS', '\Seen')

            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    # skip any text/plain (txt) attachments
                    if (ctype == 'text/plain' or ctype == 'text/html') and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True).decode('utf-8')  # decode
                        break
            # not multipart - i.e. plain text, no attachments, keeping fingers crossed
            else:
                body = msg.get_payload(decode=True).decode('utf-8')

            for obj in re.findall(reg_obj,body): objs.append(obj)
            for ra in re.findall(reg_ra,body): ras.append(ra)
            for dec in re.findall(reg_dec,body): decs.append(dec)
            if len(objs) != len(ras):
                import pdb; pdb.set_trace()

            
            # Mark messages as "Seen"
            result, wdata = mail.store(msg_ids[i], '+FLAGS', '\\Seen')
        if len(objs):
            nsn = self.GetAndUploadAllData(objs,ras,decs)
        else: nsn = 0
        return nsn

    def GetAndUploadAllData(self,objs,ras,decs,doGHOST=True,doEBV=True,doTNS=True): #doNED=True
        TransientUploadDict = {}
        assert len(ras) == len(decs)

        ebvall,nedtables = [],[]
        ebvtstart = time.time()
        ebv_timeout,ned_timeout = False,False
        if doGHOST:

            if not os.path.exists(f'{self.ghost_path}/database/GHOST.csv'):
                try:
                    getGHOST(real=True, verbose=True, install_path=self.ghost_path)
                except:
                    pass
                
            def handler(signum, frame):
                raise Exception("timeout!")
                
            signal.signal(signal.SIGALRM, handler)
            ghost_hosts = None
            try:
                signal.alarm(600)
                if type(ras[0]) == float:
                    scall = [SkyCoord(r,d,unit=u.deg) for r,d in zip(ras,decs)]
                else:
                    scall = [SkyCoord(r,d,unit=(u.hourangle,u.deg)) for r,d in zip(ras,decs)]

                ghost_hosts = getTransientHosts(objs, scall, verbose=True, starcut='gentle', ascentMatch=False, GHOSTpath=self.ghost_path)
                if is_photoz:
                    ghost_hosts = calc_photoz(ghost_hosts)[1]
                os.system(f"rm -r transients_{datetime.utcnow().isoformat().split('T')[0].replace('-','')}*")
            except:
                print('GHOST timeout!')
                ned_timeout = True

            if type(ras[0]) == float:
                scall = SkyCoord(ras,decs,frame="fk5",unit=u.deg)
            else:
                scall = SkyCoord(ras,decs,frame="fk5",unit=(u.hourangle,u.deg))
            
            signal.signal(signal.SIGALRM, handler)
            try:
                signal.alarm(600)
                ebvall = sfd(scall)*0.86
            except:
                print('MW E(B-V) timeout!')
                ebv_timeout = True

                        
            print('E(B-V)/GHOST time: %.1f seconds'%(time.time()-ebvtstart))

            signal.alarm(0)

        if doEBV and not doGHOST:
            if type(ras[0]) == float:
                scall = SkyCoord(ras,decs,frame="fk5",unit=u.deg)
            else:
                scall = SkyCoord(ras,decs,frame="fk5",unit=(u.hourangle,u.deg))
                        
            def handler(signum, frame):
                raise Exception("timeout!")
            signal.signal(signal.SIGALRM, handler)
            try:
                signal.alarm(600)
                ebvall = sfd(scall)*0.86
            except:
                print('MW E(B-V) timeout!')
                ebv_timeout = True

        if type(ras[0]) == float:
            scall = SkyCoord(ras,decs,frame="fk5",unit=u.deg)
        else:
            scall = SkyCoord(ras,decs,frame="fk5",unit=(u.hourangle,u.deg))

                
        #    signal.signal(signal.SIGALRM, handler)              
        #    try:
        #        signal.alarm(600)
        #        for sc in scall:
        #            try:
        #                ned_region_table = \
        #                    Ned.query_region(
        #                        sc, radius=self.nedradius*u.arcmin,
        #                        equinox='J2000.0')
        #            except:
        #                ned_region_table = None
        #            nedtables += [ned_region_table]
        #    except:
        #        print('NED timeout!')
        #        ned_timeout = True

            print('E(B-V)/NED time: %.1f seconds'%(time.time()-ebvtstart))
            signal.alarm(0)
        
        tstart = time.time()
        print('getting TNS data')
        TNSData = []
        json_data = []
        total_objs = 0

        for j in range(len(objs)):
            if objs[j].startswith('20'):
                if doTNS:
                    TNSGetSingle = [("objname",objs[j]),
                                    ("photometry","1"),
                                    ("spectra","1")]


                    response=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
                    if response.status_code == 429:
                        print('TNS failed!  waiting 60 seconds...')
                        time.sleep(60)
                        response=get(self.tnsapi, TNSGetSingle, self.tnsapikey, self.tns_bot_id, self.tns_bot_name)
                        
                    json_data += [format_to_json(response.text)]
                    total_objs += 1
                else:
                    json_data += [None]
            else:
                json_data += [None]
        print(time.time()-tstart)

        print('getting TNS content takes %.1f seconds'%(time.time()-tstart))
        print('updating {} transients!'.format(len(objs)))
        for j,jd in zip(range(len(objs)),json_data):
            tallstart = time.time()
            obj = objs[j]

            iobj = np.where(obj == np.array(objs))[0]
            if len(iobj) > 1: iobj = int(iobj[0])
            else: iobj = int(iobj)

            sc = scall[iobj]
            if doEBV:
                if not ebv_timeout: ebv = '%.3f'%ebvall[iobj]
                else: ebv = None
            else:
                ebv = None

            if doGHOST and ghost_hosts is not None:
                ghost_host = ghost_hosts[ghost_hosts['TransientName'] == objs[j]]
                if not len(ghost_host): ghost_host = None
            else:
                ghost_host = None
                
            #if doNED:
            #    if not ned_timeout:
            #        nedtable = nedtables[iobj]
            #    else: nedtable = None
            #else: nedtable = None
            
            print("Object: %s\nRA: %s\nDEC: %s" % (obj,ras[iobj],decs[iobj]))

            ########################################################
            # For Item in Email, Get NED
            ########################################################

            if jd is not None:
                if type(jd['data']['reply']['objname']) == str:
                    jd = jd['data']['reply']
                else:
                    jd = None

            transientdict = self.getTNSData(jd,obj,sc,ebv)
            try:
                photdict = self.getZTFPhotometry(sc)
            except: photdict = None
            try:
                if jd:
                    photdict,nondetectdate,nondetectmaglim,nondetectfilt,nondetectins = \
                        self.getTNSPhotometry(jd,PhotUploadAll=photdict)
                    transientdict['transientphotometry'] = photdict
                    specdict = self.getTNSSpectra(jd,sc)
                    transientdict['transientspectra'] = specdict

                    if nondetectdate: transientdict['non_detect_date'] = nondetectdate
                    if nondetectmaglim: transientdict['non_detect_limit'] = nondetectmaglim
                    if nondetectfilt: transientdict['non_detect_band'] =  nondetectfilt
                    if nondetectfilt: transientdict['non_detect_instrument'] =  nondetectins
                elif photdict is not None: transientdict['transientphotometry'] = photdict
            except Exception as e: pass

            #exc_type, exc_obj, exc_tb = sys.exc_info()
            #raise RuntimeError('error %s at line number %s'%(e,exc_tb.tb_lineno))

            #try:
            #    if doNED:
            #        hostdict,hostcoords = self.getNEDData(jd,sc,nedtable)
            #        transientdict['host'] = hostdict
            #        transientdict['candidate_hosts'] = hostcoords
            #except: pass

            if ghost_host is not None:
                hostdict,hostcoords = self.getGHOSTData(jd,sc,ghost_host)
                transientdict['host'] = hostdict
                transientdict['candidate_hosts'] = hostcoords
            
            #try:
            #   phot_ps1dr2 = self.get_PS_DR2_data(sc)
            #   if phot_ps1dr2 is not None:
            #       transientdict['transientphotometry']['PS1DR2'] = phot_ps1dr2
            #except:
            #   pass

            TransientUploadDict[obj] = transientdict
            if not j % 10:
                TransientUploadDict['noupdatestatus'] = self.noupdatestatus
                TransientUploadDict['TNS'] = True
                self.UploadTransients(TransientUploadDict)
                TransientUploadDict = {}
        if j % 10:
            TransientUploadDict['noupdatestatus'] = self.noupdatestatus
            TransientUploadDict['TNS'] = True
            self.UploadTransients(TransientUploadDict)

        return(len(TransientUploadDict))

    def UploadTransients(self,TransientUploadDict):

        url = '%s'%self.dburl.replace('/api','/add_transient')
        try:
            r = requests.post(url = url, data = json.dumps(TransientUploadDict),
                              auth=HTTPBasicAuth(self.dblogin,self.dbpassword))

            try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
            except: print(r.text)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            smtpserver = "%s:%s" % (self.options.SMTP_HOST, self.options.SMTP_PORT)
            from_addr = "%s@gmail.com" % self.options.SMTP_LOGIN
            subject = "TNS Transient Upload Failure in GetRecentEvents"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload transients in TNS_uploads.TNS_recent()\n"
            html_msg += "Error : %s at line number %s"
            sendemail(from_addr, self.options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      self.options.SMTP_LOGIN, self.options.dbemailpassword, smtpserver)
    
            #raise RuntimeError(e)
        print("Process done.")


def jd_to_date(jd):
    time = Time(jd,scale='utc',format='jd')
    return time.isot

def date_to_mjd(obs_date):
    time = Time(obs_date,scale='utc')
    return time.mjd

def fetch(url):
    urlresponse = None
    count = 0
    while not urlresponse and count < 3:
        try:
            urlresponse = urllib.request.urlopen(url).read()
            return url, urlresponse
        except Exception as e:
            pass
        count += 1

    print('URL %s failed after 3 tries'%(url))
    return url, None

def run_parallel_in_threads(target, args_list):
    result = queue.Queue()
    # wrapper to collect return value in a Queue
    def task_wrapper(*args):
        result.put(target(*args))
    threads = [threading.Thread(target=task_wrapper, args=args) for args in args_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result


def sendemail(from_addr, to_addr,
            subject, message,
            login, password, smtpserver, cc_addr=None):

    print("Preparing email")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    payload = MIMEText(message, 'html')
    msg.attach(payload)

    with smtplib.SMTP(smtpserver) as server:
        try:
            server.starttls()
            server.login(login, password)
            resp = server.sendmail(from_addr, [to_addr], msg.as_string())
            print("Send success")
        except Exception as e:
            print("Send fail; %s"%e)

def format_to_json(source):
    # change data to json format and return
    parsed=json.loads(source,object_pairs_hook=OrderedDict)
    #result=json.dumps(parsed,indent=4)
    return parsed #result

# function for search obj
def search(url,json_list,api_key,tns_bot_id,tns_bot_name):
  try:
    # url for search obj
    search_url=url+'/search'
    # headers
    headers={'User-Agent':'tns_marker{"tns_id":'+str(tns_bot_id)+', "type":"bot",'\
             ' "name":"'+tns_bot_name+'"}'}
    # change json_list to json format
    json_file=OrderedDict(json_list)
    # construct a dictionary of api key data and search obj data
    search_data={'api_key':api_key, 'data':json.dumps(json_file)}
    # search obj using request module
    response=requests.post(search_url, headers=headers, data=search_data)
    # return response
    return response
  except Exception as e:
    return [None,'Error message : \n'+str(e)]

# function for get obj
def get(url,json_list,api_key,tns_bot_id,tns_bot_name):
  try:
    # url for get obj
    get_url=url+'/object'
    # headers
    headers={'User-Agent':'tns_marker{"tns_id":'+str(tns_bot_id)+', "type":"bot",'\
             ' "name":"'+tns_bot_name+'"}'}
    # change json_list to json format
    json_file=OrderedDict(json_list)
    # construct a dictionary of api key data and get obj data
    get_data={'api_key':api_key, 'data':json.dumps(json_file)}
    # get obj using request module
    response=requests.post(get_url, headers=headers, data=get_data)
    # return response
    return response
  except Exception as e:
    return [None,'Error message : \n'+str(e)]

def get_file(url,api_key,tns_bot_id,tns_bot_name):
  try:
    # take filename
    filename=os.path.basename(url)
    # headers
    headers={'User-Agent':'tns_marker{"tns_id":'+str(tns_bot_id)+', "type":"bot",'\
             ' "name":"'+tns_bot_name+'"}'}
    # downloading file using request module
    response=requests.post(url, headers=headers, data={'api_key':api_key}, stream=True)
    return response
  except Exception as e:
    print ('Error message : \n'+str(e))
    return None
    
class TNS_emails(CronJobBase):

    RUN_EVERY_MINS = 3

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.TNS_uploads.TNS_emails'
    
    def do(self):

        code = 'YSE_App.data_ingest.TNS_uploads.TNS_emails'
        
        # execute only if run as a script
        print("running TNS emails at {}".format(datetime.now().isoformat()))
        usagestring = "TNS_Synopsis.py <options>"

        tstart = time.time()
        tnsproc = processTNS()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required
        parser = tnsproc.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR

        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = tnsproc.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        tnsproc.hostmatchrad = options.hostmatchrad

        tnsproc.login = options.login
        tnsproc.password = options.password
        tnsproc.dblogin = options.dblogin
        tnsproc.dbpassword = options.dbpassword
        tnsproc.dbemailpassword = options.dbemailpassword
        tnsproc.dburl = options.dburl
        tnsproc.status = options.status
        tnsproc.settingsfile = options.settingsfile
        tnsproc.clobber = options.clobber
        tnsproc.noupdatestatus = options.noupdatestatus
        tnsproc.redohost = options.redohost
        tnsproc.nedradius = options.nedradius
        tnsproc.tnsapi = options.tnsapi
        tnsproc.tnsapikey = options.tnsapikey
        tnsproc.tns_bot_id = options.tns_bot_id
        tnsproc.tns_bot_name = options.tns_bot_name
        tnsproc.ztfurl = options.ztfurl
        tnsproc.ghost_path = options.ghost_path
        
        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure"
        html_msg = f"Alert : YSE_PZ Failed to upload transients in {code} \n"
        html_msg += "Error : %s at line number %s"

        
        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="1")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)
            
        try:
            if options.update:
                tnsproc.noupdatestatus = True
                nsn = tnsproc.UpdateFromTNS()
            else:
                nsn = tnsproc.ProcessTNSEmails()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


class TNS_updates(CronJobBase):

    RUN_AT_TIMES = ['00:00', '08:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'YSE_App.data_ingest.TNS_uploads.TNS_updates'
    
    def do(self):

        code = 'YSE_App.data_ingest.TNS_uploads.TNS_updates'
        
        # execute only if run as a script
        print("running TNS updates at {}".format(datetime.now().isoformat()))
        usagestring = "TNS_Synopsis.py <options>"

        tstart = time.time()
        tnsproc = processTNS()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required
        parser = tnsproc.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR
        
        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = tnsproc.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        tnsproc.hostmatchrad = options.hostmatchrad

        tnsproc.login = options.login
        tnsproc.password = options.password
        tnsproc.dblogin = options.dblogin
        tnsproc.dbpassword = options.dbpassword
        tnsproc.dbemailpassword = options.dbemailpassword
        tnsproc.dburl = options.dburl
        tnsproc.status = options.status
        tnsproc.settingsfile = options.settingsfile
        tnsproc.clobber = options.clobber
        tnsproc.noupdatestatus = options.noupdatestatus
        tnsproc.redohost = False #True
        tnsproc.nedradius = options.nedradius
        tnsproc.tnsapi = options.tnsapi
        tnsproc.tnsapikey = options.tnsapikey
        tnsproc.tns_bot_id = options.tns_bot_id
        tnsproc.tns_bot_name = options.tns_bot_name
        tnsproc.ztfurl = options.ztfurl
        tnsproc.ghost_path = options.ghost_path
        
        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure"
        html_msg = f"Alert : YSE_PZ Failed to upload transients in {code}\n"
        html_msg += "Error : %s at line number %s"

        
        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="2")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)
        
        try:
            tnsproc.noupdatestatus = True
            nsn = tnsproc.UpdateFromTNS(ndays=options.ndays,doTNS=False)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

class TNS_Ignore_updates(CronJobBase):

    RUN_AT_TIMES = ['00:00']
    RUN_EVERY_MINS = 4320
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS,run_at_times=RUN_AT_TIMES)

    code = 'YSE_App.data_ingest.TNS_uploads.TNS_Ignore_updates'
    
    def do(self):

        code = 'YSE_App.data_ingest.TNS_uploads.TNS_Ignore_updates'
        
        # execute only if run as a script
        print("running TNS updates for Ignore transients at {}".format(datetime.now().isoformat()))
        usagestring = "TNS_Synopsis.py <options>"

        tstart = time.time()
        tnsproc = processTNS()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required
        parser = tnsproc.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR
        
        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = tnsproc.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        tnsproc.hostmatchrad = options.hostmatchrad

        tnsproc.login = options.login
        tnsproc.password = options.password
        tnsproc.dblogin = options.dblogin
        tnsproc.dbpassword = options.dbpassword
        tnsproc.dbemailpassword = options.dbemailpassword
        tnsproc.dburl = options.dburl
        tnsproc.status = options.status
        tnsproc.settingsfile = options.settingsfile
        tnsproc.clobber = options.clobber
        tnsproc.noupdatestatus = options.noupdatestatus
        tnsproc.redohost = False #True
        tnsproc.nedradius = options.nedradius
        tnsproc.tnsapi = options.tnsapi
        tnsproc.tnsapikey = options.tnsapikey
        tnsproc.tns_bot_id = options.tns_bot_id
        tnsproc.tns_bot_name = options.tns_bot_name
        tnsproc.ztfurl = options.ztfurl
        tnsproc.ghost_path = options.ghost_path
        
        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure"
        html_msg = f"Alert : YSE_PZ Failed to upload transients in {code}\n"
        html_msg += "Error : %s at line number %s"

        
        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="3")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)
        
        try:
            tnsproc.noupdatestatus = True
            nsn = tnsproc.UpdateFromTNS(ndays=30,allowed_statuses=['Ignore'],doTNS=False)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))
        
class TNS_recent(CronJobBase):

    RUN_AT_TIMES = ['00:00', '08:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'YSE_App.data_ingest.TNS_uploads.TNS_recent'
    
    def do(self):

        code = 'YSE_App.data_ingest.TNS_uploads.TNS_recent'
        
        # execute only if run as a script
        print("checking for recent TNS events at {}".format(datetime.now().isoformat()))
        usagestring = "TNS_Synopsis.py <options>"

        tstart = time.time()
        tnsproc = processTNS()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required
        parser = tnsproc.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR
        
        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = tnsproc.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        tnsproc.hostmatchrad = options.hostmatchrad

        tnsproc.login = options.login
        tnsproc.password = options.password
        tnsproc.dblogin = options.dblogin
        tnsproc.dbpassword = options.dbpassword
        tnsproc.dbemailpassword = options.dbemailpassword
        tnsproc.dburl = options.dburl
        tnsproc.status = options.status
        tnsproc.settingsfile = options.settingsfile
        tnsproc.clobber = options.clobber
        tnsproc.noupdatestatus = options.noupdatestatus
        tnsproc.redohost = True
        tnsproc.nedradius = options.nedradius
        tnsproc.tnsapi = options.tnsapi
        tnsproc.tnsapikey = options.tnsapikey
        tnsproc.tns_bot_id = options.tns_bot_id
        tnsproc.tns_bot_name = options.tns_bot_name
        tnsproc.ztfurl = options.ztfurl
        tnsproc.ghost_path = options.ghost_path
        tnsproc.ndays = float(options.tns_recent_ndays)
        tnsproc.tns_fastupdates_nminutes = float(options.tns_fastupdates_nminutes)

        # in case of errors
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure in GetRecentEvents"
        html_msg = f"Alert : YSE_PZ Failed to upload transients in {code}\n"
        html_msg += "Error : %s at line number %s"

        
        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="4")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)
            
        try:
            tnsproc.noupdatestatus = True
            nsn = tnsproc.GetRecentMissingEvents(ndays=tnsproc.ndays)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

class TNS_recent_realtime(CronJobBase):

    RUN_AT_TIMES = ['00:00', '08:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'YSE_App.data_ingest.TNS_uploads.TNS_recent_realtime'
        
    def do(self):

        code = 'YSE_App.data_ingest.TNS_uploads.TNS_recent_realtime'
        
        # execute only if run as a script
        print("checking for recent TNS events at {}".format(datetime.now().isoformat()))
        usagestring = "TNS_Synopsis.py <options>"

        tstart = time.time()
        tnsproc = processTNS()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required
        parser = tnsproc.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR
        
        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = tnsproc.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        tnsproc.hostmatchrad = options.hostmatchrad

        tnsproc.login = options.login
        tnsproc.password = options.password
        tnsproc.dblogin = options.dblogin
        tnsproc.dbpassword = options.dbpassword
        tnsproc.dbemailpassword = options.dbemailpassword
        tnsproc.dburl = options.dburl
        tnsproc.status = options.status
        tnsproc.settingsfile = options.settingsfile
        tnsproc.clobber = options.clobber
        tnsproc.noupdatestatus = options.noupdatestatus
        tnsproc.redohost = True
        tnsproc.nedradius = options.nedradius
        tnsproc.tnsapi = options.tnsapi
        tnsproc.tnsapikey = options.tnsapikey
        tnsproc.tns_bot_id = options.tns_bot_id
        tnsproc.tns_bot_name = options.tns_bot_name
        tnsproc.ztfurl = options.ztfurl
        tnsproc.ghost_path = options.ghost_path
        tnsproc.ndays = float(options.tns_recent_ndays)
        tnsproc.tns_fastupdates_nminutes = 60 #float(options.tns_fastupdates_nminutes)

        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure in GetRecentEvents"
        html_msg = f"Alert : YSE_PZ Failed to upload transients in {code}\n"
        html_msg += "Error : %s at line number %s"

        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="5")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)

        try:
            tnsproc.noupdatestatus = True
            nsn = tnsproc.GetRecentEvents(ndays=tnsproc.tns_fastupdates_nminutes/60./24.)
        except Exception as e:
            print("Sending error email")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            nsn = 0
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


class UpdateGHOST(CronJobBase):

    RUN_AT_TIMES = ['00:00', '08:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'YSE_App.data_ingest.TNS_uploads.UpdateGHOST'
    
    def do(self):
        
        # check for instance of code already running
        # no email hook on this one for now
        me = singleton.SingleInstance(flavor_id="6")

        
        from YSE_App.models import Transient,User,Host
        transients = Transient.objects.filter(
            modified_date__gt=datetime.now()-timedelta(days=5),
            host__isnull=True)

        scall = [SkyCoord(t.ra,t.dec,unit=u.deg) for t in transients]
        names = [t.name for t in transients]

        ghost_hosts = getTransientHosts(names, scall, verbose=True, starcut='gentle', ascentMatch=False, GHOSTpath=djangoSettings.ghost_path)
        if is_photoz:
            ghost_hosts = calc_photoz(ghost_hosts)[1]
        os.system(f"rm -r transients_{datetime.utcnow().isoformat().split('T')[0].replace('-','')}*")

        for i in ghost_hosts.index:
            t = Transient.objects.get(name=ghost_hosts['TransientName'][i])
            print(f'Adding host for {t.name}')
            t.host = Host.objects.create(name=ghost_hosts['objName'][i],ra=ghost_hosts['raMean'][i],dec=ghost_hosts['decMean'][i],
                                         modified_by=User.objects.get(username='admin'),created_by=User.objects.get(username='admin'))

            if ghost_hosts['NED_redshift'][i] == ghost_hosts['NED_redshift'][i]:
                t.host.redshift = ghost_hosts['NED_redshift'][i]

            if 'photo_z' in ghost_hosts.keys() and ghost_hosts['photo_z'][i] == ghost_hosts['photo_z'][i]:
                t.host.photo_z_internal = ghost_hosts['photo_z'][i]
            
            t.host.save()
            t.save()
        print('success')
