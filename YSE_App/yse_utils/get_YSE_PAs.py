#!/export/home/lowe/anaconda3/bin/python3


# PA GENERATION FOR PS2
# Version 4.5    --- added ID info to header
# Version 4.4    --- advance one day if being run before UT midnight
# Version 4.3    --- option to use NO randomized offset, for debugging purposes
# Version 4.2    --- output numbers of transients picked up by each PA
#                    output format slightly different, won't work with 
#                    ysched.py version earlier than 4.0
# Version 4.1    --- add an random offset to the list of PAs
#                    to address persistence problems
# Version 4.0    --- calculates multiple PAs
#                    Formerly known as get_YSE_PAs.newdj_041321.v2.py
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
from random import sample, shuffle
import argparse
import configparser
import datetime
import requests
from requests.auth import HTTPBasicAuth
import json
from astropy.coordinates import SkyCoord

from astropy.time import Time, TimeDelta
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

    def add_arguments(self, parser=None, usage=None, config=None):
        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('-v', '--verbose', action="count", dest="verbose",
                            default=0,help='verbosity level')
        parser.add_argument('--telescope',type=str,default='PS1',help='either PS1 or PS2')
        parser.add_argument('-noo', '--noo', action="store_true", help="do not add random offset to PA")
        parser.add_argument('-c', '--cron', action="store_true", help="use if calling from cron (e.g.)")
        parser.add_argument('--fieldlist',type=str,default=None,help='optional comma-separated list giving fields that need PAs')
        parser.add_argument('--mjds_to_schedule',type=str,default=None,help='optional comma-separated list giving the times that each field should be scheduled.  Length must match length of --fieldlist argument')
        parser.add_argument('--list_transients', action="store_true", help="list transients for each PA if set (lot of output but potentially useful)")

        if config:
            parser.add_argument('--yseurl', type=str, default=config.get('main','yseurl'),
                                help='YSE URL')
            parser.add_argument('-u','--yseuser', type=str, default=config.get('main','yseuser'),
                                help='YSE user name')
            parser.add_argument('-p','--ysepass', type=str, default=config.get('main','ysepass'),
                                help='YSE password')
            parser.add_argument('--goodcellsfile_ps1', type=str, default=config.get('main','goodcellsfile_ps1'),
                                help='file with the good PS1 cells')
            parser.add_argument('--goodcellsfile_ps2', type=str, default=config.get('main','goodcellsfile_ps2'),
                                help='file with the good PS2 cells')
            parser.add_argument('--pscoords',type=str,default=config.get('main','pscoords'),
                                help='path to pscoords binary')

        
        return parser
    
    # OLD VERSION NO LONGER USED !
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



            # If we're running this before UT midnight, advance one day

            t = Time.now()

            # We're not using this sub now, but I'll add this code anyway,
            # just in case we ever do
            # how can I define this globally??
            UTnow = datetime.datetime.utcnow()
            UThour = UTnow.hour
            if UThour > 16:
               adday = TimeDelta(86400.0, format='sec')
               t += adday

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
            rotator_angles = np.linspace(20,160,30)
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

    def yse_pa_new(self,msb_fields,msb_ras,msb_decs,transients_all,transients_goodcell,status_all,poffset,pa=None):

        transients_best,transients_2best,transients_3best,transients_4best = [],[],[],[]
        transients_best_ra,transients_2best_ra,transients_3best_ra,transients_4best_ra = [],[],[],[]
        transients_best_dec,transients_2best_dec,transients_3best_dec,transients_4best_dec = [],[],[],[]
        transients_best_field,transients_2best_field,transients_3best_field,transients_4best_field = [],[],[],[]
        for f,ra,ddec in zip(msb_fields,msb_ras,msb_decs):
            # find the transients in the field
            r = requests.get(f'{self.options.yseurl}/box_search/{ra}/{ddec}/1.65/',
                             auth=HTTPBasicAuth(self.options.yseuser,self.options.ysepass))
            data = json.loads(r.text)['transients']
            for d in data:
                # verify the transient actually is in the field
                sc = SkyCoord(d['transient_ra'],d['transient_dec'],unit=u.deg)
                scf = SkyCoord(ra,ddec,unit=u.deg)
                if scf.separation(sc).deg > 1.65: continue
                #if '575' in f and d['transient_name'] == '2022hss':
                #    import pdb; pdb.set_trace()
                if d['transient_name'] in transients_goodcell:
                    transients_best += [d['transient_name']]
                    transients_best_ra += [d['transient_ra']]
                    transients_best_dec += [d['transient_dec']]
                    transients_best_field += [f]
                elif d['transient_name'] in transients_all:
                    iTr = transients_all == d['transient_name']
                    if status_all[iTr][0] == 'Interesting':
                        transients_2best += [d['transient_name']]
                        transients_2best_ra += [d['transient_ra']]
                        transients_2best_dec += [d['transient_dec']]
                        transients_2best_field += [f]
                    elif status_all[iTr][0] == 'FollowupRequested':
                        transients_3best += [d['transient_name']]
                        transients_3best_ra += [d['transient_ra']]
                        transients_3best_dec += [d['transient_dec']]
                        transients_3best_field += [f]
                    elif status_all[iTr][0] == 'Following':
                        transients_4best += [d['transient_name']]
                        transients_4best_ra += [d['transient_ra']]
                        transients_4best_dec += [d['transient_dec']]
                        transients_4best_field += [f]

        if not len(np.concatenate((transients_best,transients_2best,transients_3best,transients_4best))):
            return None,None

        scf = SkyCoord(msb_ras[0],msb_decs[0],unit=u.deg)

        len_good,list_full = [],[]
        origpalist = np.arange(0,359,10)
        
        # add random offset to PA
        def addpoff(x):
           return(x + poffset) % 360
        palist = addpoff(origpalist)

        # DIAG
        currfield = msb_fields[0].split('.')[0]
        # palist = np.arange(0,180,5) # ORIG
        for pa in palist:

            # DIAG
            # sys.stderr.write("field: %s  trying PA: %s\n" % (currfield, pa))

            good_list = []
            for i,transient_list,transient_ra,transient_dec,transient_field in zip(
                    range(len([transients_4best,transients_3best,transients_2best,transients_best])),
                    [transients_4best,transients_3best,transients_2best,transients_best],
                    [transients_4best_ra,transients_3best_ra,transients_2best_ra,transients_best_ra],
                    [transients_4best_dec,transients_3best_dec,transients_2best_dec,transients_best_dec],
                    [transients_4best_field,transients_3best_field,transients_2best_field,transients_best_field]):
                for transient,tra,tdec,tfield in zip(transient_list,transient_ra,transient_dec,transient_field):
                    
                    msbr,msbd = msb_ras[msb_fields == tfield][0],msb_decs[msb_fields == tfield][0]
                    cmd = "echo %.7f %.7f | %s in=sky out=cell ra=%.7f dec=%.7f pa=%.1f dx=0 dy=0 dpa=0 sc=38.856"%(
                        tra,tdec,self.options.pscoords,msbr,msbd,pa)
                    output = subprocess.check_output(cmd, shell=True)
                    ota,cell,centerx,centery = output.split()
                    if 'OTA'+ota.decode('utf-8') in self.goodcells.keys() and cell.decode('utf-8') in self.goodcells['OTA'+ota.decode('utf-8')]:
                        if i < 3: good_list += [transient]
                        else: good_list += [transient]*4
                    #import pdb; pdb.set_trace()
            len_good += [len(good_list)]
            list_full += [[t for t in np.unique(good_list)],]

        iGood = np.argsort(len_good)[::-1][0:5]
        best_pa = palist[iGood]
        list_good = np.array(list_full)[iGood]
        # DIAG
        # sys.stderr.write("list_good: %s  best_pa: %s\n" % (list_good, best_pa))
        
        return best_pa,list_good

    
    def get_requested_fields(self):

        # If we're running this before UT midnight, add a day
        UTnow = datetime.datetime.utcnow()
        UThour = UTnow.hour
        mjddate = UTnow
        if UThour > 16:
           mjddate = mjddate + datetime.timedelta(days=1)

        # get tonight's observation requests
        startmjd = date_to_mjd(mjddate.date().isoformat())
        r = requests.get(f'{self.options.yseurl}/api/surveyobservations/?mjd_requested_gte={startmjd}&mjd_requested_lte={startmjd+1}&limit=1000&instrument={self.options.instrument}',
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
        r = requests.get(f'{self.options.yseurl}/api/photometricbands/?limit=1000',
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
        trans_list = []
        final_transients = {}

        origPAoffsets = list(range(10))
        usePAoffsets = []

        output = ""
        for f in fielddict.keys():
        # apply a random single digit offset to the PA
            if len(usePAoffsets) == 0:
                # this takes care of the unlikely case in which we have more
                # than 10 YSE fields: the offset array will be replenished as
                # often as needed
                # randomize the offsets here
                usePAoffsets = origPAoffsets[:]
                shuffle(usePAoffsets)
            if args.noo is True:
               PAoffset = 0
            else:
               PAoffset = usePAoffsets.pop()
            best_pa,list_good = self.yse_pa_new(fielddict[f][0],fielddict[f][1],fielddict[f][2],
                                                transients_all,transients_goodcell,status_all,PAoffset)
            # DIAG
            # sys.stderr.write("field: %s list_good: %s  best_pa: %s\n" % (f, list_good, best_pa))
            best_pa_list += [best_pa]
            trans_list += [list_good]
            final_transients[f] = list_good
            # DIAG
            # sys.stderr.write("field: %s  best_pa_list: %s  list_good: %s\n" % (f,best_pa_list,list_good))

        
        if args.cron is True:
           user = getpass.getuser()
           fullhostname = socket.gethostname()
           hostname = fullhostname.split('.')[0]
           thisScript = os.path.realpath(sys.argv[0])
           # header = "# run from cron on %s@%s\n#" % (user, hostname)
           header1 = "# generated for PS2 by %s\n" % (thisScript)
           header2 = "# run from cron on %s@%s\n#" % (user, hostname)
           header = header1 + header2
        else:
           header = "#\n#\n#"
   

        #print('field  best_pa_m90 best_pa_merid best_pa_p90 filters')
        for k,best_pa,tlist in zip(fielddict.keys(),best_pa_list,trans_list):
            # sys.stderr.write("k: %s, best_pa_list: %s, trans_list: %s\n" % (k, best_pa, tlist))
            if best_pa is None:
               outpa = "None"
               outtrans = "None"
            else:
               # are these *already* numpy arrays?  Can't tell!
               bparray = np.array(best_pa)
               trarray = np.array(tlist)
               # these are the indices which sort the best_pa list
               idx = np.argsort(bparray)
               # sorted arrays
               bplist = np.array(bparray)[idx]
               trlist = np.array(trarray)[idx]
               # number of transients for each PA, in order of increasing PA
               numtrans = list(map(lambda x: len(x), trlist))
               outpa = ','.join(map(str, bplist))
               outtrans = ','.join(map(str, numtrans))
            # print(f"{k} {','.join(fieldfilts[k])} {outpa} {outtrans}")
            if self.options.list_transients:
                if outpa != "None":
                    outtr = '['+','.join(np.concatenate(trlist))+']'
                else:
                    outtr = ''
                output += f"\n{k} {','.join(fieldfilts[k])} {outpa} {outtrans} {outtr}"
            else:
                output += f"\n{k} {','.join(fieldfilts[k])} {outpa} {outtrans}"
            # OK WE'RE OUTPUTTING AN EXTRA CARRIAGE RETURN GOTTA FIX THAT

        if len(output) == 0:
           sys.exit()
        else:
           print(header + output)


            
if __name__ == "__main__":
    ys = YSE_PA()
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


    
    if ys.options.fieldlist is not None:
        ys.options.fieldlist = np.array(ys.options.fieldlist.split(','))
    if ys.options.mjds_to_schedule is not None:
        ys.options.mjds_to_schedule = np.array(ys.options.mjds_to_schedule.split(',')).astype(float)
        if ys.options.fieldlist is None: raise RuntimeError('if --mjds_to_schedule is given, fieldlist must be as well')
        if len(ys.options.fieldlist) != len(ys.options.mjds_to_schedule):
            raise RuntimeError('--fieldlist and --mjds_to_schedule must be the same length')
        
    ys.goodcells = {}
    if ys.options.telescope == 'PS1':
        goodcellsfile = ys.options.goodcellsfile_ps1
        ys.options.instrument = 'GPC1'
    elif ys.options.telescope == 'PS2':
        goodcellsfile = ys.options.goodcellsfile_ps2
        ys.options.instrument = 'GPC2'
    else:
        raise RuntimeError('telescope must be either PS1 or PS2')
    
    with open(goodcellsfile) as fin:
        for line in fin:
            ys.goodcells[line.split()[0][:-1]] = line.split()[1:]

    
    ys.main()
