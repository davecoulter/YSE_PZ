from YSE_App.models import *
from django.db.models import Q


def GetUserGroupQuery(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)

    no_group = Q(groups__isnull=True)
    contains_group = Q(groups__name__in=user_groups)

    return no_group, contains_group

def GetAuthorizedToOResource_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)
    allowed_too_resources = ToOResource.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()

    return allowed_too_resources

def GetAuthorizedQueuedResource_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)
    allowed_queuedresources = QueuedResource.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()

    return allowed_queuedresources

def GetAuthorizedClassicalResource_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)
    allowed_classicalresources = ClassicalResource.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()

    return allowed_classicalresources

def GetAuthorizedClassicalObservingDate_ByUser(user):
    allowed_classical_resource = GetAuthorizedClassicalResource_ByUser(user)
    classical_resource_ids = allowed_classical_resource.values('id')
    allowed_classical_obs_dates_query = Q(resource__id__in=classical_resource_ids)
    allowed_classical_obs_dates = ClassicalObservingDate.objects.filter(allowed_classical_obs_dates_query)

    return allowed_classical_obs_dates




