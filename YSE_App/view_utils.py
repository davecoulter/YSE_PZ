import copy
from .models import *
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon, SkyCoord
from astropy.time import Time
import astropy.units as u
import datetime
import numpy as np

def get_recent_phot_for_host(host_id=None):

    host = Host.objects.filter(id=host_id)
    photometry = HostPhotometry.objects.filter(host=host_id)

    photdata = False
    for p in photometry:
        photdata = HostPhotData.objects.filter(photometry=p.id).order_by('-obs_date')

    
    if photdata:    
        return(photdata[0])
    else:
        return(None)

def get_all_phot_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    photdata = False
    for p in photometry:
        photdata = TransientPhotData.objects.filter(photometry=p.id)
    
    if photdata:    
        return(photdata)
    else:
        return(None)

    
def get_recent_phot_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    photdata = False
    for p in photometry:
        photdata = TransientPhotData.objects.filter(photometry=p.id).order_by('-obs_date')

    
    if photdata:    
        return(photdata[0])
    else:
        return(None)

def get_disc_phot_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    photdata = False
    firstphot = None
    for p in photometry:
        photdata = TransientPhotData.objects.filter(photometry=p.id).order_by('-obs_date')[::-1]
        for ph in photdata:
            if ph.discovery_point:
                return(ph)
            elif ph.mag:
                firstphot = ph
            
    return(firstphot)

def get_disc_mag_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    photdata = False
    firstphot = None
    for p in photometry:
            photdata = TransientPhotData.objects.filter(photometry=p.id).order_by('-obs_date')[::-1]
            for ph in photdata:
                if ph.discovery_point:
                    return(ph)
                elif ph.mag:
                    firstphot = ph

    return(firstphot)

    
def getMoonAngle(observingdate,telescope,ra,dec):
    if observingdate:
        obstime = Time(observingdate,scale='utc')
    else:
        obstime = Time(datetime.datetime.now())
    mooncoord = get_moon(obstime)
    cs = SkyCoord(ra,dec,unit=u.deg)
    return('%.1f'%cs.separation(mooncoord).deg)
    
def getObsNights(transient):

    obsnights,tellist = (),()
    for o in ClassicalObservingDate.objects.order_by('-obs_date')[::-1]:
        if not o.happening_soon(): continue
        telescope = get_telescope_from_obsnight(o.id)
        observatory = get_observatory_from_telescope(telescope.id)
        #can_obs = telescope_can_observe(transient.ra,
        #                                transient.dec, 
        #                                str(o.obs_date).split()[0],
        #                                telescope.latitude,
        #                                telescope.longitude,
        #                                telescope.elevation,
        #                                observatory.utc_offset)
        can_obs = 1
        o.telescope = telescope.name
        import time
        tstart = time.time()
        o.rise_time,o.set_time = getTimeUntilRiseSet(transient.ra,
                                                     transient.dec, 
                                                     str(o.obs_date).split()[0],
                                                     telescope.latitude,
                                                     telescope.longitude,
                                                     telescope.elevation,
                                                     observatory.utc_offset)
        o.moon_angle = getMoonAngle(str(o.obs_date).split()[0],telescope,transient.ra,transient.dec)
        print(time.time()-tstart)
        obsnights += ([o,can_obs],)
        if can_obs and telescope not in tellist: tellist += (telescope,)
    return obsnights,tellist

def getTimeUntilRiseSet(ra,dec,date,lat,lon,elev,utc_off):
    if date:
        time = Time(date)
    else:
        time = Time(datetime.datetime.now())
    sc = SkyCoord(ra,dec,unit=u.deg)

    location = EarthLocation.from_geodetic(
        lon*u.deg,lat*u.deg,
        elev*u.m)
    tel = Observer(location=location, timezone="UTC")
    #night_start = tel.twilight_evening_civil(time,which="previous")
    #night_end = tel.twilight_morning_civil(time,which="previous")
    target_rise_time = tel.target_rise_time(time,sc,horizon=18*u.deg,which="previous")
    target_set_time = tel.target_set_time(time,sc,horizon=18*u.deg,which="previous")
    
#    start_obs = False
#    starttime,endtime = None,None
#    for jd in np.arange(night_start.mjd,night_end.mjd,0.05):
#        time = Time(jd,format="mjd")
#        target_up = tel.target_is_up(time,sc,horizon=18*u.deg)
#        if target_up and not start_obs:
#            start_obs = True
#            starttime = copy.copy(time)
#        if not target_up and start_obs:
#            can_obs = False
#            endtime = copy.copy(time)
#            break

    if target_rise_time:
        returnstarttime = target_rise_time.isot.split('T')[-1]
    else: returnstarttime = None
    if target_set_time:
        returnendtime = target_set_time.isot.split('T')[-1]
    else: returnendtime = None

    
    return(returnstarttime,returnendtime)

    
def telescope_can_observe(ra,dec,date,lat,lon,elev,utc_off):
    if date:
        time = Time(date)
    else:
        time = Time(datetime.datetime.now())
    sc = SkyCoord(ra,dec,unit=u.deg)

    location = EarthLocation.from_geodetic(
        lon*u.deg,lat*u.deg,
        elev*u.m)
    tel = Observer(location=location, timezone="UTC")
    
    night_start = tel.twilight_evening_astronomical(time,which="previous")
    night_end = tel.twilight_morning_astronomical(time,which="previous")
    can_obs = False
    for jd in np.arange(night_start.mjd,night_end.mjd,0.02):
        time = Time(jd,format="mjd")
        target_up = tel.target_is_up(time,sc,horizon=18*u.deg)
        if target_up:
            can_obs = True
            break

    return(can_obs)

def get_observatory_from_telescope(telescope_id):
    tel = Telescope.objects.filter(id=telescope_id)[0]
    observatory = Observatory.objects.filter(id=tel.observatory_id)[0]
    return(observatory)

def get_telescope_from_obsnight(obsnight_id):
    classobsdate = ClassicalObservingDate.objects.filter(id=obsnight_id)[0]
    classresource = ClassicalResource.objects.filter(id=classobsdate.resource_id)[0]
    telescope = Telescope.objects.filter(id=classresource.telescope_id)[0]
    return(telescope)

## We should refactor this so that it takes:
# - transient
# - observatory (or maybe array of observatory)
# - 
# And it can returns the data which can be plotted on the front end
# i.e. a tuple of (datetime, airmass) that ChartJS can plot on the 
# client 

def airmassplot(request, transient_id, obs_id, telescope_id):
        import random
        import django
        import datetime
        from astroplan.plots import plot_airmass
        
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        from matplotlib.figure import Figure
        from matplotlib.dates import DateFormatter
        from matplotlib import rcParams
        rcParams['figure.figsize'] = (7,7)
        
        transient = Transient.objects.get(pk=transient_id)
        if int(obs_id):
            obsnight = ClassicalObservingDate.objects.get(pk=obs_id)
            obs_date = obsnight.obs_date
        else:
            obs_date = datetime.date.today() #time.now()
            
        telescope = Telescope.objects.get(pk=telescope_id)
        
        target = SkyCoord(transient.ra,transient.dec,unit=u.deg)
        time = Time(str(obs_date).split('+')[0], format='iso')
        
        location = EarthLocation.from_geodetic(telescope.longitude*u.deg, telescope.latitude*u.deg,telescope.elevation*u.m)
        tel = Observer(location=location, name=telescope.name, timezone="UTC")
        
        fig=Figure()
        ax=fig.add_subplot(111)
        canvas=FigureCanvas(fig)

        ax.set_title("%s, %s, %s"%(telescope.tostring(),transient.name, obs_date))

        night_start = tel.twilight_evening_astronomical(time,which="previous")
        night_end = tel.twilight_morning_astronomical(time,which="previous")
        delta_t = night_end - night_start
        observe_time = night_start + delta_t*np.linspace(0, 1, 75)
        plot_airmass(target, tel, observe_time, ax=ax)    

        yr,mn,day,hr,minu,sec = night_start.iso.replace(':',' ').replace('-',' ').split()
        starttime = datetime.datetime(int(yr),int(mn),int(day),int(hr),int(minu))
        xlow = datetime.datetime(int(yr),int(mn),int(day),int(hr)-1,int(minu))
        yr,mn,day,hr,minu,sec = night_end.iso.replace(':',' ').replace('-',' ').split()
        endtime = datetime.datetime(int(yr),int(mn),int(day),int(hr),int(minu))
        xhi = datetime.datetime(int(yr),int(mn),int(day),int(hr)+1,int(minu))
        ax.axvline(starttime,color='r',label='18 deg twilight')#night_start.iso)
        ax.axvline(endtime,color='r')
        ax.legend(loc='lower right')
        
        ax.set_xlim([xlow,xhi])
        
        response=django.http.HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response

def lightcurveplot(request, transient_id):

        import random
        import django
        import datetime

        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        from matplotlib.figure import Figure
        from matplotlib.dates import DateFormatter
        #from matplotlib import rcParams
        #rcParams['figure.figsize'] = (7,5)
        
        transient = Transient.objects.get(pk=transient_id)
        photdata = get_all_phot_for_transient(transient_id)
        if not photdata:
            return django.http.HttpResponse('')
        
        fig=Figure()
        ax=fig.add_subplot(111)
        canvas=FigureCanvas(fig)

        mjd,mag,magerr,band = \
            np.array([]),np.array([]),np.array([]),np.array([])
        for p in photdata:
            if p.flux and np.abs(p.flux) > 1e10: continue
            if not p.mag: continue
            mjd = np.append(mjd,[p.date_to_mjd()])
            mag = np.append(mag,[p.mag])
            if p.mag_err: magerr = np.append(magerr,p.mag_err)
            else: magerr = np.append(magerr,0)
            band = np.append(band,str(p.band))
        
        ax.set_title("%s"%transient.name)
        for b in np.unique(band):
            ax.errorbar(mjd[band == b],mag[band == b],
                        yerr=magerr[band == b],fmt='o',label=b)
        ax.set_xlabel('MJD',fontsize=15)
        ax.set_ylabel('Mag',fontsize=15)
        ax.invert_yaxis()
        ax.legend()
        
        response=django.http.HttpResponse(content_type='image/png')
        canvas.print_png(response)
        return response
