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
from .data import PhotometryService, SpectraService, ObservingResourceService

from django_filters.rest_framework import DjangoFilterBackend,filters
import django_filters

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

### `SurveyField` Filter Set ###
class SurveyFieldFilter(django_filters.FilterSet):
	field_id = django_filters.Filter(name="field_id")
	obs_group = django_filters.Filter(name="obs_group__name")
	class Meta:
		model = SurveyField
		fields = ()

### `SurveyFieldMSB` Filter Set ###
class SurveyFieldMSBFilter(django_filters.FilterSet):
	name = django_filters.Filter(name="name")
	active = django_filters.Filter(name="active")
	class Meta:
		model = SurveyFieldMSB
		fields = ('name','active')
        
### `SurveyField ViewSets` ###
class SurveyFieldViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = SurveyField.objects.all()
	serializer_class = SurveyFieldSerializer
	permission_classes = (permissions.IsAuthenticated,)
	filter_backends = (DjangoFilterBackend,)
	filter_class = SurveyFieldFilter


class SurveyFieldMSBViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet): #viewsets.ReadOnlyModelViewSet):
	queryset = SurveyFieldMSB.objects.all()
	serializer_class = SurveyFieldMSBSerializer
	permission_classes = (permissions.IsAuthenticated,)
	filter_backends = (DjangoFilterBackend,)
	filter_class = SurveyFieldMSBFilter
    
### `Transient` Filter Set ###
class SurveyObsFilter(django_filters.FilterSet):
	status_in = django_filters.BaseInFilter(name="status__name")#, lookup_expr='in')
	obs_mjd_gte = django_filters.Filter(name="obs_mjd", lookup_expr='gte')
	obs_mjd_lte = django_filters.Filter(name="obs_mjd", lookup_expr='lte')
	mjd_requested_gte = django_filters.Filter(name="mjd_requested", lookup_expr='gte')
	mjd_requested_lte = django_filters.Filter(name="mjd_requested", lookup_expr='lte')
	survey_field = django_filters.BaseInFilter(name="survey_field__field_id")
	obs_group = django_filters.BaseInFilter(name="survey_field__obs_group__name")
	
	class Meta:
		model = SurveyObservation
		fields = ()

	
class SurveyObservationViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = SurveyObservation.objects.all()
	serializer_class = SurveyObservationSerializer
	permission_classes = (permissions.IsAuthenticated,)
	filter_backends = (DjangoFilterBackend,)
	filter_class = SurveyObsFilter
	
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
	lookup_field = "id"
	permission_classes = (permissions.IsAuthenticated,)

class ClassicalNightTypeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ClassicalNightType.objects.all()
	serializer_class = ClassicalNightTypeSerializer
	permission_classes = (permissions.IsAuthenticated,)

class WebAppColorViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = WebAppColor.objects.all()
	serializer_class = WebAppColorSerializer
	permission_classes = (permissions.IsAuthenticated,)

class UnitViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Unit.objects.all()
	serializer_class = UnitSerializer
	permission_classes = (permissions.IsAuthenticated,)

class DataQualityViewSet(viewsets.ReadOnlyModelViewSet):
		queryset = DataQuality.objects.all()
		serializer_class = DataQualitySerializer
		permission_classes = (permissions.IsAuthenticated,)

class InformationSourceViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = InformationSource.objects.all()
	serializer_class = InformationSourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Followup` ViewSets ###
#class SimpleTransientSpecRequestViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
#	queryset = SimpleTransientSpecRequest.objects.all()
#	serializer_class = SimpleTransientSpecRequestSerializer
#	permission_classes = (permissions.IsAuthenticated,)

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
	lookup_field = "id"
	permission_classes = (permissions.IsAuthenticated,)

class HostSEDViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = HostSED.objects.all()
	serializer_class = HostSEDSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Instrument` ViewSets ###
class InstrumentViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Instrument.objects.all()
	serializer_class = InstrumentSerializer
	lookup_field = "id"
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

class YSEOnCallDateViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = YSEOnCallDate.objects.all()
	serializer_class = YSEOnCallDateSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Phot` ViewSets ###
class TransientPhotometryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = TransientPhotometrySerializer
	permission_classes = (permissions.IsAuthenticated,)
	lookup_field = "id"

	def get_queryset(self):
		allowed_phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser(self.request.user)
		return allowed_phot

class HostPhotometryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = HostPhotometrySerializer
	permission_classes = (permissions.IsAuthenticated,)
	lookup_field = "id"

	def get_queryset(self):
		allowed_phot = PhotometryService.GetAuthorizedHostPhotometry_ByUser(self.request.user)
		return allowed_phot

class TransientPhotDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = TransientPhotDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_phot_data = PhotometryService.GetAuthorizedTransientPhotData_ByUser(self.request.user)
		return allowed_phot_data


class HostPhotDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = HostPhotDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_phot_data = PhotometryService.GetAuthorizedHostPhotData_ByUser(self.request.user)
		return allowed_phot_data



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
	lookup_field = "id"
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

### `UserQuery` ViewSets ###
class UserQueryViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = UserQuery.objects.all()
	serializer_class = UserQuerySerializer
	permission_classes = (permissions.IsAuthenticated,)

### `UserTelescopeToFollow` ViewSets ###
class UserTelescopeToFollowViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = UserTelescopeToFollow.objects.all()
	serializer_class = UserTelescopeToFollowSerializer
	permission_classes = (permissions.IsAuthenticated,)

	
### `Spectra` ViewSets ###
class TransientSpectrumViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = TransientSpectrumSerializer
	permission_classes = (permissions.IsAuthenticated,)
	lookup_field = "id"

	def get_queryset(self):
		allowed_spec = SpectraService.GetAuthorizedTransientSpectrum_ByUser(self.request.user)
		return allowed_spec

class HostSpectrumViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = HostSpectrumSerializer
	permission_classes = (permissions.IsAuthenticated,)
	lookup_field = "id"

	def get_queryset(self):
		allowed_spec = SpectraService.GetAuthorizedHostSpectrum_ByUser(self.request.user)
		return allowed_spec

class TransientSpecDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = TransientSpecDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_spec_data = SpectraService.GetAuthorizedTransientSpecData_ByUser(self.request.user)
		return allowed_spec_data

class HostSpecDataViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = HostSpecDataSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_spec_data = SpectraService.GetAuthorizedHostSpecData_ByUser(self.request.user)
		return allowed_spec_data

### `Telescope Resource` ViewSets ###
class ToOResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = ToOResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_resource = ObservingResourceService.GetAuthorizedToOResource_ByUser(self.request.user)
		return allowed_resource

class QueuedResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = QueuedResourceSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_resource = ObservingResourceService.GetAuthorizedQueuedResource_ByUser(self.request.user)
		return allowed_resource

class ClassicalResourceViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = ClassicalResourceSerializer
	lookup_field = "id"
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_resource = ObservingResourceService.GetAuthorizedClassicalResource_ByUser(self.request.user)
		return allowed_resource

class ClassicalObservingDateViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	serializer_class = ClassicalObservingDateSerializer
	permission_classes = (permissions.IsAuthenticated,)

	def get_queryset(self):
		allowed_resource = ObservingResourceService.GetAuthorizedClassicalObservingDate_ByUser(self.request.user)
		return allowed_resource

### `Telescope` ViewSets ###
class TelescopeViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Telescope.objects.all()
	serializer_class = TelescopeSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Transient` Filter Set ###
class TransientFilter(django_filters.FilterSet):
	created_date_gte = django_filters.DateTimeFilter(name="created_date", lookup_expr='gte')
	modified_date_gte = django_filters.DateTimeFilter(name="modified_date", lookup_expr='gte')
	status_in = django_filters.BaseInFilter(name="status__name")#, lookup_expr='in')
	ra_gte = django_filters.Filter(name="ra", lookup_expr='gte')
	ra_lte = django_filters.Filter(name="ra", lookup_expr='lte')
	dec_gte = django_filters.Filter(name="dec", lookup_expr='gte')
	dec_lte = django_filters.Filter(name="dec", lookup_expr='lte')
	tag_in = django_filters.BaseInFilter(name="tags__name")
	name = django_filters.Filter(name="name")

	class Meta:
		model = Transient
		fields = ('created_date','modified_date')

### `Transient` ViewSets ###
class TransientViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = Transient.objects.all()
	serializer_class = TransientSerializer
	permission_classes = (permissions.IsAuthenticated,)
	filter_backends = (DjangoFilterBackend,)
	filter_class = TransientFilter
	#filter_fields = ('status','created_date','modified_date','mw_ebv','status__name')

class AlternateTransientNamesViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = AlternateTransientNames.objects.all()
	serializer_class = AlternateTransientNamesSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `User` ViewSets ###
class UserViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Group` ViewSets ###
class GroupViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Group.objects.all()
	serializer_class = GroupSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `Tag` ViewSets ###
class TransientTagViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = TransientTag.objects.all()
	serializer_class = TransientTagSerializer
	permission_classes = (permissions.IsAuthenticated,)

### `GW` ViewSets ###
class GWCandidateViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = GWCandidate.objects.all()
	serializer_class = GWCandidateSerializer
	permission_classes = (permissions.IsAuthenticated,)

class GWCandidateImageViewSet(custom_viewsets.ListCreateRetrieveUpdateViewSet):
	queryset = GWCandidateImage.objects.all()
	serializer_class = GWCandidateImageSerializer
	permission_classes = (permissions.IsAuthenticated,)
