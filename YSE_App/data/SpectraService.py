from YSE_App.models import *
from django.db.models import Q


def GetUserGroupQuery(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)

    no_group = Q(groups__isnull=True)
    contains_group = Q(groups__name__in=user_groups)

    return no_group, contains_group

def GetAuthorizedTransientSpectrum_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)
    allowed_spec = TransientSpectrum.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()

    return allowed_spec

def GetAuthorizedTransientSpectrum_ByUser_ByTransient(user, transient_id):

    allowed_spec_by_group = GetAuthorizedTransientSpectrum_ByUser(user)
    transient_query = Q(transient=transient_id)
    allowed_spec_by_group_by_transient = allowed_spec_by_group.filter(transient_query).distinct()

    return allowed_spec_by_group_by_transient

def GetAuthorizedHostSpectrum_ByUser(user):
    host_query_tuple = GetUserGroupQuery(user)
    allowed_phot = HostSpectrum.objects.filter(host_query_tuple[0] | host_query_tuple[1]).distinct()

    return allowed_phot

def GetAuthorizedHostSpectrum_ByUser_ByHost(user, host_id):
    allowed_spec_by_group = HostSpectrum(user)
    host_query = Q(host=host_id)
    allowed_spec_by_group_by_host = allowed_spec_by_group.filter(host_query).distinct()

    return allowed_spec_by_group_by_host

def GetAuthorizedTransientSpecData_ByUser(user):
    allowed_spec = GetAuthorizedTransientSpectrum_ByUser(user)
    spec_ids = allowed_spec.values('id')
    allowed_spec_data_query = Q(spectrum__id__in=spec_ids)
    allowed_spec_data = TransientSpecData.objects.filter(allowed_spec_data_query)

    return allowed_spec_data

def GetAuthorizedHostSpecData_ByUser(user):
    allowed_spec = GetAuthorizedHostSpectrum_ByUser(user)
    spec_ids = allowed_spec.values('id')
    allowed_spec_data_query = Q(spectrum__id__in=spec_ids)
    allowed_spec_data = HostSpecData.objects.filter(allowed_spec_data_query)

    return allowed_spec_data