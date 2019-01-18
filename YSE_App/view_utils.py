# utils for generating webpage views
import django
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response
import copy
from .models import *
from django.db import models
from astropy.coordinates import EarthLocation
from astropy.coordinates import get_moon, SkyCoord
from astropy.time import Time
import astropy.units as u
import datetime
import numpy as np
from django.conf import settings as djangoSettings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
import random
import time
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import Range1d,Span,LinearAxis,Label,Title
from bokeh.core.properties import FontSizeSpec
from .data import PhotometryService, SpectraService, ObservingResourceService
import time
from .serializers import *
from rest_framework.request import Request
from django.contrib.auth.decorators import login_required, permission_required
import matplotlib.image as mpimg
import calendar
from astropy.table import Table
import sncosmo
from .common.bandpassdict import bandpassdict
from .common.utilities import date_to_mjd

py2bokeh_symboldict = {"^":"triangle",
					   "+":"cross",
					   "s":"square",
					   "*":"asterisk",
					   "D":"diamond",
					   "d":"diamond",
					   "o":"circle"}

def get_recent_phot_for_host(user, host_id=None):
	allowed_phot = PhotometryService.GetAuthorizedHostPhotometry_ByUser_ByHost(user, host_id)

	photdata = False
	for p in allowed_phot:
		photdata = HostPhotData.objects.filter(photometry=p.id).order_by('-obs_date')
	
	if photdata:
		return(photdata[0])
	else:
		return(None)

def get_all_phot_for_transient(user, transient_id=None):
	photdata = PhotometryService.GetAuthorizedTransientPhotData_ByUser_ByTransient(user, transient_id)

	if photdata:	
		return(photdata)
	else:
		return(None)

def get_recent_phot_for_transient(user, transient_id=None):
	photdata = get_all_phot_for_transient(user, transient_id)

	if photdata:
		photdata = photdata.order_by('-obs_date')
		return(photdata[0])
	else:
		return(None)

def get_disc_mag_for_transient(user, transient_id=None):
	photdata = PhotometryService.GetAuthorizedTransientPhotData_ByUser_ByTransient(user, transient_id)

	if photdata:
		photdata = photdata.order_by('-obs_date')

	firstphot = None
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

def get_obs_nights_happening_soon(user):
	allowed_nights = ObservingResourceService.GetAuthorizedClassicalObservingDate_ByUser(user)

	allowed_nights_happening_soon = []
	for an in allowed_nights:
		if an.happening_soon():
			allowed_nights_happening_soon.append(an)

	return allowed_nights_happening_soon

def get_too_resources(user):
	allowed_too_resource = ObservingResourceService.GetAuthorizedToOResource_ByUser(user)
	return allowed_too_resource

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

	
# def telescope_can_observe(ra,dec,date,lat,lon,elev,utc_off):
#	if date:
#		time = Time(date)
#	else:
#		time = Time(datetime.datetime.now())
#	sc = SkyCoord(ra,dec,unit=u.deg)
#
#	location = EarthLocation.from_geodetic(
#		lon*u.deg,lat*u.deg,
#		elev*u.m)
#	tel = Observer(location=location, timezone="UTC")
#
#	night_start = tel.twilight_evening_astronomical(time,which="previous")
#	night_end = tel.twilight_morning_astronomical(time,which="previous")
#	can_obs = False
#	for jd in np.arange(night_start.mjd,night_end.mjd,0.02):
#		time = Time(jd,format="mjd")
#		target_up = tel.target_is_up(time,sc,horizon=18*u.deg)
#		if target_up:
#			can_obs = True
#			break
#
#	return(can_obs)

class finder(TemplateView):
	template_name = 'YSE_App/finder.html'
	
	def __init__(self):
		pass
	def finderchart(self, request, transient_id, clobber=False):
		import os
		from .util import mkFinderChart

		from django.contrib.staticfiles.templatetags.staticfiles import static
		from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
		from matplotlib.figure import Figure
	
		transient = Transient.objects.get(pk=transient_id)
		basedir = "%sYSE_App/images/findercharts"%(djangoSettings.STATIC_ROOT)
		if not os.path.exists(basedir):
			os.makedirs(basedir)
		
		outputOffsetFileName = '%s/%s/%s.offsetstars.txt'%(
			basedir,transient.name,transient.name)
		outputFinderFileName = '%s/%s/%s.finder.png'%(
			basedir,transient.name,transient.name)
		if not os.path.exists(os.path.dirname(outputFinderFileName)):
			os.makedirs(os.path.dirname(outputFinderFileName))
		#if os.path.exists(outputOffsetFileName) and\
		#	os.path.exists(outputFinderFileName):
		#	return HttpResponseRedirect(reverse('transient_detail',
		#										args=(transient.id,)))

		find = mkFinderChart.finder()
		parser = find.add_options(usage='')
		options,  args = parser.parse_args()
		options.ra = str(transient.ra)
		options.dec = str(transient.dec)
		options.snid = transient.name
		options.outputOffsetFileName = outputOffsetFileName
		options.outputFinderFileName = outputFinderFileName
		find.options = options
		import pylab as plt

		fig=Figure()
		if not os.path.exists(options.outputFinderFileName) or \
		   not os.path.exists(options.outputOffsetFileName) or \
		   clobber:
			ax = fig.add_axes([0.2,0.3,0.6,0.6])
			canvas=FigureCanvas(fig)
			ax,offdictlist = find.mkChart(options.ra,options.dec,
										  options.outputFinderFileName,
										  ax=ax,saveImg=False,
										  clobber=clobber)
			fig.savefig(options.outputFinderFileName,dpi=1000)
		else:
			image = mpimg.imread(options.outputFinderFileName)
			ax = fig.add_axes([0,0,1,1])
			ax.set_xticks([]); ax.set_yticks([])
			canvas=FigureCanvas(fig)
			ax.imshow(image)

			offid,ra_str,dec_str,ra_off,dec_off,mag = \
				np.loadtxt(outputOffsetFileName,dtype='str',unpack=True)
			offdictlist = []
			for i in range(len(offid))[1:]:
				offdict = {'id':offid[i],
						   'ra':ra_str[i],
						   'dec':dec_str[i],
						   'ra_off':'%.3f'%float(ra_off[i]),
						   'dec_off':'%.3f'%float(dec_off[i]),
						   'mag':'%.3f'%float(mag[i])}
				offdictlist += [offdict]
			
		context = {'t':transient,
				   'offsets':offdictlist}
		
		#return response
		return render(request,'YSE_App/finder.html',
					  context)

	def finderim(self, request, transient_id, clobber=False):
		import os
		from .util import mkFinderChart
		from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
		from matplotlib.figure import Figure
		import pylab as plt
		transient = Transient.objects.get(pk=transient_id)
		basedir = "%sYSE_App/images/findercharts"%(djangoSettings.STATIC_ROOT)
		if not os.path.exists(basedir):
			os.makedirs(basedir)
		print(basedir)
		outputOffsetFileName = '%s/%s/%s.offsetstars.txt'%(
			basedir,transient.name,transient.name)
		outputFinderFileName = '%s/%s/%s.finder.png'%(
			basedir,transient.name,transient.name)
		if not os.path.exists(os.path.dirname(outputFinderFileName)):
			os.makedirs(os.path.dirname(outputFinderFileName))
		#if os.path.exists(outputOffsetFileName) and\
		#	os.path.exists(outputFinderFileName):
		#	return HttpResponseRedirect(reverse('transient_detail',
		#										args=(transient.id,)))

		
		find = mkFinderChart.finder()
		parser = find.add_options(usage='')
		options,  args = parser.parse_args()
		options.ra = str(transient.ra)
		options.dec = str(transient.dec)
		options.snid = transient.name
		options.outputOffsetFileName = outputOffsetFileName
		options.outputFinderFileName = outputFinderFileName
		find.options = options

		fig=Figure()
		if not os.path.exists(options.outputFinderFileName) or \
		   not os.path.exists(options.outputOffsetFileName) or \
		   clobber:
			ax = fig.add_axes([0.2,0.3,0.6,0.6])
			canvas=FigureCanvas(fig)
		
			ax,offdictlist = find.mkChart(options.ra,options.dec,
										  options.outputFinderFileName,
										  ax=ax,saveImg=True)
		else:
			image = mpimg.imread(options.outputFinderFileName)
			ax = fig.add_axes([0,0,1,1])
			ax.set_xticks([]); ax.set_yticks([])
			canvas=FigureCanvas(fig)
			ax.imshow(image)

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
	if night_end < night_start:
		night_end = tel.twilight_morning_astronomical(time,which="next")
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

def salt2plot(request, transient_id, salt2fit):

	response = lightcurveplot(request,transient_id,salt2=int(salt2fit))
	return response
	
def lightcurveplot(request, transient_id, salt2=False):
	tstart = time.time()

	transient = Transient.objects.get(pk=transient_id)
	photdata = get_all_phot_for_transient(request.user, transient_id)

	if not photdata:
		return django.http.HttpResponse('')

	ax=figure()

	mjd,salt2mjd,date,mag,magerr,flux,fluxerr,zpsys,salt2band,band,bandstr,bandcolor,bandsym = \
		np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),\
		np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),\
		np.array([]),np.array([]),np.array([])
	upperlimmjd,upperlimdate,upperlimmag,upperlimband,upperlimbandstr,upperlimbandcolor = \
		np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([])
	limmjd = None
	for p in photdata:
		if p.flux and np.abs(p.flux) > 1e10: continue
		if p.data_quality:
			continue			
			
		if p.mag:
			if p.discovery_point:
				limmjd = p.date_to_mjd()-30
				
			mjd = np.append(mjd,[p.date_to_mjd()])
			date = np.append(date,[p.obs_date.strftime('%m/%d/%Y')])
			mag = np.append(mag,[p.mag])
			if p.mag_err: magerr = np.append(magerr,p.mag_err)
			else: magerr = np.append(magerr,0)
			bandstr = np.append(bandstr,str(p.band))
			bandcolor = np.append(bandcolor,str(p.band.disp_color))
			if p.band.disp_symbol in py2bokeh_symboldict.keys():
				bandsym = np.append(bandsym,str(py2bokeh_symboldict[p.band.disp_symbol]))
			else:
				bandsym = np.append(bandsym,str(p.band.disp_symbol))
			band = np.append(band,p.band)
			if salt2:
				if str(p.band) in bandpassdict.keys():
					if p.mag_err: mag_err = p.mag_err
					else: mag_err = 0.02
					salt2mjd = np.append(salt2mjd,[p.date_to_mjd()])
					flux = np.append(flux,10**(-0.4*(p.mag-27.5)))
					fluxerr = np.append(fluxerr,p.mag*mag_err*0.4*np.log(10))
					salt2band = np.append(salt2band,bandpassdict[str(p.band)])
					if 'bessell' in bandpassdict[str(p.band)]: zpsys = np.append(zpsys,'Vega')
					else: zpsys = np.append(zpsys,'AB')
				
		elif p.flux and p.flux_zero_point and p.flux + 3*p.flux_err > 0:
			upperlimmjd = np.append(upperlimmjd,[p.date_to_mjd()])
			upperlimdate = np.append(upperlimdate,[p.obs_date.strftime('%m/%d/%Y')])
			upperlimmag = np.append(upperlimmag,[-2.5*np.log10(p.flux + 3*p.flux_err) + p.flux_zero_point])
			upperlimbandstr = np.append(upperlimbandstr,str(p.band))
			upperlimband = np.append(upperlimband,p.band)
			upperlimbandcolor = np.append(upperlimbandcolor,p.band.disp_color)
			if salt2:
				if str(p.band) in bandpassdict.keys():
					salt2mjd = np.append(salt2mjd,[p.date_to_mjd()])
					flux = np.append(flux,p.flux)
					fluxerr = np.append(fluxerr,p.flux_err)
					salt2band = np.append(salt2band,bandpassdict[str(p.band)])
					if 'bessell' in bandpassdict[str(p.band)]: zpsys = np.append(zpsys,'Vega')
					else: zpsys = np.append(zpsys,'AB')

	if transient.non_detect_limit and transient.non_detect_band:
		upperlimmjd = np.append(upperlimmjd,[date_to_mjd(transient.non_detect_date)])
		upperlimdate = np.append(upperlimdate,[transient.non_detect_date.strftime('%m/%d/%Y')])
		upperlimmag = np.append(upperlimmag,transient.non_detect_limit)
		upperlimbandstr = np.append(upperlimbandstr,str(transient.non_detect_band))
		upperlimband = np.append(upperlimband,transient.non_detect_band)
		upperlimbandcolor = np.append(upperlimbandcolor,transient.non_detect_band.disp_color)
		
	ax.title.text = "%s"%transient.name
	#colorlist = ['#1f77b4','#ff7f0e','#2ca02c','#d62728',
	#			 '#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
	colorlist = ['#8dd3c7','#ffffb3','#bebada','#fb8072','#80b1d3','#fdb462','#b3de69','#fccde5','#d9d9d9']
	count = 0
	allband = np.append(band,upperlimband)
	allbandstr = np.append(bandstr,upperlimbandstr)
	allbandcolor = np.append(bandcolor,upperlimbandcolor)
	allbandsym = np.append(bandsym,[None]*len(upperlimbandcolor))
	bandunq,idx = np.unique(allbandstr,return_index=True)
	for bs,b,bc,bsym in zip(bandunq,allband[idx],allbandcolor[idx],allbandsym[idx]):
		if bc != 'None' and bc: color = bc
		else:
			coloridx = count % len(np.unique(colorlist))
			color = colorlist[coloridx]
			count += 1

		if bsym and bsym != 'inverted_triangle':
			try:
				plotmethod = getattr(ax, bsym)
			except:
				plotmethod = getattr(ax, 'circle')
		else:
			plotmethod = getattr(ax, 'circle')
			
		plotmethod(mjd[bandstr == bs].tolist(),mag[bandstr == bs].tolist(),
				   color=color,size=7,legend='%s - %s'%(
					   b.instrument.telescope.name,b.name))
		if len(upperlimbandstr) and len(upperlimmjd[upperlimbandstr == bs]):
			ax.inverted_triangle(upperlimmjd[upperlimbandstr == bs].tolist(),upperlimmag[upperlimbandstr == bs].tolist(),
								 color=color,size=7,legend='%s - %s'%(
									 b.instrument.telescope.name,b.name))

		err_xs,err_ys = [],[]
		for x,y,yerr in zip(mjd[bandstr == bs].tolist(),mag[bandstr == bs].tolist(),magerr[bandstr == bs].tolist()):
			err_xs.append((x, x))
			err_ys.append((y - yerr, y + yerr))
		ax.multi_line(err_xs, err_ys, color=color, legend='%s - %s'%(
					  b.instrument.telescope.name,b.name))

	today = Time(datetime.datetime.today()).mjd
	ax.line(today,20,line_width=3,line_color='black',legend='today (%i)'%today)
	vline = Span(location=today, dimension='height', line_color='black',
				 line_width=3)
	ax.add_layout(vline)
	ax.legend.location = 'bottom_left'
	ax.legend.label_height = 1
	ax.legend.glyph_height = 5

	ax.legend.label_text_font_size = "4pt"#FontSizeSpec("10")
	ax.legend.click_policy="hide"

	
	ax.xaxis.axis_label = 'MJD'
	ax.yaxis.axis_label = 'Mag'

	if limmjd:
		ax.x_range = Range1d(limmjd,np.max(mjd)+10)
		ax.y_range = Range1d(np.max(np.append(mag[mjd > limmjd],upperlimmag[upperlimmjd > limmjd]))+0.25,
							 np.min(mag[mjd > limmjd])-0.5)
		ax.extra_x_ranges = {"dateax": Range1d(limmjd,np.max(mjd)+10)}
		ax.add_layout(LinearAxis(x_range_name="dateax"), 'above')
		
	else:
		ax.x_range=Range1d(np.min(mjd)-10,np.max(mjd)+10)
		ax.y_range=Range1d(np.max(np.append(mag,upperlimmag))+0.25,np.min(mag)-0.5)
		ax.extra_x_ranges = {"dateax": Range1d(np.min(mjd)-10,np.max(mjd)+10)}
		ax.add_layout(LinearAxis(x_range_name="dateax"), 'above')
		#ax.legend()
	ax.plot_height = 400
	ax.plot_width = 500

	majorticks = []; overridedict = {}
	mjdrange = range(int(np.min(mjd)-100),int(np.max(mjd)+100))
	times = Time(mjdrange,format='mjd')
	if (not limmjd and np.max(mjd)+10 - (np.min(mjd)-10) > 300) or \
	   (limmjd and np.max(mjd)+10 - limmjd > 300):
		count = 0
		for m,t in zip(mjdrange,times):
			tm_list = t.iso.split()[0].split('-')
			if tm_list[2] == '01': count += 1
			if count % 3: continue
			if tm_list[2] == '01':
				majorticks += [m]
				overridedict[m] = '%s %i, %i'%(calendar.month_name[int(tm_list[1])][:3],int(tm_list[2]),int(tm_list[0]))
	else:
		for m,t in zip(mjdrange,times):
			tm_list = t.iso.split()[0].split('-')
			if tm_list[2] == '01':
				majorticks += [m]
				overridedict[m] = '%s %i, %i'%(calendar.month_name[int(tm_list[1])][:3],int(tm_list[2]),int(tm_list[0]))

	ax.xaxis[0].ticker = majorticks
	ax.xaxis[0].major_label_overrides = overridedict
	
	if salt2:
		model = sncosmo.Model(source='salt2')
		if transient.redshift:
			model.set(z=transient.redshift); fitparams = ['t0', 'x0', 'x1', 'c']
		elif transient.host and transient.host.redshift:
			model.set(z=transient.host.redshift); fitparams = ['t0', 'x0', 'x1', 'c']
		else: fitparams = ['z', 't0', 'x0', 'x1', 'c']
			
		zp = np.array([27.5]*len(salt2band))
		data = Table([salt2mjd,salt2band,flux,fluxerr,zp,zpsys],names=['mjd','band','flux','fluxerr','zp','zpsys'],meta={'t0':salt2mjd[flux == np.max(flux)]})

		result, fitted_model = sncosmo.fit_lc(
			data, model, fitparams,
			bounds={'t0':(salt2mjd[flux == np.max(flux)]-10, salt2mjd[flux == np.max(flux)]+10),
					'z':(0.0,0.7),'x1':(-3,3),'c':(-0.3,0.3)})	# bounds on parameters (if any)
		
		count = 0
		plotmjd = np.arange(result['parameters'][1]-20,result['parameters'][1]+50,0.5)
		bandunq,idx = np.unique(bandstr,return_index=True)
		for bs,b,bc in zip(bandunq,band[idx],bandcolor[idx]):
			if bc != 'None' and bc:
				color = bc
			else:
				coloridx = count % len(np.unique(colorlist))
				color = colorlist[coloridx]
				count += 1
				
			if bs in bandpassdict.keys() and bandpassdict[bs] in salt2band:
				salt2flux = fitted_model.bandflux(bandpassdict[bs], plotmjd, zp=27.5,zpsys=zpsys[bandpassdict[bs] == salt2band][0])
				ax.line(plotmjd,-2.5*np.log10(salt2flux)+27.5,color=color)

		lcphase = today-result['parameters'][1]
		if lcphase > 0: lcphase = '+%.1f'%(lcphase)
		else: lcphase = '%.1f'%(lcphase)
		latex1 = Label(x=10,y=280,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="phase = %s days"%(
						   lcphase))
		latex2 = Label(x=10,y=265,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="\uD835\uDE3B  = %.3f"%(result.parameters[0]))
		latex3 = Label(x=10,y=250,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="\uD835\uDC61\u2080	 = %i"%(result['parameters'][1]))
		latex4 = Label(x=10,y=235,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="\uD835\uDC5A\u2088 = %.2f"%(10.635-2.5*np.log10(result['parameters'][2])))
		latex5 = Label(x=10,y=220,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="\uD835\uDC65\u2081 = %.2f"%(result['parameters'][3]))
		latex6 = Label(x=10,y=205,x_units='screen',y_units='screen',
					   render_mode='css', text_font_size='10pt',
					   text="\uD835\uDC50  = %.2f"%(result['parameters'][4]))
		for latex in [latex1,latex2,latex3,latex4,latex5,latex6]:
			ax.add_layout(latex)

	g = file_html(ax,CDN,"my plot")
	return HttpResponse(g.replace('width: 90%','width: 100%'))

def spectrumplot(request, transient_id):
	tstart = time.time()
	transient = Transient.objects.get(pk=transient_id)
	spectrum = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(request.user, transient_id)

	if not len(spectrum):
		return django.http.HttpResponse('')
	else:
		spectrum = spectrum[0]
	spec = TransientSpecData.objects.filter(spectrum=spectrum)
	
	if not len(spec):
		return django.http.HttpResponse('')

	ax=figure()

	wave,flux = [],[]
	for s in spec:
		wave += [s.wavelength]
		flux += [s.flux]
	ax.line(np.sort(wave),np.array(flux)[np.argsort(wave)],color='black')

	ax.title.text = "%s, %s, %s, Phase: %s"%(transient.name,spectrum.obs_date.strftime('%m/%d/%Y'),spectrum.instrument,spectrum.spec_phase)
	ax.xaxis.axis_label = r'Wavelength (Angstrom)'
	ax.yaxis.axis_label = 'Flux'
	g = file_html(ax,CDN,"my plot")

	return HttpResponse(g.replace('width: 90%','width: 100%'))

def spectrumplotsingle(request, transient_id, spec_id):

	#import pdb; pdb.set_trace()
	
	#transient_id = request.GET.get('transient_id')
	#spec_id = request.GET.get('spec_id')
	
	tstart = time.time()
	print(transient_id,spec_id)
	transient = Transient.objects.get(pk=transient_id)
	spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(request.user, transient_id)
	spectrum = spectra.filter(id=spec_id)
	
	if not len(spectrum):
		return django.http.HttpResponse('')
	else:
		spectrum = spectrum[0]
	spec = TransientSpecData.objects.filter(spectrum=spectrum)
	
	if not len(spec):
		return django.http.HttpResponse('')

	ax=figure()

	wave,flux = [],[]
	for s in spec:
		wave += [s.wavelength]
		flux += [s.flux]
	ax.line(np.sort(wave),np.array(flux)[np.argsort(wave)],color='black')
		
	ax.title.text = "%s, %s, %s, Phase: %s"%(transient.name,spectrum.obs_date.strftime('%m/%d/%Y'),spectrum.instrument,spectrum.spec_phase)
	ax.xaxis.axis_label = r'Wavelength (Angstrom)'
	ax.yaxis.axis_label = 'Flux'
	g = file_html(ax,CDN,"my plot")

	return HttpResponse(g.replace('width: 90%','width: 100%'))

def rise_time(request,transient_id,obs_id):

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

def get_hst_image(request,transient_id):
	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")

	startTime = datetime.datetime.now()
	from . import common
	hst=common.mast_query.hstImages(t.ra,t.dec,'Object')
	hst.getObstable()
	hst.getJPGurl()
	print("I found",hst.Nimages,"HST images of",hst.object,"located at coordinates",hst.ra,hst.dec)
	print("The cut out images have the following URLs:")
	fitsurllist = []
	for jpg,i in zip(hst.jpglist,range(len(hst.jpglist))):
		print(jpg)
		fitsurllist += ["https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&amp;dataset=%s"%str(hst.obstable["obs_id"][i]).lower()]
	print("Run time was: ",(datetime.datetime.now() - startTime).total_seconds(),"seconds")

	if len(hst.jpglist):
		jpegurldict = {"jpegurl":hst.jpglist,
					   "fitsurl":fitsurllist,#list(hst.obstable["dataURL"]),
					   "obsdate":list(Time(hst.obstable["t_min"],format='mjd',out_subfmt='date').iso),
					   "filters":list(hst.obstable["filters"]),
					   "inst":list(hst.obstable["instrument_name"])}
	else:
		jpegurldict = {"jpegurl":[],
					   "fitsurl":[],
					   "obsdate":[],
					   "filters":[],
					   "inst":[]}

	return(JsonResponse(jpegurldict))

def get_chandra_image(request,transient_id):
	
	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")

	startTime = datetime.datetime.now()
	from . import common
	chr=common.chandra_query.chandraImages(t.ra,t.dec,'Object')
	chr.search_chandra_database()
	print("I found",chr.n_obsid,"Chandra images")
	print("The cut out images have the following URLs:")

	#fitsurllist = []
	#for jpg,i in zip(chr.jpglist,range(len(chr.jpglist))):
	#	print(jpg)
	#	fitsurllist += ["https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&amp;dataset=%s"%str(chr.obstable["obs_id"][i]).lower()]
	print("Run time was: ",(datetime.datetime.now() - startTime).total_seconds(),"seconds")

	if len(chr.jpegs):
		jpegurldict = {"jpegurl":list(chr.jpegs.data.astype(str)),
					   "fitsurl":list(chr.images.data.astype(str)),
					   "obsdate":list(chr.obs_dates.data.astype(str)),
					   "exptime":list(chr.exp_times.data.astype(str)),
					   "totalexp":chr.total_exp}
	else:
		jpegurldict = {"jpegurl":[],
					   "fitsurl":[],
					   "obsdate":[],
					   "exptime":[],
					   "totalexp":0}

	return(JsonResponse(jpegurldict))


def get_legacy_image(request,transient_id):
	
	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")

	jpegurl = "http://legacysurvey.org/viewer/jpeg-cutout?ra=%.7f&dec=%.7f&layer=decals-dr5&pixscale=0.27&bands=grz"%(
		t.ra,t.dec)

	fitsurl = "http://legacysurvey.org/viewer/fits-cutout?ra=%.7f&dec=%.7f&layer=decals-dr5&pixscale=0.27&bands=grz"%(
		t.ra,t.dec)
	
	print(jpegurl,fitsurl)
	jpegurldict = {"jpegurl":jpegurl,
				   "fitsurl":fitsurl}

	return(JsonResponse(jpegurldict))

def delta_too_hours(request,transient_id,too_id):
	too = ToOResource.objects.get(id=too_id)
	diff = (too.awarded_too_hours - too.used_too_hours)

	diffdict = {'delta_too_hours': diff}
	return JsonResponse(diffdict)

def get_authorized_classical_resources(user):
	allowed_resources = ObservingResourceService.GetAuthorizedClassicalResource_ByUser(user)

	return allowed_resources

def get_authorized_too_resources(user):
	allowed_resources = ObservingResourceService.GetAuthorizedToOResource_ByUser(user)

	return allowed_resources

def get_authorized_queued_resources(user):
	allowed_resources = ObservingResourceService.GetAuthorizedQueuedResource_ByUser(user)

	return allowed_resources

def get_authorized_phot_resources(user):
	allowed_resources = PhotometryService.GetAuthorizedTransientPhotometry_ByUser(user)

	return allowed_resources

