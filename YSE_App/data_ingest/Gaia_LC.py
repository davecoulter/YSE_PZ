import pandas as pd
import datetime
import numpy as np
import time
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
import json
import requests
import sys
from requests.auth import HTTPBasicAuth
import configparser
from YSE_App.models import Transient, TransientTag, AlternateTransientNames

def date_to_mjd(obs_date):
	time = Time(obs_date,scale='utc')
	return time.mjd

def mjd_to_date(obs_mjd):
	time = Time(obs_mjd,scale='utc',format='mjd')
	return time.isot

def get_gaia_list(look_back_days):
    gaia_list = pd.read_csv('http://gsaweb.ast.cam.ac.uk/alerts/alerts.csv')
    datelist = np.array([(datetime.datetime.now()-datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')).\
                         total_seconds()/86400 for date in gaia_list[' Date'].values])
    index = datelist<look_back_days
    targets = gaia_list[index]
    return targets

def get_gaia_phot(name, targets):
    #index = (targets[' TNSid']=='AT'+name) | (targets[' TNSid']=='SN'+name)
    index = targets['#Name'] == name
    if sum(index) >0:
        gaia_name = targets[index]['#Name'].values[0]
        data = pd.read_csv('http://gsaweb.ast.cam.ac.uk/alerts/alert/'+gaia_name+'/lightcurve.csv/')
        return data
    else:
        return

class GaiaLC(CronJobBase):

    RUN_AT_TIMES = ['00:00','08:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'YSE_App.data_ingest.Gaia_LC.GaiaLC'

    def do(self):

        try:
            print("uploading Gaia LCs at {}".format(datetime.datetime.now().isoformat()))

            tstart = time.time()
            
            parser = self.add_options()
            options,  args = parser.parse_known_args()

            config = configparser.ConfigParser()
            config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
            parser = self.add_options(config=config)
            options,  args = parser.parse_known_args()
            self.options = options
            
            self.main()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(e)
            import pdb; pdb.set_trace()
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "Gaia Upload Failure in Gaia_LC.py"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload Gaia LCs in Gaia_LC.py\n"
            html_msg += "Error : %s at line number %s"
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e,exc_tb.tb_lineno),
                      options.SMTP_LOGIN, options.dbpassword, smtpserver)

        print('Gaia -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

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

        if config:
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                              help='database password, if post=True (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                              help='URL to POST transients to a database (default=%default)')

            
            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                              help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                              help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                              help='SMTP port (default=%default)')
        else:
            pass


        return(parser)
        
    def main(self):

        # initialize the dictionary
        transientdict = {}
        
        # not sure how many this will be, but 90 days seems safe-ish
        transients = AlternateTransientNames.objects.\
                     filter(name__startswith='Gaia').\
                     filter(transient__disc_date__gt=datetime.datetime.now()-datetime.timedelta(days=90))
        targets = get_gaia_list(90)

        for t in transients:
            tdict = {'name':t.transient.name}            
            data = get_gaia_phot(t.name,targets)[t.name]

            PhotUploadAll = {"mjdmatchmin":0.01,
                             "clobber":True}
            photometrydict = {'instrument':'Gaia-Photometric',
                              'obs_group':'GaiaAlerts',
                              'photdata':{}}
            for i,d in enumerate(data):
                if not isinstance(data[i],float):
                    if data[i] == 'untrusted' or data[i].startswith('average') or \
                       data[i] == 'nan': continue
                if float(data[i]) != float(data[i]): continue

                flux = 10**(-0.4*(float(data[i])-27.5))
                flux_err = 1.086*0.01*flux
                phot_upload_dict = {'obs_date':data.index[i][0].replace(' ','T'),
                                    'band':'G',
                                    'groups':['Public'],
                                    'mag':float(data[i]),
                                    'mag_err':0.01,
                                    'flux':flux,
                                    'flux_err':flux_err,
                                    'flux_zero_point':27.5,
                                    'data_quality':0,
                                    'discovery_point':0,
                                    'forced':0,
                                    'diffim':1}
                photometrydict['photdata'][i] = phot_upload_dict
                
            PhotUploadAll['Gaia-Photometric'] = photometrydict
            transientdict[t.transient.name] = tdict
            transientdict[t.transient.name]['transientphotometry'] = PhotUploadAll

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
