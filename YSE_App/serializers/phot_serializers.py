from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientPhotometrySerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), allow_null=True, required=False, view_name='host-detail')
	followup = serializers.HyperlinkedRelatedField(queryset=TransientFollowup.objects.all(), allow_null=True, required=False, view_name='transientfollowup-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientPhotometry
		fields = ('url', 'id', 'transient', 'instrument', 'obs_group', 'host', 'followup',
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return TransientPhotometry.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.host_id = validated_data.get('host', instance.host)
		instance.followup_id = validated_data.get('followup', instance.followup)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class HostPhotometrySerializer(serializers.HyperlinkedModelSerializer):
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), view_name='host-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	followup = serializers.HyperlinkedRelatedField(queryset=HostFollowup.objects.all(), allow_null=True, required=False, view_name='hostfollowup-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostPhotometry
		fields = ('url', 'id', 'host', 'instrument', 'obs_group', 'followup',
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return HostPhotometry.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.host_id = validated_data.get('host', instance.host)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.followup_id = validated_data.get('followup', instance.followup)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class TransientPhotDataSerializer(serializers.HyperlinkedModelSerializer):
	photometry = serializers.HyperlinkedRelatedField(queryset=TransientPhotometry.objects.all(), view_name='transientphotometry-detail')
	band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientPhotData
		fields = ('url', 'id', 'photometry', 'band', 'obs_date', 'flux_zero_point', 
			'flux', 'flux_err', 'mag', 'mag_err', 'forced', 'dq', 'created_by', 
			'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return TransientPhotData.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.photometry_id = validated_data.get('host', instance.photometry)
		instance.band_id = validated_data.get('obs_group', instance.band)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.flux_zero_point = validated_data.get('flux_zero_point', instance.flux_zero_point)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)
		instance.mag = validated_data.get('mag', instance.mag)
		instance.mag_err = validated_data.get('mag_err', instance.mag_err)
		instance.forced = validated_data.get('forced', instance.forced)
		instance.dq = validated_data.get('dq', instance.dq)

		instance.save()

		return instance

class HostPhotDataSerializer(serializers.HyperlinkedModelSerializer):
	photometry = serializers.HyperlinkedRelatedField(queryset=HostPhotometry.objects.all(), view_name='hostphotometry-detail')
	band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostPhotometry
		fields = ('url', 'id', 'photometry', 'band', 'obs_date', 'flux_zero_point', 
			'flux', 'flux_err', 'mag', 'mag_err', 'forced', 'dq', 'created_by', 
			'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return HostPhotometry.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.photometry_id = validated_data.get('host', instance.photometry)
		instance.band_id = validated_data.get('obs_group', instance.band)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.flux_zero_point = validated_data.get('flux_zero_point', instance.flux_zero_point)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)
		instance.mag = validated_data.get('mag', instance.mag)
		instance.mag_err = validated_data.get('mag_err', instance.mag_err)
		instance.forced = validated_data.get('forced', instance.forced)
		instance.dq = validated_data.get('dq', instance.dq)

		instance.save()

		return instance

class TransientImageSerializer(serializers.HyperlinkedModelSerializer):
	phot_data = serializers.HyperlinkedRelatedField(queryset=TransientPhotData.objects.all(), view_name='transientphotdata-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientImage
		fields = ('url', 'id', 'phot_data', 'img_file', 'zero_point', 'zero_point_err', 
			'sky', 'sky_rms', 'dcmp_file', 'created_by', 'created_date', 'modified_by', 
			'modified_date')

	def create(self, validated_data):
		return TransientImage.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.phot_data_id = validated_data.get('phot_data', instance.phot_data)
		
		instance.img_file = validated_data.get('img_file', instance.img_file)
		instance.zero_point = validated_data.get('zero_point', instance.zero_point)
		instance.zero_point_err = validated_data.get('zero_point_err', instance.zero_point_err)
		instance.sky = validated_data.get('sky', instance.sky)
		instance.sky_rms = validated_data.get('sky_rms', instance.sky_rms)
		instance.dcmp_file = validated_data.get('dcmp_file', instance.dcmp_file)

		instance.save()

		return instance

class HostImageSerializer(serializers.HyperlinkedModelSerializer):
	phot_data = serializers.HyperlinkedRelatedField(queryset=HostPhotData.objects.all(), view_name='hostphotdata-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostImage
		fields = ('url', 'id', 'phot_data', 'img_file', 'zero_point', 'zero_point_err', 
			'sky', 'sky_rms', 'dcmp_file', 'created_by', 'created_date', 'modified_by', 
			'modified_date')

	def create(self, validated_data):
		return HostImage.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.phot_data_id = validated_data.get('phot_data', instance.phot_data)
		
		instance.img_file = validated_data.get('img_file', instance.img_file)
		instance.zero_point = validated_data.get('zero_point', instance.zero_point)
		instance.zero_point_err = validated_data.get('zero_point_err', instance.zero_point_err)
		instance.sky = validated_data.get('sky', instance.sky)
		instance.sky_rms = validated_data.get('sky_rms', instance.sky_rms)
		instance.dcmp_file = validated_data.get('dcmp_file', instance.dcmp_file)

		instance.save()

		return instance