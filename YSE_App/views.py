from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import requests

from .models import *
from .forms import *
from .common import utilities
from . import view_utils

# Create your views here.

def index(request):
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
			print('hello')
			return HttpResponseRedirect(next_page)
		else:
			print('world')
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

	status_new = TransientStatus.objects.filter(name='New')
	if len(status_new) == 1:
		new_transients = Transient.objects.filter(status=status_new[0])

	status_inprocess = TransientStatus.objects.filter(name='InProcess')
	if len(status_inprocess) == 1:
		inprocess_transients = Transient.objects.filter(status=status_inprocess[0])
	
	context = {
		'new_transients': new_transients,
		'inprocess_transients': inprocess_transients,
	}
	return render(request, 'YSE_App/dashboard.html', context)

@login_required
def dashboard_example(request):
	return render(request, 'YSE_App/dashboard_example.html')

@login_required
def transient_detail(request, transient_id):
	# transient = get_object_or_404(Transient, pk=transient_id)
	transient = Transient.objects.filter(id=transient_id)
	obs = None
	if len(transient) == 1:
		# Get associated Observations
                followups = TransientFollowup.objects.filter(transient__pk=transient_id)
                lastphotdata = view_utils.get_recent_phot_for_transient(transient_id=transient_id)
                firstphotdata = view_utils.get_first_phot_for_transient(transient_id=transient_id)
                
                context = {
			'transient':transient[0],
			'followups':followups,
                        'jpegurl':utilities.get_psstamp_url(request,transient_id,Transient),
                        'recent_mag':lastphotdata.mag,
                        'recent_filter':lastphotdata.band,
                        'recent_magdate':lastphotdata.obs_date,
                        'first_mag':firstphotdata.mag,
                        'first_filter':firstphotdata.band,
                        'first_magdate':firstphotdata.obs_date,
                        
		}

                return render(request,
			'YSE_App/transient_detail.html',
			context)
	else:
		return Http404('Transient not found')

	# ra,dec = get_coords_sexagesimal(transient.ra,transient.dec)
	# obsnights,obslist = (),()
	# for o in ObservingNightDates.objects.order_by('-observing_night')[::-1]:
	# 	can_obs = telescope_can_observe(transient.ra,transient.dec, 
	# 		str(o.observing_night).split()[0],str(o.observatory))
	# 	obsnights += ([o,can_obs],)
	# 	if can_obs and o.happening_soon() and o.observatory not in obslist: obslist += (o.observatory,)

	# return render(request, 'YSE_App/transient_detail.html', 
	# 	{'transient': transient,
	# 	 'observatory_list': obslist, #Observatory.objects.all(),
	# 	 'observing_nights': obsnights,
	# 	 'jpegurl':get_psstamp_url(request, transient_id),
	# 	 'ra':ra,'dec':dec})


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
