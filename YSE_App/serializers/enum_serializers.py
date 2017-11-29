from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class TransientHostRankSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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

class StatusSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

	class Meta:
		model = Status
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

	def create(self, validated_data):
		return Status.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class ObservationGroupSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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

class HostClassSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

	class Meta:
		model = HostClass
		fields = ('id', 'name', 'created_by', 'created_date', 
			'modified_by', 'modified_date')

	def create(self, validated_data):
		return HostClass.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		instance.name = validated_data.get('name', instance.name)
		instance.save()
		return instance

class ClassicalNightTypeSerializer(serializers.HyperlinkedModelSerializer):
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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
	created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
	modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

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