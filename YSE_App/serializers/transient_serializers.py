from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientSerializer(serializers.HyperlinkedModelSerializer):
	status = serializers.PrimaryKeyRelatedField(queryset=Status.objects.all())
	obs_group = serializers.PrimaryKeyRelatedField(queryset=ObservationGroup.objects.all())

	non_detect_band = serializers.PrimaryKeyRelatedField(queryset=PhotometricBand.objects.all(), allow_null=True)
	best_spec_class = serializers.PrimaryKeyRelatedField(queryset=TransientClass.objects.all(), allow_null=True)
	photo_class = serializers.PrimaryKeyRelatedField(queryset=TransientClass.objects.all(), allow_null=True)
	best_spectrum = serializers.PrimaryKeyRelatedField(queryset=TransientSpectrum.objects.all(), allow_null=True)
	host = serializers.PrimaryKeyRelatedField(queryset=Host.objects.all(), allow_null=True)
	abs_mag_peak_band = serializers.PrimaryKeyRelatedField(queryset=PhotometricBand.objects.all(), allow_null=True)

	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

	class Meta:
		model = Transient
		fields = ('id', 'status', 'obs_group', 'non_detect_band',
			'best_spec_class', 'photo_class', 'best_spectrum', 'host',
			'abs_mag_peak_band', 'name', 'ra', 'dec', 'disc_date',
			'candidate_hosts', 'redshift', 'redshift_err', 'redshift_source',
			'non_detect_date', 'non_detect_limit', 'mw_ebv', 'abs_mag_peak',
			'abs_mag_peak_date', 'postage_stamp_file', 'created_by', 'modified_by')

	def create(self, validated_data):
		return Transient.objects.create(**validated_data)

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

		instance.save()

		return instance


class AlternateTransientNamesSerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.PrimaryKeyRelatedField(queryset=Transient.objects.all())
	obs_group = serializers.PrimaryKeyRelatedField(queryset=ObservationGroup.objects.all())

	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

	class Meta:
		model = AlternateTransientNames
		fields = ('id', 'transient', 'obs_group', 'name', 'description', 'created_by', 'modified_by')

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