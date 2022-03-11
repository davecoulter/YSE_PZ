from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied
from .auth_helpers import NotAuthorizedToAccessParent


class ToOResourceSerializer(serializers.HyperlinkedModelSerializer):
    telescope = serializers.HyperlinkedRelatedField(
        queryset=Telescope.objects.all(), view_name="telescope-detail"
    )
    principal_investigator = serializers.HyperlinkedRelatedField(
        queryset=PrincipalInvestigator.objects.all(),
        allow_null=True,
        required=False,
        view_name="principalinvestigator-detail",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = ToOResource
        fields = "__all__"

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
                        "message": "You don't have permission to create too resource with",
                        "group": groups,
                    }
                )

        too_resource = ToOResource.objects.create(**validated_data)
        too_resource.save()

        if groups_exist:
            for group in groups:
                group_result = Group.objects.filter(pk=group.id)
                if group_result.exists():
                    g = group_result.first()
                    too_resource.groups.add(g)

            too_resource.save()

        return too_resource

    def update(self, instance, validated_data):
        instance.telescope_id = validated_data.get("telescope", instance.telescope)
        instance.principal_investigator_id = validated_data.get(
            "principal_investigator", instance.principal_investigator
        )

        instance.begin_date_valid = validated_data.get(
            "begin_date_valid", instance.begin_date_valid
        )
        instance.end_date_valid = validated_data.get(
            "end_date_valid", instance.end_date_valid
        )
        instance.awarded_too_hours = validated_data.get(
            "awarded_too_hours", instance.awarded_too_hours
        )
        instance.used_too_hours = validated_data.get(
            "used_too_hours", instance.used_too_hours
        )
        instance.awarded_too_triggers = validated_data.get(
            "awarded_too_hours", instance.awarded_too_triggers
        )
        instance.used_too_triggers = validated_data.get(
            "used_too_hours", instance.used_too_triggers
        )
        instance.description = validated_data.get("description", instance.description)

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
                        "too resource": instance,
                    }
                )

            update_groups = validated_data.pop("groups")

            # Any difference in groups, must be for groups that the user is a member
            diff_groups = set(update_groups) ^ set(existing_groups)
            authorized_groups = set(diff_groups).issubset(set(user_groups))

            if not authorized_groups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify too resource with",
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


class QueuedResourceSerializer(serializers.HyperlinkedModelSerializer):
    telescope = serializers.HyperlinkedRelatedField(
        queryset=Telescope.objects.all(), view_name="telescope-detail"
    )
    principal_investigator = serializers.HyperlinkedRelatedField(
        queryset=PrincipalInvestigator.objects.all(),
        allow_null=True,
        required=False,
        view_name="principalinvestigator-detail",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = QueuedResource
        fields = "__all__"

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
                        "message": "You don't have permission to create queued resource with",
                        "group": groups,
                    }
                )

        queued_resource = QueuedResource.objects.create(**validated_data)
        queued_resource.save()

        if groups_exist:
            for group in groups:
                group_result = Group.objects.filter(pk=group.id)
                if group_result.exists():
                    g = group_result.first()
                    queued_resource.groups.add(g)

            queued_resource.save()

        return queued_resource

    def update(self, instance, validated_data):
        instance.telescope_id = validated_data.get("telescope", instance.telescope)
        instance.principal_investigator_id = validated_data.get(
            "principal_investigator", instance.principal_investigator
        )

        instance.begin_date_valid = validated_data.get(
            "begin_date_valid", instance.begin_date_valid
        )
        instance.end_date_valid = validated_data.get(
            "end_date_valid", instance.end_date_valid
        )
        instance.awarded_hours = validated_data.get(
            "awarded_hours", instance.awarded_hours
        )
        instance.used_hours = validated_data.get("used_hours", instance.used_hours)
        instance.description = validated_data.get("description", instance.description)

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
                        "queued resource": instance,
                    }
                )

            update_groups = validated_data.pop("groups")

            # Any difference in groups, must be for groups that the user is a member
            diff_groups = set(update_groups) ^ set(existing_groups)
            authorized_groups = set(diff_groups).issubset(set(user_groups))

            if not authorized_groups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify queued resource with",
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


class ClassicalResourceSerializer(serializers.HyperlinkedModelSerializer):
    telescope = serializers.HyperlinkedRelatedField(
        queryset=Telescope.objects.all(), view_name="telescope-detail"
    )
    principal_investigator = serializers.HyperlinkedRelatedField(
        queryset=PrincipalInvestigator.objects.all(),
        allow_null=True,
        required=False,
        view_name="principalinvestigator-detail",
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = ClassicalResource
        fields = "__all__"
        # extra_kwargs = {
        # 	'url': {'view_name': 'classicalresource-detail', 'lookup_field': 'id'}
        # }

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
                        "message": "You don't have permission to create classical resource with",
                        "group": groups,
                    }
                )

        classical_resource = ClassicalResource.objects.create(**validated_data)
        classical_resource.save()

        if groups_exist:
            for group in groups:
                group_result = Group.objects.filter(pk=group.id)
                if group_result.exists():
                    g = group_result.first()
                    classical_resource.groups.add(g)

            classical_resource.save()

        return classical_resource

    def update(self, instance, validated_data):
        instance.telescope_id = validated_data.get("telescope", instance.telescope)
        instance.principal_investigator_id = validated_data.get(
            "principal_investigator", instance.principal_investigator
        )

        instance.begin_date_valid = validated_data.get(
            "begin_date_valid", instance.begin_date_valid
        )
        instance.end_date_valid = validated_data.get(
            "end_date_valid", instance.end_date_valid
        )
        instance.description = validated_data.get("description", instance.description)

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
                        "classical resource": instance,
                    }
                )

            update_groups = validated_data.pop("groups")

            # Any difference in groups, must be for groups that the user is a member
            diff_groups = set(update_groups) ^ set(existing_groups)
            authorized_groups = set(diff_groups).issubset(set(user_groups))

            if not authorized_groups:
                raise PermissionDenied(
                    {
                        "message": "You don't have permission to modify classical resource with",
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


class ClassicalObservingDateSerializer(serializers.HyperlinkedModelSerializer):
    resource = serializers.HyperlinkedRelatedField(
        queryset=ClassicalResource.objects.all(), view_name="classicalresource-detail"
    )  # , lookup_field="id")
    night_type = serializers.HyperlinkedRelatedField(
        queryset=ClassicalNightType.objects.all(), view_name="classicalnighttype-detail"
    )

    created_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )
    modified_by = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="user-detail"
    )

    class Meta:
        model = ClassicalObservingDate
        fields = "__all__"

    def create(self, validated_data):
        classical_observing_date = ClassicalObservingDate.objects.create(
            **validated_data
        )

        parent_resource = ClassicalResource.objects.get(
            pk=classical_observing_date.resource.id
        )
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(parent_resource, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to create classical observing date for",
                    "classical_resource_id": parent_resource.id,
                }
            )
        else:
            classical_observing_date.save()

        return classical_observing_date

    def update(self, instance, validated_data):
        instance.resource_id = validated_data.get("resource", instance.resource)
        instance.night_type_id = validated_data.get("night_type", instance.night_type)
        instance.obs_date = validated_data.get("obs_date", instance.obs_date)
        instance.modified_by_id = validated_data.get(
            "modified_by", instance.modified_by
        )

        new_parent_classical_resource = ClassicalResource.objects.get(
            pk=instance.resource_id.id
        )
        user_groups = self.context["request"].user.groups.all()

        if NotAuthorizedToAccessParent(new_parent_classical_resource, user_groups):
            raise PermissionDenied(
                {
                    "message": "You don't have permission to modify classical observing date point for",
                    "classical_resource_id": new_parent_classical_resource.id,
                }
            )

        instance.save()

        return instance
