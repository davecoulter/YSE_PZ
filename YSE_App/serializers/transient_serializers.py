from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientSerializer(serializers.HyperlinkedModelSerializer):
	status = serializers.HyperlinkedRelatedField(queryset=TransientStatus.objects.all(), view_name='transientstatus-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	non_detect_band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), allow_null=True, required=False, view_name='photometricband-detail')
	best_spec_class = serializers.HyperlinkedRelatedField(queryset=TransientClass.objects.all(), allow_null=True, required=False, view_name='transientclass-detail', lookup_field="id")
	photo_class = serializers.HyperlinkedRelatedField(queryset=TransientClass.objects.all(), allow_null=True, required=False, view_name='transientclass-detail', lookup_field="id")
	best_spectrum = serializers.HyperlinkedRelatedField(queryset=TransientSpectrum.objects.all(), allow_null=True, required=False, view_name='transientspectrum-detail')
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), allow_null=True, required=False, view_name='host-detail', lookup_field="id")
	abs_mag_peak_band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), allow_null=True, required=False, view_name='photometricband-detail')
	antares_classification = serializers.HyperlinkedRelatedField(queryset=AntaresClassification.objects.all(), allow_null=True, required=False, view_name='antaresclassification-detail')
	internal_survey = serializers.HyperlinkedRelatedField(queryset=InternalSurvey.objects.all(), allow_null=True, required=False, view_name='internalsurvey-detail')
	tags = serializers.HyperlinkedRelatedField(queryset=TransientTag.objects.all(), many=True, view_name='transienttag-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Transient
		fields = "__all__"

	def create(self, validated_data):

		tags_exist = 'tags' in validated_data.keys()
		transient_tags = None
		if tags_exist:
			transient_tags = validated_data.pop('tags')

		transient = Transient.objects.create(**validated_data)
		transient.save()

		if tags_exist:
			for tag in transient_tags:
				tag_result = TransientTag.objects.filter(pk=tag.id)
				if tag_result.exists():
					t = tag_result.first()
					transient.tags.add(t)

			transient.save()

		return transient

	def update(self, instance, validated_data):
		instance.status_id = validated_data.get('status', instance.status)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.non_detect_band_id = validated_data.get('non_detect_band', instance.non_detect_band)
		instance.best_spec_class_id = validated_data.get('best_spec_class', instance.best_spec_class)
		instance.photo_class_id = validated_data.get('photo_class', instance.photo_class)
		instance.best_spectrum_id = validated_data.get('best_spectrum', instance.best_spectrum)
		instance.host_id = validated_data.get('host', instance.host)
		instance.abs_mag_peak_band_id = validated_data.get('abs_mag_peak_band', instance.abs_mag_peak_band)
		instance.created_by_id = validated_data.get('created_by', instance.created_by)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.antares_classification_id = validated_data.get('antares_classification', instance.antares_classification)
		instance.internal_survey_id = validated_data.get('internal_survey', instance.internal_survey)

		instance.name = validated_data.get('name', instance.name)
		instance.ra = validated_data.get('ra', instance.ra)
		instance.dec = validated_data.get('dec', instance.dec)
		instance.disc_date = validated_data.get('disc_date', instance.disc_date)
		instance.candidate_hosts = validated_data.get('candidate_hosts', instance.candidate_hosts)
		instance.redshift = validated_data.get('redshift', instance.redshift)
		instance.redshift_err = validated_data.get('redshift_err', instance.redshift_err)
		instance.redshift_source = validated_data.get('redshift_source', instance.redshift_source)
		instance.non_detect_date = validated_data.get('non_detect_date', instance.non_detect_date)
		instance.non_detect_limit = validated_data.get('non_detect_limit', instance.non_detect_limit)

		instance.mw_ebv = validated_data.get('mw_ebv', instance.mw_ebv)
		instance.abs_mag_peak = validated_data.get('abs_mag_peak', instance.abs_mag_peak)
		instance.abs_mag_peak_date = validated_data.get('abs_mag_peak_date', instance.abs_mag_peak_date)
		instance.postage_stamp_file = validated_data.get('postage_stamp_file', instance.postage_stamp_file)
		instance.k2_validated = validated_data.get('k2_validated', instance.k2_validated)
		instance.k2_msg = validated_data.get('k2_msg', instance.k2_msg)
		instance.TNS_spec_class = validated_data.get('TNS_spec_class', instance.TNS_spec_class)

		if 'tags' in validated_data.keys():
			# Disassociate existing `Transient Tags`
			transient_tags = instance.tags.all()
			for tag in transient_tags:
				instance.tags.remove(tag)

			transient_tags = validated_data.pop('tags')
			for tag in transient_tags:
				tag_result = TransientTag.objects.filter(pk=tag.id)
				if tag_result.exists():
					t = tag_result.first()
					instance.tags.add(t)

		instance.save()

		return instance


class AlternateTransientNamesSerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = AlternateTransientNames
		fields = "__all__"

	def create(self, validated_data):
		return AlternateTransientNames.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.created_by_id = validated_data.get('created_by', instance.created_by)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.name = validated_data.get('name', instance.name)
		instance.description = validated_data.get('description', instance.description)
		
		instance.save()

		return instance
