from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader

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
		{'transient': transient})