from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class TransientObservationTaskSerializer(serializers.HyperlinkedModelSerializer):
    followup = serializers.HyperlinkedRelatedField(
        queryset=TransientFollowup.objects.all(), view_name="transientfollowup-detail"
    )
    instrument_config = serializers.HyperlinkedRelatedField(
        queryset=InstrumentConfig.objects.all(), view_name="instrumentconfig-detail"
    )
    status = serializers.HyperlinkedRelatedField(
        queryset=TaskStatus.objects.all(), view_name="taskstatus-detail"
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = TransientObservationTask
        fields = "__all__"

    def create(self, validated_data):
        return TransientObservationTask.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.followup_id = validated_data.get("followup", instance.followup)
        instance.instrument_config_id = validated_data.get(
            "instrument_config", instance.instrument_config
        )
        instance.status_id = validated_data.get("status", instance.status)

        instance.exposure_time = validated_data.get(
            "exposure_time", instance.exposure_time
        )
        instance.number_of_exposures = validated_data.get(
            "number_of_exposures", instance.number_of_exposures
        )
        instance.desired_obs_date = validated_data.get(
            "desired_obs_date", instance.desired_obs_date
        )
        instance.actual_obs_date = validated_data.get(
            "actual_obs_date", instance.actual_obs_date
        )
        instance.description = validated_data.get("description", instance.description)

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance


class HostObservationTaskSerializer(serializers.HyperlinkedModelSerializer):
    followup = serializers.HyperlinkedRelatedField(
        queryset=HostFollowup.objects.all(), view_name="hostfollowup-detail"
    )
    instrument_config = serializers.HyperlinkedRelatedField(
        queryset=InstrumentConfig.objects.all(), view_name="instrumentconfig-detail"
    )
    status = serializers.HyperlinkedRelatedField(
        queryset=TaskStatus.objects.all(), view_name="taskstatus-detail"
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = HostObservationTask
        fields = "__all__"

    def create(self, validated_data):
        return HostObservationTask.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.followup_id = validated_data.get("followup", instance.followup)
        instance.instrument_config_id = validated_data.get(
            "instrument_config", instance.instrument_config
        )
        instance.status_id = validated_data.get("status", instance.status)

        instance.exposure_time = validated_data.get(
            "exposure_time", instance.exposure_time
        )
        instance.number_of_exposures = validated_data.get(
            "number_of_exposures", instance.number_of_exposures
        )
        instance.desired_obs_date = validated_data.get(
            "desired_obs_date", instance.desired_obs_date
        )
        instance.actual_obs_date = validated_data.get(
            "actual_obs_date", instance.actual_obs_date
        )
        instance.description = validated_data.get("description", instance.description)

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance
