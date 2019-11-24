from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class OnCallDateSerializer(serializers.HyperlinkedModelSerializer):
	user = serializers.HyperlinkedRelatedField(queryset=User.objects.all(), many=True, allow_null=True, required=False, view_name='user-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = OnCallDate
		fields = "__all__"

	def create(self, validated_data):
		users = validated_data.pop('user')
		
		ocd = OnCallDate.objects.create(**validated_data)
		ocd.save()

		# if users is not None:
		for user in users:
			user_result = User.objects.filter(pk=user.id)
			if user_result.exists():
				u = user_result.first()
				ocd.user.add(u)
		
		ocd.save()
		return ocd

	def update(self, instance, validated_data):
		# Disassociate existing `Observation Groups`
		users = instance.user.all()
		for user in users:
			instance.user.remove(user)

		users = validated_data.pop('user')
		for user in users:
			user_result = User.objects.filter(pk=user.id)
			if user_result.exists():
				u = user_result.first()
				instance.user.add(u)

		instance.on_call_date = validated_data.get('on_call_date', instance.on_call_date)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()
		
		return instance

class YSEOnCallDateSerializer(serializers.HyperlinkedModelSerializer):
	user = serializers.HyperlinkedRelatedField(queryset=User.objects.all(), many=True, allow_null=True, required=False, view_name='user-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = YSEOnCallDate
		fields = "__all__"

	def create(self, validated_data):
		users = validated_data.pop('user')
		
		ocd = YSEOnCallDate.objects.create(**validated_data)
		ocd.save()

		# if users is not None:
		for user in users:
			user_result = User.objects.filter(pk=user.id)
			if user_result.exists():
				u = user_result.first()
				ocd.user.add(u)
		
		ocd.save()
		return ocd

	def update(self, instance, validated_data):
		# Disassociate existing `Observation Groups`
		users = instance.user.all()
		for user in users:
			instance.user.remove(user)

		users = validated_data.pop('user')
		for user in users:
			user_result = User.objects.filter(pk=user.id)
			if user_result.exists():
				u = user_result.first()
				instance.user.add(u)

		instance.on_call_date = validated_data.get('on_call_date', instance.on_call_date)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()
		
		return instance	
