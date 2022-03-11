from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class ObservatorySerializer(serializers.HyperlinkedModelSerializer):
    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = Observatory
        fields = "__all__"

    def create(self, validated_data):
        return Observatory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.utc_offset = validated_data.get("utc_offset", instance.utc_offset)
        instance.tz_name = validated_data.get("tz_name", instance.tz_name)
        instance.DLS_utc_offset = validated_data.get(
            "DLS_utc_offset", instance.DLS_utc_offset
        )
        instance.DLS_tz_name = validated_data.get("DLS_tz_name", instance.DLS_tz_name)
        instance.DLS_start = validated_data.get("DLS_start", instance.DLS_start)
        instance.DLS_end = validated_data.get("DLS_end", instance.DLS_end)

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance
