from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.http import Http404
from rest_framework import mixins
from rest_framework import generics
from YSE_App.common import custom_mixins
from YSE_App.common import custom_generics

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

@permission_classes((permissions.AllowAny, )) # IsAuthenticated
class TransientList(generics.ListCreateAPIView):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer

@permission_classes((permissions.AllowAny, )) # IsAuthenticated
class TransientDetail(custom_generics.RetrieveUpdateAPIView):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer


# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# class TransientList(mixins.ListModelMixin,
# 						mixins.CreateModelMixin,
# 						generics.GenericAPIView):
# 	queryset = Transient.objects.all()
# 	serializer_class = TransientSerializer

# 	def get(self, request, *args, **kwargs):
# 		return self.list(request, *args, **kwargs)

# 	def post(self, request, *args, **kwargs):
# 		return self.create(request, *args, partial=True, **kwargs)

# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# class TransientDetail(mixins.RetrieveModelMixin,
# 						custom_mixins.UpdateModelMixin,
# 						generics.GenericAPIView):
# 	queryset = Transient.objects.all()
# 	serializer_class = TransientSerializer

# 	def get(self, request, *args, **kwargs):
# 		return self.retrieve(request, *args, **kwargs)

# 	def put(self, request, *args, **kwargs):
# 		return self.update(request, *args, partial=True, **kwargs)



# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# class TransientList(APIView):
# 	def get(self, request, format=None):
# 		transients = Transient.objects.all()
# 		serializer = TransientSerializer(transients, many=True)
# 		return Response(serializer.data)

# 	def post(self, request, format=None):
# 		serializer = TransientSerializer(data=request.data, partial=True)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# class TransientDetail(APIView):
# 	def get_object(self, pk):
# 		try:
# 			return Transient.objects.get(pk=pk)
# 		except Snippet.DoesNotExist:
# 			raise Http404

# 	def get(self, request, pk, format=None):
# 		transient = self.get_object(pk)
# 		serializer = TransientSerializer(transient)
# 		return Response(serializer.data)

# 	def put(self, request, pk, format=None):
# 		transient = self.get_object(pk)
# 		serializer = TransientSerializer(transient, data=request.data, partial=True)
# 		if serializer.is_valid():
# 			serializer.save()

# 			# Hack - for some reason after TransientSerializer performs
# 			# an update, it's `data` property contains object representations
# 			# of PrimaryKeyRelatedField members. These cannot be serialized
# 			# in the Response. Instead, I "re-serialize" the data :( 
# 			serializer = TransientSerializer(serializer.data)
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# @api_view(['GET', 'POST'])
# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# def transient_list(request, format=None):
# 	if request.method == 'GET':
# 		transients = Transient.objects.all()
# 		serializer = TransientSerializer(transients, many=True)
# 		return Response(serializer.data)

# 	elif request.method == 'POST':
# 		serializer = TransientSerializer(data=request.data, partial=True)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET', 'PUT'])
# @permission_classes((permissions.AllowAny, )) # IsAuthenticated
# def transient_detail(request, pk, format=None):
# 	try:
# 		transient = Transient.objects.get(pk=pk)
# 	except Transient.DoesNotExist:
# 		return HttpResponse(status=status.HTTP_404_NOT_FOUND)

# 	if request.method == 'GET':
# 		serializer = TransientSerializer(transient)
# 		return Response(serializer.data)

# 	elif request.method == 'PUT':
# 		serializer = TransientSerializer(transient, data=request.data, partial=True)
# 		if serializer.is_valid():
# 			serializer.save()

# 			# Hack - for some reason after TransientSerializer performs
# 			# an update, it's `data` property contains object representations
# 			# of PrimaryKeyRelatedField members. These cannot be serialized
# 			# in the Response. Instead, I "re-serialize" the data :( 
# 			serializer = TransientSerializer(serializer.data)
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










@csrf_exempt
def transienthostrank_list(request, format=None):
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
def status_list(request, format=None):
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
def observationgroup_list(request, format=None):
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
def sedtype_list(request, format=None):
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
def hostmorphology_list(request, format=None):
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
def phase_list(request, format=None):
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
def transientclass_list(request, format=None):
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
def hostclass_list(request, format=None):
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
def classicalnighttype_list(request, format=None):
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
def informationsource_list(request, format=None):
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