import time
from astropy.time import Time
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon, SkyCoord, Angle
import astropy.units as u
from astroplan import Observer

def set_func(coords,obs_date,longitude,latitude,elevation,setdict):
    tstart = time.time()

    #transient = Transient.objects.filter(id=transient_id)[0]
    #coords = transient.CoordString()

    #obsnight = ClassicalObservingDate.objects.get(pk=obs_id)

    tme = Time(str(obs_date).split()[0])
    sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

    location = EarthLocation.from_geodetic(
        longitude*u.deg,latitude*u.deg,
        elevation*u.m)
    tel = Observer(location=location, timezone="UTC")

    target_set_time = tel.target_set_time(tme,sc,horizon=18*u.deg,which="previous")

    if target_set_time:
        try: settime = target_set_time.isot.split('T')[-1]
        except: settime = None
    else: 
        settime = None

    print('set time took %s'%(time.time()-tstart))
    setdict['set_time'] = settime
    
def rise_func(coords,obs_date,longitude,latitude,elevation,risedict):
    tstart = time.time()
    #transient = Transient.objects.filter(id=transient_id)[0]
    #coords = transient.CoordString()

    #obsnight = ClassicalObservingDate.objects.get(pk=obs_id)

    tme = Time(str(obs_date).split()[0])
    sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

    location = EarthLocation.from_geodetic(
        longitude*u.deg,latitude*u.deg,
        elevation*u.m)
    tel = Observer(location=location, timezone="UTC")

    target_rise_time = tel.target_rise_time(
        tme,sc,horizon=18*u.deg,which="previous")

    if target_rise_time:
        try: risetime = target_rise_time.isot.split('T')[-1]
        except: risetime = None
    else: 
        risetime = None

    print('rise time took %s'%(time.time()-tstart))
    risedict['rise_time'] = risetime

