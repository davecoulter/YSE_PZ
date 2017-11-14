from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.views import generic
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u

from .models import *

# Create your views here.
def index(request):
	all_transients = Transient.objects.order_by('id')
	context = {
		'all_transients': all_transients,
	}
	return render(request, 'YSE_App/index.html', context)

def index2(request):
	return render(request, 'YSE_App/index2.html')

def transient_detail(request, transient_id):
        transient = get_object_or_404(Transient, pk=transient_id)
        ra,dec = get_coords_sexagesimal(transient.ra,transient.dec)
        return render(request, 'YSE_App/transient_detail.html', 
                      {'transient': transient,
                       'jpegurl':get_psstamp_url(request, transient_id),
                       'ra':ra,'dec':dec})

def get_psstamp_url(request, transient_id):
        ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color"%(
                Transient.objects.get(pk=transient_id).ra,Transient.objects.get(pk=transient_id).dec)
        
        response = requests.get(url=ps1url)
        jpegurl = response.content.decode('utf-8').split('<td><img src="')[1].split('" width="240" height="240" /></td>')[0]
        jpegurl = "http:%s"%jpegurl

        return(jpegurl)

def get_coords_sexagesimal(radeg,decdeg):
        sc = SkyCoord(radeg,decdeg,unit=u.deg)
        return('%02i:%02i:%02.2f'%(sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2]),
               '%02i:%02i:%02.2f'%(sc.dec.dms[0],sc.dec.dms[1],sc.dec.dms[2]))
