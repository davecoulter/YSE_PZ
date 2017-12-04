from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class TelescopeSerializer(serializers.HyperlinkedModelSerializer):
	observatory = serializers.HyperlinkedRelatedField(queryset=Observatory.objects.all(), view_name='observatory-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Telescope
		fields = "__all__"

	def create(self, validated_data):
		return Telescope.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.observatory_id = validated_data.get('observatory', instance.observatory)

		instance.name = validated_data.get('name', instance.name)
		instance.latitude = validated_data.get('latitude', instance.latitude)
		instance.longitude = validated_data.get('longitude', instance.longitude)
		instance.elevation = validated_data.get('elevation', instance.elevation)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance