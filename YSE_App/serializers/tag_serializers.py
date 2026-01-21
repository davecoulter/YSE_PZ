from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class TransientTagSerializer(serializers.HyperlinkedModelSerializer):
    color = serializers.HyperlinkedRelatedField(queryset=WebAppColor.objects.all(), allow_null=True, required=False, view_name='webappcolor-detail')

    created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
    modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

    class Meta:
        model = TransientTag
        fields = "__all__"

    def create(self, validated_data):
        return TransientTag.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.color_id = validated_data.get('color', instance.color)
        instance.name = validated_data.get('name', instance.name)

        instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

        instance.save()

        return instance

# FRB
class FRBTagSerializer(serializers.HyperlinkedModelSerializer):
    color = serializers.HyperlinkedRelatedField(queryset=WebAppColor.objects.all(), allow_null=True, required=False, view_name='webappcolor-detail')

    created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
    modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

    class Meta:
        model = FRBTag
        fields = "__all__"

    '''
    def create(self, validated_data):
        return TransientTag.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.color_id = validated_data.get('color', instance.color)
        instance.name = validated_data.get('name', instance.name)

        instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

        instance.save()

        return instance
    '''