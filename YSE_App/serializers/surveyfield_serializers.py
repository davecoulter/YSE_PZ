from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class SurveyFieldSerializer(serializers.HyperlinkedModelSerializer):
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail',lookup_field="id")

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = SurveyField
		fields = "__all__"

	def create(self, validated_data):
		return SurveyField.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.obs_group = validated_data.get('obs_group', instance.obs_group)
		instance.field_id = validated_data.get('field_id', instance.field_id)
		instance.first_mjd = validated_data.get('first_mjd', instance.first_mjd)
		instance.last_mjd = validated_data.get('last_mjd', instance.last_mjd)
		instance.cadence = validated_data.get('cadence', instance.cadence)
		instance.instrument = validated_data.get('instrument', instance.instrument)
		instance.ztf_field_id = validated_data.get('ztf_field_id', instance.ztf_field_id)

		instance.ra_cen = validated_data.get('ra_cen', instance.ra_cen)
		instance.dec_cen = validated_data.get('dec_cen', instance.dec_cen)
		instance.width_deg = validated_data.get('width_deg', instance.width_deg)
		instance.height_deg = validated_data.get('height_deg', instance.height_deg)
		
		instance.save()

		return instance

class SurveyObservationTaskSerializer(serializers.HyperlinkedModelSerializer):
	survey_field = serializers.HyperlinkedRelatedField(queryset=SurveyField.objects.all(), view_name='surveyfield-detail')
	status = serializers.HyperlinkedRelatedField(queryset=TaskStatus.objects.all(), view_name='taskstatus-detail')
	requested_photometric_band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail',lookup_field="id")
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = SurveyObservationTask
		fields = "__all__"

	def create(self, validated_data):
		return SurveyObservationTask.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.survey_field = validated_data.get('survey_field', instance.survey_field)
		instance.mjd_requested = validated_data.get('mjd_requested', instance.mjd_requested)
		instance.status = validated_data.get('status', instance.status)
		instance.requested_exposure_time = validated_data.get('requested_exposure_time', instance.requested_exposure_time)
		instance.requested_photometric_band = validated_data.get('requested_photometric_band', instance.requested_photometric_band)
		
		instance.save()

		return instance

class SurveyObservationSerializer(serializers.HyperlinkedModelSerializer):
	survey_observation_task = serializers.HyperlinkedRelatedField(queryset=SurveyObservation.objects.all(), view_name='surveyobservationtask-detail')
	status = serializers.HyperlinkedRelatedField(queryset=TaskStatus.objects.all(), view_name='taskstatus-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail',lookup_field="id")
	requested_photometric_band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail',lookup_field="id")
	
	class Meta:
		model = SurveyObservation
		fields = "__all__"

	def create(self, validated_data):
		return SurveyObservation.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.obs_mjd = validated_data.get('obs_mjd', instance.obs_mjd)
		instance.survey_observation_task = validated_data.get('survey_observation_task', instance.survey_observation_task)
		instance.status = validated_data.get('status', instance.status)
		instance.instrument = validated_data.get('instrument', instance.instrument)
		instance.exposure_time = validated_data.get('exposure_time', instance.exposure_time)
		instance.photometric_band = validated_data.get('photometric_band', instance.photometric_band)
		instance.pos_angle_deg = validated_data.get('pos_angle_deg', instance.pos_angle_deg)

		instance.fwhm = validated_data.get('fwhm', instance.fwhm)
		instance.eccentricity = validated_data.get('eccentricity', instance.eccentricity)
		instance.airmass = validated_data.get('airmass', instance.airmass)
		instance.image_id = validated_data.get('image_id', instance.image_id)
		
		instance.save()

		return instance

