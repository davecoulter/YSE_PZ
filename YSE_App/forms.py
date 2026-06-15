from django.db import models
from django.forms import ModelForm
from django import forms
from YSE_App.models import *
from django.utils import timezone
from datetime import timedelta
from YSE_App.queries.yse_python_queries import python_query_reg

class TransientForm(ModelForm):
    class Meta:
        model = Transient
        fields = [
            'status',
            'obs_group',
            'non_detect_band',
            'best_spec_class',
            'best_spectrum',
            'host',
            'abs_mag_peak_band',
            'host',
            'name',
            'ra',
            'dec',
            'disc_date',
            'candidate_hosts',
            'redshift',
            'redshift_err',
            'redshift_source',
            'non_detect_date',
            'non_detect_limit',
            'mw_ebv',
            'abs_mag_peak',
            'abs_mag_peak_date',
            'postage_stamp_file']

class TransientFollowupForm(ModelForm):
    audience_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label="Collaboration groups",
        widget=forms.CheckboxSelectMultiple,
    )

    status = forms.ModelChoiceField(
        FollowupStatus.objects.all(),
        initial=FollowupStatus.objects.filter(name='Requested').first())
    qs = ClassicalResource.objects.filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('end_date_valid').select_related()
    if len(qs):
        classical_resource = forms.ModelChoiceField(
            queryset=qs,
            initial=qs[0],
            required=False)
        valid_start = forms.DateTimeField(initial=qs[0].begin_date_valid)
        valid_stop = forms.DateTimeField(initial=qs[0].end_date_valid)
    else:
        classical_resource = forms.ModelChoiceField(
            queryset=qs,
            required=False)
        valid_start = forms.DateTimeField()
        valid_stop = forms.DateTimeField()
    comment = forms.CharField(required=False)

    def __init__(self, *args, user=None, transient_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        self.fields["valid_start"].required = False
        self.fields["valid_stop"].required = False
        if transient_id is not None:
            self.fields["transient"].initial = transient_id
            self.fields["transient"].widget = forms.HiddenInput()
        self.show_audience_picker = False
        self.followup_audience_choices = []
        self.resource_audience_map = {}

        if user is not None:
            from YSE_App import view_utils

            valid_after = timezone.now() - timedelta(days=1)
            self.fields["classical_resource"].queryset = (
                view_utils.get_authorized_classical_resources(user)
                .filter(end_date_valid__gt=valid_after)
                .order_by("telescope__name")
            )
            self.fields["too_resource"].queryset = (
                view_utils.get_authorized_too_resources(user)
                .filter(end_date_valid__gt=valid_after)
                .order_by("telescope__name")
            )
            self.fields["queued_resource"].queryset = (
                view_utils.get_authorized_queued_resources(user)
                .filter(end_date_valid__gt=valid_after)
                .order_by("telescope__name")
            )
            classical_qs = self.fields["classical_resource"].queryset
            if classical_qs.exists():
                initial_resource = classical_qs.first()
                self.fields["classical_resource"].initial = initial_resource
                self.fields["valid_start"].initial = initial_resource.begin_date_valid
                self.fields["valid_stop"].initial = initial_resource.end_date_valid

            self.fields["audience_groups"].queryset = user.groups.order_by("name")
            self.show_audience_picker = user.groups.exists()
            from YSE_App.services.audience import (
                build_followup_audience_choices,
                build_followup_resource_audience_map,
            )

            linked_resource = self._linked_resource_from_bound_data()
            self.followup_audience_choices = build_followup_audience_choices(
                user, linked_resource
            )
            eligible_ids = [
                choice["group"].pk
                for choice in self.followup_audience_choices
                if choice["enabled"]
            ]
            self.fields["audience_groups"].initial = eligible_ids
            self.resource_audience_map = build_followup_resource_audience_map(self)
            self.public_group_id = next(
                (
                    choice["group"].pk
                    for choice in self.followup_audience_choices
                    if choice["is_public_group"]
                ),
                None,
            )

    def _linked_resource_from_bound_data(self):
        data = self.data if self.is_bound else None
        for field_name in ("classical_resource", "too_resource", "queued_resource"):
            if data is not None:
                raw_pk = data.get(field_name)
                if raw_pk:
                    return self.fields[field_name].queryset.filter(pk=raw_pk).first()
            initial = self.fields[field_name].initial
            if initial is not None:
                if hasattr(initial, "pk"):
                    return initial
                return self.fields[field_name].queryset.filter(pk=initial).first()
        return None

    def clean(self):
        cleaned_data = super().clean()
        classical = cleaned_data.get("classical_resource")
        too = cleaned_data.get("too_resource")
        queued = cleaned_data.get("queued_resource")
        linked_resource = classical or too or queued
        if classical:
            cleaned_data["valid_start"] = classical.begin_date_valid
            cleaned_data["valid_stop"] = classical.end_date_valid
        elif not cleaned_data.get("valid_start") or not cleaned_data.get("valid_stop"):
            if too or queued:
                raise forms.ValidationError(
                    "Provide a date range for ToO or queued follow-up requests."
                )
            raise forms.ValidationError(
                "Select a classical, ToO, or queued resource for this follow-up."
            )

        if self._user is not None:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            from YSE_App.services.audience import (
                resolve_followup_audience,
                resource_is_creator_only,
            )

            if not linked_resource:
                raise forms.ValidationError(
                    "Select a classical, ToO, or queued resource for this follow-up."
                )

            selected = cleaned_data.get("audience_groups")
            selected_list = list(selected) if selected is not None else []
            if not selected_list and not resource_is_creator_only(linked_resource):
                raise forms.ValidationError(
                    {
                        "audience_groups": "Select at least one collaboration group.",
                    }
                )

            try:
                resolve_followup_audience(
                    self._user,
                    cleaned_data.get("transient").pk
                    if cleaned_data.get("transient") is not None
                    else 0,
                    audience_groups=selected_list,
                    linked_resource=linked_resource,
                    explicit_audience=True,
                )
            except DRFValidationError as exc:
                raise forms.ValidationError(exc.detail) from exc
        return cleaned_data

    class Meta:
        model = TransientFollowup
        fields = [
            'status',
            'too_resource',
            'classical_resource',
            'queued_resource',
            'comment',
            'valid_start',
            'valid_stop',
            'spec_priority',
            'phot_priority',
            'offset_star_ra',
            'offset_star_dec',
            'offset_north',
            'offset_east',
            'transient']

class ClassicalResourceForm(ModelForm):

    observing_date = forms.DateTimeField()

    class Meta:
        model = ClassicalResource
        fields = [
            'telescope',
            'principal_investigator']

class ToOResourceForm(ModelForm):

    awarded_too_hours = forms.FloatField(initial=0)
    used_too_hours = forms.FloatField(initial=0)
    awarded_too_triggers = forms.FloatField(initial=0)
    used_too_triggers = forms.FloatField(initial=0)

    class Meta:
        model = ToOResource
        fields = [
            'telescope',
            'principal_investigator',
            'begin_date_valid',
            'end_date_valid',
            'awarded_too_hours',
            'used_too_hours',
            'awarded_too_triggers',
            'used_too_triggers']

class SurveyFieldForm(ModelForm):

    valid_start = forms.DateTimeField()
    valid_stop = forms.DateTimeField()
    coord = forms.CharField()
    qs = Instrument.objects.filter(name__startswith = 'GPC').select_related()
    if len(qs):
        instrument = forms.ModelChoiceField(
            queryset=qs,
            initial=qs[0],
            required=False)

    class Meta:
        model = SurveyField
        fields = ['field_id',
                  'cadence',
                  'ztf_field_id',
                  'instrument']

class SurveyObsForm(ModelForm):

    survey_obs_date = forms.DateTimeField()

    qs = [(i['ztf_field_id'], i['ztf_field_id']) for i in SurveyField.objects.filter(~Q(obs_group__name='ZTF')).values('ztf_field_id').distinct().order_by('ztf_field_id')]

    if len(qs):
        ztf_field_id = forms.MultipleChoiceField(
            choices=qs,
            initial=qs[0],
            required=True)
    else:
        ztf_field_id = forms.MultipleChoiceField(
            choices=[],
            required=True)


    instrument = forms.MultipleChoiceField(
        choices=[['GPC1','GPC1'],['GPC2','GPC2']],
        initial=['GPC1','GPC1'],
        required=True)

    class Meta:
        model = SurveyObservation
        fields = ['survey_obs_date','ztf_field_id','priority','instrument']


class OncallForm(ModelForm):

    valid_start = forms.DateTimeField()
    valid_stop = forms.DateTimeField()
    qs = User.objects.all().filter(groups__name='YSE').filter(~Q(username='admin')).order_by('username')
    if len(qs):
        user = forms.ModelChoiceField(
            queryset=qs,
            initial=qs[0],
            required=False)

    class Meta:
        model = YSEOnCallDate
        fields = [] #['field_id',
        #		  'cadence',
        #		  'ztf_field_id',
        #		  'instrument']



class TransientCommentForm(ModelForm):
    is_public = forms.BooleanField(
        required=False,
        initial=False,
        label="Visible to all YSE users who can open this transient",
    )
    audience_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label="Collaboration groups",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, user=None, transient_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_audience_picker = False
        if user is not None and transient_id is not None:
            from YSE_App.services.audience import selectable_audience_groups

            qs = selectable_audience_groups(user, transient_id)
            self.fields["audience_groups"].queryset = qs
            self.fields["audience_groups"].initial = list(qs.values_list("pk", flat=True))
            self.show_audience_picker = qs.exists()

    class Meta:
        model = Log
        fields = [
            'comment',
            'transient']


class TransientObservationTaskForm(ModelForm):
    class Meta:
        model = TransientObservationTask
        fields = [
            'status',
            'instrument_config',
            'exposure_time',
            'number_of_exposures',
            'desired_obs_date',
            'actual_obs_date',
            'description',
            'followup']

class QueryModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.__str__

class AddDashboardQueryForm(ModelForm):
    query = QueryModelChoiceField(Query.objects.all(),required=False)
    query_names = [('', '---------')] + [(q,q) for i,q in enumerate(python_query_reg.all.keys())]
    python_query = forms.ChoiceField(choices=query_names,required=False)
    #import pdb; pdb.set_trace()

    class Meta:
        model = UserQuery
        fields = [
            'query','python_query']

class RemoveDashboardQueryForm(ModelForm):
    #query = QueryModelChoiceField(Query.objects.all())

    class Meta:
        model = UserQuery
        fields = ['id']

class AddFollowupNoticeForm(ModelForm):
    telescope = QueryModelChoiceField(Telescope.objects.all())
    #import pdb; pdb.set_trace()
    class Meta:
        model = UserTelescopeToFollow
        fields = ['telescope']
    #		'id']

class RemoveFollowupNoticeForm(ModelForm):
    telescope = QueryModelChoiceField(Telescope.objects.all())

    class Meta:
        model = UserTelescopeToFollow
        fields = [
            'id']


class SpectrumUploadForm(ModelForm):
    filename = forms.FileField()
    obs_date = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'])
    obs_group = forms.ModelChoiceField(
        ObservationGroup.objects.filter(Q(name='SSS') | Q(name='Foundation') |
                                        Q(name='TESS') | Q(name='YSE') |
                                        Q(name='UCSC') |
                                        Q(name='Other')))
    data_quality = forms.ModelChoiceField(
        DataQuality.objects.filter(Q(name='Quicklook')),required=False)

    qs = [(i['name'], i['name']) for i in Group.objects.all().values('name').distinct().order_by('name')]
    permissions = forms.MultipleChoiceField(
            choices=qs,
            required=False)

    spec_instruments = [
        'SED-Machine','P200-TSPEC','SPRAT',
        'LFC','DBSP','MIKE','LDSS-3',
        'aade - MagE','aade - Boller & Chivens',
        'WFC3','STIS','IRS','B&C-Asi-1.22m',
        'IMACS','lay - LDSS-2','ALFOSC',
        'Mod-spec','B&C-duPont',
        'WFCCD','V-grism','UV-grism',
        'X-Shooter','EFOSC-2.2','Sofi',
        'EFOSC2-NTT','EMMI','EFOSC2-3.6',
        'OSIRIS','FLOYDS-N','FLOYDS-S','NIRC2',
        'NIRSPEC','NIRES','KCWI','ESI',
        'DEIMOS','OSIRIS','MOSFIRE','LRIS','LRS2',
        'HIRES','GMOS','Goodman','KAST','WiFeS','WFCCD','DIS','Binospec','SpeX','UVES',
        'GNIRS','FLAMINGOS-2','DOLORES']
    instrument = forms.ModelChoiceField(Instrument.objects.filter(Q(name__in=spec_instruments)))
    #import pdb; pdb.set_trace()
    class Meta:
        model = TransientSpectrum
        fields = ('transient','ra',
                  'dec','spec_phase')#,'obs_group','instrument')

class AutomatedSpectrumRequest(ModelForm):

    spec_instruments = ['FLOYDS-N','FLOYDS-S','Goodman']
    instrument = forms.ModelChoiceField(Instrument.objects.filter(Q(name__in=spec_instruments)))
    exp_time = forms.IntegerField(initial=1800) # 1800s seems like a reasonable default
    spectrum_valid_start = forms.DateTimeField()
    spectrum_valid_stop = forms.DateTimeField()

    class Meta:
        model = TransientFollowup
        fields =('transient',)
  
