from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.views import generic
import requests

from .models import *

# Create your views here.
def index(request):
	all_transients = Transient.objects.order_by('id')
	context = {
		'all_transients': all_transients,
	}
	return render(request, 'YSE_App/index.html', context)

        
def transient_detail(request, transient_id):
        transient = get_object_or_404(Transient, pk=transient_id)
        return render(request, 'YSE_App/transient_detail.html', 
                      {'transient': transient,
                       'jpegurl':get_psstamp_url(request, transient_id)})

def get_psstamp_url(request, transient_id):
        ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color"%(
                Transient.objects.get(pk=transient_id).ra,Transient.objects.get(pk=transient_id).dec)
        
        response = requests.get(url=ps1url)
        jpegurl = response.content.decode('utf-8').split('<td><img src="')[1].split('" width="240" height="240" /></td>')[0]
        jpegurl = "http:%s"%jpegurl

        return(jpegurl)
