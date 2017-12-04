from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class PrincipalInvestigatorSerializer(serializers.HyperlinkedModelSerializer):
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), many=True, allow_null=True, required=False, view_name='observationgroup-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = PrincipalInvestigator
		fields = "__all__"

	def create(self, validated_data):
		ogs = validated_data.pop('obs_group')

		pi = PrincipalInvestigator.objects.create(**validated_data)
		pi.save()

		for og in ogs:
			og_result = ObservationGroup.objects.filter(pk=og.id)
			if og_result.exists():
				o = og_result.first()
				pi.obs_group.add(o)
		
		pi.save()
		return pi

	def update(self, instance, validated_data):
		# Disassociate existing `Observation Groups`
		ogs = instance.obs_group.all()
		for og in ogs:
			instance.obs_group.remove(og)

		ogs = validated_data.pop('obs_group')
		for og in ogs:
			og_result = ObservationGroup.objects.filter(pk=og.id)
			if og_result.exists():
				o = og_result.first()
				instance.obs_group.add(o)

		instance.name = validated_data.get('name', instance.name)
		instance.phone = validated_data.get('phone', instance.phone)
		instance.email = validated_data.get('email', instance.email)
		instance.institution = validated_data.get('institution', instance.institution)
		instance.description = validated_data.get('description', instance.description)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()
		
		return instance