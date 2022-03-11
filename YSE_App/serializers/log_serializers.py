from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class LogSerializer(serializers.HyperlinkedModelSerializer):
    transient = serializers.HyperlinkedRelatedField(
        queryset=Transient.objects.all(),
        allow_null=True,
        required=False,
        view_name="transient-detail",
    )
    host = serializers.HyperlinkedRelatedField(
        queryset=Host.objects.all(),
        allow_null=True,
        required=False,
        view_name="host-detail",
        lookup_field="id",
    )
    host_sed = serializers.HyperlinkedRelatedField(
        queryset=HostSED.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostsed-detail",
    )

    transient_image = serializers.HyperlinkedRelatedField(
        queryset=TransientImage.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientimage-detail",
    )
    host_image = serializers.HyperlinkedRelatedField(
        queryset=HostImage.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostimage-detail",
    )

    transient_spectrum = serializers.HyperlinkedRelatedField(
        queryset=TransientSpectrum.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientspectrum-detail",
        lookup_field="id",
    )
    host_spectrum = serializers.HyperlinkedRelatedField(
        queryset=HostSpectrum.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostspectrum-detail",
        lookup_field="id",
    )

    transient_photometry = serializers.HyperlinkedRelatedField(
        queryset=TransientPhotometry.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientphotometry-detail",
        lookup_field="id",
    )
    host_photometry = serializers.HyperlinkedRelatedField(
        queryset=HostPhotometry.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostphotometry-detail",
        lookup_field="id",
    )

    transient_web_resource = serializers.HyperlinkedRelatedField(
        queryset=TransientWebResource.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientwebresource-detail",
    )
    host_web_resource = serializers.HyperlinkedRelatedField(
        queryset=HostWebResource.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostwebresource-detail",
    )

    transient_observation_task = serializers.HyperlinkedRelatedField(
        queryset=TransientObservationTask.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientobservationtask-detail",
    )
    host_observation_task = serializers.HyperlinkedRelatedField(
        queryset=HostObservationTask.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostobservationtask-detail",
    )

    transient_followup = serializers.HyperlinkedRelatedField(
        queryset=TransientFollowup.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientfollowup-detail",
    )
    host_followup = serializers.HyperlinkedRelatedField(
        queryset=HostFollowup.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostfollowup-detail",
    )

    instrument = serializers.HyperlinkedRelatedField(
        queryset=Instrument.objects.all(),
        allow_null=True,
        required=False,
        view_name="instrument-detail",
        lookup_field="id",
    )
    instrument_config = serializers.HyperlinkedRelatedField(
        queryset=InstrumentConfig.objects.all(),
        allow_null=True,
        required=False,
        view_name="instrumentconfig-detail",
    )
    config_element = serializers.HyperlinkedRelatedField(
        queryset=ConfigElement.objects.all(),
        allow_null=True,
        required=False,
        view_name="configelement-detail",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = Log
        fields = "__all__"

    def create(self, validated_data):
        return Log.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.transient_id = validated_data.get("transient", instance.transient)
        instance.host_id = validated_data.get("host", instance.host)
        instance.host_sed_id = validated_data.get("host_sed", instance.host_sed)
        instance.transient_image_id = validated_data.get(
            "transient_image", instance.transient_image
        )
        instance.host_image_id = validated_data.get("host_image", instance.host_image)
        instance.transient_spectrum_id = validated_data.get(
            "transient_spectrum", instance.transient_spectrum
        )
        instance.host_spectrum_id = validated_data.get(
            "host_spectrum", instance.host_spectrum
        )
        instance.transient_photometry_id = validated_data.get(
            "transient_photometry", instance.transient_photometry
        )
        instance.host_photometry_id = validated_data.get(
            "host_photometry", instance.host_photometry
        )
        instance.transient_web_resource_id = validated_data.get(
            "transient_web_resource", instance.transient_web_resource
        )
        instance.host_web_resource_id = validated_data.get(
            "host_web_resource", instance.host_web_resource
        )
        instance.transient_observation_task_id = validated_data.get(
            "transient_observation_task", instance.transient_observation_task
        )
        instance.host_observation_task_id = validated_data.get(
            "host_observation_task", instance.host_observation_task
        )
        instance.transient_followup_id = validated_data.get(
            "transient_followup", instance.transient_followup
        )
        instance.host_followup_id = validated_data.get(
            "host_followup", instance.host_followup
        )
        instance.instrument_id = validated_data.get("instrument", instance.instrument)
        instance.instrument_config_id = validated_data.get(
            "instrument_config", instance.instrument_config
        )
        instance.config_element_id = validated_data.get(
            "config_element", instance.config_element
        )

        instance.comment = validated_data.get("comment", instance.comment)

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance
