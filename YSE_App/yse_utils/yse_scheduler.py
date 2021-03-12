#!/usr/bin/env python
# D. Jones - 2/1/21
"""Schedule YSE fields"""

import argparse
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import configparser
import datetime
from django.conf import settings as djangoSettings
import dateutil.parser
import os
from bs4 import BeautifulSoup
import pandas as pd
import astropy.table as at
from astropy.table import vstack
import json
from astropy.time import Time
from astropy.coordinates import get_moon, SkyCoord
import astropy.units as u

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_ztf_obs_url = "http://skyvision.caltech.edu/ztf/msip/nightly_summary?obsdate=%04i-%02i-%02i"

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

def date_to_mjd(date):
    time = Time(date,scale='utc')
    return time.mjd

def mjd_to_date(mjd):
    time = Time(mjd,format='mjd',scale='utc')
    return time.isot

def getmoonpos(ra,dec,obstime):
    #obstime = datetime.datetime.now(timezone('US/Hawaii'))+datetime.timedelta(1)
    newtime = obstime.replace(hour=0,minute=0)

    obstime = Time(newtime+datetime.timedelta(hours=7))
    mooncoord = get_moon(obstime)
    mc = SkyCoord(mooncoord.ra.deg,mooncoord.dec.deg,unit=u.deg)
    cs = SkyCoord("%s %s"%(ra,dec),frame="fk5",unit=u.deg) #(u.hourangle,u.deg))
    return(cs.separation(mc).deg)


class HTMLTableParser:
       
    def parse_url(self, url):
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(self.parse_html_table(table)) for table in soup.find_all('table')]  

    def parse_html_table(self, table):
        n_columns = 0
        n_rows=0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):

            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows+=1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

            # Handle column names if we find them
            th_tags = row.find_all('th') 
            if len(th_tags) > 0 and len(column_names) == 0:
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        if len(column_names) > 0 and len(column_names) != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(column_names) > 0 else range(0,n_columns)
        df = pd.DataFrame(columns = columns,
                          index= range(0,n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column in columns:
                df.iat[row_marker,column_marker] = column.get_text()
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        # Convert to float if possible
        for col in df:
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass

        return df


class YSE_Scheduler:
    def __init__(self):
        pass

    def add_arguments(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('-d','--obs_date', default=None, type=str,
                            help='observation date')
        parser.add_argument('--debug', default=False, action="store_true",
                            help='debug mode')

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
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                                help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                                help='SMTP port (default=%default)')
            
        return parser

    def get_field_list(self):
        data = requests.get('https://ziggy.ucolick.org/yse/api/surveyfieldmsbs/?active=1',
                            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        field_list = [data['results'][i]['name'] for i in range(len(data['results']))]

        return field_list

    def get_ps_obs(self,date_to_schedule,field_list=None):

        nowmjd = date_to_mjd(date_to_schedule)

        if self.options.debug:
            dburl = 'http://127.0.0.1:8000/api/'
        else:
            dburl = 'https://ziggy.ucolick.org/yse/api/'
            
        offsetcount = 0
        r = requests.get('%ssurveyobservations/?obs_mjd_gte=%i&obs_mjd_lte=%i&limit=1000&status_in=Successful&obs_group=YSE'%(
            dburl,nowmjd-40,nowmjd),
                         auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

        data = json.loads(r.text)
        data_results = data['results']
        while len(data['results']) == 1000:
            offsetcount += 1000
            r = requests.get('%ssurveyobservations/?obs_mjd_gte=%i&obs_mjd_lte=%i&limit=1000&offset=%i&status_in=Successful&obs_group=YSE'%(
                dburl,nowmjd-40,nowmjd,offsetcount),
                             auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
            data = json.loads(r.text)

            data_results = np.append(data_results,data['results']) #r['results'])
        
        r = requests.get('%ssurveyfields/?limit=1000&obs_group=YSE'%dburl,
                         auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        surveyfielddata = json.loads(r.text)['results']
        while len(data['results']) == 1000:
            offsetcount += 1000
            r = requests.get('%ssurveyfields/?limit=1000&offset=%i&obs_group=YSE'%(
                self.options.dburl,nowmjd-40,nowmjd,offsetcount),
                             auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
            surveyfielddata_single = json.loads(r.text)['results']
            surveyfielddata = np.append(surveyfielddata,surveyfielddata_single)

        fields,obs_mjds,ras,decs,obs_dates = np.array([]),np.array([]),np.array([]),np.array([]),np.array([])
        for d in data_results:
            survey_field_url = d['survey_field']
            obs_mjd = d['obs_mjd']
            #if self.options.debug:
            if d['obs_mjd'] is None: obs_mjd = d['mjd_requested']
            obs_mjds = np.append(obs_mjds,obs_mjd)
            obs_dates = np.append(obs_dates,mjd_to_date(obs_mjd))
            for s in surveyfielddata:
                if s['url'] == survey_field_url:
                    fields = np.append(fields,s['ztf_field_id'])
                    ras = np.append(ras,s['ra_cen'])
                    decs = np.append(decs,s['dec_cen'])
        unqfields,idx = np.unique(fields,return_index=True)
        ras = ras[idx]; decs = decs[idx]

        last_obs_dates = np.array([])
        for uf in unqfields:
            most_recent_mjd = np.sort(obs_mjds[fields == uf])[-1]
            last_obs_dates = np.append(last_obs_dates,mjd_to_date(most_recent_mjd))

        if field_list is not None:
            for f in field_list:
                if f not in unqfields:
                    for s in surveyfielddata:
                        if s['ztf_field_id'] == f:
                            unqfields = np.append(unqfields,f)
                            ras = np.append(ras,s['ra_cen'])
                            decs = np.append(decs,s['dec_cen'])
                            last_obs_dates = np.append(last_obs_dates,['2018-01-01T00:00:00'])
                            break

        count = 0
        iGood = np.array([],dtype=int)
        for i,u in enumerate(unqfields):
            if u in field_list:
                iGood = np.append(iGood,i)
        unqfields,ras,decs,last_obs_dates = \
            unqfields[iGood],ras[iGood],decs[iGood],last_obs_dates[iGood]
                
        obsmjds = np.array([date_to_mjd(t) for t in last_obs_dates])
        timedeltas = nowmjd-obsmjds

        return unqfields,ras,decs,last_obs_dates,timedeltas

    def get_ztf_schedule(self,date_to_schedule,field_list=[],clear=True,ndays=21):

        # HACK
        #rootdir = '%s/ztf_obs_record'%djangoSettings.STATIC_ROOT
        #print('hack!!!')
        rootdir = '/data/yse_pz/YSE_PZ/YSE_PZ/static/ztf_obs_record'
        #rootdir = '/Users/David/Dropbox/research/YSE_PZ/YSE_PZ/static/ztf_obs_record'
        
        
        # make sure we have the last two weeks
        nowdate = date_to_schedule-datetime.timedelta(ndays)
        date_list = [nowdate + datetime.timedelta(days=x) for x in range(ndays)]

        count = 0
        obstimes = []
        for i,d in enumerate(date_list):
            if not os.path.exists('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day)):
                hp = HTMLTableParser()
                print(d)
                tables = hp.parse_url(_ztf_obs_url%(d.year,d.month,d.day))
                if len(tables) > 1:
                    table = tables[1]
                    table.to_csv('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day))
                    if count == 0:
                        atable = at.Table.read('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day),format='ascii.csv')

                        count += 1
                    else:
                        tmptable = at.Table.read('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day),format='ascii.csv')
                        atable = vstack([atable, tmptable])
                    obstimes += [d]
                else:
                    fout = open('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day),'w')
                    print('No Obs',file=fout)
                    fout.close()

            else:
                if count == 0:
                    atable = at.Table.read('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day),format='ascii.csv')
                    count += 1
                    obstimes += [d]
                else:
                    has_data = True
                    with open('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day)) as fin:
                        for line in fin:
                            if line.startswith('No'): has_data = False
                            break

                    if has_data:
                        tmptable = at.Table.read('%s/ztf_obs_%04i-%02i-%02i.csv'%(rootdir,d.year,d.month,d.day),format='ascii.csv')
                            
                        atable = vstack([atable, tmptable])
                        obstimes += [d]
                        
        n_bad_nights = 0
        nights_count = 0
        for i,d in enumerate(date_list[::-1]):
            if d not in obstimes:
                n_bad_nights += 1
            else:
                nights_count += 1
            if nights_count > 3: break

        # now get the scheduled observations for tonight
        # if the weather looks to be bad, these are tomorrow's fields!
        last_date = date_to_schedule - datetime.timedelta(1)
        data = requests.get('http://schedule.ztf.uw.edu/ZTF_ObsLoc_%04i-%02i-%02i.json'%(
            last_date.year,last_date.month,last_date.day)).json()

        tonights_fields = []
        for d in data:
            target = d['target_name'].replace('ZTF_field_','')
            if target in field_list:
                tonights_fields += [target]

        prev_fields = []
        for a in atable:
            if str(int(a['field'])) in field_list and \
               (date_to_schedule-dateutil.parser.parse(a['obsdatetime'])).days < 5 and \
               str(int(a['field'])) not in tonights_fields:
                prev_fields += [str(int(a['field']))]

        if not clear:
            return np.unique(tonights_fields)
        else:
            # otherwise, anything observed in the last 4 days and *not* scheduled for tonight is the way to go
            return np.unique(prev_fields)

    def get_palomar_weather(self):

        noaa_url = 'https://api.weather.gov/points/33.357030000000066,-116.86538999999999'
        noaa_forecast_url = 'https://api.weather.gov/gridpoints/SGX/71,39/forecast'
        r = requests.get(url=noaa_forecast_url)
        data = json.loads(r.text)

        if data['properties']['periods'][0]['name'] == 'Tonight':
            if 'clear' in data['properties']['periods'][0]['shortForecast'].lower():
                clear = True
            else: clear = False
        elif data['properties']['periods'][1]['name'] == 'Tonight':
            if 'clear' in data['properties']['periods'][1]['shortForecast'].lower():
                clear = True
            else: clear = False
        else:
            raise RuntimeError('ummmm this code doesn\'t work unless you run it in daytime US/Pacific....')

        return clear

    def moon_cut(self,fields,ras,decs,obstime,timedeltas=None):

        data = requests.get('https://ziggy.ucolick.org/yse/api/surveyfieldmsbs/?active=1',
                            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        results = {}
        for d in data['results']:
            results[d['name']] = d
        
        iGood = []
        for i,f in enumerate(fields):
            if f not in results.keys():
                sep = getmoonpos(ras[i],decs[i],obstime)
                if sep > 40:
                    iGood += [i]
            else:
                sep = 999
                for d in results[f]['survey_fields']:
                    sep_ind = getmoonpos(d['ra_cen'],d['dec_cen'],obstime)
                    if sep_ind < sep: sep = sep_ind
                if sep > 40:
                    iGood += [i]
                    
        if timedeltas is None:
            return np.array(fields)[np.array(iGood)],np.array(ras)[np.array(iGood)],np.array(decs)[np.array(iGood)]
        else:
            if not len(iGood):
                return np.array([]),np.array([]),np.array([]),np.array([])
            else:
                return np.array(fields)[np.array(iGood)],np.array(ras)[np.array(iGood)],\
                    np.array(decs)[np.array(iGood)],np.array(timedeltas)[np.array(iGood)]
    
    def get_decam_obs(self):
        # grab the file somehow

        # read in the coordinates
        fid,ra,dec = np.loadtxt('/Users/David/Downloads/20201122.inv',unpack=True,usecols=[0,1,2],dtype=str)
        scdecam = SkyCoord(ra,dec,unit=(u.hour,u.deg))
        
        # get the coords for active YSE fields(ok this is redundant but whatever)
        data = requests.get('https://ziggy.ucolick.org/yse/api/surveyfieldmsbs/?active=1',
                            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        name_list,ra_list,dec_list = [],[],[],[]
        for i in range(len(data['results'])):
            if data['results'][i]['active']:
                for s in data['results'][i]['survey_fields']:
                    name_list += [data['results'][i]['name']]
                    ra_list += [s['ra_cen']]
                    dec_list += [s['dec_cen']]

        # match up the coords to active YSE fields
        # and get the list of YSE fields to observe
        decam_list_to_schedule = []
        for n,r,d in zip(name_list,ra_list,dec_list):
            sc = SkyCoord(r,d,unit=(u.hour,u.deg))
            sep = sc.separation(scdecam).deg
            if np.min(sep) < 1.55 and n not in decam_list_to_schedule:
                decam_list_to_schedule += [n]
        
        # return the fields
        return decam_list_to_schedule


    def add_obs_requests(self,date_requested,field_id):
        
        survey_obs_dict = {'survey_obs_date':date_requested.strftime('%m/%d/%y'),
                           'ztf_field_id':'%s'%field_id}
        r = requests.post(url = '%sadd_survey_obs/'%(self.options.dburl.replace('api/','')),
                          data = survey_obs_dict,
                          auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

    def choose_fields(self,ps_fields,ztf_fields,decam_fields,ps_timedeltas):
        daily_set_1 = ['523','525','577']
        daily_set_2 = ['575','577','674']
        do_set_1,do_set_2 = True,True

        # Virgo
        if 'Virgo' in ps_fields: fields_to_observe = ['Virgo']; timegaps = [ps_timedeltas[ps_fields == 'Virgo'][0]]
        else: fields_to_observe = []; timegaps = []

        add_fields = True
        for cadence in ['daily','normal']:
            if not add_fields: break
            for fieldset in [decam_fields,ztf_fields,ps_fields]:
                if not add_fields: break
                for timegap in [5,4,3,2,1,0]:
                    if not add_fields: break
                    
                    iNotRecent = np.where(ps_timedeltas > timegap)[0]
                    for i,field in enumerate(ps_fields[iNotRecent]):
                        if field in fieldset and field not in fields_to_observe:
                            if cadence == 'normal':
                                # max 1 field from each of daily set 1 and daily set 2
                                if field in daily_set_1: continue
                                if field in daily_set_2: continue
                                fields_to_observe += [field]
                                timegaps += [ps_timedeltas[iNotRecent[i]]]
                            elif field in daily_set_1 and do_set_1:
                                fields_to_observe += [field]
                                timegaps += [ps_timedeltas[iNotRecent[i]]]
                                do_set_1 = False
                            elif field in daily_set_2 and do_set_2:
                                fields_to_observe += [field]
                                timegaps += [ps_timedeltas[iNotRecent[i]]]
                                do_set_2 = False
                            #if cadence == 'normal':
                            #    fields_to_observe += [field]
                            #    timegaps += [ps_timedeltas[iNotRecent[i]]]
                            #elif field in daily_set_1 and do_set_1:
                            #    fields_to_observe += [field]
                            #    timegaps += [ps_timedeltas[iNotRecent[i]]]
                            #    do_set_1 = False
                            #elif field in daily_set_2 and do_set_2:
                            #    fields_to_observe += [field]
                            #    timegaps += [ps_timedeltas[iNotRecent[i]]]
                            #    do_set_2 = False

                            # failsafe
                            if (len(fields_to_observe) == 7 and 'Virgo' in fields_to_observe) or \
                               (len(fields_to_observe) == 6 and 'Virgo' not in fields_to_observe):
                                add_fields = False
                                break
                            if (len(fields_to_observe) > 7 and 'Virgo' in fields_to_observe) or \
                               (len(fields_to_observe) > 6 and 'Virgo' not in fields_to_observe):
                                print('trying to schedule the following fields:')
                                print(','.join(fields_to_observe))
                                raise RuntimeError('Error : scheduled too many fields!')

        print('scheduling fields %s'%(','.join(fields_to_observe)))
        print('fields were last observed %s days ago'%(','.join(np.array(timegaps).astype(int).astype(str))))
        
        return fields_to_observe
        
    def main(self,date_to_schedule):

        # guess the probability that ZTF will observe tonight (get weather forecast)
        clear = None
        try:
            if clear is None: clear = self.get_palomar_weather()
            if clear:
                print('forecast tonight is CLEAR')
            else:
                print('forecast tonight is NOT CLEAR')
        except:
            print('weather fail!  Assuming clear')
            clear = True
        
        # field list from the YSE-PZ API
        # to edit go to ziggy.ucolick.org/yse/select_yse_fields
        print('getting PS field list')
        field_list = self.get_field_list()

        print('finding recent PS1 observations')
        # get the YSE observing history, important to avoid long gaps
        ps_fields,ps_ras,ps_decs,ps_dates,ps_timedeltas = self.get_ps_obs(
            date_to_schedule,field_list=field_list)

        print('cutting out fields near the moon')
        # remove fields too close to the moon
        
        print('all YSE fields: %s'%(','.join(ps_fields)))
        ps_fields,ps_ras,ps_decs,ps_timedeltas = self.moon_cut(ps_fields,ps_ras,ps_decs,date_to_schedule,timedeltas=ps_timedeltas)
        print('YSE fields out of the moon: %s'%(','.join(ps_fields)))
        
        # get the DECam observing history
        #print('getting DECam fields')
        #self.get_decam_obs()
        decam_fields = []

        print('looking for the ZTF schedule')
        # get the ZTF observing history and plans
        # https://zwickytransientfacility.github.io/schedule_reporting_service/
        # http://schedule.ztf.uw.edu/ZTF_ObsLoc_YYYY-MM-DD.json
        likely_ztf_fields = self.get_ztf_schedule(date_to_schedule,clear=clear,field_list=field_list)

        print('choosing fields')
        # then weight the ZTF constraints against YSE fields w/o recent data
        # and availability of DECam
        fields_to_observe = self.choose_fields(ps_fields,likely_ztf_fields,decam_fields,ps_timedeltas)

        for f in fields_to_observe:
            self.add_obs_requests(date_to_schedule-datetime.timedelta(hours=9),f)
        print('success!')
            
if __name__ == "__main__":

    ys = YSE_Scheduler()

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

    try:
        
        obs_date = datetime.datetime.utcnow()+datetime.timedelta(hours=9) #datetime.timedelta(1)
        ys.main(dateutil.parser.parse(obs_date.isoformat().split()[0]))
        
    except Exception as e:
        print(e)
        nsn = 0
        smtpserver = "%s:%s" % (ys.options.SMTP_HOST, ys.options.SMTP_PORT)
        from_addr = "%s@gmail.com" % ys.options.SMTP_LOGIN
        subject = "YSE Field Scheduling Failure"
        print("Sending error email")
        html_msg = "Alert : failed to schedule YSE fields in /home/djones/ysefields/predict_ztf.py\n"
        html_msg += "Error : %s"
        sendemail(from_addr, ys.options.dbemail, subject,
                  html_msg%(e),
                  ys.options.SMTP_LOGIN, ys.options.dbpassword, smtpserver)
