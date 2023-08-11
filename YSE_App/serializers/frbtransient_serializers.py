""" Serializers for FRB Transients """
from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class FRBTransientSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for the FRBTransient table
    """

    class Meta:
        model = FRBTransient
        fields = "__all__"
        

class FRBGalaxySerializer(serializers.HyperlinkedModelSerializer):

    # Only here for testing
    def create(self, validated_data):
        return FRBGalaxy.objects.create(**validated_data)

    class Meta:
        model = FRBGalaxy
        fields = "__all__"
        
class PathSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for the PATH table
    """

    # We use ingest_path() to create new entries
    class Meta:
        model = Path
        fields = "__all__"
        