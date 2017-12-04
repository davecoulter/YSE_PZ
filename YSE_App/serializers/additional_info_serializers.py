from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientWebResourceSerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	information_source = serializers.HyperlinkedRelatedField(queryset=InformationSource.objects.all(), view_name='informationsource-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientWebResource
		fields = "__all__"

	def create(self, validated_data):
		return TransientWebResource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.information_source_id = validated_data.get('information_source', instance.information_source)
		
		instance.information_text = validated_data.get('information_text', instance.information_text)
		instance.resource_url = validated_data.get('resource_url', instance.resource_url)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class HostWebResourceSerializer(serializers.HyperlinkedModelSerializer):
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), view_name='host-detail')
	information_source = serializers.HyperlinkedRelatedField(queryset=InformationSource.objects.all(), view_name='informationsource-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostWebResource
		fields = "__all__"

	def create(self, validated_data):
		return HostWebResource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.host_id = validated_data.get('host', instance.host)
		instance.information_source_id = validated_data.get('information_source', instance.information_source)

		instance.information_text = validated_data.get('information_text', instance.information_text)
		instance.resource_url = validated_data.get('resource_url', instance.resource_url)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance