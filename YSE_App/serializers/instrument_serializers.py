from rest_framework import serializers
from YSE_App.models import *
from django.contrib.auth.models import User

class InstrumentSerializer(serializers.HyperlinkedModelSerializer):
	telescope = serializers.HyperlinkedRelatedField(queryset=Telescope.objects.all(), view_name='telescope-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = Instrument
		fields = "__all__"

	def create(self, validated_data):
		return Instrument.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.telescope_id = validated_data.get('telescope', instance.telescope)

		instance.name = validated_data.get('name', instance.name)
		instance.description = validated_data.get('description', instance.description)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class InstrumentConfigSerializer(serializers.HyperlinkedModelSerializer):
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = InstrumentConfig
		fields = "__all__"

	def create(self, validated_data):
		return InstrumentConfig.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.instrument_id = validated_data.get('instrument', instance.instrument)

		instance.name = validated_data.get('name', instance.name)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)
		
		instance.save()

		return instance

class ConfigElementSerializer(serializers.HyperlinkedModelSerializer):
	instrument = serializers.HyperlinkedRelatedField(queryset=Instrument.objects.all(), view_name='instrument-detail')
	instrument_config = serializers.HyperlinkedRelatedField(queryset=InstrumentConfig.objects.all(), many=True, view_name='instrumentconfig-detail')
	
	created_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')
	modified_by = serializers.HyperlinkedRelatedField(read_only=True, view_name='user-detail')

	class Meta:
		model = ConfigElement
		fields = "__all__"
		extra_kwargs = {
			'url': {'view_name': 'configelement-detail', 'lookup_field': 'id'}
		}

	def create(self, validated_data):
		configs = validated_data.pop('instrument_config')

		config_element = ConfigElement.objects.create(**validated_data)
		config_element.save()

		for config in configs:
			config_result = InstrumentConfig.objects.filter(pk=config.id)
			if config_result.exists():
				c = config_result.first()
				config_element.instrument_config.add(c)
		
		config_element.save()
		return config_element

	def update(self, instance, validated_data):
		instance.instrument_id = validated_data.get('instrument', instance.instrument)
		
		# Disassociate existing `Instrument Configs`
		configs = instance.instrument_config.all()
		for config in configs:
			instance.instrument_config.remove(config)

		configs = validated_data.pop('instrument_config')
		for config in configs:
			config_result = InstrumentConfig.objects.filter(pk=config.id)
			if config_result.exists():
				c = config_result.first()
				instance.instrument_config.add(c)

		instance.name = validated_data.get('name', instance.name)

		instance.modified_by_id = validated_data.get('modified_by', instance.modified_by)

		instance.save()
		
		return instance