from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User, Group
from rest_framework.exceptions import PermissionDenied

class TransientPhotometrySerializer(serializers.HyperlinkedModelSerializer):
	transient = serializers.HyperlinkedRelatedField(queryset=Transient.objects.all(), view_name='transient-detail')
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail', lookup_field="id")
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), allow_null=True, required=False, view_name='host-detail', lookup_field="id")
	followup = serializers.HyperlinkedRelatedField(queryset=TransientFollowup.objects.all(), allow_null=True, required=False, view_name='transientfollowup-detail')

	groups = serializers.HyperlinkedRelatedField(queryset=Group.objects.all(), many=True, view_name='group-detail')
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientPhotometry
		fields = "__all__"
		extra_kwargs = {
			'url': {'view_name': 'transientphotometry-detail', 'lookup_field': 'id'}
		}

	def create(self, validated_data):

		groups_exist = 'groups' in validated_data.keys()
		groups = None

		if groups_exist:
			groups = validated_data.pop('groups')
			user_groups = self.context['request'].user.groups.all()

			validGroups = set(groups).issubset(set(user_groups))
			if not validGroups:
				raise PermissionDenied({"message": "You don't have permission to create transient photometry with",
										"group": groups })

		transient_photometry = TransientPhotometry.objects.create(**validated_data)
		transient_photometry.save()

		if groups_exist:
			for group in groups:
				group_result = Group.objects.filter(pk=group.id)
				if group_result.exists():
					g = group_result.first()
					transient_photometry.groups.add(g)

			transient_photometry.save()

		return transient_photometry

	def update(self, instance, validated_data):
		instance.transient_id = validated_data.get('transient', instance.transient)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.host_id = validated_data.get('host', instance.host)
		instance.followup_id = validated_data.get('followup', instance.followup)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		if 'groups' in validated_data.keys():

			existing_groups = instance.groups.all() # From the existing instance
			user_groups = self.context['request'].user.groups.all()

			groupsExist = existing_groups.count() > 0
			atLeastOneValidGroup = len(set.intersection(set(user_groups), set(existing_groups))) > 0

			if groupsExist and not atLeastOneValidGroup:
				raise PermissionDenied({"message": "You don't have permission to modify",
										"transient photometry": instance})

			update_groups = validated_data.pop('groups')

			# Any difference in groups, must be for groups that the user is a member
			diff_groups = set(update_groups) ^ set(existing_groups)
			authorized_groups = set(diff_groups).issubset(set(user_groups))

			if not authorized_groups:
				raise PermissionDenied(
					{"message": "You don't have permission to modify transient photometry with",
					 "group": diff_groups})
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

class HostPhotometrySerializer(serializers.HyperlinkedModelSerializer):
	host = serializers.HyperlinkedRelatedField(queryset=Host.objects.all(), view_name='host-detail', lookup_field="id")
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail', lookup_field="id")
	obs_group = serializers.HyperlinkedRelatedField(queryset=ObservationGroup.objects.all(), view_name='observationgroup-detail')

	followup = serializers.HyperlinkedRelatedField(queryset=HostFollowup.objects.all(), allow_null=True, required=False, view_name='hostfollowup-detail')

	groups = serializers.HyperlinkedRelatedField(queryset=Group.objects.all(), many=True, view_name='group-detail')
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostPhotometry
		fields = "__all__"
		extra_kwargs = {
			'url': {'view_name': 'hostphotometry-detail', 'lookup_field': 'id'}
		}

	def create(self, validated_data):

		groups_exist = 'groups' in validated_data.keys()
		groups = None

		if groups_exist:
			groups = validated_data.pop('groups')
			user_groups = self.context['request'].user.groups.all()

			validGroups = set(groups).issubset(set(user_groups))
			if not validGroups:
				raise PermissionDenied({"message": "You don't have permission to create host photometry with",
										"group": groups})

		host_photometry = HostPhotometry.objects.create(**validated_data)
		host_photometry.save()

		if groups_exist:
			for group in groups:
				group_result = Group.objects.filter(pk=group.id)
				if group_result.exist():
					g = group_result.first()
					host_photometry.groups.add(g)

			host_photometry.save()

		return host_photometry

	def update(self, instance, validated_data):
		instance.host_id = validated_data.get('host', instance.host)
		instance.obs_group_id = validated_data.get('obs_group', instance.obs_group)
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		instance.followup_id = validated_data.get('followup', instance.followup)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		if 'groups' in validated_data.keys():

			existing_groups = instance.groups.all() # From the existing instance
			user_groups = self.context['request'].user.groups.all()

			groupsExist = existing_groups.count() > 0
			atLeastOneValidGroup = len(set.intersection(set(user_groups), set(existing_groups))) > 0

			if groupsExist and not atLeastOneValidGroup:
				raise PermissionDenied({"message": "You don't have permission to modify",
										"host photometry": instance})

			update_groups = validated_data.pop('groups')

			# Any difference in groups, must be for groups that the user is a member
			diff_groups = set(update_groups) ^ set(existing_groups)
			authorized_groups = set(diff_groups).issubset(set(user_groups))

			if not authorized_groups:
				raise PermissionDenied(
					{"message": "You don't have permission to modify host photometry with",
					 "group": diff_groups})
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

class TransientPhotDataSerializer(serializers.HyperlinkedModelSerializer):
	photometry = serializers.HyperlinkedRelatedField(queryset=TransientPhotometry.objects.all(), view_name='transientphotometry-detail', lookup_field="id")
	band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail', lookup_field="id")

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientPhotData
		fields = "__all__"

	def create(self, validated_data):
		transient_phot_data = TransientPhotData.objects.create(**validated_data)
		parent_photometry = TransientPhotometry.objects.get(pk=transient_phot_data.photometry.id)
		existing_groups = parent_photometry.groups.all()
		user_groups = self.context['request'].user.groups.all()

		# Does the phot record belong to a group that the user belongs to?
		authorized_groups = len(set.intersection(set(user_groups),set(existing_groups))) > 0
		if not authorized_groups:
			raise PermissionDenied(
				{"message": "You don't have permission to create transient photometry data point for",
				 "transient_photometry_id": parent_photometry.id})
		else:
			transient_phot_data.save()

		return transient_phot_data


	def update(self, instance, validated_data):
		instance.photometry_id = validated_data.get('photometry', instance.photometry)
		instance.band_id = validated_data.get('obs_group', instance.band)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.obs_date = validated_data.get('obs_date', instance.obs_date)
		instance.flux_zero_point = validated_data.get('flux_zero_point', instance.flux_zero_point)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)
		instance.mag = validated_data.get('mag', instance.mag)
		instance.mag_err = validated_data.get('mag_err', instance.mag_err)
		instance.forced = validated_data.get('forced', instance.forced)
		instance.dq = validated_data.get('dq', instance.dq)
		instance.discovery_point = validated_data.get('discovery_point', instance.discovery_point)

		new_parent_photometry = TransientPhotometry.objects.get(pk=instance.photometry_id.id)
		existing_groups = new_parent_photometry.groups.all()
		groupsExist = existing_groups.count() > 0
		user_groups = self.context['request'].user.groups.all()

		# Does the phot record belong to a group that the user belongs to?
		authorized_groups = len(set.intersection(set(user_groups), set(existing_groups))) > 0
		if groupsExist and not authorized_groups:
			raise PermissionDenied(
				{"message": "You don't have permission to modify transient photometry data point for",
				 "transient_photometry_id": new_parent_photometry.id })

		instance.save()

		return instance

class HostPhotDataSerializer(serializers.HyperlinkedModelSerializer):
	photometry = serializers.HyperlinkedRelatedField(queryset=HostPhotometry.objects.all(), view_name='hostphotometry-detail', lookup_field="id")
	band = serializers.HyperlinkedRelatedField(queryset=PhotometricBand.objects.all(), view_name='photometricband-detail', lookup_field="id")

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostPhotData
		fields = "__all__"

	def create(self, validated_data):
		host_phot_data = HostPhotData.objects.create(**validated_data)
		parent_photometry = HostPhotometry.objects.get(pk=host_phot_data.photometry.id)
		existing_groups = parent_photometry.groups.all()
		user_groups = self.context['request'].user.groups.all()

		# Does the phot record belong to a group that the user belongs to?
		authorized_groups = len(set.intersection(set(user_groups), set(existing_groups))) > 0
		if not authorized_groups:
			raise PermissionDenied(
				{"message": "You don't have permission to create host photometry data point for",
				 "host_photometry_id": parent_photometry.id})
		else:
			host_phot_data.save()

		return host_phot_data

	def update(self, instance, validated_data):
		instance.photometry_id = validated_data.get('photometry', instance.photometry)
		instance.band_id = validated_data.get('obs_group', instance.band)
		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.obs_date = validated_data.get('obs_date', instance.obs_date)
		instance.flux_zero_point = validated_data.get('flux_zero_point', instance.flux_zero_point)
		instance.flux = validated_data.get('flux', instance.flux)
		instance.flux_err = validated_data.get('flux_err', instance.flux_err)
		instance.mag = validated_data.get('mag', instance.mag)
		instance.mag_err = validated_data.get('mag_err', instance.mag_err)
		instance.forced = validated_data.get('forced', instance.forced)
		instance.dq = validated_data.get('dq', instance.dq)

		new_parent_photometry = HostPhotometry.objects.get(pk=instance.photometry_id.id)
		existing_groups = new_parent_photometry.groups.all()
		groupsExist = existing_groups.count() > 0
		user_groups = self.context['request'].user.groups.all()

		# Does the phot record belong to a group that the user belongs to?
		authorized_groups = len(set.intersection(set(user_groups), set(existing_groups))) > 0
		if groupsExist and not authorized_groups:
			raise PermissionDenied(
				{"message": "You don't have permission to modify host photometry data point for",
				 "host_photometry_id": new_parent_photometry.id})

		instance.save()

		return instance

class TransientImageSerializer(serializers.HyperlinkedModelSerializer):
	phot_data = serializers.HyperlinkedRelatedField(queryset=TransientPhotData.objects.all(), view_name='transientphotdata-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = TransientImage
		fields = "__all__"

	def create(self, validated_data):
		return TransientImage.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.phot_data_id = validated_data.get('phot_data', instance.phot_data)
		
		instance.img_file = validated_data.get('img_file', instance.img_file)
		instance.zero_point = validated_data.get('zero_point', instance.zero_point)
		instance.zero_point_err = validated_data.get('zero_point_err', instance.zero_point_err)
		instance.sky = validated_data.get('sky', instance.sky)
		instance.sky_rms = validated_data.get('sky_rms', instance.sky_rms)
		instance.dcmp_file = validated_data.get('dcmp_file', instance.dcmp_file)

		instance.save()

		return instance

class HostImageSerializer(serializers.HyperlinkedModelSerializer):
	phot_data = serializers.HyperlinkedRelatedField(queryset=HostPhotData.objects.all(), view_name='hostphotdata-detail')

	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = HostImage
		fields = "__all__"

	def create(self, validated_data):
		return HostImage.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.phot_data_id = validated_data.get('phot_data', instance.phot_data)
		
		instance.img_file = validated_data.get('img_file', instance.img_file)
		instance.zero_point = validated_data.get('zero_point', instance.zero_point)
		instance.zero_point_err = validated_data.get('zero_point_err', instance.zero_point_err)
		instance.sky = validated_data.get('sky', instance.sky)
		instance.sky_rms = validated_data.get('sky_rms', instance.sky_rms)
		instance.dcmp_file = validated_data.get('dcmp_file', instance.dcmp_file)

		instance.save()

		return instance
