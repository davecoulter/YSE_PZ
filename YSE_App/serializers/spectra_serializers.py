from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .auth_helpers import NotAuthorizedToAccessParent
from YSE_App.models import *


class TransientSpectrumSerializer(serializers.HyperlinkedModelSerializer):
    transient = serializers.HyperlinkedRelatedField(
        queryset=Transient.objects.all(), view_name="transient-detail"
    )
    instrument = serializers.HyperlinkedRelatedField(
        queryset=Instrument.objects.all(),
        view_name="instrument-detail",
        lookup_field="id",
    )
    obs_group = serializers.HyperlinkedRelatedField(
        queryset=ObservationGroup.objects.all(), view_name="observationgroup-detail"
    )
    followup = serializers.HyperlinkedRelatedField(
        queryset=TransientFollowup.objects.all(),
        allow_null=True,
        required=False,
        view_name="transientfollowup-detail",
    )
    unit = serializers.HyperlinkedRelatedField(
        queryset=Unit.objects.all(),
        allow_null=True,
        required=False,
        view_name="unit-detail",
    )
    data_quality = serializers.HyperlinkedRelatedField(
        queryset=DataQuality.objects.all(),
        allow_null=True,
        required=False,
        view_name="dataquality-detail",
    )

    groups = serializers.HyperlinkedRelatedField(
        queryset=Group.objects.all(), many=True, view_name="group-detail"
    )
    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = TransientSpectrum
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "transientspectrum-detail", "lookup_field": "id"}
        }

    def create(self, validated_data):
        groups_exist = "groups" in validated_data.keys()
        groups = None

        if groups_exist:
            groups = validated_data.pop("groups")
            user_groups = self.context["request"].user.groups.all()

            validGroups = set(groups).issubset(set(user_groups))
            if not validGroups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to create transient spectrum with",
                        "group": groups,
                    }
                )

        transient_spectrum = TransientSpectrum.objects.create(**validated_data)
        transient_spectrum.save()

        if groups_exist:
            for group in groups:
                group_result = Group.objects.filter(pk=group.id)
                if group_result.exists():
                    g = group_result.first()
                    transient_spectrum.groups.add(g)

            transient_spectrum.save()

        return transient_spectrum

    def update(self, instance, validated_data):
        instance.transient_id = validated_data.get("transient", instance.transient)
        instance.instrument_id = validated_data.get("instrument", instance.instrument)
        instance.obs_group_id = validated_data.get("obs_group", instance.obs_group)
        instance.followup_id = validated_data.get("followup", instance.followup)
        instance.unit_id = validated_data.get("unit", instance.unit)
        instance.data_quality_id = validated_data.get(
            "data_quality", instance.data_quality
        )

        instance.ra = validated_data.get("ra", instance.ra)
        instance.dec = validated_data.get("dec", instance.dec)
        instance.spec_phase = validated_data.get("spec_phase", instance.spec_phase)
        instance.obs_date = validated_data.get("obs_date", instance.obs_date)
        instance.redshift = validated_data.get("redshift", instance.redshift)
        instance.redshift_err = validated_data.get(
            "redshift_err", instance.redshift_err
        )
        instance.redshift_quality = validated_data.get(
            "redshift_quality", instance.redshift_quality
        )

        instance.spec_plot_file = validated_data.get(
            "spec_plot_file", instance.spec_plot_file
        )
        instance.spec_data_file = validated_data.get(
            "spec_data_file", instance.spec_data_file
        )
        instance.spectrum_notes = validated_data.get(
            "spectrum_notes", instance.spectrum_notes
        )
        instance.rlap = validated_data.get("rlap", instance.rlap)
        instance.snid_plot_file = validated_data.get(
            "snid_plot_file", instance.snid_plot_file
        )

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        if "groups" in validated_data.keys():

            existing_groups = instance.groups.all()  # From the existing instance
            user_groups = self.context["request"].user.groups.all()

            groupsExist = existing_groups.count() > 0
            atLeastOneValidGroup = (
                len(set.intersection(set(user_groups), set(existing_groups))) > 0
            )

            if groupsExist and not atLeastOneValidGroup:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify",
                        "transient spectrum": instance,
                    }
                )

            update_groups = validated_data.pop("groups")

            # Any difference in groups, must be for groups that the user is a member
            diff_groups = set(update_groups) ^ set(existing_groups)
            authorized_groups = set(diff_groups).issubset(set(user_groups))

            if not authorized_groups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify transient spectrum with",
                        "group": diff_groups,
                    }
                )
            else:
                # Only update with groups that a user is a member of
                member_groups = set.intersection(set(update_groups), set(user_groups))

                # remove User groups
                for user_group in user_groups:
                    instance.groups.remove(user_group)

                for member_group in member_groups:
                    group_result = Group.objects.filter(pk=member_group.id)
                    if group_result.exists():
                        g = group_result.first()
                        instance.groups.add(g)

        instance.save()

        return instance


class HostSpectrumSerializer(serializers.HyperlinkedModelSerializer):
    host = serializers.HyperlinkedRelatedField(
        queryset=Host.objects.all(), view_name="host-detail", lookup_field="id"
    )
    instrument = serializers.HyperlinkedRelatedField(
        queryset=Instrument.objects.all(),
        view_name="instrument-detail",
        lookup_field="id",
    )
    obs_group = serializers.HyperlinkedRelatedField(
        queryset=ObservationGroup.objects.all(), view_name="observationgroup-detail"
    )
    followup = serializers.HyperlinkedRelatedField(
        queryset=HostFollowup.objects.all(),
        allow_null=True,
        required=False,
        view_name="hostfollowup-detail",
    )
    unit = serializers.HyperlinkedRelatedField(
        queryset=Unit.objects.all(),
        allow_null=True,
        required=False,
        view_name="unit-detail",
    )
    data_quality = serializers.HyperlinkedRelatedField(
        queryset=DataQuality.objects.all(),
        allow_null=True,
        required=False,
        view_name="dataquality-detail",
    )

    groups = serializers.HyperlinkedRelatedField(
        queryset=Group.objects.all(), many=True, view_name="group-detail"
    )
    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = HostSpectrum
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "hostspectrum-detail", "lookup_field": "id"}
        }

    def create(self, validated_data):
        groups_exist = "groups" in validated_data.keys()
        groups = None

        if groups_exist:
            groups = validated_data.pop("groups")
            user_groups = self.context["request"].user.groups.all()

            validGroups = set(groups).issubset(set(user_groups))
            if not validGroups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to create host spectrum with",
                        "group": groups,
                    }
                )

        host_spectrum = HostSpectrum.objects.create(**validated_data)
        host_spectrum.save()

        if groups_exist:
            for group in groups:
                group_result = Group.objects.filter(pk=group.id)
                if group_result.exist():
                    g = group_result.first()
                    host_spectrum.groups.add(g)

            host_spectrum.save()

        return host_spectrum

    def update(self, instance, validated_data):
        instance.host_id = validated_data.get("host", instance.host)
        instance.instrument_id = validated_data.get("instrument", instance.instrument)
        instance.obs_group_id = validated_data.get("obs_group", instance.obs_group)
        instance.followup_id = validated_data.get("followup", instance.followup)
        instance.unit_id = validated_data.get("unit", instance.unit)
        instance.data_quality_id = validated_data.get(
            "data_quality", instance.data_quality
        )

        instance.ra = validated_data.get("ra", instance.ra)
        instance.dec = validated_data.get("dec", instance.dec)
        instance.obs_date = validated_data.get("obs_date", instance.obs_date)
        instance.redshift = validated_data.get("redshift", instance.redshift)
        instance.redshift_err = validated_data.get(
            "redshift_err", instance.redshift_err
        )
        instance.redshift_quality = validated_data.get(
            "redshift_quality", instance.redshift_quality
        )
        instance.tdr = validated_data.get("tdr", instance.tdr)
        instance.spec_plot_file = validated_data.get(
            "spec_plot_file", instance.spec_plot_file
        )
        instance.spec_data_file = validated_data.get(
            "spec_data_file", instance.spec_data_file
        )
        instance.spectrum_notes = validated_data.get(
            "spectrum_notes", instance.spectrum_notes
        )

        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        if "groups" in validated_data.keys():

            existing_groups = instance.groups.all()  # From the existing instance
            user_groups = self.context["request"].user.groups.all()

            groupsExist = existing_groups.count() > 0
            atLeastOneValidGroup = (
                len(set.intersection(set(user_groups), set(existing_groups))) > 0
            )

            if groupsExist and not atLeastOneValidGroup:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify",
                        "host spectrum": instance,
                    }
                )

            update_groups = validated_data.pop("groups")

            # Any difference in groups, must be for groups that the user is a member
            diff_groups = set(update_groups) ^ set(existing_groups)
            authorized_groups = set(diff_groups).issubset(set(user_groups))

            if not authorized_groups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify host spectrum with",
                        "group": diff_groups,
                    }
                )
            else:
                # Only update with groups that a user is a member of
                member_groups = set.intersection(set(update_groups), set(user_groups))

                # remove User groups
                for user_group in user_groups:
                    instance.groups.remove(user_group)

                for member_group in member_groups:
                    group_result = Group.objects.filter(pk=member_group.id)
                    if group_result.exists():
                        g = group_result.first()
                        instance.groups.add(g)

        instance.save()

        return instance


class TransientSpecDataSerializer(serializers.HyperlinkedModelSerializer):
    spectrum = serializers.HyperlinkedRelatedField(
        queryset=TransientSpectrum.objects.all(),
        view_name="transientspectrum-detail",
        lookup_field="id",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = TransientSpecData
        fields = "__all__"

    def create(self, validated_data):
        transient_spec_data = TransientSpecData.objects.create(**validated_data)

        parent_spectrum = TransientSpectrum.objects.get(
            pk=transient_spec_data.spectrum.id
        )
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(parent_spectrum, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to create transient spectrum data point for",
                    "transient_photometry_id": parent_spectrum.id,
                }
            )
        else:
            transient_spec_data.save()

        return transient_spec_data

    def update(self, instance, validated_data):
        instance.spectrum_id = validated_data.get("spectrum", instance.spectrum)
        instance.wavelength = validated_data.get("wavelength", instance.wavelength)
        instance.flux = validated_data.get("flux", instance.flux)
        instance.wavelength_err = validated_data.get(
            "wavelength_err", instance.wavelength_err
        )
        instance.flux_err = validated_data.get("flux_err", instance.flux_err)
        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        new_parent_spectrum = TransientSpectrum.objects.get(pk=instance.spectrum_id.id)
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(new_parent_spectrum, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to modify transient spectrum data point for",
                    "transient_spectrum_id": new_parent_spectrum.id,
                }
            )

        instance.save()

        return instance


class HostSpecDataSerializer(serializers.HyperlinkedModelSerializer):
    spectrum = serializers.HyperlinkedRelatedField(
        queryset=HostSpectrum.objects.all(),
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
        model = HostSpecData
        fields = "__all__"

    def create(self, validated_data):
        host_spec_data = HostSpecData.objects.create(**validated_data)

        parent_spectrum = HostSpectrum.objects.get(pk=host_spec_data.spectrum.id)
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(parent_spectrum, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to create host spectrum data point for",
                    "host_spectrum_id": parent_spectrum.id,
                }
            )
        else:
            host_spec_data.save()

        return host_spec_data

    def update(self, instance, validated_data):
        instance.spectrum_id = validated_data.get("spectrum", instance.spectrum)
        instance.wavelength = validated_data.get("wavelength", instance.wavelength)
        instance.flux = validated_data.get("flux", instance.flux)
        instance.wavelength_err = validated_data.get(
            "wavelength_err", instance.wavelength_err
        )
        instance.flux_err = validated_data.get("flux_err", instance.flux_err)
        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        new_parent_spectrum = HostSpectrum.objects.get(pk=instance.spectrum_id.id)
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(new_parent_spectrum, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to modify host spectrum data point for",
                    "host_spectrum_id": new_parent_spectrum.id,
                }
            )

        instance.save()

        return instance
