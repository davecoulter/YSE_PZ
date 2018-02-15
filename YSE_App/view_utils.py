# utils for generating webpage views
import django
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response
import copy
from .models import *
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon, SkyCoord
from astropy.time import Time
import astropy.units as u
import datetime
import json
import numpy as np
from django.conf import settings as djangoSettings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

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
	pidlist = []
	for p in photometry:
		pidlist += [p.id]
	photdata = TransientPhotData.objects.filter(photometry__in=pidlist)

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
		can_obs = 1
		o.telescope = telescope.name
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
	
#	 start_obs = False
#	 starttime,endtime = None,None
#	 for jd in np.arange(night_start.mjd,night_end.mjd,0.05):
#		 time = Time(jd,format="mjd")
#		 target_up = tel.target_is_up(time,sc,horizon=18*u.deg)
#		 if target_up and not start_obs:
#			 start_obs = True
#			 starttime = copy.copy(time)
#		 if not target_up and start_obs:
#			 can_obs = False
#			 endtime = copy.copy(time)
#			 break

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

class finder(TemplateView):
	template_name = 'YSE_App/finder.html'
	
	def __init__(self):
		pass
	def finderchart(self, request, transient_id):
		import os
		from .util import mkFinderChart

		from django.contrib.staticfiles.templatetags.staticfiles import static
		from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
		from matplotlib.figure import Figure
	
		transient = Transient.objects.get(pk=transient_id)
		basedir = "%sYSE_App/images/findercharts"%(djangoSettings.STATIC_ROOT)
		if not os.path.exists(basedir):
			os.makedirs(basedir)
		
		outputOffsetFileName = '%s/%s.offsetstars.txt'%(
			basedir,transient.name)
		outputFinderFileName = '%s/%s.finder.png'%(
			basedir,transient.name)
		if os.path.exists(outputOffsetFileName) and\
		   os.path.exists(outputFinderFileName):
			return HttpResponseRedirect(reverse('transient_detail',
												args=(transient.id,)))

		find = mkFinderChart.finder()
		parser = find.add_options(usage='')
		options,  args = parser.parse_args()
		options.ra = str(transient.ra)
		options.dec = str(transient.dec)
		options.snid = transient.name
		#options.outputOffsetFileName = outputOffsetFileName
		options.outputFinderFileName = outputFinderFileName
		find.options = options
		import pylab as plt
	
		fig=Figure()
		ax = fig.add_axes([0.2,0.3,0.6,0.6])
		canvas=FigureCanvas(fig)
		ax,offdictlist = find.mkChart(options.ra,options.dec,
									  options.outputFinderFileName,
									  ax=ax,saveImg=False)
		
		context = {'t':transient,
				   'offsets':offdictlist}
		
		#return response
		return render(request,'YSE_App/finder.html',
					  context)

	def finderim(self, request, transient_id):
		import os
		from .util import mkFinderChart
		from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
		from matplotlib.figure import Figure
		import pylab as plt
		transient = Transient.objects.get(pk=transient_id)
		basedir = "%sYSE_App/images/findercharts"%(djangoSettings.STATIC_ROOT)
		if not os.path.exists(basedir):
			os.makedirs(basedir)
		
		outputOffsetFileName = '%s/%s.offsetstars.txt'%(
			basedir,transient.name)
		outputFinderFileName = '%s/%s.finder.png'%(
			basedir,transient.name)
		if os.path.exists(outputOffsetFileName) and\
		   os.path.exists(outputFinderFileName):
			return HttpResponseRedirect(reverse('transient_detail',
												args=(transient.id,)))

		
		fig=Figure()
		ax = fig.add_axes([0.2,0.3,0.6,0.6])
		canvas=FigureCanvas(fig)

		find = mkFinderChart.finder()
		parser = find.add_options(usage='')
		options,  args = parser.parse_args()
		options.ra = str(transient.ra)
		options.dec = str(transient.dec)
		options.snid = transient.name
		#options.outputOffsetFileName = outputOffsetFileName
		options.outputFinderFileName = outputFinderFileName
		find.options = options
		ax,offdictlist = find.mkChart(options.ra,options.dec,
									  options.outputFinderFileName,
									  ax=ax,saveImg=False)
		
		response=django.http.HttpResponse(content_type='image/png')
		canvas.print_png(response)

		return response
	
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
		if int(hr) == 0:
			xlow = datetime.datetime(int(yr),int(mn),int(day)-1,23,int(minu))
		else:
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
		import time
		from bokeh.plotting import figure
		from bokeh.resources import CDN
		from bokeh.embed import file_html
		from bokeh.models import Range1d,Span
		tstart = time.time()
		
		transient = Transient.objects.get(pk=transient_id)
		photdata = get_all_phot_for_transient(transient_id)
		if not photdata:
			return django.http.HttpResponse('')

		ax=figure()

		mjd,mag,magerr,band = \
			np.array([]),np.array([]),np.array([]),np.array([])
		limmjd = None
		for p in photdata:
			if p.flux and np.abs(p.flux) > 1e10: continue
			if not p.mag: continue
			
			if p.discovery_point:
				limmjd = p.date_to_mjd()-30
				
			mjd = np.append(mjd,[p.date_to_mjd()])
			mag = np.append(mag,[p.mag])
			if p.mag_err: magerr = np.append(magerr,p.mag_err)
			else: magerr = np.append(magerr,0)
			band = np.append(band,str(p.band))
		
		ax.title.text = "%s"%transient.name
		colorlist = ['#1f77b4','#ff7f0e','#2ca02c','#d62728',
					 '#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
		count = 0
		for b in np.unique(band):
			coloridx = count % len(np.unique(colorlist))
			#ax.errorbar(mjd[band == b].tolist(),mag[band == b].tolist(),
			#			yerr=magerr[band == b].tolist(),fmt='o',label=b,zorder=30)
			ax.circle(mjd[band == b].tolist(),mag[band == b].tolist(),
					  color=colorlist[coloridx],size=7,legend=b)

			err_xs,err_ys = [],[]
			for x,y,yerr in zip(mjd[band == b].tolist(),mag[band == b].tolist(),magerr[band == b].tolist()):
				err_xs.append((x, x))
				err_ys.append((y - yerr, y + yerr))
			ax.multi_line(err_xs, err_ys, color=colorlist[coloridx])
			count += 1
			
		today = Time(datetime.datetime.today()).mjd
		ax.line(today,20,line_width=3,line_color='black',legend='today (%i)'%today)
		vline = Span(location=today, dimension='height', line_color='black',
					 line_width=3)#, legend='today (%i)'%today)
		ax.add_layout(vline)
		#ax.renderers.extend([vline])
		ax.legend.location = 'top_right'

		#ax.vlines(today,ymin=-10,ymax=30,
		#		  color='k',label='today (%i)'%today,zorder=1)

		ax.xaxis.axis_label = 'MJD'
		ax.yaxis.axis_label = 'Mag'

		if limmjd:
			ax.x_range = Range1d(limmjd,np.max(mjd)+10)
			ax.y_range = Range1d(np.max(mag[mjd > limmjd])+0.25,np.min(mag[mjd > limmjd])-0.5)
		else:
			ax.x_range=Range1d(np.min(mjd)-10,np.max(mjd)+10)
			ax.y_range=Range1d(np.max(mag)+0.25,np.min(mag)-0.5)
		#ax.legend()

		#ax.grid(color='lightgray', alpha=0.7)
		#g = mpld3.fig_to_html(fig,template_type='simple')

		g = file_html(ax,CDN,"my plot")
		
		return HttpResponse(g.replace('width: 90%','width: 100%'))

def rise_time(request,transient_id,obs_id):

	import time
	tstart = time.time()
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obsnight = ClassicalObservingDate.objects.get(pk=obs_id)
	
	tme = Time(str(obsnight.obs_date).split()[0])
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.resource.telescope.longitude*u.deg,obsnight.resource.telescope.latitude*u.deg,
		obsnight.resource.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_rise_time = tel.target_rise_time(tme,sc,horizon=18*u.deg,which="previous")
	
	if target_rise_time:
		risetime = target_rise_time.isot.split('T')[-1]
	else: 
		risetime = None
			
	print(time.time()-tstart)
	risedict = {'rise_time':risetime}
	return JsonResponse(risedict)

def set_time(request,transient_id,obs_id):

	import time
	tstart = time.time()
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obsnight = ClassicalObservingDate.objects.get(pk=obs_id)
	
	tme = Time(str(obsnight.obs_date).split()[0])
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.resource.telescope.longitude*u.deg,obsnight.resource.telescope.latitude*u.deg,
		obsnight.resource.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_set_time = tel.target_set_time(tme,sc,horizon=18*u.deg,which="previous")
	
	if target_set_time:
		settime = target_set_time.isot.split('T')[-1]
	else: 
		settime = None
			
	print(time.time()-tstart)
	setdict = {'set_time':settime}
	return JsonResponse(setdict)

def moon_angle(request,transient_id,obs_id):
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obsnight = ClassicalObservingDate.objects.get(pk=obs_id)
	
	obstime = Time(str(obsnight.obs_date).split()[0],scale='utc')

	mooncoord = get_moon(obstime)
	cs = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))
	moondict = {'moon_angle':'%.1f deg'%cs.separation(mooncoord).deg}
	return JsonResponse(moondict)

def tonight_rise_time(request,transient_id,too_id):
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obsnight = ToOResource.objects.filter(id=too_id)[0]
	
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

	risedict = {'rise_time':returnstarttime}
	return JsonResponse(risedict)
	

def tonight_set_time(request,transient_id,too_id):
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obsnight = ToOResource.objects.filter(id=too_id)[0]
	
	time = Time(datetime.datetime.now())
	sc = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))

	location = EarthLocation.from_geodetic(
		obsnight.telescope.longitude*u.deg,obsnight.telescope.latitude*u.deg,
		obsnight.telescope.elevation*u.m)
	tel = Observer(location=location, timezone="UTC")

	target_set_time = tel.target_set_time(time,sc,horizon=18*u.deg,which="previous")

	if target_set_time:
		returnstarttime = target_set_time.isot.split('T')[-1]
	else: returnstarttime = None

	setdict = {'set_time':returnstarttime}
	return JsonResponse(setdict)
	
def tonight_moon_angle(request,transient_id,too_id):
	transient = Transient.objects.filter(id=transient_id)[0]
	coords = transient.CoordString()

	obstime = Time(datetime.datetime.now())
	mooncoord = get_moon(obstime)
	cs = SkyCoord('%s %s'%(coords[0],coords[1]),unit=(u.hourangle,u.deg))
	moondict = {'moon_angle':'%.1f deg'%cs.separation(mooncoord).deg}
	return JsonResponse(moondict)

def get_ps1_image(request,transient_id):
	
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

	jpegurldict = {"jpegurl":jpegurl}
	return(JsonResponse(jpegurldict))
