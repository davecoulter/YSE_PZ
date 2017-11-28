from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np
from astroplan import Observer
from astropy.time import Time

def GetSexigesimalString(ra_decimal, dec_decimal):
	c = SkyCoord(ra_decimal,dec_decimal,unit=(u.deg, u.deg))
	ra = c.ra.hms
	dec = c.dec.dms

	ra_string = "%02d:%02d:%0.1f" % (ra[0],ra[1],ra[2])
	dec_string = "%02d:%02d:%0.1f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))

	# Python has a -0.0 object. If the deg is this (because object lies < 60 min south), the string formatter will drop the negative sign
	if c.dec < 0.0 and dec[0] == 0.0:
		dec_string = "-0:%02d:%0.1f" % (np.abs(dec[1]),np.abs(dec[2]))

	return (ra_string, dec_string)

def get_psstamp_url(request, transient_id):

	ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color"%(
		Transient.objects.get(pk=transient_id).ra,Transient.objects.get(pk=transient_id).dec)

	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")
	
	ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color" % (t.ra,t.dec)
	response = requests.get(url=ps1url)
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


## We should refactor this so that it takes:
# - transient
# - observatory (or maybe array of observatory)
# - 
# And it can returns the data which can be plotted on the front end
# i.e. a tuple of (datetime, airmass) that ChartJS can plot on the 
# client 
def airmassplot(request, transient_id, obs, observatory):
	import random
	import django
	import datetime
	from astroplan.plots import plot_airmass
	
	from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
	from matplotlib.figure import Figure
	from matplotlib.dates import DateFormatter
	#from matplotlib import rcParams
	#rcParams['figure.figsize'] = (7,5)
	
	transient = Transient.objects.get(pk=transient_id)
	
	target = SkyCoord(transient.ra,transient.dec,unit=u.deg)
	time = Time(obs, format='iso')
	tel = Observer.at_site(observatory)
	
	fig=Figure()
	ax=fig.add_subplot(111)
	canvas=FigureCanvas(fig)

	ax.set_title("%s, %s, %s"%(observatory,transient.name, obs))

	night_start = tel.twilight_evening_astronomical(time,which="previous")
	night_end = tel.twilight_morning_astronomical(time,which="previous")
	delta_t = night_end - night_start
	observe_time = night_start + delta_t*np.linspace(0, 1, 75)
	plot_airmass(target, tel, observe_time, ax=ax)    
	#ax.axvline(night_start)
	#ax.axvline(night_end)
	
	response=django.http.HttpResponse(content_type='image/png')
	canvas.print_png(response)
	return response