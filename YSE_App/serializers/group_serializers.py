from rest_framework import serializers
from django.contrib.auth.models import Group

class GroupSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Group
		fields = "__all__"