""" Serializers for FRB Transients """
from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class FRBFollowUpRequestSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for the FRBFollowUpRequest table
    """

    class Meta:
        model = FRBFollowUpRequest
        fields = "__all__"
        

class FRBFollowUpResourceSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for the FRBFollowUpResource table
    """
    instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail', lookup_field="id")

    class Meta:
        model = FRBFollowUpResource
        fields = "__all__"
        