""" Serializers for FRB Transients """
from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class FRBSampleCriteriaSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for the FRBSampleCriteria table
    """
    #instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail', lookup_field="id")

    class Meta:
        model = FRBSampleCriteria
        fields = "__all__"
        