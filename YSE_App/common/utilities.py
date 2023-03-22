from astropy.coordinates import SkyCoord
from astropy.coordinates import EarthLocation
import astropy.units as u
import numpy as np
from astroplan import Observer
from astropy.time import Time
import requests

def coordstr_to_decimal(coord):
	if ',' in coord:
		ra,dec = coord.split(',')
	elif ' ' in coord:
		ra,dec = coord.split()
	else:
		raise RuntimeError('RA/Dec format not recognized')

	try:
		ra = float(ra); dec = float(dec)
		return ra,dec
	except:
		if ':' in ra and ':' in dec:
			sc = SkyCoord(ra,dec,unit=(u.hourangle,u.deg))
			return sc.ra.degree,sc.dec.degree
		else:
			sc = SkyCoord(ra,dec)
			return sc.ra.degree,sc.dec.degree

def date_to_mjd(date):
	time = Time(date,scale='utc')
	return time.mjd

def mjd_to_date(mjd):
    time = Time(mjd,format='mjd',scale='utc')
    return time.isot

def getSeparation(ra1_decimal,dec1_decimal,
				  ra2_decimal,dec2_decimal):
		c1 = SkyCoord(ra1_decimal,dec1_decimal,unit=(u.deg, u.deg))
		c2 = SkyCoord(ra2_decimal,dec2_decimal,unit=(u.deg, u.deg))
		return(c1.separation(c2).arcsec)
		
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

def get_psstamp_url(request, transient_id, Transient):

	ps1url = ("http://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f+%.7f&filter=color"%(
		Transient.objects.get(pk=transient_id).ra,Transient.objects.get(pk=transient_id).dec))

	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")
	
	ps1url = ("http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f+%.7f&filter=color" % (t.ra,t.dec))
	try:
		response = requests.get(url=ps1url,timeout=5)
	except: return("")
	response_text = response.content.decode('utf-8')
	if "<td><img src=" in response.content.decode('utf-8'):
		jpegurl = response.content.decode('utf-8').split('<td><img src="')[1].split('" width="240" height="240" /></td>')[0]
		jpegurl = "http:%s"%jpegurl
	else:
		jpegurl=""

	return(jpegurl)

def telescope_can_observe(ra,dec,date,tel):
	time = Time(date)
	sc = SkyCoord(ra,dec,unit=u.deg)
	tel = Observer.at_site(tel)

	night_start = tel.twilight_evening_astronomical(time,which="previous")
	night_end = tel.twilight_morning_astronomical(time,which="previous")
	can_obs = False
	for jd in np.arange(night_start.mjd,night_end.mjd,0.02):
			time = Time(jd,format="mjd")
			target_up = tel.target_is_up(time,sc)
			if target_up:
					can_obs = True
					break

	return(can_obs)

def getRADecBox(ra,dec,size=None):
	RAboxsize = DECboxsize = size

	# get the maximum 1.0/cos(DEC) term: used for RA cut
	minDec = dec-0.5*DECboxsize
	if minDec<=-90.0:minDec=-89.9
	maxDec = dec+0.5*DECboxsize
	if maxDec>=90.0:maxDec=89.9

	invcosdec = max(1.0/np.cos(dec*np.pi/180.0),
					1.0/np.cos(minDec  *np.pi/180.0),
					1.0/np.cos(maxDec  *np.pi/180.0))

	ramin = ra-0.5*RAboxsize*invcosdec
	ramax = ra+0.5*RAboxsize*invcosdec
	decmin = dec-0.5*DECboxsize
	decmax = dec+0.5*DECboxsize

	if ra<0.0: ra+=360.0
	if ra>=360.0: ra-=360.0

	if ramin!=None:
		if (ra-ramin)<-180:
			ramin-=360.0
			ramax-=360.0
		elif (ra-ramin)>180:
			ramin+=360.0
			ramax+=360.0
	return(ramin,ramax,decmin,decmax)
