#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from io import open as iopen
import configparser
import time
from html.parser import HTMLParser
import astropy.table as at
import re
import os
from bs4 import BeautifulSoup
import dateutil.parser
from astropy.coordinates import SkyCoord
import astropy.units as u
from YSE_App.util.TNS_Synopsis import mastrequests
#from YSE_App.data_ingest.TNS_uploads import get_ps_score
from astro_ghost.ghostHelperFunctions import *
try:
    from astro_ghost.photoz_helper import calc_photoz
except:
    pass
import datetime
import json
from astropy.time import Time

_decam_url = "https://stsci-transients.stsci.edu/YSE/sniff/"
_google_doc_url = "https://docs.google.com/document/d/17dNoIDlV0TAfi3byMTeLJPsPHAomXIg1ijKb3ioA7to/edit?usp=sharing&export=download"
_google_doc_regex = "?:https:\/\/stsci-transients\.stsci\.edu.*index\.html#.*\""
#_google_doc_url = "https://drive.google.com/uc?export=download&id=17dNoIDlV0TAfi3byMTeLJPsPHAomXIg1ijKb3ioA7to"
#google_doc_url = "https://drive.google.com/uc?export=download&id=17dNoIDlV0TAfi3byMTeLJPsPHAomXIg1ijKb3ioA7to&usp=sharing"
#"https://docs.google.com/document/d/17dNoIDlV0TAfi3byMTeLJPsPHAomXIg1ijKb3ioA7to/edit?usp=sharing"
_google_doc_regex = "(http|ftp|https):\/\/stsci([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"

try:
  from dustmaps.sfd import SFDQuery
  sfd = SFDQuery()
except:
  raise RuntimeError("""can\'t import dust maps

run:
import dustmaps
import dustmaps.sfd
dustmaps.sfd.fetch()""")

def mjd_to_date(obs_mjd):
    time = Time(obs_mjd,scale='utc',format='mjd')
    return time.isot

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

class DECam(CronJobBase):

    RUN_EVERY_MINS = 120

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.DECam_upload.DECam'

    def do(self):
        usagestring = "DECam_upload.py <options>"

        tstart = time.time()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required

        parser = self.add_options(usage=usagestring)
        options,  args = parser.parse_known_args()

        config = configparser.ConfigParser()
        config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
        parser = self.add_options(usage=usagestring,config=config)
        options,  args = parser.parse_known_args()
        self.options = options

        try:
            nsn = self.main()
        except Exception as e:
            print(e)
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "QUB Transient Upload Failure"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload transients from PSST in QUB_data.py\n"
            html_msg += "Error : %s"
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


    def add_options(self, parser=None, usage=None, config=None):
        import argparse
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
        parser.add_argument('--max_days', default=7, type=float,
                          help='grab photometry/objects from the last x days')

        if config:
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                              help='database password, if post=True (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                              help='email password, if post=True (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                              help='URL to POST transients to a database (default=%default)')
            parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
                              help='ZTF URL (default=%default)')
            parser.add_argument('--STATIC', default=config.get('site_settings','STATIC'), type=str,
                              help='static directory (default=%default)')
            
            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                              help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                              help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                              help='SMTP port (default=%default)')

            parser.add_argument('--max_decam_days', default=config.get('main','max_days_decam'), type=float,
                                help='grab photometry/objects from the last x days')

        else:
            pass


        return(parser)

    def getGHOSTData(self,sc,ghost_host):
        hostdict = {}; hostcoords = ''
        hostdict = {'name':ghost_host['objName'].to_numpy()[0],'ra':ghost_host['raMean'].to_numpy()[0],
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
    
    def main(self):
        # get all the DECam links
        good_transient_data = requests.get(_google_doc_url).text
        urls = re.findall(_google_doc_regex,good_transient_data)

        # let's grab the most recent phot. data for each transient
        # if the DECam data on the sniff pages doesn't have more recent
        # data, hopefully we can assume things are up to date
        tr = requests.get(f"{self.options.dburl.replace('/api','')}query_api/DECAT_transients_mags/",
                          auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        etdata = tr.json()['transients']
        etdict = {}; ra = []; dec = []; dict_names = np.array([])
        for et in etdata:
            etdict[et['name']] = et
            ra += [et['ra']]
            dec += [et['dec']]
            dict_names = np.append(dict_names,et['name'])
        scexisting = SkyCoord(ra,dec,unit=u.deg)
            
        # prelims
        transientdict = {}
        if not os.path.exists('database/GHOST.csv'):
            getGHOST(real=True, verbose=True)
            

        count = 0
        nowdate = datetime.datetime.now()
        for (str1,str2,str3) in urls:
            if '#' not in str3: continue
            #if '21466' not in str3: continue
            url_single = f"https://stsci{str2}{str3}"
            candid_toupload = str3.split('#')[-1]
            r = requests.get(url_single)

            soup = BeautifulSoup(r.text)
            tables = soup.find_all("table", attrs={"cols":"6","border":"1"})
            #table = soup.find("table", attrs={"cols":"6","border":"1"}) #,"CELLSPACING":"0","CELLPADDING":"2"})  #, attrs={"class":"details"})
            #headings = [th.get_text() for th in table.find("tr").find_all("th")]
            
            for table in tables:
                data = at.Table.read(str(table).\
                                     replace('<table align="center" border="1" cellpadding="2" cellspacing="0" cols="6" width="100%">',
                                             '<table align="center" border="1" cellpadding="2" cellspacing="0" cols="6" width="100%"><tr>'),
                                     format='html',names=('rowname','rowval'))

            # get RA/Dec
            ra = data['rowval'][data['rowname'] == 'RA'][0]
            dec = data['rowval'][data['rowname'] == 'Dec'][0]
            candid = data['rowval'][data['rowname'] == 'ID'][0]
            if candid != candid_toupload: continue

            field = url_single.split('/')[-2]
            tname = f"{field.replace('.','_')}_cand{candid}"  #
            print(f'trying to upload data for transient {tname}')
            
            transient_exists = False
            sc = None
            if tname in etdict.keys():
                transient_exists = True
                dict_name = tname[:]
            else:
                sc = SkyCoord([ra],[dec],unit=(u.hour,u.deg))
                sep_arcsec = scexisting.separation(sc).arcsec
                if np.min(sep_arcsec) < 2:
                    transient_exists = True
                    dict_name = dict_names[sep_arcsec == np.min(sep_arcsec)][0]
                    print(f'transient {tname} is called {dict_name} on YSE-PZ!')
            if transient_exists:
                print(f'transient {tname} is already on YSE-PZ!  I will ignore metadata queries')

            lcurlbase = '/'.join(url_single.split('/')[:-1])
            lcurldatebase = '/'.join(url_single.split('/')[:-2])
            rdatetext = requests.get(lcurldatebase).text
            rdate = rdatetext.split('Last updated :')[-1].split('\n')[0]
            date_updated = dateutil.parser.parse(rdate)
            #if (nowdate-date_updated).days > self.options.max_decam_days: continue

            
            # get the lightcurve file
            lcr = requests.get(f"{lcurlbase}/{field}_cand{candid}.difflc.txt")
            if lcr.status_code != 200:
                lcr = requests.get(f"{lcurlbase}/{field}_cand{candid}.forced.difflc.txt")
            lcdata = at.Table.read(lcr.text,format='ascii')

            # is the most recent photometry greater than what exists on YSE-PZ?
            if transient_exists:
                tdate = dateutil.parser.parse(mjd_to_date(np.max(lcdata['MJD'])))
                ysedate = dateutil.parser.parse(etdict[dict_name]['obs_date'])
                if ysedate < tdate + datetime.timedelta(0.1):
                    print(f'the latest data for transient {tname} already exists on YSE-PZ!  skipping...')
                    continue
                
            # some metadata
            if not transient_exists:
                # only do this if YSE-PZ doesn't already have the transient!
                if sc is None:
                    sc = SkyCoord([ra],[dec],unit=(u.hour,u.deg))
                mw_ebv = float('%.3f'%(sfd(sc[0])*0.86))
                try:
                    ps_prob = get_ps_score(sc[0].ra.deg,sc[0].dec.deg)
                except:
                    ps_prob = None

                # run GHOST
                try:
                    ghost_hosts = getTransientHosts(
                        ['tmp'+candid],[SkyCoord(ra,dec,unit=(u.hour,u.deg))], verbose=True, starcut='gentle', ascentMatch=False)
                    ghost_hosts = calc_photoz(ghost_hosts)
                except:
                    ghost_hosts = None

                if ghost_hosts is not None:
                    ghost_host = ghost_hosts[ghost_hosts['TransientName'] == candid]
                    if not len(ghost_host): ghost_host = None
                else:
                    ghost_host = None
            else: ghost_host = None

            # get photometry
            tdict = {'name':tname,
                     'ra':sc[0].ra.deg,
                     'dec':sc[0].dec.deg,
                     'obs_group':'YSE',
                     'status':self.options.status,
                     #'disc_date':None,
                     'mw_ebv':mw_ebv,
                     'tags':['DECAT']}
            if not transient_exists:
                tdict['point_source_probability'] = ps_prob
            
            if ghost_host is not None:
                hostdict,hostcoords = self.getGHOSTData(sc,ghost_host)
                tdict['host'] = hostdict
                tdict['candidate_hosts'] = hostcoords


            PhotUploadAll = {"mjdmatchmin":0.01,
                             "clobber":self.options.clobber}
            photometrydict = {'instrument':'DECam',
                              'obs_group':'YSE',
                              'photdata':{}}

            for j,lc in enumerate(lcdata):

                try:
                    mag = float(lc['m'])
                    mag_err = float(lc['dm'])
                except:
                    mag = None
                    mag_err = None
                
                phot_upload_dict = {'obs_date':mjd_to_date(lc['MJD']),
                                    'band':lc['filt'],
                                    'groups':['YSE'],
                                    'mag':mag,
                                    'mag_err':mag_err,
                                    'flux':lc['flux_c']*10**(0.4*(27.5-lc['ZPTMAG_c'])),
                                    'flux_err':lc['dflux_c']*10**(0.4*(27.5-lc['ZPTMAG_c'])),
                                    'data_quality':0,
                                    'forced':1,
                                    'discovery_point':0,
                                    'flux_zero_point':27.5,
                                    'diffim':1}

                photometrydict['photdata']['%s_%i'%(mjd_to_date(lc['MJD']),j)] = phot_upload_dict

            PhotUploadAll['DECam'] = photometrydict
            transientdict[tname] = tdict
            transientdict[tname]['transientphotometry'] = PhotUploadAll
            count += 1

            if not count % 10:
                # do the uploads
                self.send_data(transientdict)
                transientdict = {}

        self.send_data(transientdict)
                    
    def send_data(self,TransientUploadDict):

        TransientUploadDict['noupdatestatus'] = True
        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self,TransientUploadDict):

        url = '%s'%self.options.dburl.replace('/api','/add_transient')
        try:
            r = requests.post(url = url, data = json.dumps(TransientUploadDict),
                              auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword),
                              timeout=60)
            try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
            except: print(r.text)
            print("Process done.")

        except Exception as e:
            print("Error: %s"%e)
    
