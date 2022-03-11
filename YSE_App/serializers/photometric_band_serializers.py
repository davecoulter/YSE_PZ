from django.contrib.auth.models import User
from rest_framework import serializers

from YSE_App.models import *


class PhotometricBandSerializer(serializers.HyperlinkedModelSerializer):
    instrument = serializers.HyperlinkedRelatedField(
        queryset=Instrument.objects.all(),
        view_name="instrument-detail",
        lookup_field="id",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = PhotometricBand
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "photometricband-detail", "lookup_field": "id"}
        }

    def create(self, validated_data):
        return PhotometricBand.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.instrument_id = validated_data.get("instrument", instance.instrument)

        instance.name = validated_data.get("name", instance.name)
        instance.lambda_eff = validated_data.get("lambda_eff", instance.lambda_eff)
        instance.throughput_file = validated_data.get(
            "throughput_file", instance.throughput_file
        )
        instance.disp_color = validated_data.get("disp_color", instance.disp_color)
        instance.disp_symbol = validated_data.get("disp_color", instance.disp_symbol)

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance
