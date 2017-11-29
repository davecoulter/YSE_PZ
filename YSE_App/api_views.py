from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import serializers, viewsets

from .models import *
from .serializers import *

### API views
# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer

class TransientViewSet(viewsets.ModelViewSet):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer


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


@csrf_exempt
def transienthostrank_list(request):
	if request.method == 'GET':
		transienthostranks = TransientHostRank.objects.all()
		serializer = TransientHostRankSerializer(transienthostranks, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = TransientHostRankSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def status_list(request):
	if request.method == 'GET':
		statuses = Status.objects.all()
		serializer = StatusSerializer(statuses, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = StatusSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def observationgroup_list(request):
	if request.method == 'GET':
		obs_groups = ObservationGroup.objects.all()
		serializer = ObservationGroupSerializer(obs_groups, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = ObservationGroupSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def sedtype_list(request):
	if request.method == 'GET':
		sedtypes = SEDType.objects.all()
		serializer = SEDTypeSerializer(sedtypes, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = SEDTypeSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def hostmorphology_list(request):
	if request.method == 'GET':
		hostmorphologies = HostMorphology.objects.all()
		serializer = HostMorphologySerializer(hostmorphologies, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = HostMorphologySerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def phase_list(request):
	if request.method == 'GET':
		phases = Phase.objects.all()
		serializer = PhaseSerializer(phases, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = PhaseSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def transientclass_list(request):
	if request.method == 'GET':
		transientclasses = TransientClass.objects.all()
		serializer = TransientClassSerializer(transientclasses, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = TransientClassSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def hostclass_list(request):
	if request.method == 'GET':
		hostclasses = HostClass.objects.all()
		serializer = HostClassSerializer(hostclasses, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = HostClassSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def classicalnighttype_list(request):
	if request.method == 'GET':
		classicalnighttypes = ClassicalNightType.objects.all()
		serializer = ClassicalNightTypeSerializer(classicalnighttypes, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = ClassicalNightTypeSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def informationsource_list(request):
	if request.method == 'GET':
		informationsources = InformationSource.objects.all()
		serializer = InformationSourceSerializer(informationsources, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser().parse(request)
		serializer = InformationSourceSerializer(data=data)
		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)
		return JsonResponse(serializer.errors, status=400)