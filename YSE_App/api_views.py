from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from YSE_App.common import custom_generics
from rest_framework.reverse import reverse

from .models import *
from .serializers import *

### API views
@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def api_root(request, format=None):
	return Response({
		'users': reverse('user-list', request=request, format=format),
		'transients': reverse('transient-list', request=request, format=format),
		'transienthostranks': reverse('transienthostrank-list', request=request, format=format),
		'statuses': reverse('status-list', request=request, format=format),
		'observationgroups': reverse('observationgroup-list', request=request, format=format),
		'sedtypes': reverse('sedtype-list', request=request, format=format),
		'hostmorphologies': reverse('hostmorphology-list', request=request, format=format),
		'phases': reverse('phase-list', request=request, format=format),
		'transientclasses': reverse('transientclass-list', request=request, format=format),
		'hostclasses': reverse('hostclass-list', request=request, format=format),
		'classicalnighttypes': reverse('classicalnighttype-list', request=request, format=format),
		'informationsources': reverse('informationsource-list', request=request, format=format),
	})


# ViewSets define the view behavior.
# class UserViewSet(viewsets.ModelViewSet):
# 	queryset = User.objects.all()
# 	serializer_class = UserSerializer

# class TransientViewSet(viewsets.ModelViewSet):
# 	queryset = Transient.objects.all()
# 	serializer_class = TransientSerializer


@permission_classes((permissions.IsAuthenticated, ))
class UserList(generics.ListAPIView):
	queryset = User.objects.all()
	serializer_class = UserSerializer

@permission_classes((permissions.IsAuthenticated, ))
class UserDetail(generics.RetrieveAPIView):
	queryset = User.objects.all()
	serializer_class = UserSerializer


@permission_classes((permissions.IsAuthenticated, ))
class TransientList(generics.ListCreateAPIView):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer
	
	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, 
			modified_by=self.request.user)

@permission_classes((permissions.IsAuthenticated, ))
class TransientDetail(custom_generics.RetrieveUpdateAPIView):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer

	def perform_update(self, serializer):
		serializer.save(modified_by=self.request.user)

	def perform_partial_update(self, serializer):
		serializer.save(modified_by=self.request.user)



## Just expose the ability to GET these objects
class TransientHostRankList(generics.ListAPIView):
	queryset = TransientHostRank.objects.all()
	serializer_class = TransientHostRankSerializer

class StatusList(generics.ListAPIView):
	queryset = Status.objects.all()
	serializer_class = StatusSerializer

class ObservationGroupList(generics.ListAPIView):
	queryset = ObservationGroup.objects.all()
	serializer_class = ObservationGroupSerializer

class SEDTypeList(generics.ListAPIView):
	queryset = SEDType.objects.all()
	serializer_class = SEDTypeSerializer

class HostMorphologyList(generics.ListAPIView):
	queryset = HostMorphology.objects.all()
	serializer_class = HostMorphologySerializer

class PhaseList(generics.ListAPIView):
	queryset = Phase.objects.all()
	serializer_class = PhaseSerializer

class TransientClassList(generics.ListAPIView):
	queryset = TransientClass.objects.all()
	serializer_class = TransientClassSerializer

class HostClassList(generics.ListAPIView):
	queryset = HostClass.objects.all()
	serializer_class = HostClassSerializer

class ClassicalNightTypeList(generics.ListAPIView):
	queryset = ClassicalNightType.objects.all()
	serializer_class = ClassicalNightTypeSerializer

class InformationSourceList(generics.ListAPIView):
	queryset = InformationSource.objects.all()
	serializer_class = InformationSourceSerializer