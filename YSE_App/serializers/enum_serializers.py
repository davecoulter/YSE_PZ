from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientHostRankSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientHostRank
		fields = ('id', 'rank', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

	def create(self, validated_data):
		return TransientHostRank.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.rank = validated_data.get('rank', instance.rank)
		instance.save()
		return instance

class TransientStatusSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientStatus
		fields = ('url', 'id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('url', 'id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('url', 'id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('url', 'id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('url', 'id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

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
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

	def create(self, validated_data):
		return InformationSource.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance