from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class GWCandidateSerializer(serializers.HyperlinkedModelSerializer):

    transient = serializers.HyperlinkedRelatedField(
        queryset=Transient.objects.all(), view_name="transient-detail"
    )

    class Meta:
        model = GWCandidate
        fields = "__all__"

    def create(self, validated_data):
        return GWCandidate.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.field_name = validated_data.get("field_name", instance.field_name)
        instance.candidate_id = validated_data.get(
            "candidate_id", instance.candidate_id
        )
        instance.name = validated_data.get("name", instance.name)
        instance.transient = validated_data.get("transient", instance.transient)
        instance.websniff_url = validated_data.get(
            "websniff_url", instance.websniff_url
        )

        instance.save()

        return instance


class GWCandidateImageSerializer(serializers.HyperlinkedModelSerializer):

    gw_candidate = serializers.HyperlinkedRelatedField(
        queryset=GWCandidate.objects.all(), view_name="gwcandidate-detail"
    )  # , lookup_field="id")
    image_filter = serializers.HyperlinkedRelatedField(
        queryset=PhotometricBand.objects.all(),
        view_name="photometricband-detail",
        lookup_field="id",
    )
    # image_filter = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail', lookup_field="id")

    class Meta:
        model = GWCandidateImage
        fields = "__all__"

    def create(self, validated_data):
        return GWCandidateImage.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.gw_candidate = validated_data.get(
            "gw_candidate", instance.gw_candidate
        )
        instance.image_filename = validated_data.get(
            "image_filename", instance.image_filename
        )
        instance.image_filter = validated_data.get(
            "image_filter", instance.image_filter
        )
        instance.dophot_class = validated_data.get(
            "dophot_class", instance.dophot_class
        )

        instance.save()

        return instance
