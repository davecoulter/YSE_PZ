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
import wget
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
import mastcasjobs

reg_obj = "https://wis-tns.weizmann.ac.il/object/(\w+)"
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

    print(query)

    jobs = mastcasjobs.MastCasJobs(context="HLSP_PS1_PSC")
    results = jobs.quick(query, task_name="python cross-match")

    output = results.split('\n')[1]
    if not output:
        output = None

    return output

class processTNS():
    def __init__(self):
        self.verbose = None

    def add_options(self, parser=None, usage=None, config=None):
        import optparse
        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_option('--clobber', default=False, action="store_true",
                          help='clobber output file')
        parser.add_option('-s','--settingsfile', default=None, type="string",
                          help='settings file (login/password info)')
        parser.add_option('--status', default='New', type="string",
                          help='transient status to enter in YS_PZ')
        parser.add_option('--noupdatestatus', default=False, action="store_true",
                          help='if set, don\'t promote ignore -> new when uploading')
        parser.add_option('--update', default=False, action="store_true",
                          help='if set, scrape TNS pages to update events already in YSE_PZ')
        parser.add_option('--updatefromZTF', default=False, action="store_true",
                          help='if set, update photometry from ZTF')
        parser.add_option('--redoned', default=False, action="store_true",
                          help='if set, repeat NED search to find host matches (slow-ish)')
        parser.add_option('--nedradius', default=5, type='float',
                          help='NED search radius, in arcmin')
        parser.add_option('--ndays', default=None, type='int',
                          help='number of days before today update events')

        if config:
            parser.add_option('--login', default=config.get('main','login'), type="string",
                              help='gmail login (default=%default)')
            parser.add_option('--password', default=config.get('main','password'), type="string",
                              help='gmail password (default=%default)')
            parser.add_option('--dblogin', default=config.get('main','dblogin'), type="string",
                              help='database login, if post=True (default=%default)')
            parser.add_option('--dbemail', default=config.get('main','dbemail'), type="string",
                              help='database login, if post=True (default=%default)')
            parser.add_option('--dbpassword', default=config.get('main','dbpassword'), type="string",
                              help='database password, if post=True (default=%default)')
            parser.add_option('--dburl', default=config.get('main','dburl'), type="string",
                              help='URL to POST transients to a database (default=%default)')
            parser.add_option('--tnsapi', default=config.get('main','tnsapi'), type="string",
                              help='TNS API URL (default=%default)')
            parser.add_option('--tnsapikey', default=config.get('main','tnsapikey'), type="string",
                              help='TNS API key (default=%default)')
            parser.add_option('--hostmatchrad', default=config.get('main','hostmatchrad'), type="float",
                              help='matching radius for hosts (arcmin) (default=%default)')
            parser.add_option('--ztfurl', default=config.get('main','ztfurl'), type="string",
                              help='ZTF URL (default=%default)')

            parser.add_option('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type="string",
                              help='SMTP login (default=%default)')
            parser.add_option('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type="string",
                              help='SMTP host (default=%default)')
            parser.add_option('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type="string",
                              help='SMTP port (default=%default)')

        else:
            parser.add_option('--login', default="", type="string",
                              help='gmail login (default=%default)')
            parser.add_option('--password', default="", type="string",
                              help='gmail password (default=%default)')
            parser.add_option('--dblogin', default="", type="string",
                              help='database login, if post=True (default=%default)')
            parser.add_option('--dbemail', default="", type="string",
                              help='database login, if post=True (default=%default)')
            parser.add_option('--dbpassword', default="", type="string",
                              help='database password, if post=True (default=%default)')
            parser.add_option('--url', default="", type="string",
                              help='URL to POST transients to a database (default=%default)')
            parser.add_option('--hostmatchrad', default=0.001, type="float",
                              help='matching radius for hosts (arcmin) (default=%default)')
            parser.add_option('--tnsapi', default="", type="string",
                              help='TNS API URL (default=%default)')
            parser.add_option('--tnsapikey', default="", type="string",
                              help='TNS API key (default=%default)')
            parser.add_option('--ztfurl', default="", type="string",
                              help='ZTF URL (default=%default)')

            parser.add_option('--SMTP_LOGIN', default='', type="string",
                              help='SMTP login (default=%default)')
            parser.add_option('--SMTP_HOST', default='', type="string",
                              help='SMTP host (default=%default)')
            parser.add_option('--SMTP_PORT', default='', type="string",
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

        TransientDict = {'name':obj,
                         'slug':obj,
                         'ra':sc.ra.deg,
                         'dec':sc.dec.deg,
                         'obs_group':'Unknown',
                         'mw_ebv':ebv,
                         'status':status,
                         'point_source_probability':ps_prob,
                         'tags':[]}

        if jd:
            TransientDict['disc_date'] = jd['discoverydate']
            TransientDict['obs_group'] = jd['source_group']['group_name']
            if not TransientDict['obs_group']:
                TransientDict['obs_group'] = 'Unknown'
            z = jd['redshift']
            if z: TransientDict['redshift'] = float(z)
            evt_type = jd['object_type']['name']
            if evt_type:
                TransientDict['best_spec_class'] = evt_type
                TransientDict['TNS_spec_class'] = evt_type

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

                PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
                                  'band':'%s-ZTF'%phot['filter'],
                                  'groups':[]}
                PhotUploadDict['mag'] = phot['magap']
                PhotUploadDict['mag_err'] = phot['sigmagap']
                PhotUploadDict['flux'] = None
                PhotUploadDict['flux_err'] = None
                PhotUploadDict['data_quality'] = 0
                PhotUploadDict['forced'] = None
                PhotUploadDict['flux_zero_point'] = None
                PhotUploadDict['discovery_point'] = 0

                photometrydict['photdata']['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict
            PhotUploadAll['ZTF'] = photometrydict
            return PhotUploadAll

        else: return None


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
        iMag = tmag != -99
        disc_flag[iMag][(mjd[iMag] == np.min(mjd[iMag]))] = 1

        photometrycount = 0
        for ins in np.unique(tinst):

            photometrydict = {'instrument':ins,
                              'obs_group':np.array(obsgroups)[np.array(tinst) == ins][0],
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
            os.system('rm %s spec_tns_upload.txt'%s.split('/')[-1])
            dlfile = wget.download(unquote(s))
            fout = open('spec_tns_upload.txt','w')
            print('# wavelength flux',file=fout)
            print('# instrument %s'%si,file=fout)
            print('# obs_date %s'%so.replace(' ','T'),file=fout)
            print('# obs_group %s'%sog,file=fout)
            print('# ra %s'%sc.ra.deg,file=fout)
            print('# dec %s'%sc.dec.deg,file=fout)
            fin = open(dlfile,'r')
            for line in fin:
                print(line.replace('\n',''),file=fout)
            fout.close()
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

            os.system('rm %s spec_tns_upload.txt'%s.split('/')[-1])
            Spectrum['specdata'] = SpecData
            Spectrum['instrument'] = si
            Spectrum['obs_date'] = so
            Spectrum['obs_group'] = sog
            SpecDictAll[s] = Spectrum
        return SpecDictAll

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

        galaxy_names = []
        galaxy_zs = []
        galaxy_seps = []
        galaxies_with_z = []
        galaxy_ras = []
        galaxy_decs = []
        galaxy_mags = []
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
                hostdict = {'name':name,'ra':ra,'dec':dec,'redshift':z}

            hostcoords += 'ra=%.7f, dec=%.7f\n'%(ra,dec)

        return hostdict,hostcoords

    def UpdateFromTNS(self):

        if options.ndays:
            date_format = '%Y-%m-%d'
            datemin = (datetime.now() - timedelta(days=options.ndays)).strftime(date_format)
            argstring = 'created_date_gte=%s'%datemin
        else:
            argstring = 'status_in=New,Following,Watch,FollowupRequested'
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

        if self.redoned: nsn = self.GetAndUploadAllData(objs,ras,decs,doNED=True)
        else: nsn = self.GetAndUploadAllData(objs,ras,decs,doNED=False)
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
        for i in range(len(msg_ids)):
            ########################################################
            # Iterate Over Email
            ########################################################
            typ, data = mail.fetch(msg_ids[i],'(RFC822)')
            msg = email.message_from_bytes(data[0][1])
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

            # Mark messages as "Seen"
            result, wdata = mail.store(msg_ids[i], '+FLAGS', '\\Seen')

        nsn = self.GetAndUploadAllData(objs,ras,decs)
        return nsn

    def GetAndUploadAllData(self,objs,ras,decs,doNED=True):
        TransientUploadDict = {}

        assert len(ras) == len(decs)

        if type(ras[0]) == float:
            scall = SkyCoord(ras,decs,frame="fk5",unit=u.deg)
        else:
            scall = SkyCoord(ras,decs,frame="fk5",unit=(u.hourangle,u.deg))

        ebvall,nedtables = [],[]
        ebvtstart = time.time()
        if doNED:
            for sc in scall:
                try:
                    ebvall += [float('%.3f'%sfd(sc)*0.86)]
                except:
                    dust_table_l = IrsaDust.get_query_table(sc)
                    ebvall += [dust_table_l['ext SandF mean'][0]]
                try:
                    ned_region_table = Ned.query_region(sc, radius=self.nedradius*u.arcmin, equinox='J2000.0')
                except:
                    ned_region_table = None
                nedtables += [ned_region_table]
            print('E(B-V)/NED time: %.1f seconds'%(time.time()-ebvtstart))

        tstart = time.time()
        TNSData = []
        json_data = []
        for j in range(len(objs)):
            TNSGetSingle = [("objname",objs[j]),
                            ("photometry","1"),
                            ("spectra","1")]

            response=get(self.tnsapi, TNSGetSingle, self.tnsapikey)
            json_data += [format_to_json(response.text)]
        print(time.time()-tstart)

        print('getting TNS content takes %.1f seconds'%(time.time()-tstart))

        for j,jd in zip(range(len(objs)),json_data):
            tallstart = time.time()

            obj = objs[j]

            iobj = np.where(obj == np.array(objs))[0]
            if len(iobj) > 1: iobj = int(iobj[0])
            else: iobj = int(iobj)

            if doNED: sc,ebv,nedtable = scall[iobj],ebvall[iobj],nedtables[iobj]
            else: sc = scall[iobj]; ebv = None; nedtable = None

            print("Object: %s\nRA: %s\nDEC: %s" % (obj,ras[iobj],decs[iobj]))

            ########################################################
            # For Item in Email, Get NED
            ########################################################
            if type(jd['data']['reply']['name']) == str:
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
                    specdict = self.getTNSSpectra(jd,sc)
                    transientdict['transientphotometry'] = photdict
                    transientdict['transientspectra'] = specdict

                    if nondetectdate: transientdict['non_detect_date'] = nondetectdate
                    if nondetectmaglim: transientdict['non_detect_limit'] = nondetectmaglim
                    if nondetectfilt: transientdict['non_detect_band'] =  nondetectfilt
                    if nondetectfilt: transientdict['non_detect_instrument'] =  nondetectins
            except: pass

            try:
                if doNED:
                    hostdict,hostcoords = self.getNEDData(jd,sc,nedtable)
                    transientdict['host'] = hostdict
                    transientdict['candidate_hosts'] = hostcoords
            except: pass

            TransientUploadDict[obj] = transientdict

        TransientUploadDict['noupdatestatus'] = self.noupdatestatus
        self.UploadTransients(TransientUploadDict)

        return(len(TransientUploadDict))

    def UploadTransients(self,TransientUploadDict):

        url = '%s'%self.dburl.replace('/api','/add_transient')
        r = requests.post(url = url, data = json.dumps(TransientUploadDict),
                          auth=HTTPBasicAuth(self.dblogin,self.dbpassword))

        print('YSE_PZ says: %s'%json.loads(r.text)['message'])
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
        except:
            print("Send fail")

def format_to_json(source):
    # change data to json format and return
    parsed=json.loads(source,object_pairs_hook=OrderedDict)
    #result=json.dumps(parsed,indent=4)
    return parsed #result

def get(url,json_list,api_key):
    try:
        # url for get obj
        get_url=url+'/object'
        # change json_list to json format
        json_file=OrderedDict(json_list)
        # construct the list of (key,value) pairs
        get_data=[('api_key',(None, api_key)),
                  ('data',(None,json.dumps(json_file)))]
        # get obj using request module
        response=requests.post(get_url, files=get_data)
        return response
    except Exception as e:
        return [None,'Error message : \n'+str(e)]

if __name__ == "__main__":
    # execute only if run as a script

    import optparse
    import configparser

    usagestring = "TNS_Synopsis.py <options>"

    tstart = time.time()
    tnsproc = processTNS()

    # read in the options from the param file and the command line
    # some convoluted syntax here, making it so param file is not required
    parser = tnsproc.add_options(usage=usagestring)
    options,  args = parser.parse_args()
    if options.settingsfile:
        config = configparser.ConfigParser()
        config.read(options.settingsfile)
    else: config=None
    parser = tnsproc.add_options(usage=usagestring,config=config)
    options,  args = parser.parse_args()
    tnsproc.hostmatchrad = options.hostmatchrad

    tnsproc.login = options.login
    tnsproc.password = options.password
    tnsproc.dblogin = options.dblogin
    tnsproc.dbpassword = options.dbpassword
    tnsproc.dburl = options.dburl
    tnsproc.status = options.status
    tnsproc.settingsfile = options.settingsfile
    tnsproc.clobber = options.clobber
    tnsproc.noupdatestatus = options.noupdatestatus
    tnsproc.redoned = options.redoned
    tnsproc.nedradius = options.nedradius
    tnsproc.tnsapi = options.tnsapi
    tnsproc.tnsapikey = options.tnsapikey
    tnsproc.ztfurl = options.ztfurl

    if 'hi': #try:
        if options.update:
            tnsproc.noupdatestatus = True
            nsn = tnsproc.UpdateFromTNS()
        else:
            nsn = tnsproc.ProcessTNSEmails()
    else: #except Exception as e:
        nsn = 0
        from django.conf import settings as djangoSettings
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "TNS Transient Upload Failure"
        print("Sending error email")
        html_msg = "Alert : YSE_PZ Failed to upload transients\n"
        html_msg += "Error : %s"
        sendemail(from_addr, options.dbemail, subject,
                  html_msg%(e),
                  options.SMTP_LOGIN, options.dbpassword, smtpserver)

    print('TNS -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))
