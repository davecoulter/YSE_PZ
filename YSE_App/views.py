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

        k2_survey = InternalSurvey.objects.filter(name='K2')[0]
        status_new = TransientStatus.objects.filter(name='New')
        if len(status_new) == 1:
                new_transients = Transient.objects.filter(status=status_new[0])
                new_notk2_transients = new_transients.exclude(k2_validated=1)
                for i in range(len(new_notk2_transients)):
                        disc = view_utils.get_first_phot_for_transient(transient_id=new_notk2_transients[i].id)
                        if disc: new_notk2_transients[i].disc_mag = disc.mag
                        
                new_k2_transients = new_transients.filter(k2_validated=1)#internal_survey=k2_survey.id)
                for i in range(len(new_k2_transients)):
                        disc = view_utils.get_first_phot_for_transient(transient_id=new_k2_transients[i].id)
                        if disc: new_k2_transients[i].disc_mag = disc.mag
                
        status_watch = TransientStatus.objects.filter(name='Watch')
        if len(status_watch) == 1:
                watch_transients = Transient.objects.filter(status=status_watch[0])
                for i in range(len(watch_transients)):
                        disc = view_utils.get_first_phot_for_transient(transient_id=watch_transients[i].id)
                        if disc: watch_transients[i].disc_mag = disc.mag

        status_followrequest = TransientStatus.objects.filter(name='FollowupRequested')
        if len(status_followrequest) == 1:
                followup_requested_transients = Transient.objects.filter(status=status_followrequest[0])
                for i in range(len(followup_requested_transients)):
                        disc = view_utils.get_first_phot_for_transient(transient_id=followup_requested_transients[i].id)
                        if disc: followup_requested_transients[i].disc_mag = disc.mag

                
        status_following = TransientStatus.objects.filter(name='Following')
        if len(status_following) == 1:
                following_transients = Transient.objects.filter(status=status_following[0])
                for i in range(len(following_transients)):
                        disc = view_utils.get_first_phot_for_transient(transient_id=following_transients[i].id)
                        if disc: following_transients[i].disc_mag = disc.mag

                
        #status_inprocess = TransientStatus.objects.filter(name='Watch')
        #if len(status_inprocess) == 1:
        #       inprocess_transients = Transient.objects.filter(status=status_inprocess[0])
        
        context = {
                'new_k2_transients': new_k2_transients,
                'new_transients': new_notk2_transients,
                'watch_transients': watch_transients,
                'followup_requested_transients': followup_requested_transients,
                'following_transients': following_transients,
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
                transient[0].hostdata = Host.objects.get(pk=transient[0].host_id)
                lastphotdata = view_utils.get_recent_phot_for_transient(transient_id=transient_id)
                firstphotdata = view_utils.get_first_phot_for_transient(transient_id=transient_id)
                
                obsnights,tellist = view_utils.getObsNights(transient[0])
                too_resources = ToOResource.objects.all()
                for i in range(len(too_resources)):
                        telescope = too_resources[i].telescope
                        telescope = Telescope.objects.filter(name=telescope)[0]
                        too_resources[i].telescope_id = telescope.id
                        observatory = Observatory.objects.get(pk=telescope.observatory_id)
                        too_resources[i].deltahours = too_resources[i].awarded_too_hours - too_resources[i].used_too_hours
                        too_resources[i].rise_time,too_resources[i].set_time = view_utils.getTimeUntilRiseSet(transient[0].ra,
                                                                                                              transient[0].dec, 
                                                                                                              0,
                                                                                                              telescope.latitude,
                                                                                                              telescope.longitude,
                                                                                                              telescope.elevation,
                                                                                                              observatory.utc_offset)
                        too_resources[i].moon_angle = view_utils.getMoonAngle(0,telescope,transient[0].ra,transient[0].dec)
                        
                if lastphotdata and firstphotdata:
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
                                'telescope_list': tellist,
                                'observing_nights': obsnights,
                                'too_resource_list': too_resources
                        }
                else:
                        context = {
                                'transient':transient[0],
                                'followups':followups,
                                'jpegurl':utilities.get_psstamp_url(request,transient_id,Transient),
                                'telescope_list': tellist,
                                'observing_nights': obsnights,
                                'too_resource_list': too_resources
                        }
                        
                return render(request,
                        'YSE_App/transient_detail.html',
                        context)
        else:
                return Http404('Transient not found')


        # return render(request, 'YSE_App/transient_detail.html', 
        #       {'transient': transient,
        #        'observatory_list': obslist, #Observatory.objects.all(),
        #        'observing_nights': obsnights,
        #        'jpegurl':get_psstamp_url(request, transient_id),
        #        'ra':ra,'dec':dec})


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
