from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class ToOResourceSerializer(serializers.HyperlinkedModelSerializer):
	telescope = serializers.HyperlinkedRelatedField(queryset=Telescope.objects.all(), view_name='telescope-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ToOResource
		fields = ('url', 'id', 'telescope', 'begin_date_valid', 'end_date_valid',
			'awarded_too_hours', 'used_too_hours', 'description'
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return ToOResource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.telescope_id = validated_data.get('telescope', instance.telescope)

		instance.begin_date_valid = validated_data.get('begin_date_valid', instance.begin_date_valid)
		instance.end_date_valid = validated_data.get('end_date_valid', instance.end_date_valid)
		instance.awarded_too_hours = validated_data.get('awarded_too_hours', instance.awarded_too_hours)
		instance.used_too_hours = validated_data.get('used_too_hours', instance.used_too_hours)
		instance.description = validated_data.get('description', instance.description)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class QueuedResourceSerializer(serializers.HyperlinkedModelSerializer):
	telescope = serializers.HyperlinkedRelatedField(queryset=Telescope.objects.all(), view_name='telescope-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = QueuedResource
		fields = ('url', 'id', 'telescope', 'begin_date_valid', 'end_date_valid',
			'awarded_too_hours', 'used_too_hours', 'description'
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return QueuedResource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.telescope_id = validated_data.get('telescope', instance.telescope)

		instance.begin_date_valid = validated_data.get('begin_date_valid', instance.begin_date_valid)
		instance.end_date_valid = validated_data.get('end_date_valid', instance.end_date_valid)
		instance.awarded_too_hours = validated_data.get('awarded_too_hours', instance.awarded_too_hours)
		instance.used_too_hours = validated_data.get('used_too_hours', instance.used_too_hours)
		instance.description = validated_data.get('description', instance.description)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class ClassicalResourceSerializer(serializers.HyperlinkedModelSerializer):
	telescope = serializers.HyperlinkedRelatedField(queryset=Telescope.objects.all(), view_name='telescope-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ClassicalResource
		fields = ('url', 'id', 'telescope', 'begin_date_valid', 'end_date_valid',
			'description'
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return ClassicalResource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.telescope_id = validated_data.get('telescope', instance.telescope)

		instance.begin_date_valid = validated_data.get('begin_date_valid', instance.begin_date_valid)
		instance.end_date_valid = validated_data.get('end_date_valid', instance.end_date_valid)
		instance.description = validated_data.get('description', instance.description)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class ClassicalObservingDateSerializer(serializers.HyperlinkedModelSerializer):
	resource = serializers.HyperlinkedRelatedField(queryset=ClassicalResource.objects.all(), view_name='classicalresource-detail')
	night_type = serializers.HyperlinkedRelatedField(queryset=ClassicalNightType.objects.all(), view_name='classicalnighttype-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ClassicalObservingDate
		fields = ('url', 'id', 'resource', 'night_type', 'obs_date',
			'created_by', 'created_date', 'modified_by', 'modified_date')

	def create(self, validated_data):
		return ClassicalObservingDate.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.resource_id = validated_data.get('resource', instance.resource)
		instance.night_type_id = validated_data.get('night_type', instance.night_type)

		instance.obs_date = validated_data.get('obs_date', instance.obs_date)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance