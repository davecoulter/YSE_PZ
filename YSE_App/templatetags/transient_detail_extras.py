import datetime
from django.utils import timezone
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon, SkyCoord, FK5
from astroplan import Observer
from astropy.time import Time
import astropy.units as u
from django import template
from ..models import *

register = template.Library()

@register.filter(name='galcoords')
def galcoords(coordstring):

	sc = SkyCoord('%s %s'%(coordstring[0],coordstring[1]),frame="fk5",unit=(u.hourangle,u.deg))
	return '%.7f  %.7f'%(sc.galactic.l.value,sc.galactic.b.value)

@register.filter(name='galcoordsl')
def galcoordsl(coordstring):

	sc = SkyCoord('%s %s'%(coordstring[0],coordstring[1]),frame="fk5",unit=(u.hourangle,u.deg))
	return '%.7f'%sc.galactic.l.value

@register.filter(name='galcoordsb')
def galcoordsb(coordstring):

	sc = SkyCoord('%s %s'%(coordstring[0],coordstring[1]),frame="fk5",unit=(u.hourangle,u.deg))
	return '%.7f'%sc.galactic.b.value


@register.filter(name='replace_space')
def replace_space(object):
	return(object.name.replace(' ','_'))

@register.filter(name='rise_time')
def rise_time(obsnight,coords,tel=None):

	import time
	tstart = time.time()
	
	tme = Time(str(obsnight.obs_date).split()[0])
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))


	location = EarthLocation.from_geodetic(
		obsnight.resource.telescope.longitude*u.deg,obsnight.resource.telescope.latitude*u.deg,
		obsnight.resource.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_rise_time = tel.target_rise_time(tme,sc,horizon=18*u.deg,which="previous")

	if target_rise_time:
		returnstarttime = target_rise_time.isot.split('T')[-1]
	else: returnstarttime = None

	print(time.time()-tstart)
	
	return(returnstarttime)

@register.filter(name='set_time')
def set_time(obsnight,coords):
	
	time = Time(str(obsnight.obs_date).split()[0])
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.resource.telescope.longitude*u.deg,obsnight.resource.telescope.latitude*u.deg,
		obsnight.resource.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_set_time = tel.target_set_time(time,sc,horizon=18*u.deg,which="previous")

	if target_set_time:
		returnendtime = target_set_time.isot.split('T')[-1]
	else: returnendtime = None

	return(returnendtime)

@register.filter(name='tonight_rise_time')
def tonight_rise_time(obsnight,coords):
	
	time = Time(datetime.datetime.now())
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.telescope.longitude*u.deg,obsnight.telescope.latitude*u.deg,
		obsnight.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_rise_time = tel.target_rise_time(time,sc,horizon=18*u.deg,which="previous")

	if target_rise_time:
		returnstarttime = target_rise_time.isot.split('T')[-1]
	else: returnstarttime = None

	return(returnstarttime)

@register.filter(name='tonight_set_time')
def tonight_set_time(obsnight,coords):

	time = Time(datetime.datetime.now())
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.telescope.longitude*u.deg,obsnight.telescope.latitude*u.deg,
		obsnight.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_set_time = tel.target_set_time(time,sc,horizon=18*u.deg,which="previous")

	if target_set_time:
		returnendtime = target_set_time.isot.split('T')[-1]
	else: returnendtime = None

	return(returnendtime)

@register.filter(name='moon_angle')
def moon_angle(obsnight,coords):

	obstime = Time(str(obsnight.obs_date).split()[0],scale='utc')

	mooncoord = get_moon(obstime)
	cs = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))
	return('%.1f'%cs.separation(mooncoord).deg)

@register.filter(name='too_moon_angle')
def too_moon_angle(too_resource,coords):
	obstime = Time(datetime.datetime.now())
	mooncoord = get_moon(obstime)
	cs = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))
	return('%.1f'%cs.separation(mooncoord).deg)

@register.filter(name='get_ps1_image')
def get_ps1_image(transient):

	transient_id = transient.id
	
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

@register.filter(name='lightcurveplt')
def lightcurveplt(transient_id):

		import random
		import django
		import datetime
		import mpld3
		import time
		tstart = time.time()
		
		from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
		from matplotlib.figure import Figure
		#import matplotlib.pyplot as plt
		#fig, ax = plt.subplots()
		#from matplotlib.dates import DateFormatter
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
		limmjd = None
		for p in photdata:
			if p.flux and np.abs(p.flux) > 1e10: continue
			if not p.mag: continue
			
			if p.discovery_point:
				limmjd = p.date_to_mjd()-10
				
			mjd = np.append(mjd,[p.date_to_mjd()])
			mag = np.append(mag,[p.mag])
			if p.mag_err: magerr = np.append(magerr,p.mag_err)
			else: magerr = np.append(magerr,0)
			band = np.append(band,str(p.band))
		
		ax.set_title("%s"%transient.name)
		for b in np.unique(band):

			ax.errorbar(mjd[band == b].tolist(),mag[band == b].tolist(),
						yerr=magerr[band == b].tolist(),fmt='o',label=b,zorder=30)
		ax.vlines(Time(datetime.datetime.today()).mjd,ymin=-10,ymax=30,
				  color='k',label='today',zorder=1)

		ax.set_xlabel('MJD',fontsize=15)
		ax.set_ylabel('Mag',fontsize=15)
		ax.invert_yaxis()
		if limmjd:
			ax.set_xlim([limmjd,np.max(mjd)+10])
			ax.set_ylim([np.max(mag)+0.25,np.min(mag[mjd > limmjd])-0.5])
		else:
			ax.set_xlim([np.min(mjd)-10,np.max(mjd)+10])
			ax.set_ylim([np.max(mag)+0.25,np.min(mag)-0.5])
		ax.legend()

		#ax.grid(color='lightgray', alpha=0.7)
		#response=django.http.HttpResponse(content_type='image/png')
		#canvas.print_png(response)
		g = mpld3.fig_to_html(fig,template_type='simple')
		#print(g)
		#plt.close(fig)
		print(time.time()-tstart)
		return g #response

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
	
