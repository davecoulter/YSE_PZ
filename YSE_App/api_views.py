from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework import viewsets
from YSE_App.common import custom_viewsets
from rest_framework.reverse import reverse

from .models import *
from .serializers import *

### `Additional Info` ViewSets ###
class TransientWebResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientWebResource.objects.all()
	serializer_class = TransientWebResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostWebResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostWebResource.objects.all()
	serializer_class = HostWebResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Enum` ViewSets ###
# Only exposing GET
class TransientStatusViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TransientStatus.objects.all()
	serializer_class = TransientStatusSerializer
	permission_classes = (permissions.IsAuthenticated,)

class FollowupStatusViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = FollowupStatus.objects.all()
	serializer_class = FollowupStatusSerializer
	permission_classes = (permissions.IsAuthenticated,)

class TaskStatusViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TaskStatus.objects.all()
	serializer_class = TaskStatusSerializer
	permission_classes = (permissions.IsAuthenticated,)

class AntaresClassificationViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AntaresClassification.objects.all()
	serializer_class = AntaresClassificationSerializer
	permission_classes = (permissions.IsAuthenticated,)

class InternalSurveyViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = InternalSurvey.objects.all()
	serializer_class = InternalSurveySerializer
	permission_classes = (permissions.IsAuthenticated,)

class ObservationGroupViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ObservationGroup.objects.all()
	serializer_class = ObservationGroupSerializer
	permission_classes = (permissions.IsAuthenticated,)

class SEDTypeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = SEDType.objects.all()
	serializer_class = SEDTypeSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostMorphologyViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = HostMorphology.objects.all()
	serializer_class = HostMorphologySerializer
	permission_classes = (permissions.IsAuthenticated,)

class PhaseViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Phase.objects.all()
	serializer_class = PhaseSerializer
	permission_classes = (permissions.IsAuthenticated,)

class TransientClassViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TransientClass.objects.all()
	serializer_class = TransientClassSerializer
	permission_classes = (permissions.IsAuthenticated,)

class ClassicalNightTypeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ClassicalNightType.objects.all()
	serializer_class = ClassicalNightTypeSerializer
	permission_classes = (permissions.IsAuthenticated,)

class InformationSourceViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = InformationSource.objects.all()
	serializer_class = InformationSourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Followup` ViewSets ###
class TransientFollowupViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientFollowup.objects.all()
	serializer_class = TransientFollowupSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostFollowupViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostFollowup.objects.all()
	serializer_class = HostFollowupSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Host` ViewSets ###
class HostViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Host.objects.all()
	serializer_class = HostSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostSEDViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostSED.objects.all()
	serializer_class = HostSEDSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Instrument` ViewSets ###
class InstrumentViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Instrument.objects.all()
	serializer_class = InstrumentSerializer
	permission_classes = (permissions.IsAuthenticated,)

class InstrumentConfigViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = InstrumentConfig.objects.all()
	serializer_class = InstrumentConfigSerializer
	permission_classes = (permissions.IsAuthenticated,)

class ConfigElementViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = ConfigElement.objects.all()
	serializer_class = ConfigElementSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Log` ViewSets ###
class LogViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Log.objects.all()
	serializer_class = LogSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Observation Task` ViewSets ###
class TransientObservationTaskViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientObservationTask.objects.all()
	serializer_class = TransientObservationTaskSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostObservationTaskViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostObservationTask.objects.all()
	serializer_class = HostObservationTaskSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Observatory` ViewSets ###
class ObservatoryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Observatory.objects.all()
	serializer_class = ObservatorySerializer
	permission_classes = (permissions.IsAuthenticated,)

### `On Call Date` ViewSets ###
class OnCallDateViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = OnCallDate.objects.all()
	serializer_class = OnCallDateSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Phot` ViewSets ###
class TransientPhotometryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientPhotometry.objects.all()
	serializer_class = TransientPhotometrySerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostPhotometryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostPhotometry.objects.all()
	serializer_class = HostPhotometrySerializer
	permission_classes = (permissions.IsAuthenticated,)

class TransientPhotDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientPhotData.objects.all()
	serializer_class = TransientPhotDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostPhotDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostPhotData.objects.all()
	serializer_class = HostPhotDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

class TransientImageViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientImage.objects.all()
	serializer_class = TransientImageSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostImageViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostImage.objects.all()
	serializer_class = HostImageSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Photometric Band` ViewSets ###
class PhotometricBandViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = PhotometricBand.objects.all()
	serializer_class = PhotometricBandSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Principal Investigator` ViewSets ###
class PrincipalInvestigatorViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = PrincipalInvestigator.objects.all()
	serializer_class = PrincipalInvestigatorSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Profile` ViewSets ###
class ProfileViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Profile.objects.all()
	serializer_class = ProfileSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Spectra` ViewSets ###
class TransientSpectrumViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientSpectrum.objects.all()
	serializer_class = TransientSpectrumSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostSpectrumViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostSpectrum.objects.all()
	serializer_class = HostSpectrumSerializer
	permission_classes = (permissions.IsAuthenticated,)

class TransientSpecDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientSpecData.objects.all()
	serializer_class = TransientSpecDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

class HostSpecDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostSpecData.objects.all()
	serializer_class = HostSpecDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Telescope Resource` ViewSets ###
class ToOResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = ToOResource.objects.all()
	serializer_class = ToOResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

class QueuedResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = QueuedResource.objects.all()
	serializer_class = QueuedResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

class ClassicalResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = ClassicalResource.objects.all()
	serializer_class = ClassicalResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

class ClassicalObservingDateViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = ClassicalObservingDate.objects.all()
	serializer_class = ClassicalObservingDateSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Telescope` ViewSets ###
class TelescopeViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Telescope.objects.all()
	serializer_class = TelescopeSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Transient` ViewSets ###
class TransientViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer
	permission_classes = (permissions.IsAuthenticated,)

class AlternateTransientNamesViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = AlternateTransientNames.objects.all()
	serializer_class = AlternateTransientNamesSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `User` ViewSets ###
class UserViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = (permissions.IsAuthenticated,)