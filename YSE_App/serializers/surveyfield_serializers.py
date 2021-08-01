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

class SurveyFieldMSBSerializer(serializers.ModelSerializer):
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')
#	survey_fields = serializers.HyperlinkedRelatedField(queryset=SurveyField.objects.all(), many=True, view_name='surveyfield-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = SurveyFieldMSB
		fields = "__all__"
		depth = 1

	def create(self, validated_data):

		survey_fields_exist = 'survey_fields' in validated_data.keys()
		survey_fields = None
		if survey_fields_exist:
			survey_fields = validated_data.pop('survey_fields')

		surveyfieldmsb = SurveyFieldMSB.objects.create(**validated_data)
		surveyfieldmsb.save()
		instance.active = validated_data.get('active', instance.active)
        
		if survey_fields_exist:
			for field in survey_fields:
				survey_field_result = SurveyField.objects.filter(pk=tag.id)
				if survey_field_result.exists():
					s = survey_field_result.first()
					surveyfieldmsb.tags.add(s)

			surveyfieldmsb.save()
		
		return surveyfieldmsb

	def update(self, instance, validated_data):
		instance.obs_group = validated_data.get('obs_group', instance.obs_group)
		instance.name = validated_data.get('name', instance.name)
		instance.active = validated_data.get('active', instance.active)
		
		if 'survey_fields' in validated_data.keys():
			# Disassociate existing `Transient Tags`
			survey_fields = instance.survey_fields.all()
			for field in survey_fields:
				instance.survey_fields.remove(field)

			survey_fields = validated_data.pop('tags')
			for field in survey_fields:
				survey_field_result = SurveyField.objects.filter(pk=tag.id)
				if survey_field_result.exists():
					s = survey_field_result.first()
					instance.tags.add(s)
		
		instance.save()

		return instance

	
class SurveyObservationSerializer(serializers.HyperlinkedModelSerializer):
	survey_field = serializers.HyperlinkedRelatedField(queryset=SurveyField.objects.all(), view_name='surveyfield-detail')
	status = serializers.HyperlinkedRelatedField(queryset=TaskStatus.objects.all(), view_name='taskstatus-detail')
	photometric_band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail',lookup_field="id")
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = SurveyObservation
		fields = "__all__"
		depth = 1

	def create(self, validated_data):
		return SurveyObservation.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.mjd_requested = validated_data.get('mjd_requested', instance.mjd_requested)
		instance.obs_mjd = validated_data.get('obs_mjd', instance.obs_mjd)
		instance.survey_field = validated_data.get('survey_field', instance.survey_field)
		instance.status = validated_data.get('status', instance.status)
		instance.exposure_time = validated_data.get('exposure_time', instance.exposure_time)
		instance.photometric_band = validated_data.get('photometric_band', instance.photometric_band)

		instance.status = validated_data.get('status', instance.status)
		instance.pos_angle_deg = validated_data.get('pos_angle_deg', instance.pos_angle_deg)

		instance.fwhm_major = validated_data.get('fwhm', instance.fwhm_major)
		instance.eccentricity = validated_data.get('eccentricity', instance.eccentricity)
		instance.airmass = validated_data.get('airmass', instance.airmass)
		instance.image_id = validated_data.get('image_id', instance.image_id)

		instance.mag_lim = validated_data.get('mag_lim', instance.mag_lim)
		instance.zpt_obs = validated_data.get('zpt_obs', instance.zpt_obs)
		instance.quality = validated_data.get('quality', instance.quality)
		instance.n_good_skycell = validated_data.get('n_good_skycell', instance.n_good_skycell)		

		instance.save()

		return instance
