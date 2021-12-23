from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

#class SimpleTransientSpecRequestSerializer(serializers.HyperlinkedModelSerializer):
#	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
#	status = serializers.HyperlinkedRelatedField(queryset=FollowupStatus.objects.all(), view_name='followupstatus-detail')
#
#	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
#	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
#
#	class Meta:
#		model = SimpleTransientSpecRequest
#		fields = "__all__"
#
#	def create(self, validated_data):
#		return SimpleTransientSpecRequest.objects.create(**validated_data)
#
#	def update(self, instance, validated_data):
#		instance.transient_id = validated_data.get('transient', instance.transient)
#		instance.status_id = validated_data.get('status', instance.status)
#
#		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
#		
#		instance.save()
#
#		return instance

class TransientFollowupSerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	status = serializers.HyperlinkedRelatedField(queryset=FollowupStatus.objects.all(), view_name='followupstatus-detail')

	too_resource = serializers.HyperlinkedRelatedField(queryset=ToOResource.objects.all(), allow_null=True, required=False, view_name='tooresource-detail')
	classical_resource = serializers.HyperlinkedRelatedField(queryset=ClassicalResource.objects.all(), allow_null=True, required=False, view_name='classicalresource-detail') #, lookup_field="id")
	queued_resource = serializers.HyperlinkedRelatedField(queryset=QueuedResource.objects.all(), allow_null=True, required=False, view_name='queuedresource-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientFollowup
		fields = "__all__"

	def create(self, validated_data):
		return TransientFollowup.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.status_id = validated_data.get('status', instance.status)
		instance.too_resource_id = validated_data.get('too_resource', instance.too_resource)
		instance.classical_resource_id = validated_data.get('classical_resource', instance.classical_resource)
		instance.queued_resource_id = validated_data.get('queued_resource', instance.queued_resource)

		instance.valid_start = validated_data.get('valid_start', instance.valid_start)
		instance.valid_stop = validated_data.get('valid_stop', instance.valid_stop)
		instance.spec_priority = validated_data.get('spec_priority', instance.spec_priority)
		instance.phot_priority = validated_data.get('phot_priority', instance.phot_priority)
		instance.offset_star_ra = validated_data.get('offset_star_ra', instance.offset_star_ra)
		instance.offset_star_dec = validated_data.get('offset_star_dec', instance.offset_star_dec)
		instance.offset_north = validated_data.get('offset_north', instance.offset_north)
		instance.offset_east = validated_data.get('offset_east', instance.offset_east)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class HostFollowupSerializer(serializers.HyperlinkedModelSerializer):
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), view_name='host-detail', lookup_field="id")
	status = serializers.HyperlinkedRelatedField(queryset=FollowupStatus.objects.all(), view_name='followupstatus-detail')

	too_resource = serializers.HyperlinkedRelatedField(queryset=ToOResource.objects.all(), allow_null=True, required=False, view_name='tooresource-detail')
	classical_resource = serializers.HyperlinkedRelatedField(queryset=ClassicalResource.objects.all(), allow_null=True, required=False, view_name='classicalresource-detail', lookup_field="id")
	queued_resource = serializers.HyperlinkedRelatedField(queryset=QueuedResource.objects.all(), allow_null=True, required=False, view_name='queuedresource-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostFollowup
		fields = "__all__"

	def create(self, validated_data):
		return HostFollowup.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.host_id = validated_data.get('transient', instance.transient)
		instance.status_id = validated_data.get('status', instance.status)
		instance.too_resource_id = validated_data.get('too_resource', instance.too_resource)
		instance.classical_resource_id = validated_data.get('classical_resource', instance.classical_resource)
		instance.queued_resource_id = validated_data.get('queued_resource', instance.queued_resource)

		instance.valid_start = validated_data.get('valid_start', instance.valid_start)
		instance.valid_stop = validated_data.get('valid_stop', instance.valid_stop)
		instance.spec_priority = validated_data.get('spec_priority', instance.spec_priority)
		instance.phot_priority = validated_data.get('phot_priority', instance.phot_priority)
		instance.offset_star_ra = validated_data.get('offset_star_ra', instance.offset_star_ra)
		instance.offset_star_dec = validated_data.get('offset_star_dec', instance.offset_star_dec)
		instance.offset_north = validated_data.get('offset_north', instance.offset_north)
		instance.offset_east = validated_data.get('offset_east', instance.offset_east)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance
