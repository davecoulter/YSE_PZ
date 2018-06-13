from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q
from rest_framework.renderers import JSONRenderer
import requests
from django.template.defaulttags import register
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Lower

from .models import *
from .forms import *
from .common import utilities
from . import view_utils
import datetime
import pytz
from pytz import timezone
from .serializers import *
from django.core import serializers
import os
from .data import PhotometryService, SpectraService, ObservingResourceService
import json
import time

from .table_utils import TransientTable,FollowupTable
import django_tables2 as tables
from django_tables2 import RequestConfig

# Create your views here.

def index(request):
	if request.user.is_authenticated:
		return HttpResponseRedirect(reverse_lazy('dashboard'))
	return render(request, 'YSE_App/index.html')

#def add_followup(request,obj):
#		 return '<a href="%s">Add followup for %s</a>' % (obj.firm_url,obj.firm_url)

# Create your views here.
def auth_login(request):
	logout(request)
	next_page = request.POST.get('next')

	user = None
	if request.POST:
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)

	if user is not None:
		login(request, user)
		
		# Redirect to requested page
		if next_page:
			return HttpResponseRedirect(next_page)
		else:
			return render_to_response('dashboard')
	else:
		return render(request, 'YSE_App/login.html')

def auth_logout(request):
	logout(request)
	return render(request, 'YSE_App/index.html')

@login_required
def dashboard(request):
	new_transients = None
	inprocess_transients = None
	new_k2_transients = None
	new_notk2_transients = None
	watch_transients = None
	following_transients = None
	followup_requested_transients = None
	finishedfollowing_transients = None

	k2_transients = Transient.objects.filter(k2_validated=1).order_by('-disc_date')
	k2_table = TransientTable(k2_transients,prefix='k2')
	RequestConfig(request, paginate={'per_page': 10}).configure(k2_table)
	
	status_new = TransientStatus.objects.filter(name='New').order_by('-modified_date')
	if len(status_new) == 1:
		new_transients = Transient.objects.filter(status=status_new[0]).order_by('-disc_date')
	new_table = TransientTable(new_transients,prefix='new')
	RequestConfig(request, paginate={'per_page': 10}).configure(new_table)
		
	status_watch = TransientStatus.objects.filter(name='Watch').order_by('-modified_date')
	if len(status_watch) == 1:
		watch_transients = Transient.objects.filter(status=status_watch[0]).order_by('-disc_date')
	watch_table = TransientTable(watch_transients,prefix='watch')
	RequestConfig(request, paginate={'per_page': 10}).configure(watch_table)
	
	status_followrequest = TransientStatus.objects.filter(name='FollowupRequested').order_by('-modified_date')
	if len(status_followrequest) == 1:
		followup_requested_transients = Transient.objects.filter(status=status_followrequest[0]).order_by('-disc_date')
	follow_request_table = TransientTable(followup_requested_transients,prefix='followrequest')
	RequestConfig(request, paginate={'per_page': 10}).configure(follow_request_table)
		
	status_following = TransientStatus.objects.filter(name='Following').order_by('-modified_date')
	if len(status_following) == 1:
		following_transients = Transient.objects.filter(status=status_following[0]).order_by('-disc_date')
	following_table = TransientTable(following_transients,prefix='following')
	RequestConfig(request, paginate={'per_page': 10}).configure(following_table)

	status_finishedfollowing = TransientStatus.objects.filter(name='FollowupFinished').order_by('-modified_date')
	if len(status_finishedfollowing) == 1:
		finishedfollowing_transients = Transient.objects.filter(status=status_finishedfollowing[0]).order_by('-disc_date')
	finished_following_table = TransientTable(finishedfollowing_transients,prefix='finishedfollowing')
	RequestConfig(request, paginate={'per_page': 10}).configure(finished_following_table)
		
	transient_categories = [(k2_table,'Validated K2 Transients','k2'),
							(new_table,'New Transients','new'),
							(follow_request_table,'Followup Requested','followrequest'),
							(following_table,'Following','following'),
							(watch_table,'Watch','watch'),
							(finished_following_table,'Finished Following','finishedfollowing')]
		
	context = {
			'transient_categories':transient_categories,
	}

	return render(request, 'YSE_App/dashboard.html', context)

@login_required
def followup(request):

	followup_transients = None

	telescopes = Telescope.objects.all()

	table_list = []
	for t in telescopes:
		followup_transients = TransientFollowup.objects.filter(Q(too_resource__telescope__name=t) |
															   Q(classical_resource__telescope__name=t) |
															   Q(queued_resource__telescope__name=t))
	
		followup_table = FollowupTable(followup_transients,prefix=t)
		RequestConfig(request, paginate={'per_page': 10}).configure(followup_table)
		table_list += [(t.name,followup_table,t.name.replace(' ','_'),followup_transients)]
	
	context = {
		'followup_tables':table_list,
	}
	return render(request, 'YSE_App/transient_followup_test.html', context)


@login_required
def followup_bkp(request):

	followup_transients = None
	
	status_followrequest = TransientStatus.objects.order_by('-modified_date')
	followup_transients = Transient.objects.filter(Q(status=status_followrequest[0]) |
												   Q(status=status_followrequest[1]) |
												   Q(status=status_followrequest[2]) |
												   Q(status=status_followrequest[3]) |
												   Q(status=status_followrequest[4]) |
												   Q(status=status_followrequest[5]))
	for i in range(len(followup_transients)):
		disc = view_utils.get_disc_mag_for_transient(request.user, transient_id=followup_transients[i].id)

		if disc:
			followup_transients[i].disc_mag = disc.mag

		followup_transients[i].followups = TransientFollowup.objects.filter(transient=followup_transients[i].id)

		for j in range(len(followup_transients[i].followups)):

			if followup_transients[i].followups[j].classical_resource:
				followup_transients[i].followups[j].resource = followup_transients[i].followups[j].classical_resource

			elif followup_transients[i].followups[j].too_resource:
				followup_transients[i].followups[j].resource = followup_transients[i].followups[j].too_resource

			elif followup_transients[i].followups[j].queued_resource:
				followup_transients[i].followups[j].resource = followup_transients[i].followups[j].queued_resource

	context = {
		'transients': followup_transients,
		'telescopes':Telescope.objects.all()
	}
	return render(request, 'YSE_App/transient_followup.html', context)

@login_required
def transient_tags(request):
	all_transient_tags = TransientTag.objects.all()
	context = {
		'all_transient_tags': all_transient_tags
	}
	return render(request, 'YSE_App/transient_tags.html', context)

@login_required
def get_transient_tags(request):
	id_str= request.GET.getlist('tagid')
	ids = []
	for id in id_str:
		ids.append(int(id))

	transient_queryset = Transient.objects.filter(tags__in=ids).distinct()
	transient_objs = [t for t in transient_queryset]

	serializer = TransientSerializer(transient_objs, context={'request': request}, many=True)
	return_data = {}

	for i,data in enumerate(serializer.data):
		return_data[i] = data

	return JsonResponse(return_data)

@login_required
def dashboard_example(request):
	return render(request, 'YSE_App/dashboard_example.html')


@register.filter
def get_item(dictionary, key):
	return dictionary.get(key)

@login_required
def calendar(request):
	all_dates = OnCallDate.objects.all()
	colors = ['#dd4b39', 
				'#f39c12', 
				'#00c0ef', 
				'#0073b7', 
				'#f012be', 
				'#3c8dbc',
				'#00a65a',
				'#d2d6de',
				'#001f3f']

	user_colors = {}
	for i, u in enumerate(User.objects.all().exclude(username='admin')):
		user_colors[u.username] = colors[i % len(colors)]

	context = {
		'all_dates': all_dates,
		'user_colors': user_colors
	}
	return render(request, 'YSE_App/calendar.html', context)

@login_required
def transient_detail(request, slug):

	transient = Transient.objects.filter(slug=slug)
	logs = Log.objects.filter(transient=transient[0].id)

	obs = None
	if len(transient) == 1:

		transient_obj = transient.first() # This should throw an exception if more than one or none are returned
		transient_id = transient[0].id

		alt_names = AlternateTransientNames.objects.filter(transient__pk=transient_id)

		transient_followup_form = TransientFollowupForm()
		transient_followup_form.fields["classical_resource"].queryset = view_utils.get_authorized_classical_resources(request.user)
		transient_followup_form.fields["too_resource"].queryset = view_utils.get_authorized_too_resources(request.user)
		transient_followup_form.fields["queued_resource"].queryset = view_utils.get_authorized_queued_resources(request.user)

		transient_observation_task_form = TransientObservationTaskForm()

		# Status update properties
		all_transient_statuses = TransientStatus.objects.all()
		transient_status_follow = TransientStatus.objects.get(name="Following")
		transient_status_watch = TransientStatus.objects.get(name="Watch")
		transient_status_ignore = TransientStatus.objects.get(name="Ignore")
		transient_comment_form = TransientCommentForm()

		# Transient tag
		all_colors = WebAppColor.objects.all()
		all_transient_tags = TransientTag.objects.all()
		assigned_transient_tags = transient_obj.tags.all()

		# Get associated Observations
		followups = TransientFollowup.objects.filter(transient__pk=transient_id)
		if followups:
			for i in range(len(followups)):
				followups[i].observation_set = TransientObservationTask.objects.filter(followup=followups[i].id)

				if followups[i].classical_resource:
					followups[i].resource = followups[i].classical_resource
				elif followups[i].too_resource:
					followups[i].resource = followups[i].too_resource
				elif followups[i].queued_resource:
					followups[i].resource = followups[i].queued_resource
		else:
			followups = None

		hostdata = Host.objects.filter(pk=transient_obj.host_id)
		if hostdata:
			hostphotdata = view_utils.get_recent_phot_for_host(request.user, host_id=hostdata[0].id)
			transient_obj.hostdata = hostdata[0]
		else:
			hostphotdata = None

		if hostphotdata: transient_obj.hostphotdata = hostphotdata

		lastphotdata = view_utils.get_recent_phot_for_transient(request.user, transient_id=transient_id)
		firstphotdata = view_utils.get_disc_mag_for_transient(request.user, transient_id=transient_id)

		# obsnights,tellist = view_utils.getObsNights(transient[0])
		# too_resources = ToOResource.objects.all()
		#
		# for i in range(len(too_resources)):
		#	telescope = too_resources[i].telescope
		#	too_resources[i].telescope_id = telescope.id
		#	observatory = Observatory.objects.get(pk=telescope.observatory_id)
		#	too_resources[i].deltahours = too_resources[i].awarded_too_hours - too_resources[i].used_too_hours
		obsnights = view_utils.get_obs_nights_happening_soon(request.user)
		too_resources = view_utils.get_too_resources(request.user)

		date = datetime.datetime.now(tz=pytz.utc)
		date_format='%m/%d/%Y %H:%M:%S'

		spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(request.user, transient_id)
		
		context = {
			'transient':transient_obj,
			'followups':followups,
			# 'telescope_list': tellist,
			'observing_nights': obsnights,
			'too_resource_list': too_resources,
			'nowtime':date.strftime(date_format),
			'transient_followup_form': transient_followup_form,
			'transient_observation_task_form': transient_observation_task_form,
			'transient_comment_form': transient_comment_form,
			'alt_names': alt_names,
			'all_transient_statuses': all_transient_statuses,
			'transient_status_follow': transient_status_follow,
			'transient_status_watch': transient_status_watch,
			'transient_status_ignore': transient_status_ignore,
			'logs':logs,
			'all_transient_tags': all_transient_tags,
			'assigned_transient_tags': assigned_transient_tags,
			'all_colors': all_colors,
			'all_transient_spectra': spectra,
		}

		if lastphotdata and firstphotdata:
			context['recent_mag'] = lastphotdata.mag
			context['recent_filter'] = lastphotdata.band
			context['recent_magdate'] = lastphotdata.obs_date
			context['first_mag'] = firstphotdata.mag
			context['first_filter'] = firstphotdata.band
			context['first_magdate'] = firstphotdata.obs_date

		return render(request,
			'YSE_App/transient_detail.html',
			context)

	else:
		return Http404('Transient not found')

@login_required
def transient_edit(request, transient_id=None):
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = TransientForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required
			# ...
			# redirect to a new URL:
			return HttpResponseRedirect('/thanks/')

	# if a GET (or any other method) we'll create a blank form
	else:
		form = TransientForm()

	return render(request, 'YSE_App/transient_edit.html', {'form': form})


from wsgiref.util import FileWrapper
@login_required
def download_data(request, slug):

	transient = Transient.objects.filter(slug=slug)
	data = {transient[0].name:{'transient':{},'host':{},'photometry':{},'spectra':{}}}
	data[transient[0].name]['transient'] = json.loads(serializers.serialize("json", transient, use_natural_foreign_keys=True))

	if transient[0].host:
		host = Host.objects.filter(id=transient[0].host.id)
		data[transient[0].name]['host'] = json.loads(serializers.serialize("json", host, use_natural_foreign_keys=True))


	# Get photometry by user & transient
	authorized_phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(request.user, transient[0].id)
	if len(authorized_phot):
		data[transient[0].name]['photometry'] = json.loads(serializers.serialize("json", authorized_phot,use_natural_foreign_keys=True))

		# Get data points
		for p,pd in zip(authorized_phot,range(len(data[transient[0].name]['photometry']))):
			photdata = PhotometryService.GetAuthorizedTransientPhotData_ByPhotometry(request.user, p.id, includeBadData=True)
			data[transient[0].name]['photometry'][pd]['data'] = json.loads(serializers.serialize("json", photdata, use_natural_foreign_keys=True))


	# Get spectra by user & transient
	authorized_spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(request.user, transient[0].id, includeBadData=True)
	if len(authorized_spectra):
		data[transient[0].name]['spectra'] = json.loads(serializers.serialize("json", authorized_spectra, use_natural_foreign_keys=True))

		for s,sd in zip(authorized_spectra,range(len(data[transient[0].name]['spectra']))):
			specdata = SpectraService.GetAuthorizedHostSpecData_BySpectrum(request.user, s.id, includeBadData=True)
			if specdata:
				data[transient[0].name]['spectra'][sd]['data'] = json.loads(serializers.serialize("json", specdata, use_natural_foreign_keys=True))

	response = JsonResponse(data)
	response['Content-Disposition'] = 'attachment; filename=%s' % '%s_data.json'%slug
	return response
