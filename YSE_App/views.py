from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
import requests

from .models import *
from .forms import *
from .common import utilities
from . import view_utils
import datetime
import pytz
from pytz import timezone

# Create your views here.

def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse_lazy('dashboard'))
	return render(request, 'YSE_App/index.html')

#def add_followup(request,obj):
#        return '<a href="%s">Add followup for %s</a>' % (obj.firm_url,obj.firm_url)

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

	k2_transients = Transient.objects.filter(k2_validated=1).order_by('-modified_date')
	for i in range(len(k2_transients)):
		disc = view_utils.get_disc_mag_for_transient(transient_id=k2_transients[i].id)
		if disc:
			k2_transients[i].disc_mag = disc.mag
			k2_transients[i].disc_date = disc.obs_date

	
	status_new = TransientStatus.objects.filter(name='New').order_by('-modified_date')
	if len(status_new) == 1:
		new_transients = Transient.objects.filter(status=status_new[0]).order_by('-modified_date')
		new_notk2_transients = new_transients.exclude(k2_validated=1).order_by('-modified_date')
		for i in range(len(new_notk2_transients)):
			disc = view_utils.get_disc_mag_for_transient(transient_id=new_notk2_transients[i].id)
			if disc:
				new_notk2_transients[i].disc_mag = disc.mag
				new_notk2_transients[i].disc_date = disc.obs_date

	status_watch = TransientStatus.objects.filter(name='Watch').order_by('-modified_date')
	if len(status_watch) == 1:
		watch_transients = Transient.objects.exclude(k2_validated=1).filter(status=status_watch[0])
		for i in range(len(watch_transients)):
			disc = view_utils.get_disc_mag_for_transient(transient_id=watch_transients[i].id)
			if disc:
				watch_transients[i].disc_mag = disc.mag
				watch_transients[i].disc_date = disc.obs_date

	status_followrequest = TransientStatus.objects.filter(name='FollowupRequested').order_by('-modified_date')
	if len(status_followrequest) == 1:
		followup_requested_transients = Transient.objects.exclude(k2_validated=1).filter(status=status_followrequest[0])
		for i in range(len(followup_requested_transients)):
			disc = view_utils.get_disc_mag_for_transient(transient_id=followup_requested_transients[i].id)
			if disc:
				followup_requested_transients[i].disc_mag = disc.mag
				followup_requested_transients[i].disc_date = disc.obs_date

	status_following = TransientStatus.objects.filter(name='Following').order_by('-modified_date')
	if len(status_following) == 1:
		following_transients = Transient.objects.exclude(k2_validated=1).filter(status=status_following[0])
		for i in range(len(following_transients)):
			disc = view_utils.get_disc_mag_for_transient(transient_id=following_transients[i].id)
			if disc:
				following_transients[i].disc_mag = disc.mag
				following_transients[i].disc_date = disc.obs_date

	status_finishedfollowing = TransientStatus.objects.filter(name='FollowupFinished').order_by('-modified_date')
	if len(status_following) == 1:
		finishedfollowing_transients = Transient.objects.exclude(k2_validated=1).filter(status=status_finishedfollowing[0])
		for i in range(len(finishedfollowing_transients)):
			disc = view_utils.get_disc_mag_for_transient(transient_id=finishedfollowing_transients[i].id)
			if disc:
				finishedfollowing_transients[i].disc_mag = disc.mag
				finishedfollowing_transients[i].disc_date = disc.obs_date

	context = {
			'k2_transients': k2_transients,
			'new_transients': new_notk2_transients,
			'watch_transients': watch_transients,
			'followup_requested_transients': followup_requested_transients,
			'following_transients': following_transients,
			'finishedfollowing_transients': finishedfollowing_transients,
	}
	return render(request, 'YSE_App/dashboard.html', context)

@login_required
def followup(request):

	followup_transients = None
	
	status_followrequest = TransientStatus.objects.filter(
		Q(name='FollowupRequested') | Q(name='Following') | Q(name='New') | Q(name='Watch')).order_by('-modified_date')
	followup_transients = Transient.objects.filter(Q(status=status_followrequest[0]) |
												   Q(status=status_followrequest[1]) |
												   Q(status=status_followrequest[2]) |
												   Q(status=status_followrequest[3]))
	for i in range(len(followup_transients)):
		disc = view_utils.get_disc_mag_for_transient(transient_id=followup_transients[i].id)
		if disc: followup_transients[i].disc_mag = disc.mag
		followup_transients[i].followups = \
			TransientFollowup.objects.filter(transient=followup_transients[i].id)
		for j in range(len(followup_transients[i].followups)):
			if followup_transients[i].followups[j].classical_resource:
				followup_transients[i].followups[j].resource = \
					followup_transients[i].followups[j].classical_resource
			elif followup_transients[i].followups[j].too_resource:
				followup_transients[i].followups[j].resource = \
					followup_transients[i].followups[j].too_resource
			elif followup_transients[i].followups[j].queued_resource:
				followup_transients[i].followups[j].resource = \
					followup_transients[i].followups[j].queued_resource

	context = {
		'transients': followup_transients,
		'telescopes':Telescope.objects.all()
	}
	return render(request, 'YSE_App/transient_followup.html', context)


@login_required
def dashboard_example(request):
	return render(request, 'YSE_App/dashboard_example.html')

from django.template.defaulttags import register
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

	obs = None
	if len(transient) == 1:
		transient_id = transient[0].id
		
		alt_names = AlternateTransientNames.objects.filter(transient__pk=transient_id)
		transient_followup_form = TransientFollowupForm()
		transient_observation_task_form = TransientObservationTaskForm()

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

		hostdata = Host.objects.filter(pk=transient[0].host_id)
		if hostdata:
			hostphotdata = view_utils.get_recent_phot_for_host(host_id=hostdata[0].id)
			transient[0].hostdata = hostdata[0]
		else: 
			hostphotdata = None

		if hostphotdata: transient[0].hostphotdata = hostphotdata

		lastphotdata = view_utils.get_recent_phot_for_transient(transient_id=transient_id)
		firstphotdata = view_utils.get_disc_mag_for_transient(transient_id=transient_id)
		
		obsnights,tellist = view_utils.getObsNights(transient[0])
		too_resources = ToOResource.objects.all()
		
		for i in range(len(too_resources)):
			telescope = too_resources[i].telescope
			too_resources[i].telescope_id = telescope.id
			observatory = Observatory.objects.get(pk=telescope.observatory_id)
			too_resources[i].deltahours = too_resources[i].awarded_too_hours - too_resources[i].used_too_hours

		date = datetime.datetime.now(tz=pytz.utc)
		date_format='%m/%d/%Y %H:%M:%S'

		context = {
			'transient':transient[0],
			'followups':followups,
			'telescope_list': tellist,
			'observing_nights': obsnights,
			'too_resource_list': too_resources,
			'nowtime':date.strftime(date_format),
			'transient_followup_form': transient_followup_form,
			'transient_observation_task_form': transient_observation_task_form,
			'alt_names': alt_names,
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
