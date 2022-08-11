#!/usr/bin/env python
# D. Jones - 3/1/22
# grab the list of active fields
# see which ones haven't been observed in >5 days
# send an email

import requests
from requests.auth import HTTPBasicAuth
import configparser
import argparse
from astropy.time import Time
import datetime
import numpy as np

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

class check_obs:
    def __init__(self):
        pass

    def add_arguments(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('-d','--obs_date', default=None, type=str,
                            help='observation date')
        parser.add_argument('--ndays', default=6, type=int,
                            help='observation date')
        parser.add_argument('--debug', default=False, action="store_true",
                        help='debug mode')
        parser.add_argument('--dburl', default='https://ziggy.ucolick.org/yse/api/', type=str,
                            help='base URL to POST/GET,PUT to/from a database (default=%default)')

        if config:
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                        help='gmail login (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                            help='gmail password (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                            help='gmail password (default=%default)')
            #parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
            #    help='base URL to POST/GET,PUT to/from a database (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                                help='database login, if post=True (default=%default)')

            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                                help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                                help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                                help='SMTP port (default=%default)')

        return parser
        
    def main(self):

        nowmjd = Time(datetime.datetime.now()).mjd
        
        # get all the active fields
        data = requests.get(f'{self.options.dburl}/surveyfieldmsbs/?active=1',
                            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        results = {}
        n_active = 0
        active_fields = []
        for d in data['results']:
            active_fields += [d['name']]
            n_active += 1

        # see which ones have been observed in n days
        offsetcount = 0
        r = requests.get(f'{self.options.dburl}surveyobservations/?obs_mjd_gte={nowmjd-self.options.ndays}&obs_mjd_lte={nowmjd}&limit=1000&status_in=Successful&obs_group=YSE',
                         auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        data = r.json()
        msbs_observed = []
        for d in data['results']:
            msbs_observed += [d['msb']['name']]
        msbs_observed = np.unique(msbs_observed)

        active_fields_missing = [a for a in active_fields if a not in msbs_observed]
        if len(active_fields_missing):
            print(f"fields {','.join(active_fields_missing)} have not been observed in {self.options.ndays} days")
            self.send_email(active_fields_missing,n_active)
        else:
            print(f"all {n_active} fields have been observed in the last {self.options.ndays} days!")
            
    def send_email(self,field_list,n_active):

        smtpserver = "%s:%s" % (self.options.SMTP_HOST, self.options.SMTP_PORT)
        from_addr = "%s@gmail.com" % self.options.SMTP_LOGIN
        subject = f"YSE Fields {','.join(field_list)} not observed in 6 days"
        html_msg = f"Out of {n_active} fields, {','.join(field_list)} have not been observed in 6 days"
        sendemail(from_addr, self.options.dbemail, subject,
                  html_msg,
                  self.options.SMTP_LOGIN,
                  self.options.dbemailpassword, smtpserver)
    
if __name__ == "__main__":
    co = check_obs()

    # read args
    parser = co.add_arguments(usage='')
    args = parser.parse_args()
    if args.settingsfile:
        config = configparser.ConfigParser()
        config.read(args.settingsfile)
    else: config=None
    parser = co.add_arguments(usage='',config=config)
    args = parser.parse_args()
    co.options = args
    
    co.main()
