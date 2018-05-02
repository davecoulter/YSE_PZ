from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientStatusSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientStatus
		fields = "__all__"

	def create(self, validated_data):
		return TransientStatus.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class FollowupStatusSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = FollowupStatus
		fields = "__all__"

	def create(self, validated_data):
		return FollowupStatus.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class TaskStatusSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TaskStatus
		fields = "__all__"

	def create(self, validated_data):
		return TaskStatus.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class AntaresClassificationSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = AntaresClassification
		fields = "__all__"

	def create(self, validated_data):
		return AntaresClassification.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class InternalSurveySerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = InternalSurvey
		fields = "__all__"

	def create(self, validated_data):
		return TaskStatus.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class ObservationGroupSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ObservationGroup
		fields = "__all__"

	def create(self, validated_data):
		return ObservationGroup.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class SEDTypeSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = SEDType
		fields = "__all__"

	def create(self, validated_data):
		return SEDType.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class HostMorphologySerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostMorphology
		fields = "__all__"

	def create(self, validated_data):
		return HostMorphology.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class PhaseSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Phase
		fields = "__all__"

	def create(self, validated_data):
		return Phase.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class TransientClassSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientClass
		fields = "__all__"
		extra_kwargs = {
			'url': {'view_name': 'transientclass-detail', 'lookup_field': 'id'}
		}

	def create(self, validated_data):
		return TransientClass.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class ClassicalNightTypeSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ClassicalNightType
		fields = "__all__"

	def create(self, validated_data):
		return ClassicalNightType.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class InformationSourceSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = InformationSource
		fields = "__all__"

	def create(self, validated_data):
		return InformationSource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class WebAppColorSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = WebAppColor
		fields = "__all__"

	def create(self, validated_data):
		return WebAppColor.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.color = validated_data.get('color', instance.color)
		instance.save()
		return instance

class UnitSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Unit
		fields = "__all__"

	def create(self, validated_data):
		return Unit.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.unit = validated_data.get('unit', instance.unit)
		instance.save()
		return instance
