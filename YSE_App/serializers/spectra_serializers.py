from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientSpectrumSerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')
	followup = serializers.HyperlinkedRelatedField(queryset=TransientFollowup.objects.all(), allow_null=True, required=False, view_name='transientfollowup-detail')
	spec_phase = serializers.HyperlinkedRelatedField(queryset=Phase.objects.all(), allow_null=True, required=False, view_name='phase-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientSpectrum
		fields = "__all__"

	def create(self, validated_data):
		return TransientSpectrum.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.followup_id = validated_data.get('followup', instance.followup)
		instance.spec_phase_id = validated_data.get('spec_phase', instance.spec_phase)

		instance.ra = validated_data.get('ra', instance.ra)
		instance.dec = validated_data.get('dec', instance.dec)
		instance.obs_date = validated_data.get('obs_date', instance.obs_date)
		instance.redshift = validated_data.get('redshift', instance.redshift)
		instance.redshift_err = validated_data.get('redshift_err', instance.redshift_err)
		instance.redshift_quality = validated_data.get('redshift_quality', instance.redshift_quality)
		instance.tdr = validated_data.get('tdr', instance.tdr)
		instance.spec_plot_file = validated_data.get('spec_plot_file', instance.spec_plot_file)
		instance.spec_data_file = validated_data.get('spec_data_file', instance.spec_data_file)
		instance.spectrum_notes = validated_data.get('spectrum_notes', instance.spectrum_notes)
		instance.rlap = validated_data.get('rlap', instance.rlap)
		instance.snid_plot_file = validated_data.get('snid_plot_file', instance.snid_plot_file)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class HostSpectrumSerializer(serializers.HyperlinkedModelSerializer):
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), view_name='host-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')
	followup = serializers.HyperlinkedRelatedField(queryset=HostFollowup.objects.all(), allow_null=True, required=False, view_name='hostfollowup-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostSpectrum
		fields = "__all__"

	def create(self, validated_data):
		return HostSpectrum.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.host_id = validated_data.get('host', instance.host)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.followup_id = validated_data.get('followup', instance.followup)

		instance.ra = validated_data.get('ra', instance.ra)
		instance.dec = validated_data.get('dec', instance.dec)
		instance.obs_date = validated_data.get('obs_date', instance.obs_date)
		instance.redshift = validated_data.get('redshift', instance.redshift)
		instance.redshift_err = validated_data.get('redshift_err', instance.redshift_err)
		instance.redshift_quality = validated_data.get('redshift_quality', instance.redshift_quality)
		instance.tdr = validated_data.get('tdr', instance.tdr)
		instance.spec_plot_file = validated_data.get('spec_plot_file', instance.spec_plot_file)
		instance.spec_data_file = validated_data.get('spec_data_file', instance.spec_data_file)
		instance.spectrum_notes = validated_data.get('spectrum_notes', instance.spectrum_notes)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class TransientSpecDataSerializer(serializers.HyperlinkedModelSerializer):
	spectrum = serializers.HyperlinkedRelatedField(queryset=TransientSpectrum.objects.all(), view_name='transientspectrum-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientSpecData
		fields = "__all__"

	def create(self, validated_data):
		return TransientSpecData.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.spectrum_id = validated_data.get('spectrum', instance.spectrum)

		instance.wavelength = validated_data.get('wavelength', instance.wavelength)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.wavelength_err = validated_data.get('wavelength_err', instance.wavelength_err)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class HostSpecDataSerializer(serializers.HyperlinkedModelSerializer):
	spectrum = serializers.HyperlinkedRelatedField(queryset=HostSpectrum.objects.all(), view_name='hostspectrum-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostSpecData
		fields = "__all__"

	def create(self, validated_data):
		return HostSpecData.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.spectrum_id = validated_data.get('spectrum', instance.spectrum)

		instance.wavelength = validated_data.get('wavelength', instance.wavelength)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.wavelength_err = validated_data.get('wavelength_err', instance.wavelength_err)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance