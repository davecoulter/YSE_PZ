#!/home/lowe/anaconda3/bin/python3

###############
#### This version has username/password baked in
#### For testing purpose
#### Descendant of get_YSE_PAs.py

# Version 2.0    --- prints out filters as well as PAs
###############

import astropy.coordinates as cd
import astropy.units as u
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
import subprocess
from random import sample
import argparse
import datetime
import requests
from requests.auth import HTTPBasicAuth
import json
from astropy.coordinates import SkyCoord

from astropy.time import Time
from astroplan import Observer
tel = Observer.at_site('keck', timezone='US/Hawaii')

# For local stuff
import sys
import os.path
import getpass
# sys.path.append("/otis/ops/src/python")
# import ps1util
import socket
import pprint

def date_to_mjd(date):
    time = Time(date,scale='utc')
    return time.mjd

def mjd_to_date(mjd):
    time = Time(mjd,format='mjd',scale='utc')
    return time.isot

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

    # Python has a -0.0 object. If the deg is this (because object lies < 60 min south), the string formatter will drop the negative sign
    if c.dec < 0.0 and dec[0] == 0.0:
        dec_string = "-00:%02d:%05.2f" % (np.abs(dec[1]),np.abs(dec[2]))
    return (ra_string, dec_string)

class YSE_PA:

    def __init__(self):
        pass

    def add_options(self, parser=None, usage=None, config=None):
        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument('-v', '--verbose', action="count", dest="verbose",
                            default=0,help='verbosity level')
        parser.add_argument('--yseurl', type=str, default='https://ziggy.ucolick.org/yse',
                            help='YSE URL')
        parser.add_argument('-u','--yseuser', type=str, default='psobs',
                            help='YSE user name')
        parser.add_argument('-p','--ysepass', type=str, default='!ps-yse!',
                            help='YSE password')
        parser.add_argument('-c', '--cron', action="store_true", help="use if calling from cron (e.g.)")
        parser.add_argument('--goodcellsfile', type=str, default="/home/schultz/YSE/getPA/good_cells.txt",
                            help='file with the good PS1 cells')
        parser.add_argument('--pscoords',type=str,default='/home/schultz/YSE/getPA/pscoords',help='path to pscoords binary')
        parser.add_argument('--fieldlist',type=str,default=None,help='optional comma-separated list giving fields that need PAs')
        parser.add_argument('--mjds_to_schedule',type=str,default=None,help='optional comma-separated list giving the times that each field should be scheduled.  Length must match length of --fieldlist argument')
        
        return parser
    
    def yse_pa(self,msb_fields,msb_ras,msb_decs,transients_all,transients_goodcell,status_all,pa=None):

            
        transients_best,transients_2best,transients_3best,transients_4best = [],[],[],[]
        transients_best_ra,transients_2best_ra,transients_3best_ra,transients_4best_ra = [],[],[],[]
        transients_best_dec,transients_2best_dec,transients_3best_dec,transients_4best_dec = [],[],[],[]
        for f,ra,ddec in zip(msb_fields,msb_ras,msb_decs):
            # find the transients in the field
            r = requests.get(f'{self.options.yseurl}/box_search/{ra}/{ddec}/1.65/',
                             auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
            data = json.loads(r.text)['transients']
            for d in data:
                if d['transient_name'] in transients_goodcell:
                    transients_best += [d['transient_name']]
                    transients_ra += [d['transient_ra']]
                    transients_dec += [d['transient_dec']]
                elif d['transient_name'] in transients_all:
                    iTr = transients_all == d['transient_name']
                    if status_all[iTr][0] == 'Interesting':
                        transients_2best += [d['transient_name']]
                        transients_2best_ra += [d['transient_ra']]
                        transients_2best_dec += [d['transient_dec']]
                    elif status_all[iTr][0] == 'FollowupRequested':
                        transients_3best += [d['transient_name']]
                        transients_3best_ra += [d['transient_ra']]
                        transients_3best_dec += [d['transient_dec']]
                    elif status_all[iTr][0] == 'Following':
                        transients_4best += [d['transient_name']]
                        transients_4best_ra += [d['transient_ra']]
                        transients_4best_dec += [d['transient_dec']]
        
        if not len(np.concatenate((transients_best,transients_2best,transients_3best,transients_4best))):
            return None,None

        scf = SkyCoord(msb_ras[0],msb_decs[0],unit=u.deg)

        # figure out the PA for today, best airmass
        if self.options.mjds_to_schedule is None or msb_fields[0].split('.')[0] not in self.options.fieldlist:
            print('no preferred MJD given for field %s'%msb_fields[0].split('.')[0])
            t = Time.now()
            time_start='05:00:00'; time_end='15:00:00'
            night_start = tel.twilight_evening_astronomical(t,which="previous")
            night_end = tel.twilight_morning_astronomical(t,which="previous")
            hourmin,hourmax = int(night_start.iso.split()[-1].split(':')[0]),int(night_end.iso.split()[-1].split(':')[0])
            airmass,times = np.array([]),np.array([])
            for hour in range(hourmin,hourmax+1):
                time_obs = '%s %02i:%s:00'%(t.iso.split()[0],hour,time_start.split(':')[1])
                time = Time(time_obs)
                altaz = tel.altaz(time,scf)
                if altaz.alt.value < 0: continue
                airmass = np.append(airmass,1/np.cos((90.-altaz.alt.value)*np.pi/180.))
                times = np.append(times,time)
            time = times[airmass == np.min(airmass)]
        else:
            time = [mjd_to_date(self.options.mjds_to_schedule[self.options.fieldlist == msb_fields[0].split('.')[0]][0])]
            
        parallactic_angle = tel.parallactic_angle(time[0],scf)

        if pa is not None:
            rotator_angles = np.array([180 - pa + parallactic_angle.deg])
        else:
            rotator_angles = np.linspace(-44,-183,30)
        len_good,list_full = [],[]
        for rotator_angle in rotator_angles:
            good_list = []
            pa = 180 - (-parallactic_angle.deg + rotator_angle)
            for i,transient_list,transient_ra,transient_dec in zip(
                    range(len([transients_4best,transients_3best,transients_2best,transients_best])),
                    [transients_4best,transients_3best,transients_2best,transients_best],
                    [transients_4best_ra,transients_3best_ra,transients_2best_ra,transients_best_ra],
                    [transients_4best_dec,transients_3best_dec,transients_2best_dec,transients_best_dec]):
                for transient,tra,tdec in zip(transient_list,transient_ra,transient_dec):
                    cmd = "echo %.7f %.7f | %s in=sky out=cell ra=%.7f dec=%.7f pa=%.1f dx=0 dy=0 dpa=0 sc=38.856"%(
                        tra,tdec,self.options.pscoords,msb_ras[0],msb_decs[0],pa)
                    output = subprocess.check_output(cmd, shell=True)
                    ota,cell,centerx,centery = output.split()
                    if 'OTA'+ota.decode('utf-8') in self.goodcells.keys() and cell.decode('utf-8') in self.goodcells['OTA'+ota.decode('utf-8')]:
                        if i < 3: good_list += [transient]
                        else: good_list += [transient]*4
            len_good += [len(good_list)]
            list_full += [[t for t in np.unique(good_list)],]

        iGood = np.argsort(len_good)[::-1][0:5]
        best_idx = sample(iGood.tolist(),1)
        best_rotator = rotator_angles[best_idx]
        list_good = np.array(list_full)[best_idx][0]
        best_pa = 180 - (-parallactic_angle.deg + best_rotator[0])

        return best_pa,list_good

    def get_requested_fields(self):

        # get tonight's observation requests
        nowmjd = date_to_mjd(datetime.datetime.now().isoformat())
        # ORIG
        # r = requests.get(f'{self.options.yseurl}/api/surveyobservations/?mjd_requested_gte={nowmjd-1}&mjd_requested_lte={nowmjd}&limit=1000',
        r = requests.get(f'{self.options.yseurl}/api/surveyobservations/?mjd_requested_gte={nowmjd}&mjd_requested_lte={nowmjd+1}&limit=1000',
                         auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
        data_results = json.loads(r.text)['results']

        # match to survey field names
        # here he's getting ALL the survey fields, and will later compare them 
        # with the surveyobservations fields
        r = requests.get(f'{self.options.yseurl}/api/surveyfields/?limit=3000',
                         auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
        surveyfielddata = json.loads(r.text)['results']


        filtdict = {}
        fieldfilts = {}
        # get all the photometric bands
        r = requests.get(f'{self.options.yseurl}/api/photometricbands/',
                         auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
        pbdata = json.loads(r.text)['results']
        for pb in pbdata:
           filtdict[pb['url']] = pb['name']
        
        field_msbs,fields,obs_mjds,ras,decs,obs_dates = np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([])
        for d in data_results: # data_results is the requested fields
            survey_field_url = d['survey_field']
            obs_mjd = d['obs_mjd']
            pb_url = d['photometric_band']
            if d['obs_mjd'] is None: obs_mjd = d['mjd_requested']
            obs_mjds = np.append(obs_mjds,obs_mjd)
            obs_dates = np.append(obs_dates,mjd_to_date(obs_mjd))
            for s in surveyfielddata: # surveyfielddata is the defined fields
                if s['url'] == survey_field_url:
                    # "fields" is full position e.g. 666.F
                    fields = np.append(fields,s['field_id'])
                    # "field_msbs" is the overall field name e.g. 666
                    field_msbs = np.append(field_msbs,s['field_id'].split('.')[0])
                    ras = np.append(ras,s['ra_cen'])
                    decs = np.append(decs,s['dec_cen'])

                    # create a dict associating filters with the 
                    # overall field names
                    thisfield = s['field_id'].split('.')[0]
                    thisfilt = filtdict[pb_url]
                    fieldfilts.setdefault(thisfield, set()).add(thisfilt)
                    # Because there are multiple filters per field name,
                    # I can't just np.append them as is done above
                    # the filters have twice as many list elements 
                    # as the fields
            

        fielddict = {}
        fields_unique,idx = np.unique(fields,return_index=True)
        fields,ras,decs,field_msbs = fields[idx],ras[idx],decs[idx],field_msbs[idx]
        for f in np.unique(field_msbs):
            fielddict[f] = ((fields[field_msbs == f]),(ras[field_msbs == f]),(decs[field_msbs == f]))

        return fielddict,fieldfilts
                    
    def main(self):

        fielddict,fieldfilts = self.get_requested_fields()


        transients_all,transients_goodcell,status_all = np.array([]),np.array([]),np.array([])
        r = requests.get(f'{self.options.yseurl}/query_api/all_yse_transients/',
                         auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
        data_all = json.loads(r.text)['transients']
        r = requests.get(f'{self.options.yseurl}/query_api/yse_transients_goodcell/',
                         auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
        data_goodcell = json.loads(r.text)['transients']
        for dg in data_goodcell:
            transients_goodcell = np.append(transients_goodcell,dg['name'])
        for da in data_all:
            transients_all = np.append(transients_all,da['name'])
            status_all = np.append(status_all,da['status'])

        
        best_pa_list = []
        for f in fielddict.keys():
            best_pa,list_good = self.yse_pa(fielddict[f][0],fielddict[f][1],fielddict[f][2],
                                            transients_all,transients_goodcell,status_all)
            best_pa_list += [best_pa]

        if args.cron is True:
           user = getpass.getuser()
           fullhostname = socket.gethostname()
           hostname = fullhostname.split('.')[0]
           print("# run from cron on %s@%s" % (user, hostname))
           print("#")
        else:
           print("#\n#")
   

        for k,best_pa in zip(fielddict.keys(),best_pa_list):
            if best_pa is not None:
                if best_pa > 360: best_pa -= 360
                elif best_pa < 0: best_pa += 360
            print(f"{k} {best_pa} {'.'.join(fieldfilts[k])}")
            
            
if __name__ == "__main__":
    ys = YSE_PA()
    parser = ys.add_options(usage='')
    args = parser.parse_args()
    ys.options = args

    if ys.options.fieldlist is not None:
        ys.options.fieldlist = np.array(ys.options.fieldlist.split(','))
    if ys.options.mjds_to_schedule is not None:
        ys.options.mjds_to_schedule = np.array(ys.options.mjds_to_schedule.split(',')).astype(float)
        if ys.options.fieldlist is None: raise RuntimeError('if --mjds_to_schedule is given, fieldlist must be as well')
        if len(ys.options.fieldlist) != len(ys.options.mjds_to_schedule):
            raise RuntimeError('--fieldlist and --mjds_to_schedule must be the same length')
        
    ys.goodcells = {}
    with open(ys.options.goodcellsfile) as fin:
        for line in fin:
            ys.goodcells[line.split()[0][:-1]] = line.split()[1:]

    
    ys.main()
