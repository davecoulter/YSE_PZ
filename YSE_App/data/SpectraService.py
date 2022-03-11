from YSE_App.models import *
from django.db.models import Q


def GetUserGroupQuery(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)

    no_group = Q(groups__isnull=True)
    contains_group = Q(groups__name__in=user_groups)

    return no_group, contains_group


def GetAuthorizedTransientSpectrum_ByUser(user, includeBadData=False):
    group_query_tuple = GetUserGroupQuery(user)
    query = Q(group_query_tuple[0] | group_query_tuple[1])
    allowed_spec = _GetTransientSpectrum(includeBadData, query).distinct()
    return allowed_spec


def GetAuthorizedTransientSpectrum_ByUser_ByTransient(
    user, transient_id, includeBadData=False
):

    allowed_spec_by_group = GetAuthorizedTransientSpectrum_ByUser(user, includeBadData)
    transient_query = Q(transient=transient_id)
    allowed_spec_by_group_by_transient = allowed_spec_by_group.filter(
        transient_query
    ).distinct()

    return allowed_spec_by_group_by_transient


def GetAuthorizedHostSpectrum_ByUser(user, includeBadData=False):
    host_query_tuple = GetUserGroupQuery(user)
    query = Q(host_query_tuple[0] | host_query_tuple[1])
    allowed_phot = _GetHostSpectrum(includeBadData, query).distinct()

    return allowed_phot


def GetAuthorizedHostSpectrum_ByUser_ByHost(user, host_id, includeBadData=False):
    allowed_spec_by_group = GetAuthorizedHostSpectrum_ByUser(user, includeBadData)
    host_query = Q(host=host_id)
    allowed_spec_by_group_by_host = allowed_spec_by_group.filter(host_query).distinct()

    return allowed_spec_by_group_by_host


def GetAuthorizedTransientSpecData_ByUser(user, includeBadData=False):
    allowed_spec = GetAuthorizedTransientSpectrum_ByUser(user, includeBadData)
    spec_ids = allowed_spec.values("id")
    allowed_spec_data_query = Q(spectrum__id__in=spec_ids)
    allowed_spec_data = TransientSpecData.objects.filter(allowed_spec_data_query)

    return allowed_spec_data


def GetAuthorizedHostSpecData_ByUser(user, includeBadData=False):
    allowed_spec = GetAuthorizedHostSpectrum_ByUser(user, includeBadData)
    spec_ids = allowed_spec.values("id")
    allowed_spec_data_query = Q(spectrum__id__in=spec_ids)
    allowed_spec_data = HostSpecData.objects.filter(allowed_spec_data_query)

    return allowed_spec_data


def GetAuthorizedTransientSpecData_BySpectrum(user, spectrum_id, includeBadData=False):
    # First check if they're allowed to access...
    allowed_spec = GetAuthorizedTransientSpectrum_ByUser(user, includeBadData)
    if allowed_spec:
        allowed_spec = allowed_spec.filter(pk=spectrum_id)

    spec_data = None
    if allowed_spec:
        # ... then get the data according to the dq flag preference
        spec_data = TransientSpecData.objects.filter(spectrum__id=spectrum_id)

    return spec_data


def GetAuthorizedHostSpecData_BySpectrum(user, spectrum_id, includeBadData=False):
    # First check if they're allowed to access...
    allowed_spec = GetAuthorizedHostSpectrum_ByUser(user, includeBadData)
    if allowed_spec:
        allowed_spec = allowed_spec.filter(pk=spectrum_id)

    spec_data = None
    if allowed_spec:
        # ... then get the data according to the dq flag preference
        spec_data = HostSpecData.objects.filter(spectrum__id=spectrum_id)

    return spec_data


# This are private methods. Don't invoke them outside of this module!
def _GetTransientSpectrum(includeBadData, filter):
    if includeBadData:
        return TransientSpectrum.objects.filter(filter)
    else:
        return TransientSpectrum.objects.exclude(data_quality__isnull=False).filter(
            filter
        )


def _GetHostSpectrum(includeBadData, filter):
    if includeBadData:
        return HostSpectrum.objects.filter(filter)
    else:
        return HostSpectrum.objects.exclude(data_quality__isnull=False).filter(filter)
