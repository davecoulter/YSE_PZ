from YSE_App.models import *
from django.db.models import Q


def GetUserGroupQuery(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)

    no_group = Q(groups__isnull=True)
    contains_group = Q(groups__name__in=user_groups)

    return no_group, contains_group

def GetAuthorizedTransientPhotometry_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)
    allowed_phot = TransientPhotometry.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()

    return allowed_phot

def GetAuthorizedTransientPhotometry_ByUser_ByTransient(user, transient_id):

    allowed_phot_by_group = GetAuthorizedTransientPhotometry_ByUser(user)
    transient_query = Q(transient=transient_id)
    allowed_phot_by_group_by_transient = allowed_phot_by_group.filter(transient_query).distinct()

    return allowed_phot_by_group_by_transient

def GetAuthorizedHostPhotometry_ByUser(user):
    host_query_tuple = GetUserGroupQuery(user)
    allowed_phot = HostPhotometry.objects.filter(host_query_tuple[0] | host_query_tuple[1]).distinct()

    return allowed_phot

def GetAuthorizedHostPhotometry_ByUser_ByHost(user, host_id):
    allowed_phot_by_group = GetAuthorizedHostPhotometry_ByUser(user)
    host_query = Q(host=host_id)
    allowed_phot_by_group_by_host = allowed_phot_by_group.filter(host_query).distinct()

    return allowed_phot_by_group_by_host

def GetAuthorizedTransientPhotData_ByUser(user):
    allowed_phot = GetAuthorizedTransientPhotometry_ByUser(user)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = TransientPhotData.objects.filter(allowed_phot_data_query)

    return allowed_phot_data

def GetAuthorizedHostPhotData_ByUser(user):
    allowed_phot = GetAuthorizedHostPhotometry_ByUser(user)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = HostPhotData.objects.filter(allowed_phot_data_query)

    return allowed_phot_data
