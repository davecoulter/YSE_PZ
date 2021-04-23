# check for ZTF forced photometry
from YSE_App.models import *
import datetime
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
from YSE_App.data_ingest import ZTF_Forced_Phot
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import astropy.table as at
import argparse
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def jd_to_date(jd):
    time = Time(jd,scale='utc',format='jd')
    return time.isot

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

class ForcedPhot(CronJobBase):

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhot'

    def __init__(self): 
        pass
    
    def do(self):

        tstart = time.time()
        parser = self.add_options()
        options,  args = parser.parse_known_args()
        options.settingsfile = "%s/settings.ini"%djangoSettings.PROJECT_DIR
        config = configparser.ConfigParser()
        config.read(options.settingsfile)

        parser = self.add_options(config=config)
        options,  args = parser.parse_known_args()
        self.options = options

        try:
            self.main()
        except Exception as e:
            print(e)
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "ZTF Forced Photometry Failure"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to get forced photometry from ZTF\n"
            html_msg += "Error : %s"
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            
    def add_options(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')

        if config:
            parser.add_argument('--ztfforcedphotpass', default=config.get('yse_forcedphot','ztfforcedphotpass'), type=str,
                                help='ZTF password (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                                help='YSE-PZ API URL (default=%default)')
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                                help='YSE-PZ login (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                                help='YSE-PZ password (default=%default)')

            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                                help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                                help='email password, if post=True (default=%default)')
            
            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                              help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                              help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                              help='SMTP port (default=%default)')

        return parser
        
    def main(self):

        # check for logs starting with "ZTF Forced Phot" and
        # created_by date is in the last day or so
        
        nowdate = datetime.datetime.utcnow()
        logs = Log.objects.filter(created_date__gt=nowdate-datetime.timedelta(1))

        # now see which ones already have ZTF forced phot uploaded, so
        # we don't do extra work
        list_already_done = []
        for l in logs:
            if l.transient is None: continue
            t = l.transient
            # these ones already have had photometry uploaded in the last 12 hours
            # assume it doesn't need to happen again
            existing_phot = TransientPhotData.objects.filter(photometry__transient=t).\
                filter(photometry__instrument__name="ZTF-Cam").\
                filter(forced=True).filter(obs_date__gt=nowdate-datetime.timedelta(60)).\
                filter(modified_date__gt=nowdate-datetime.timedelta(0.5))
            if len(existing_phot):
                list_already_done += [t.name]

        # run ZTF forced phot script
        ztf = ZTF_Forced_Phot.ZTF_Forced_Phot(
            ztf_email_address='%s@gmail.com'%djangoSettings.SMTP_LOGIN,ztf_email_password=djangoSettings.SMTP_PASSWORD,
            ztf_email_imapserver='imap.gmail.com',ztf_user_address='%s@gmail.com'%djangoSettings.SMTP_LOGIN,
            ztf_user_password=self.options.ztfforcedphotpass)

                
        # now recover the data
        DataForYSEPZ = {'noupdatestatus':True}
        for l in logs:
            if l.transient is None: continue
            if l.transient.name in list_already_done: continue
            print(l.transient.name)
            log_file_name = l.comment.split('=')[-2].split('\n')[0]

            try:
                output_files = ztf.get_ztf_fp(
                    log_file_name, directory_path='/tmp/forced_phot_out',
                    source_name=l.transient.name,verbose=True)
            except Exception as e:
                print(e)
                print('No data yet for %s'%l.transient.name)
                continue

            if output_files is None:
                print('No data yet for %s'%l.transient.name)
                continue
            
            # first we have to figure out how to parse these output files
            try:
                data = at.Table.read('/tmp/forced_phot_out/%s/%s_lc.txt'%(l.transient.name,l.transient.name),format='ascii',header_start=0)
            except:
                print('No LC data for %s'%l.transient.name)
                continue

            # then dump everything in a dictionary
            DataForYSEPZ[l.transient.name] = {'name':l.transient.name,
                                              'ra':l.transient.ra,
                                              'dec':l.transient.dec,
                                              'obs_group':'Unknown',
                                              'status':'Ignore'}
            PhotUploadAll = {"mjdmatchmin":0.01,
                             "clobber":True}
            PhotUploadAll["ZTF"] = {'instrument':'ZTF-Cam',
                                    'obs_group':'ZTF'}
            PhotUploadAll["ZTF"]["photdata"] = {}
            
            # loop over the photometry
            for i,d in enumerate(data):
                if d['forcediffimfluxap,'] == 'null': continue
                
                mag = -2.5*np.log10(float(d['forcediffimfluxap,']))+float(d['zpdiff,'])
                mag_err = 1.086*float(d['forcediffimfluxuncap,'])/float(d['forcediffimfluxap,'])
                if mag != mag: mag = None; mag_err = None

                PhotDataDict = {'obs_date':jd_to_date(float(d['jd,'])),
                                'mag':mag,
                                'mag_err':mag_err,
                                'band':'%s-ZTF'%d['filter,'][-1],
                                'data_quality':0,
                                'diffim':1,
                                'flux':float(d['forcediffimfluxap,'])*10**(-0.4*(float(d['zpdiff,'])-27.5)),
                                'flux_err':float(d['forcediffimfluxuncap,'])*10**(-0.4*(float(d['zpdiff,'])-27.5)),
                                'flux_zero_point':27.5,
                                'forced':1,
                                'discovery_point':0}
                PhotUploadAll["ZTF"]["photdata"][i] = PhotDataDict

            DataForYSEPZ[l.transient.name]['transientphotometry'] = PhotUploadAll

            # don't upload the same LC 50 times
            list_already_done += [l.transient.name]

        # send the data to YSE-PZ
        self.UploadTransients(DataForYSEPZ)
        print('success!')
        
    def UploadTransients(self,TransientUploadDict):

        url = '%s'%self.options.dburl.replace('/api','/add_transient')
        try:
            r = requests.post(
              url = url, data = json.dumps(TransientUploadDict),
              auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword),
              timeout=60)
            try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
            except: print(r.text)
            print("Process done.")

        except Exception as e:
            print("Error: %s"%e)
