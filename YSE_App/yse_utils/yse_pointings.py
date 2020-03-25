import astropy.coordinates as cd
import astropy.units as u
import numpy as np
from YSE_App.models import *
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response
from YSE_App.common.utilities import GetSexigesimalString
from matplotlib.patches import Rectangle
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
from YSE_App.table_utils import TransientTable,TransientFilter
from YSE_App.queries.yse_python_queries import *
from django_tables2 import RequestConfig
from django.shortcuts import redirect

def get_yse_pointings_base(field_name,snid):

	sf = SurveyField.objects.filter(field_id=field_name)[0]
	sc = cd.SkyCoord(sf.ra_cen,sf.dec_cen,unit=u.deg)
	transient = Transient.objects.filter(name=snid)[0]
	sc_transient = cd.SkyCoord(transient.ra,transient.dec,unit=u.deg)
	
	d = sc.dec.deg*np.pi/180 #self.coord.dec.radian
	width_corr = 1.55/np.abs(np.cos(d))
	# Define the tile offsets:
	ra_offset = cd.Angle(width_corr, unit=u.deg)
	dec_offset = cd.Angle(3.1/2., unit=u.deg)
	
	# 6 pointings, spaced in usual way
	PS_SW = cd.SkyCoord(sc.ra - ra_offset, sc.dec - dec_offset)
	PS_NW = cd.SkyCoord(sc.ra - ra_offset, sc.dec + dec_offset)
	PS_SE = cd.SkyCoord(sc.ra + ra_offset, sc.dec - dec_offset)
	PS_NE = cd.SkyCoord(sc.ra + ra_offset, sc.dec + dec_offset)
	# last two are further over in RA
	PS_SE2 = cd.SkyCoord(sc.ra + ra_offset*3, sc.dec - dec_offset)
	PS_NE2 = cd.SkyCoord(sc.ra + ra_offset*3, sc.dec + dec_offset)

	#import pdb; pdb.set_trace()
	
	# try to move a field up/down to accommodate SN
	suggested_pointings = []
	suggested_pointing_names = []
	ra_adj,dec_adj = None,0
	sep_list = []
	for pointing in [PS_SW,PS_NW,PS_SE,PS_NE,PS_SE2,PS_NE2]:
		sep_list += [sc_transient.separation(pointing).deg]
	sep_list = np.array(sep_list)
	for pointing,name,pointing_name,sep in zip([PS_SW,PS_NW,PS_SE,PS_NE,PS_SE2,PS_NE2],
											   ['PS_SW','PS_NW','PS_SE','PS_NE','PS_SE2','PS_NE2'],
											   ['A','B','C','D','E','F'],sep_list):
		#print(sep)
		#if abs(sep - np.min(sep_list)) > 1e-4:
		#	suggested_pointings += [pointing]
		#	suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]
		#	continue
		#if sep < 1.55:
		dra,ddec = sc_transient.spherical_offsets_to(pointing)
		print(dra.deg,ddec.deg)
		if abs(dra.deg) < 1.45 and abs(ddec.deg) < 1.45:
			if sep > 0.4:
				# pointing is good as is
				suggested_pointings += [pointing]
				suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]
				continue
			else:
				# can we move up or down to put this at a
				# reasonable radius from center?
				#ra_offset = (sc_transient.ra.deg-pointing.ra.deg)/np.abs(np.cos(sc_transient.dec.deg))
				#dec_offset = np.sqrt(0.75**2.-ra_offset**2.)
				if 'PS_N' in name:
					dec_offset = 0.75 - ddec.deg
					new_pointing = cd.SkyCoord(pointing.ra.deg,pointing.dec.deg+dec_offset,unit=u.deg)
				if 'PS_S' in name:
					dec_offset = 0.75 + ddec.deg
					new_pointing = cd.SkyCoord(pointing.ra.deg,pointing.dec.deg-dec_offset,unit=u.deg)
				# verify that this worked
				if sc_transient.separation(new_pointing).deg > 0.4 and sc_transient.separation(new_pointing).deg < 1:
					suggested_pointings += [new_pointing]
					suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]
				else: raise Http404('Something went wrong!')
				#import pdb; pdb.set_trace()
		elif abs(dra.deg) > 1.45 and abs(dra.deg) < 1.55:
			# really don't want SNe right near the edge
			ra_offset = dra.deg - 1.35
			#import pdb; pdb.set_trace()
			if ra_adj is None:
				if dra.deg > 1.45:
					ra_adj = -0.4
				elif dra.deg < -1.45:
					ra_adj = 0.4
			suggested_pointings += [pointing]
			suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]
		elif abs(ddec.deg) > 1.45 and abs(ddec.deg) < 1.55:
			ra_offset = (sc_transient.ra.deg-pointing.ra.deg)/np.abs(np.cos(sc_transient.dec.deg))
			dec_offset = np.sqrt(0.75**2.-ra_offset**2.)
			if 'PS_N' in name: new_pointing = cd.SkyCoord(pointing.ra.deg,pointing.dec.deg+dec_offset,unit=u.deg)
			if 'PS_S' in name: new_pointing = cd.SkyCoord(pointing.ra.deg,pointing.dec.deg-dec_offset,unit=u.deg)
			# verify that this worked
			if sc_transient.separation(new_pointing).deg > 0.4 and sc_transient.separation(new_pointing).deg < 1:
				suggested_pointings += [new_pointing]
				suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]
			else: raise Http404('Something went wrong!')
		else:
			suggested_pointings += [pointing]
			suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%pointing_name]

		#print('hi',sep,dra.deg,ddec.deg)
		if ((abs(dra.deg) < 1.55 and abs(ddec.deg) < 1.55) or abs(sep - np.min(sep_list)) < 1e-4) \
		   and (abs(dra.deg) > 1.05 or abs(ddec.deg) > 1.05):
			# four corners at +0.75,+0.75 deg, +0.75,-0.75, etc etc
			d = pointing.dec.deg*np.pi/180 #self.coord.dec.radian
			width_corr = 0.75/np.abs(np.cos(d))

			ra_offset = cd.Angle(width_corr, unit=u.deg)
			dec_offset = cd.Angle(0.75, unit=u.deg)
	
			# 6 pointings, spaced in usual way
			SW = cd.SkyCoord(sc_transient.ra - ra_offset, sc_transient.dec - dec_offset)
			NW = cd.SkyCoord(sc_transient.ra - ra_offset, sc_transient.dec + dec_offset)
			SE = cd.SkyCoord(sc_transient.ra + ra_offset, sc_transient.dec - dec_offset)
			NE = cd.SkyCoord(sc_transient.ra + ra_offset, sc_transient.dec + dec_offset)
			sep1 = pointing.separation(SW).deg
			sep2 = pointing.separation(NW).deg
			sep3 = pointing.separation(SE).deg
			sep4 = pointing.separation(NE).deg
			if sep1 == np.min([sep1,sep2,sep3,sep4]):
				ddra,dddec = pointing.spherical_offsets_to(SW)
			elif sep2 == np.min([sep1,sep2,sep3,sep4]):
				ddra,dddec = pointing.spherical_offsets_to(NW)
			elif sep3 == np.min([sep1,sep2,sep3,sep4]):
				ddra,dddec = pointing.spherical_offsets_to(SE)
			elif sep4 == np.min([sep1,sep2,sep3,sep4]):
				ddra,dddec = pointing.spherical_offsets_to(NE)
			ra_adj,dec_adj = ddra.deg,dddec.deg
			#import pdb; pdb.set_trace()
		print(ddec.deg)
			
	# if necessary, move all fields right or left
	# to accomodate SN
	if ra_adj:
		new_suggested_pointings = []
		new_suggested_pointing_names = []
		for p,n in zip(suggested_pointings,['A','B','C','D','E','F']):
			new_suggested_pointings += [cd.SkyCoord(p.ra.deg+ra_adj,p.dec.deg+dec_adj,unit=u.deg)]
			new_suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%n]
		suggested_pointings = new_suggested_pointings
		suggested_pointing_names = new_suggested_pointing_names
	# if necessary, move all fields up or down
	# to accomodate SN
	#if dec_adj:
	#	new_suggested_pointings = []
	#	new_suggested_pointing_names = []
	#	for p,n in zip(suggested_pointings,['A','B','C','D','E','F']):
	#		new_suggested_pointings += [cd.SkyCoord(p.ra.deg,p.dec.deg_dec_adj,unit=u.deg)]
	#		new_suggested_pointing_names += [field_name.replace('ZTF.','')+'.%s'%n]
	#	suggested_pointings = new_suggested_pointings
	#	suggested_pointing_names = new_suggested_pointing_names

		
	# check that new pointings don't overlap
	# with any existing pointings
	for p in suggested_pointings:
		d = p.dec.deg*np.pi/180
		width_corr = 3.1/np.abs(np.cos(d))
		# Define the tile offsets:
		ra_offset = cd.Angle(width_corr/2., unit=u.deg)
		dec_offset = cd.Angle(3.1/2., unit=u.deg)
		
		sf_test = SurveyField.objects.filter(~Q(obs_group__name='ZTF')).\
			filter((Q(ra_cen__gt = p.ra.deg-ra_offset.degree) &
					Q(ra_cen__lt = p.ra.deg+ra_offset.degree) &
					Q(dec_cen__gt = p.dec.deg-dec_offset.degree) &
					Q(dec_cen__lt = p.dec.deg+dec_offset.degree)))
		if len(sf_test):
			raise Http404('Suggested pointing overlaps with field %s'%sf_test[0].field_id)


	# check that one pointings is at the right position
	good_pointing_exists = False
	for p in suggested_pointings:
		dra,ddec = sc_transient.spherical_offsets_to(p)
		if np.abs(dra.deg) < 1.45 and np.abs(ddec.deg) < 1.45:
			good_pointing_exists = True

	if not good_pointing_exists:
		raise Http404('can\'t find the right pointings for this transient')

	# generate a plot of what the pointings look like?
	# this can be done in template

    # formatting stuff
	pointings_for_html = ()
	for p,n in zip(suggested_pointings,suggested_pointing_names):
		dra,ddec = sc_transient.spherical_offsets_to(p)
		pointings_for_html += ((n,GetSexigesimalString(
			p.ra.deg,p.dec.deg)[0],GetSexigesimalString(p.ra.deg,p.dec.deg)[1],
								'%.2f'%dra.deg,'%.2f'%ddec.deg),)


	return suggested_pointings,suggested_pointing_names,pointings_for_html,transient,sf

def get_yse_pointings(request,field_name,snid):

	suggested_pointings,suggested_pointing_names,pointings_for_html,transient,sf = get_yse_pointings_base(field_name,snid)
	
	# hand off the suggested IDs, RAs, Decs
	context = {'pointings':pointings_for_html,
			   'transient':transient,
			   'ztf_field':sf
	}
	return render(request, 'YSE_App/yse_pointings.html', context)

def yse_pointing_plot(request,field_name,snid):

	suggested_pointings,suggested_pointing_names,pointings_for_html,transient,sf = get_yse_pointings_base(
		field_name,snid)

	rcParams['figure.figsize'] = (12,6)
	fig=Figure()#dpi=288,figsize=(1,1))
	ax=fig.add_subplot(111)
	#ax=fig.add_axes([0.2,0.2,0.75,0.65])
	canvas=FigureCanvas(fig)

	ra,dec = [],[]
	for p,n in zip(suggested_pointings,suggested_pointing_names):
		d = p.dec.deg*np.pi/180
		width_corr = 3.1/np.abs(np.cos(d))
		rect = Rectangle(xy=[p.ra.deg-width_corr/2.,p.dec.deg-1.55],width=width_corr,height=3.1,fill=False,lw=5)
		ax.add_artist(rect)
		ax.text(p.ra.deg,p.dec.deg,n,ha='center',va='center',fontsize=25)
		ra += [p.ra.deg]
		dec += [p.dec.deg]
		
	ax.plot(transient.ra,transient.dec,'+',ms=30,mew=5,zorder=100,color='r')
	ax.text(transient.ra-width_corr/10.,transient.dec+0.15,snid,color='r',fontsize=25,ha='left',va='bottom')
	ax.set_xlim([np.max(ra)+5,np.min(ra)-5])
	ax.set_ylim([np.min(dec)-2,np.max(dec)+2])
	ax.set_xlabel(r'$\alpha$',fontsize=15)
	ax.set_ylabel(r'$\delta$',fontsize=15)
	
	response=HttpResponse(content_type='image/png')
	canvas.print_jpg(response)
	return response

def adjust_yse_pointings(request,field_name,snid):

	new_pointing,pointings,pointing_names,pointings_for_html,new_pointing_for_html,transient,sf = adjust_yse_pointings_base(field_name,snid)

	field_name = field_name.split('.')[0]
	surveyfields = SurveyField.objects.filter(ztf_field_id = field_name).filter(~Q(obs_group__name='ZTF'))
	all_pointings,all_pointing_names = [],[]
	for s in surveyfields:
		all_pointings += [SkyCoord(s.ra_cen,s.dec_cen,unit=u.deg)]
		all_pointing_names += [s.field_id]
	
	tables = []
	for p,n in zip(all_pointings,all_pointing_names):
		transients = sne_in_yse_field_with_ignore(n)

		transientfilter = TransientFilter(request.GET, queryset=transients,prefix=n.replace('.',''))
		table = TransientTable(transientfilter.qs,prefix=n.replace('.',''))
		RequestConfig(request, paginate={'per_page': 10}).configure(table)
		tables += [(table,n,n.replace('.',''),transientfilter,n,p.ra.deg,p.dec.deg)]
	#	import pdb; pdb.set_trace()
	# hand off the suggested IDs, RAs, Decs
	context = {'pointings':pointings_for_html,
			   'new_pointing':new_pointing_for_html,
			   'pointing_names':pointing_names,
			   'transient':transient,
			   'ztf_field':sf,
			   'pointings_good_flag': False,
			   'transient_categories':tables,
			   'transient_field_name':'%s.%s'%(field_name,snid)
	}
	return render(request, 'YSE_App/yse_adjusted_pointings.html', context)

def adjust_yse_pointings_plot(request,field_name,snid):

	new_pointing,pointings,pointing_names,pointings_for_html,new_pointing_for_html,transient,sf = adjust_yse_pointings_base(field_name,snid)

	rcParams['figure.figsize'] = (12,6)
	fig=Figure()#dpi=288,figsize=(1,1))
	ax=fig.add_subplot(111)
	#ax=fig.add_axes([0.2,0.2,0.75,0.65])
	canvas=FigureCanvas(fig)

	ra,dec = [],[]
	for p,n in zip(pointings,pointing_names):
		d = p.dec.deg*np.pi/180
		width_corr = 3.1/np.abs(np.cos(d))
		rect = Rectangle(xy=[p.ra.deg-width_corr/2.,p.dec.deg-1.55],width=width_corr,height=3.1,fill=False,lw=5)
		ax.add_artist(rect)
		ax.text(p.ra.deg,p.dec.deg,n,ha='center',va='center',fontsize=25)
		ra += [p.ra.deg]
		dec += [p.dec.deg]

	if new_pointing is not None:
		for p in [new_pointing]:
			d = p.dec.deg*np.pi/180
			width_corr = 3.1/np.abs(np.cos(d))
			rect = Rectangle(xy=[p.ra.deg-width_corr/2.,p.dec.deg-1.55],width=width_corr,height=3.1,fill=False,lw=5,color='b')
			ax.add_artist(rect)
			ax.text(p.ra.deg,p.dec.deg+1.85,'%s.%s'%(field_name,snid),ha='center',va='center',fontsize=25,color='b')
			ra += [p.ra.deg]
			dec += [p.dec.deg]
		
	ax.plot(transient.ra,transient.dec,'+',ms=30,mew=5,zorder=100,color='r')
	#ax.text(transient.ra-width_corr/10.,transient.dec+0.15,snid,color='r',fontsize=25,ha='left',va='bottom')
	ax.set_xlim([np.max(np.append(ra,transient.ra))+5,np.min(np.append(ra,transient.ra))-5])
	ax.set_ylim([np.min(np.append(dec,transient.dec))-2,np.max(np.append(dec,transient.dec))+2])
	ax.set_xlabel(r'$\alpha$',fontsize=15)
	ax.set_ylabel(r'$\delta$',fontsize=15)
	
	response=HttpResponse(content_type='image/png')
	canvas.print_jpg(response)
	return response

def adjust_yse_pointings_base(field_name,snid):

	# cases
	# 1. SN is already being observed
	# 2. SN is not being observed, can test 4 candidate pointings - SN 0.75 deg N/S/E/W of pointing center
	#    the first of these that doesn't overlap with any other blocks can be used
	# 3. if all of them overlap, this is a very weird edge case that I don't really want to address right now

	# report SNe w/i last 3 months - both all and "not Ignore" in each block
	# report best location for new block
	field_name = field_name.split('.')[0]
	surveyfields = SurveyFieldMSB.objects.filter(name=field_name)[0].survey_fields.all()
	#surveyfields = SurveyField.objects.filter(ztf_field_id = field_name).filter(~Q(obs_group__name='ZTF'))
	pointings,pointing_names = [],[]
	for s in surveyfields:
		pointings += [SkyCoord(s.ra_cen,s.dec_cen,unit=u.deg)]
		pointing_names += [s.field_id]
		
	transient = Transient.objects.filter(name=snid)[0]
	sc_transient = cd.SkyCoord(transient.ra,transient.dec,unit=u.deg)

	good_pointing_exists = False
	ra_adj = None
	for p in pointings:
		dra,ddec = sc_transient.spherical_offsets_to(p)
		if np.abs(dra.deg) < 1.55 and np.abs(ddec.deg) < 1.55:
			# SN is already getting observed
			good_pointing_exists = True

	if good_pointing_exists:
		pointings_for_html = ()
		for p,n in zip(pointings,pointing_names):
			dra,ddec = sc_transient.spherical_offsets_to(p)
			pointings_for_html += ((n,GetSexigesimalString(
				p.ra.deg,p.dec.deg)[0],GetSexigesimalString(p.ra.deg,p.dec.deg)[1],
									'%.2f'%dra.deg,'%.2f'%ddec.deg,p.ra.deg,p.dec.deg),)
		
		return None,pointings,pointing_names,pointings_for_html,None,transient,surveyfields[0].ztf_field_id

		# hand off the suggested IDs, RAs, Decs
		#context = {'pointings':pointings_for_html,
		#		   'transient':transient,
		#		   'ztf_field':sf,
		#		   'pointings_good_flag': True
		#}
		#return render(request, 'YSE_App/yse_pointings.html', context)

	# test 4 candidate positions for new SN block
	d = sc_transient.dec.deg*np.pi/180 #self.coord.dec.radian
	width_corr = 0.75/np.abs(np.cos(d))
	# Define the tile offsets:
	ra_offset = cd.Angle(width_corr, unit=u.deg)
	dec_offset = cd.Angle(0.75, unit=u.deg)

	newPS_S = SkyCoord(sc_transient.ra.deg,sc_transient.dec.deg-dec_offset.deg,unit=u.deg)
	newPS_N = SkyCoord(sc_transient.ra.deg,sc_transient.dec.deg+dec_offset.deg,unit=u.deg)
	newPS_E = SkyCoord(sc_transient.ra.deg+ra_offset.deg,sc_transient.dec.deg,unit=u.deg)
	newPS_W = SkyCoord(sc_transient.ra.deg-ra_offset.deg,sc_transient.dec.deg,unit=u.deg)
	good_new_pointings = []
	min_seps = []
	for new_pointing in [newPS_S,newPS_N,newPS_E,newPS_W]:
		good = True
		sep_list = []
		for p in pointings:
			sep = new_pointing.separation(p).deg
			dra,ddeg = new_pointing.spherical_offsets_to(p)
			sep_list += [sep]
			if np.abs(dra.deg) < 3.1 and np.abs(ddec.deg) < 3.1:
				good = False
				break
		if good:
			good_new_pointings += [new_pointing]
			min_seps += [min(sep_list)]
	#import pdb; pdb.set_trace()
	if not len(good_new_pointings):
		new_pointing = None #raise Http404('can\'t find a good pointing')
	else:
		new_pointing = np.array(good_new_pointings)[np.array(min_seps) == np.min(min_seps)][0]
	
    # formatting stuff
	pointings_for_html = ()
	for p,n in zip(pointings,pointing_names):
		dra,ddec = sc_transient.spherical_offsets_to(p)
		pointings_for_html += ((n,GetSexigesimalString(
			p.ra.deg,p.dec.deg)[0],GetSexigesimalString(p.ra.deg,p.dec.deg)[1],
								'%.2f'%dra.deg,'%.2f'%ddec.deg,p.ra.deg,p.dec.deg),)

	if new_pointing is not None:
		for p in [new_pointing]:
			dra,ddec = sc_transient.spherical_offsets_to(p)
			new_pointing_for_html = ('%s.%s'%(field_name.split('.')[0],transient.name),GetSexigesimalString(
				p.ra.deg,p.dec.deg)[0],GetSexigesimalString(p.ra.deg,p.dec.deg)[1],
									 '%.2f'%dra.deg,'%.2f'%ddec.deg,p.ra.deg,p.dec.deg)
	else:
		new_pointing_for_html = None
		
	return new_pointing,pointings,pointing_names,pointings_for_html,new_pointing_for_html,transient,surveyfields[0].ztf_field_id
