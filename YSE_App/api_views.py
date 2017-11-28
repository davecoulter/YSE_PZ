from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from .models import *
from .serializers import *

### API views
@csrf_exempt
def transient_list(request):
	if request.method == 'GET':
		transients = Transient.objects.all()
		serializer = TransientSerializer(transients, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = TransientSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def transient_detail(request, pk):
	try:
		transient = Transient.objects.get(pk=pk)
	except Transient.DoesNotExist:
		return HttpResponse(status=404)

	if request.method == 'GET':
		serializer = TransientSerializer(transient)
		return JsonResponse(serializer.data)

	elif request.method == 'PUT':
		data = JSONParser().parse(request)
		serializer = TransientSerializer(transient, data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data)
		return JsonResponse(serializer.errors, status=400)
	# NO DELETES!
	# elif request.method == 'DELETE':
	# 	transient.delete()
	# 	return HttpResponse(status=204)