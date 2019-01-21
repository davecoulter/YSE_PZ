from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class ProfileSerializer(serializers.HyperlinkedModelSerializer):
	user = serializers.HyperlinkedRelatedField(queryset=User.objects.all(), view_name='user-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Profile
		fields = "__all__"

	def create(self, validated_data):
		return Profile.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.user_id = validated_data.get('user', instance.user)

		instance.phone_country_code = validated_data.get('phone_country_code', instance.phone_country_code)
		instance.phone_area = validated_data.get('phone_area', instance.phone_area)
		instance.phone_first_three = validated_data.get('phone_first_three', instance.phone_first_three)
		instance.phone_last_four = validated_data.get('phone_last_four', instance.phone_last_four)
		instance.phone_provider_str = validated_data.get('phone_provider_str', instance.phone_provider_str)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()

		return instance

class UserQuerySerializer(serializers.HyperlinkedModelSerializer):
	user = serializers.HyperlinkedRelatedField(queryset=User.objects.all(), view_name='user-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = UserQuery
		fields = "__all__"
		
	def create(self, validated_data):
		return UserQuery.objects.create(**validated_data)

	def update(self, instance, validated_data):

		instance.profile = validated_data.get('profile', instance.profile)
		instance.name = validated_data.get('name', instance.name)
		instance.query = validated_data.get('query', instance.query)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()

		return instance
