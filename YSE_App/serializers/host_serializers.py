from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User


class HostSerializer(serializers.HyperlinkedModelSerializer):
    host_morphology = serializers.HyperlinkedRelatedField(
        queryset=HostMorphology.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostmorphology-detail",
    )
    host_sed = serializers.HyperlinkedRelatedField(
        queryset=HostSED.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostsed-detail",
    )
    band_sextract = serializers.HyperlinkedRelatedField(
        queryset=PhotometricBand.objects.all(),
        allow_null=True,
        required=False,
        view_name="photometricband-detail",
        lookup_field="id",
    )
    best_spec = serializers.HyperlinkedRelatedField(
        queryset=HostSpectrum.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostspectrum-detail",
        lookup_field="id",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = Host
        fields = "__all__"
        extra_kwargs = {"url": {"view_name": "host-detail", "lookup_field": "id"}}

    def create(self, validated_data):
        return Host.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.host_morphology_id = validated_data.get(
            "host_morphology", instance.host_morphology
        )
        instance.host_sed_id = validated_data.get("host_sed", instance.host_sed)
        instance.band_sextract_id = validated_data.get(
            "band_sextract", instance.band_sextract
        )
        instance.best_spec_id = validated_data.get("best_spec", instance.best_spec)

        instance.ra = validated_data.get("ra", instance.ra)
        instance.dec = validated_data.get("dec", instance.dec)
        instance.name = validated_data.get("name", instance.name)
        instance.redshift = validated_data.get("redshift", instance.redshift)
        instance.redshift_err = validated_data.get(
            "redshift_err", instance.redshift_err
        )
        instance.r_a = validated_data.get("r_a", instance.r_a)
        instance.r_b = validated_data.get("r_b", instance.r_b)
        instance.theta = validated_data.get("theta", instance.theta)
        instance.eff_offset = validated_data.get("eff_offset", instance.eff_offset)
        instance.photo_z = validated_data.get("photo_z", instance.photo_z)
        instance.photo_z_err = validated_data.get("photo_z_err", instance.photo_z_err)
        instance.photo_z_source = validated_data.get(
            "photo_z_source", instance.photo_z_source
        )
        instance.transient_host_rank = validated_data.get(
            "transient_host_rank", instance.transient_host_rank
        )

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance


class HostSEDSerializer(serializers.HyperlinkedModelSerializer):
    sed_type = serializers.HyperlinkedRelatedField(
        queryset=SEDType.objects.all(), view_name="sedtype-detail"
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = HostSED
        fields = "__all__"

    def create(self, validated_data):
        return HostSED.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.sed_type_id = validated_data.get("sed_type", instance.sed_type)

        instance.metalicity = validated_data.get("metalicity", instance.metalicity)
        instance.metalicity_err = validated_data.get(
            "metalicity_err", instance.metalicity_err
        )
        instance.log_SFR = validated_data.get("log_SFR", instance.log_SFR)
        instance.log_SFR_err = validated_data.get("log_SFR_err", instance.log_SFR_err)
        instance.log_sSFR = validated_data.get("log_sSFR", instance.log_sSFR)
        instance.log_sSFR_err = validated_data.get(
            "log_sSFR_err", instance.log_sSFR_err
        )
        instance.log_mass = validated_data.get("log_mass", instance.log_mass)
        instance.log_mass_err = validated_data.get(
            "log_mass_err", instance.log_mass_err
        )
        instance.ebv = validated_data.get("ebv", instance.ebv)
        instance.ebv_err = validated_data.get("ebv_err", instance.ebv_err)
        instance.log_age = validated_data.get("log_age", instance.log_age)
        instance.log_age_err = validated_data.get("log_age_err", instance.log_age_err)
        instance.redshift = validated_data.get("redshift", instance.redshift)
        instance.redshift_err = validated_data.get(
            "redshift_err", instance.redshift_err
        )
        instance.fit_chi2 = validated_data.get("fit_chi2", instance.fit_chi2)
        instance.fit_n = validated_data.get("fit_n", instance.fit_n)
        instance.fit_plot_file = validated_data.get(
            "fit_plot_file", instance.fit_plot_file
        )

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        instance.save()

        return instance
