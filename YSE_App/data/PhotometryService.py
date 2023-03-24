from YSE_App.models import *
from django.db.models import Q
from YSE_App.models import phot_models

def GetUserGroupQuery(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)


    # Check if you're a member, by string of the observation group associated with the record
    contains_obs_group = Q(obs_group__name__in=user_groups)

    # Default to viewable, any photometry with no many-to-many auth group association
    no_group = Q(groups__isnull=True)

    # Check if user within many-to-many auth_group collection
    contains_many_to_many_group = Q(groups__name__in=user_groups)

    # return no_group, contains_group
    return contains_obs_group, no_group, contains_many_to_many_group

def GetAuthorizedTransientPhotometry_ByUser(user):
    group_query_tuple = GetUserGroupQuery(user)

    contains_obs_group = group_query_tuple[0]
    no_auth_groups = group_query_tuple[1]
    auth_groups = group_query_tuple[2]

    # allowed_phot = TransientPhotometry.objects.filter(group_query_tuple[0] | group_query_tuple[1]).distinct()
    # allowed_phot = TransientPhotometry.objects.filter(group_query_tuple[1]).distinct()
    # allowed_phot = TransientPhotometry.objects.filter(group_query_tuple[0])
    # test = allowed_phot.filter(group_query_tuple[1]).distinct()

    # get photometry that has no auth_group look ups, and is in the same obs_group as a user
    allowed_phot = TransientPhotometry.objects.filter((no_auth_groups & contains_obs_group) | contains_obs_group)
    return allowed_phot
    # return test

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

def GetAuthorizedTransientPhotData_ByUser(user, includeBadData=True):
    allowed_phot = GetAuthorizedTransientPhotometry_ByUser(user)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = _GetTransientPhotData(includeBadData, allowed_phot_data_query)

    return allowed_phot_data

def GetAuthorizedTransientPhotData_ByUser_ByTransient(user, transient_id, includeBadData=True):
    allowed_phot = GetAuthorizedTransientPhotometry_ByUser_ByTransient(user, transient_id)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = _GetTransientPhotData(includeBadData, allowed_phot_data_query)

    return allowed_phot_data

def GetAuthorizedHostPhotData_ByUser(user, includeBadData=True):
    allowed_phot = GetAuthorizedHostPhotometry_ByUser(user)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = _GetHostPhotData(includeBadData, allowed_phot_data_query)

    return allowed_phot_data

def GetAuthorizedHostPhotData_ByUser_ByHost(user, host_id, includeBadData=True):
    allowed_phot = GetAuthorizedHostPhotometry_ByUser_ByHost(user, host_id)
    phot_ids = allowed_phot.values('id')
    allowed_phot_data_query = Q(photometry__id__in=phot_ids)
    allowed_phot_data = _GetHostPhotData(includeBadData, allowed_phot_data_query)

    return allowed_phot_data

def GetAuthorizedTransientPhotData_ByPhotometry(user, photometry_id, includeBadData=True):
    # First check if they're allowed to access...
    allowed_phot = GetAuthorizedTransientPhotometry_ByUser(user).filter(pk=photometry_id)

    phot_data = None
    if allowed_phot:
        #... then get the data according to the dq flag preference
        query = Q(photometry__id=photometry_id)
        phot_data = _GetTransientPhotData(includeBadData, query)

    return phot_data

def GetAuthorizedHostPhotData_ByPhotometry(user, photometry_id, includeBadData=True):
    # First check if they're allowed to access...
    allowed_phot = GetAuthorizedHostPhotometry_ByUser(user).filter(photometry__id=photometry_id)

    phot_data = None
    if allowed_phot:
        # ... then get the data according to the dq flag preference
        query = Q(pk=photometry_id)
        phot_data = _GetHostPhotData(includeBadData, query)

    return phot_data


# This are private methods. Don't invoke them outside of this module!
def _GetTransientPhotData(includeBadData,filter):
    if includeBadData:
        return TransientPhotData.objects.filter(filter)
    else:
        return TransientPhotData.objects.exclude(data_quality__isnull=False).filter(filter)

def _GetHostPhotData(includeBadData, filter):
    if includeBadData:
        return HostPhotData.objects.filter(filter)
    else:
        return HostPhotData.objects.exclude(data_quality__isnull=False).filter(filter)
