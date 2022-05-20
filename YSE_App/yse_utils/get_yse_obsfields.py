#!/usr/bin/env python
# D. Jones - 5/18/22
# try and figure out when fields are settings, and which fields can replace them

import requests
from astropy.time import Time
from astroplan import Observer
from astropy.coordinates import SkyCoord
import astropy.units as u
import datetime
from requests.auth import HTTPBasicAuth
import astropy.table as at
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import argparse
import configparser

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


def GetSexigesimalString(ra_decimal, dec_decimal):
    c = SkyCoord(ra_decimal,dec_decimal,unit=(u.deg, u.deg))
    ra = c.ra.hms
    #dec = c.dec.dms
    dec = np.array(c.dec.to_string(precision=2).replace('d',':').replace('m',':').replace('s','').split(':')).astype(float)
    ra_string = "%02d:%02d:%05.2f" % (ra[0],ra[1],ra[2])
    if dec[0] >= 0:
        dec_string = "+%02d:%02d:%05.2f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))
    else:
        dec_string = "%03d:%02d:%05.2f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))

    # Python has a -0.0 object. If the deg is this (because object
    # lies < 60 min south), the string formatter will drop the negative sign
    if c.dec < 0.0 and dec[0] == 0.0:
        dec_string = "-00:%02d:%05.2f" % (np.abs(dec[1]),np.abs(dec[2]))
    return (ra_string, dec_string)

class yse_obsfields:
    def __init__(self):
        pass

    def add_arguments(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        parser.add_argument('settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('--debug', default=False, action="store_true",
                            help='debug mode')
        parser.add_argument('--email_recipients', default='david.jones@ucsc.edu,sd919@cam.ac.uk', type=str,
                            help='email recipients')

        if config:
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                                help='gmail login (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                                help='gmail password (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                                help='base URL to POST/GET,PUT to/from a database (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                                help='database login, if post=True (default=%default)')
            
            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                                help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_PASSWORD', default=config.get('SMTP_provider','SMTP_PASSWORD'), type=str,
                                help='SMTP password (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                                help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                                help='SMTP port (default=%default)')
            
        return parser
    
    def main(self,maxairmass=1.5,max_days=150):
        # get the YSE active and inactive MSBs
        data = requests.get('https://ziggy.ucolick.org/yse/api/surveyfieldmsbs',
                            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()

        name_list,ra_list,dec_list,active_list = [],[],[],[]
        for i in range(len(data['results'])):
            for s in data['results'][i]['survey_fields'][0:1]:
                name_list += [data['results'][i]['name']] #s['field_id']]
                ra_list += [s['ra_cen']]
                dec_list += [s['dec_cen']]
                active_list += [data['results'][i]['active']]
        yse_pos = SkyCoord(ra=ra_list, dec=dec_list, unit=u.deg, frame='fk5')
        yse = at.Table(names=('ID','RA','Dec','active'),data=(name_list,ra_list,dec_list,active_list))
        
        # use astroplan to figure out when they're no longer observable
        print('active fields')
        drop_list,drop_date,drop_days_until_set = [],[],[]
        for target,name in zip(yse_pos[yse['active'] == 1],yse['ID'][yse['active'] == 1]):
            site='keck'; timezone='US/Hawaii'
            time_start='05:00:00'; time_end='15:00:00'
            nowmjd = Time.now().mjd
            start_date,end_date = None,None
            for i in range(0,max_days,4):
                t = Time(nowmjd+i,format='mjd')
                tel = Observer.at_site(site, timezone=timezone)
                night_start = tel.twilight_evening_astronomical(t,which="previous")
                night_end = tel.twilight_morning_astronomical(t,which="previous")
                hourmin,hourmax = int(night_start.iso.split()[-1].split(':')[0]),int(night_end.iso.split()[-1].split(':')[0])
                canObs = False; field_up = True
                for hour in range(hourmin,hourmax+1):
                    time = night_start.datetime.replace(hour=hour)
                    altaz = tel.altaz(time,target)
                    if altaz.alt.value < 0: continue
                    airmass = altaz.secz
                    if airmass < maxairmass: canObs = True
                if canObs and start_date is None:
                    start_date = t.iso
                    start_ap = t.copy()
                if canObs == False and i == 0:
                    # target is currently not up!
                    print(f'field {name} is currently not up!')
                    #drop_list += [name]
                    field_up = False
                    break
                if not canObs and start_date is not None:
                    end_date = t.iso
                    end_mjd = t.mjd
                    break
                
            if end_date is None:
                end_date = t.iso
                end_mjd = nowmjd
            print(name,end_date,end_mjd-nowmjd)
            if end_mjd-nowmjd < 14 and (end_mjd-nowmjd != 0 or field_up == False):
                drop_list += [name]
                drop_date += [end_date]
                drop_days_until_set += [end_mjd-nowmjd]
                
        # grab the inactive fields, figure out if
        # they're observable and for how long
        print('inactive fields')
        fields_to_add = []; fields_not_to_add = []
        days_until_set = []; ra_add = []; dec_add = []
        for target,name in zip(yse_pos[yse['active'] == 0],yse['ID'][yse['active'] == 0]):
            site='keck'; timezone='US/Hawaii'
            time_start='05:00:00'; time_end='15:00:00'
            nowmjd = Time.now().mjd
            start_date,end_date = None,None
            for i in range(0,max_days,4):
                t = Time(nowmjd+i,format='mjd')
                tel = Observer.at_site(site, timezone=timezone)
                night_start = tel.twilight_evening_astronomical(t,which="previous")
                night_end = tel.twilight_morning_astronomical(t,which="previous")
                hourmin,hourmax = int(night_start.iso.split()[-1].split(':')[0]),int(night_end.iso.split()[-1].split(':')[0])
                canObs = False
                for hour in range(hourmin,hourmax+1):
                    time = night_start.datetime.replace(hour=hour)
                    altaz = tel.altaz(time,target)
                    if altaz.alt.value < 0: continue
                    airmass = altaz.secz
                    if airmass < maxairmass: canObs = True
                if canObs and start_date is None:
                    start_date = t.iso
                    start_ap = t.copy()
                if canObs == False and i == 0:
                    # target is currently not up!
                    print(f'field {name} is currently not up!')
                    fields_not_to_add += [name]
                    break
                if not canObs and start_date is not None:
                    end_date = t.iso
                    end_mjd = t.mjd
                    break
                
            if end_date is None:
                end_date = t.iso
                end_mjd = nowmjd
            print(name,end_date,end_mjd-nowmjd)
            if (end_mjd-nowmjd > 60 or end_mjd-nowmjd == 0) and name not in fields_not_to_add:
                fields_to_add += [name]
                days_until_set += [end_mjd-nowmjd]
                ra_add += [GetSexigesimalString(yse['RA'][yse['ID'] == name][0],yse['Dec'][yse['ID'] == name][0])[0]]
                dec_add += [GetSexigesimalString(yse['RA'][yse['ID'] == name][0],yse['Dec'][yse['ID'] == name][0])[1]]
        print('fields to drop:')
        print(f"{','.join(drop_list)}")
        print('fields to add:')
        print(f"{','.join(fields_to_add)}")
        
        # now we need to email everything within ~2 weeks of setting
        if len(drop_list):
            email_text = """<p>The following fields are within two weeks of being unobservable at airmass < 1.5:</p>
<p>name last_obs_date days_until_set</p>"""
            
            for dl,dd,ds in zip(drop_list,drop_date,drop_days_until_set):
                email_text += f"<p>{dl} {dd.split()[0]} {ds:.0f}</p>"

            email_text += """<p>The following fields are observable and are not currently being observed:</p>
<p>name ra dec days_until_set</p>"""
            for fl,r,d,ds in zip(fields_to_add,ra_add,dec_add,days_until_set):
                if ds == 0:
                    ds = f'>{max_days}'
                email_text += f"<p>{fl} {r} {d} {ds}</p>"

            subject = 'setting YSE fields'

            smtpserver = "%s:%s" % (self.options.SMTP_HOST, self.options.SMTP_PORT)
            from_addr = "%s@gmail.com" % self.options.SMTP_LOGIN
            for to_addr in self.options.email_recipients.split(','):
                sendemail(from_addr, to_addr, subject, email_text,
                          self.options.SMTP_LOGIN, self.options.SMTP_PASSWORD, smtpserver)
            
if __name__ == "__main__":
    ys = yse_obsfields()

    # read args
    parser = ys.add_arguments(usage='')
    args = parser.parse_args()
    if args.settingsfile:
        config = configparser.ConfigParser()
        config.read(args.settingsfile)
    else: config=None
    parser = ys.add_arguments(usage='',config=config)
    args = parser.parse_args()
    ys.options = args

    if 'hi': #try:

        ys.main()
        
    else: #except Exception as e:
        print(e)
        nsn = 0
        smtpserver = "%s:%s" % (ys.options.SMTP_HOST, ys.options.SMTP_PORT)
        from_addr = "%s@gmail.com" % ys.options.SMTP_LOGIN
        subject = "YSE Setting Field Failure"
        print("Sending error email")
        html_msg = "Alert : failed to figure out setting YSE fields in get_yse_obsfields.py\n"
        html_msg += "Error : %s"
        sendemail(from_addr, ys.options.dbemail, subject,
                  html_msg%(e),
                  ys.options.SMTP_LOGIN, ys.options.dbpassword, smtpserver)
    
