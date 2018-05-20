import django
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response
from .models import *
from django.db import models
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
from .data import PhotometryService, SpectraService, ObservingResourceService
from .serializers import *
from rest_framework.request import Request
from django.contrib.auth.decorators import login_required, permission_required
import json
from .basicauth import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

@csrf_exempt
@login_or_basic_auth_required
def add_transient_phot(request):
	phot_data = JSONParser().parse(request)

	auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
	credentials = base64.b64decode(credentials.strip()).decode('utf-8')
	username, password = credentials.split(':', 1)
	user = auth.authenticate(username=username, password=password)
	
	if 'header' in phot_data.keys() and 'transient' in phot_data.keys() and 'photheader' in phot_data.keys():
		hd = phot_data['header']
		tr = phot_data['transient']
		ph = phot_data['photheader']
	else:
		return_dict = {"message":"header, transient, and photheader keys are required"}
		return JsonResponse(return_dict)

	# get all the foreign keys we need
	instrument = Instrument.objects.filter(name=ph['instrument'])
	if not len(instrument):
		instrument = Instrument.objects.filter(name='Unknown')
	instrument = instrument[0]

	obs_group = ObservationGroup.objects.filter(name=ph['obs_group'])
	if not len(obs_group):
		obs_group = ObservationGroup.objects.filter(name='Unknown')
	obs_group = obs_group[0]

	status = TransientStatus.objects.filter(name=tr['status'])
	if not len(status):
		return_dict = {"message":"status %s is not in DB"%tr['status']}
		return JsonResponse(return_dict)
	status = status[0]

	allgroups = []
	if ph['groups']:
		for photgroup in ph['groups'].split(','):
			group = Group.objects.filter(name=photgroup)
			if not len(group):
				return_dict = {"message":"group %s is not in DB"%ph['groups']}
				return JsonResponse(return_dict)
			group = group[0]
			allgroups += [group]

	# get or create transient
	transient = Transient.objects.filter(name=tr['name'])
	if not len(transient):
		transient = Transient.objects.create(name=tr['name'],ra=tr['ra'],dec=tr['dec'],
											 status=status,created_by_id=user.id,
											 obs_group=obs_group,
											 modified_by_id=user.id)
	else: transient = transient[0]
		
	# get all existing photometry
	transientphot = TransientPhotometry.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group)
	if not len(transientphot):
		transientphot = TransientPhotometry.objects.create(
			instrument=instrument,obs_group=obs_group,transient=transient,
			created_by_id=user.id,modified_by_id=user.id)
	else:
		transientphot = transientphot[0]
		if hd['clobber']:
			transientphot.instrument = instrument
			transientphot.obs_group = obs_group
			transientphot.modified_by_id = user.id
			transientphot.save()

	if len(allgroups):
		for group in allgroups:
			if group not in transientphot.groups.all():
				transientphot.groups.add(group)
				transientphot.save()
		
	existingphot = TransientPhotData.objects.filter(photometry=transientphot)
	#if hd['delete']:
	#	for e in existingphot:
	#		if e.photometry.id == transientphot.id:
	#			e.delete()
	#existingphot = TransientPhotData.objects.filter(photometry=transientphot)
				
	# loop through new, comp against existing
	for k in phot_data.keys():
		if k == 'header' or k == 'transient' or k == 'photheader': continue
		p = phot_data[k]
		pmjd = Time(p['obs_date'],format='isot').mjd
		band = PhotometricBand.objects.filter(name=p['band'])
		if len(band): band = band[0]
		
		obsExists = False
		for e in existingphot:
			if e.photometry.id == transientphot.id:
				if e.band == band:
					try:
						mjd = Time(e.obs_date.isoformat().split('+')[0],format='isot').mjd
					except:
						mjd = Time(e.obs_date,format='isot').mjd
					if np.abs(mjd - pmjd) < hd['mjdmatchmin']:
						obsExists = True
						if hd['clobber']:
							if p['data_quality']:
								dq = DataQuality.objects.filter(name=p['data_quality'])
								if not dq:
									dq = DataQuality.objects.filter(name='Bad')
								dq = dq[0]
							else: dq = None
								
							e.obs_date = p['obs_date']
							e.flux = p['flux']
							e.flux_err = p['flux_err']
							e.mag = p['mag']
							e.mag_err = p['mag_err']
							e.forced = p['forced']
							e.data_quality = dq
							e.photometry = transientphot
							e.discovery_point = p['discovery_point']
							e.band = band
							e.modified_by_id = user.id
							e.save()

		if not obsExists:
			if p['data_quality']:
				dq = DataQuality.objects.filter(name=p['data_quality'])
				if not dq:
					dq = DataQuality.objects.filter(name='Bad')
				dq = dq[0]
			else: dq = None
			TransientPhotData.objects.create(obs_date=p['obs_date'],flux=p['flux'],flux_err=p['flux_err'],
											 mag=p['mag'],mag_err=p['mag_err'],forced=p['forced'],
											 data_quality=dq,photometry=transientphot,
											 discovery_point=p['discovery_point'],band=band,
											 created_by_id=user.id,modified_by_id=user.id)

	return_dict = {"message":"success"}

	return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_transient_spec(request):
	spec_data = JSONParser().parse(request)

	auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
	credentials = base64.b64decode(credentials.strip()).decode('utf-8')
	username, password = credentials.split(':', 1)
	user = auth.authenticate(username=username, password=password)
	
	if 'header' in spec_data.keys() and 'transient' in spec_data.keys():
		hd = spec_data['header']
		tr = spec_data['transient']
	else:
		return_dict = {"message":"header and transient keys are required"}
		return JsonResponse(return_dict)

	# get all the foreign keys we need
	instrument = Instrument.objects.filter(name=hd['instrument'])
	if not len(instrument):
		instrument = Instrument.objects.filter(name='Unknown')
	instrument = instrument[0]

	obs_group = ObservationGroup.objects.filter(name=hd['obs_group'])
	if not len(obs_group):
		obs_group = ObservationGroup.objects.filter(name='Unknown')
	obs_group = obs_group[0]

	allgroups = []
	if hd['groups']:
		for specgroup in hd['groups'].split(','):
			group = Group.objects.filter(name=specgroup)
			if not len(group):
				return_dict = {"message":"group %s is not in DB"%hd['groups']}
				return JsonResponse(return_dict)
			group = group[0]
			allgroups += [group]

	# get or create transient
	transient = Transient.objects.filter(name=tr['name'])
	if not len(transient):
		return_dict = {"message":"transient %s is not in DB"%tr['name']}
		return JsonResponse(return_dict)
	else: transient = transient[0]

	if hd['data_quality']:
		dq = DataQuality.objects.filter(name=hd['data_quality'])
		if not dq:
			dq = DataQuality.objects.filter(name='Bad')
			dq = dq[0]
	else: dq = None

	
	# get the spectrum
	transientspec = TransientSpectrum.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group).filter(obs_date=hd['obs_date'])
	if not len(transientspec):
		transientspec = TransientSpectrum.objects.create(
			ra=hd['ra'],dec=hd['dec'],instrument=instrument,obs_group=obs_group,transient=transient,
			rlap=hd['rlap'],redshift=hd['redshift'],redshift_err=hd['redshift_err'],
			redshift_quality=hd['redshift_quality'],spectrum_notes=hd['spectrum_notes'],
			spec_phase=hd['spec_phase'],obs_date=hd['obs_date'],data_quality=dq,
			created_by_id=user.id,modified_by_id=user.id)
	else:
		transientspec = transientspec[0]
		if hd['clobber']:
			transientspec.data_quality = dq
			transientspec.ra = hd['ra']
			transientspec.dec = hd['dec']
			transientspec.rlap = hd['rlap']
			transientspec.redshift = hd['redshift']
			transientspec.redshift_err = hd['redshift_err']
			transientspec.redshift_quality = hd['redshift_quality']
			transientspec.spectrum_notes = hd['spectrum_notes']
			transientspec.spec_phase = hd['spec_phase']
			transientspec.modified_by_id = user.id
			transientspec.save()
	if len(allgroups):
		for group in allgroups:
			if group not in transientspec.groups.all():
				transientspec.groups.add(group)
				transientspec.save()
				
	# add the spec data
	existingspec = TransientSpecData.objects.filter(spectrum=transientspec)
	# loop through new, comp against existing
	if len(existingspec) and hd['clobber']:
		for e in existingspec: e.delete()
	elif len(existingspec):
		return_dict = {"message":"spectrum exists.  Not clobbering"}
		return JsonResponse(return_dict)

	for k in spec_data.keys():
		if k == 'header' or k == 'transient': continue
		s = spec_data[k]

		TransientSpecData.objects.create(spectrum=transientspec,wavelength=s['wavelength'],
										 flux=s['flux'],flux_err=s['flux_err'],
										 created_by_id=user.id,modified_by_id=user.id)
	
	return_dict = {"message":"success"}
	return JsonResponse(return_dict)

@login_or_basic_auth_required
def get_transient(request, slug):
	t = Transient.objects.filter(slug=slug)

	return_dict = {"transient":""}
	if t.exists():
		transient = t[0]
		serializer = TransientSerializer(instance=transient, context={"request":Request(request)})
		return_dict["transient"] = serializer.data

	return JsonResponse(return_dict)


def find_separation(host_queryset, query_coord, sep_threshold):

	ra,dec = [],[]
	for host in host_queryset:
		ra += [host.ra]; dec += [host.dec]
	host_coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))
	sep = host_coords.separation(query_coord)
	for idx in np.where(sep.arcminute <= sep_threshold)[0]:
		yield host_queryset[int(idx)],sep.arcminute[idx]

@login_or_basic_auth_required		
def get_host(request, ra, dec, sep):

	query_coord = SkyCoord(ra,dec,unit=(u.deg, u.deg))
	host_candidates = find_separation(Host.objects.all(), query_coord, float(sep))

	serialized_hosts = []
	for host,sep in host_candidates:
		serialized_hosts.append(
			{"host_ra":host.ra,"host_dec":host.dec,
			 "host_name":host.name,"host_id":host.id,
			 "host_sep":sep}
		)

	return_dict = {"requested ra":float(ra),
				   "requested dec":float(dec),
				   "requested sep":float(sep),
				   "host candidates":serialized_hosts }

	return JsonResponse(return_dict)
