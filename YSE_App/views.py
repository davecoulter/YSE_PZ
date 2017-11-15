from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

import requests

from astropy.coordinates import SkyCoord
import astropy.units as u

from .models import *

def index(request):
	return render(request, 'YSE_App/index.html')

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
		print("NEXT: %s" % next_page)
		return HttpResponseRedirect(next_page)
	else:
		return render(request, 'YSE_App/login.html')

def logout_view(request):
    logout(request)
    # Redirect to a success page.

@login_required
def dashboard(request):
	logout(request)
	all_transients = Transient.objects.order_by('id')
	context = {
		'all_transients': all_transients,
	}
	return render(request, 'YSE_App/dashboard.html', context)

@login_required
def dashboard_example(request):
	return render(request, 'YSE_App/dashboard_example.html')

@login_required
def transient_detail(request, transient_id):
	transient = get_object_or_404(Transient, pk=transient_id)
	ra,dec = get_coords_sexagesimal(transient.ra,transient.dec)
	return render(request, 'YSE_App/transient_detail.html', 
		{'transient': transient,
		 'jpegurl':get_psstamp_url(request, transient_id),
		 'ra':ra,'dec':dec})

def get_psstamp_url(request, transient_id):

	try:
		t = Transient.objects.get(pk=transient_id)
	except t.DoesNotExist:
		raise Http404("Transient id does not exist")
	
	ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color" % (t.ra,t.dec)
	response = requests.get(url=ps1url)
	response_text = response.content.decode('utf-8')

	jpegurl = ""
	if '<td><img src="' in response_text:
		jpegurl = response_text.split('<td><img src=T"')[1].split('" width="240" height="240" /></td>')[0]
		jpegurl = "http:%s" % jpegurl

	return(jpegurl)

def get_coords_sexagesimal(radeg,decdeg):
        sc = SkyCoord(radeg,decdeg,unit=u.deg)
        return('%02i:%02i:%02.2f'%(sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2]),
               '%02i:%02i:%02.2f'%(sc.dec.dms[0],sc.dec.dms[1],sc.dec.dms[2]))
