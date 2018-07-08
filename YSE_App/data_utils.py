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
from django.db.models import ForeignKey
from .common.alert import sendemail

@csrf_exempt
@login_or_basic_auth_required
def add_transient(request):
	transient_data = JSONParser().parse(request)
	
	auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
	credentials = base64.b64decode(credentials.strip()).decode('utf-8')
	username, password = credentials.split(':', 1)
	user = auth.authenticate(username=username, password=password)

	# ready to send error emails
	smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
	from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
	subject = "TNS Transient Upload Failure"
	txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
	
	for transientlistkey in transient_data.keys():
		if transientlistkey == 'noupdatestatus': continue

		transient = transient_data[transientlistkey]

		transientkeys = transient.keys()
		if 'name' not in transientkeys:
			return_dict = {"message":"Error : Transient name not provided for transient %s!"%transientlistkey}
			return JsonResponse(return_dict)
		print('updating transient %s'%transient['name'])
		try:
			transientdict = {'created_by_id':user.id,'modified_by_id':user.id}
			for transientkey in transientkeys:
				if transientkey == 'transientphotometry' or \
				   transientkey == 'transientspectra' or \
				   transientkey == 'host' or \
				   transientkey == 'tags': continue

				if not isinstance(Transient._meta.get_field(transientkey), ForeignKey):
					transientdict[transientkey] = transient[transientkey]
				else:
					fkmodel = Transient._meta.get_field(transientkey).remote_field.model
					fk = fkmodel.objects.filter(name=transient[transientkey])
					if not len(fk):
						fk = fkmodel.objects.filter(name='Unknown')
						print("Sending email to: %s" % user.username)
						html_msg = "Alert : YSE_PZ Failed to upload transient %s "
						html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
						sendemail(from_addr, user.email, subject,
								  html_msg%(transient['name'],transient[transientkey],transientkey),
								  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

					transientdict[transientkey] = fk[0]

			dbtransient = Transient.objects.filter(name=transient['name'])
			if not len(dbtransient):
				dbtransient = Transient.objects.create(**transientdict)
			else: #if clobber:
				if 'noupdatestatus' in transient_data.keys() and not transient_data['noupdatestatus']:
					if dbtransient[0].status.name == 'Ignore': dbtransient[0].status = TransientStatus.objects.filter(name='New')[0]
					else: transientdict['status'] = dbtransient[0].status
				else: transientdict['status'] = dbtransient[0].status
				dbtransient.update(**transientdict)
				dbtransient = dbtransient[0]
			if 'tags' in transientkeys:
				for tag in transient['tags']:
					dbtransient.tags.add(tags=transient['tags'])
				dbtransient.save()
			
			if 'transientphotometry' in transientkeys:
				# do photometry
				add_transient_phot_util(transient['transientphotometry'],dbtransient,user)
			
			if 'transientspectra' in transientkeys:
				# spectrum
				add_transient_spec_util(transient['transientspectra'],dbtransient,user)
		
			if 'host' in transientkeys:
				# host galaxy
				add_transient_host_util(transient['host'],dbtransient,user)

		except Exception as e:
			print('Transient %s failed!'%transient['name'])
			print("Sending email to: %s" % user.username)
			html_msg = "Alert : YSE_PZ Failed to upload transient %s with error %s"
			sendemail(from_addr, user.email, subject, html_msg%(transient['name'],e),
                      djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
			# sending SMS is too scary for now
			#sendsms(from_addr, phone_email, subject, txt_msg%transient['name'],
            #        djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
			
	return_dict = {"message":"success"}

	return JsonResponse(return_dict)

def add_transient_host_util(hostdict,transient,user):
	
	if 'name' not in hostdict.keys():
		return_dict = {"message":"no host"}
		return JsonResponse(return_dict)

	dbhostdict = {'created_by_id':user.id,'modified_by_id':user.id}
	for hostkey in hostdict.keys():
		if not isinstance(Host._meta.get_field(hostkey), ForeignKey):
				dbhostdict[hostkey] = hostdict[hostkey]
		else:
			fkmodel = Host._meta.get_field(hostkey).remote_field.model
			fk = fkmodel.objects.filter(name=hostdict[hostkey])
			if not len(fk):
				# ready to send error emails
				smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
				from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
				subject = "TNS Transient Upload Failure"
				html_msg = "Alert : YSE_PZ Failed to upload transient %s "
				txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
				html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
				print("Sending email to: %s" % user.username)
				sendemail(from_addr, user.email, subject,
						  html_msg%(transient['name'],transient[transientkey],transientkey),
						  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
				
			hostdict[hostkey] = fk[0]

	dbhost = Host.objects.filter(name=dbhostdict['name'])
	if not len(dbhost):
		dbhost = Host.objects.create(**dbhostdict)
	else: #if clobber:
		dbhost.update(**dbhostdict)
		dbhost = dbhost[0]

	transient.host = dbhost
	transient.save()
	
	return_dict = {"message":"host success"}
	return JsonResponse(return_dict)		

def add_transient_phot_util(photdict,transient,user):
	
	for k in photdict.keys():
		if k == 'clobber' or k == 'mjdmatchmin': continue
		photometry = photdict[k]
		
		instrument = Instrument.objects.filter(name=photometry['instrument'])
		if not len(instrument):
			instrument = Instrument.objects.filter(name='Unknown')
		instrument = instrument[0]

		obs_group = ObservationGroup.objects.filter(name=photometry['obs_group'])
		if not len(obs_group):
			obs_group = ObservationGroup.objects.filter(name='Unknown')
		obs_group = obs_group[0]

		transientphot = TransientPhotometry.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group)
		if not len(transientphot):
			transientphot = TransientPhotometry.objects.create(
				instrument=instrument,obs_group=obs_group,transient=transient,
				created_by_id=user.id,modified_by_id=user.id)
		else: transientphot = transientphot[0]
		existingphot = TransientPhotData.objects.filter(photometry=transientphot)

		existingphot = TransientPhotData.objects.filter(photometry=transientphot)
		
		for k in photometry['photdata']:
			p = photometry['photdata'][k]

			pmjd = Time(p['obs_date'],format='isot').mjd

			band = PhotometricBand.objects.filter(name=p['band']).filter(instrument__name=photometry['instrument'])
			if len(band): band = band[0]
			else: band = PhotometricBand.objects.filter(name='Unknown')[0]
			
			obsExists = False
			for e in existingphot:
				if e.photometry.id == transientphot.id:
					if e.band == band:
						try:
							mjd = Time(e.obs_date.isoformat().split('+')[0],format='isot').mjd
						except:
							mjd = Time(e.obs_date,format='isot').mjd
						if np.abs(mjd - pmjd) < photdict['mjdmatchmin']:
							obsExists = True
							if photdict['clobber']:
								if p['data_quality']:
									dq = DataQuality.objects.filter(name=p['data_quality'])
									if not dq:
										dq = DataQuality.objects.filter(name='Bad')
									dq = dq[0]
								else: dq = None
								
								e.obs_date = p['obs_date']
								e.flux = p['flux']
								e.flux_err = p['flux_err']
								e.flux_zero_point = p['flux_zero_point']
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
				TransientPhotData.objects.create(
					obs_date=p['obs_date'],flux=p['flux'],flux_err=p['flux_err'],
					mag=p['mag'],mag_err=p['mag_err'],forced=p['forced'],
					data_quality=dq,photometry=transientphot,
					flux_zero_point=p['flux_zero_point'],
					discovery_point=p['discovery_point'],band=band,
					created_by_id=user.id,modified_by_id=user.id)

	return_dict = {"message":"successfully added phot data"}
	return JsonResponse(return_dict)


def add_transient_spec_util(specdict,transient,user):

	for k in specdict.keys():
		if k == 'clobber': continue
		spectrum = specdict[k]
		# get all the foreign keys we need
		instrument = Instrument.objects.filter(name=spectrum['instrument'])
		if not len(instrument):
			instrument = Instrument.objects.filter(name='Unknown')
		instrument = instrument[0]

		obs_group = ObservationGroup.objects.filter(name=spectrum['obs_group'])
		if not len(obs_group):
			obs_group = ObservationGroup.objects.filter(name='Unknown')
		obs_group = obs_group[0]
		
		allgroups = []
		if 'groups' in spectrum.keys() and spectrum['groups']:
			for specgroup in spectrum['groups'].split(','):
				group = Group.objects.filter(name=specgroup)
				if not len(group):
					return_dict = {"message":"group %s is not in DB"%hd['groups']}
					return JsonResponse(return_dict)
				group = group[0]
				allgroups += [group]

		if 'data_quality' in spectrum.keys() and spectrum['data_quality']:
			dq = DataQuality.objects.filter(name=spectrum['data_quality'])
			if not dq:
				dq = DataQuality.objects.filter(name='Bad')
				dq = dq[0]
			else: dq = None
			spectrum['data_quality'] = dq

		spectrum['instrument'] = instrument
		spectrum['obs_group'] = obs_group
	
		# get the spectrum
		transientspec = TransientSpectrum.objects.filter(transient=transient).\
			filter(instrument=instrument).filter(obs_group=obs_group).filter(obs_date=spectrum['obs_date'])
		spectrum['created_by_id'] = user.id
		spectrum['modified_by_id'] = user.id
		spectrum['transient'] = transient
		spectrum_copy = spectrum.copy()
		del spectrum_copy['specdata']

		if not len(transientspec):
			transientspec = TransientSpectrum.objects.create(**spectrum_copy)
		else:
			transientspec = transientspec[0]
			if specdict['clobber']:
				transientspec.update(**spectrum_copy)
				transientspec.save()

		if len(allgroups):
			for group in allgroups:
				if group not in transientspec.groups.all():
					transientspec.groups.add(group)
					transientspec.save()
				
		# add the spec data
		existingspec = TransientSpecData.objects.filter(spectrum=transientspec)
		# loop through new, comp against existing
		if len(existingspec) and specdict['clobber']:
			for e in existingspec: e.delete()
		elif len(existingspec):
			return_dict = {"message":"spectrum exists.  Not clobbering"}
			return JsonResponse(return_dict)

		specdata = spectrum['specdata']
		for k in specdata.keys():
			s = specdata[k]

			TransientSpecData.objects.create(spectrum=transientspec,wavelength=s['wavelength'],
											 flux=s['flux'],flux_err=s['flux_err'],
											 created_by_id=user.id,modified_by_id=user.id)
	
	return_dict = {"message":"successfully added spec data"}
	return JsonResponse(return_dict)
	
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
		band = PhotometricBand.objects.filter(name=p['band']).filter(instrument__name=ph['instrument'])
		if len(band): band = band[0]
		else: band = PhotometricBand.objects.filter(name='Unknown')[0]
		
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
							e.flux_zero_point = p['flux_zero_point']
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
											 flux_zero_point=p['flux_zero_point'],
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
