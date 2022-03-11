def NotAuthorizedToAccessParent(parent_obj, user_groups):

    existing_groups = parent_obj.groups.all()
    existing_groups_exist = existing_groups.count() > 0
    authorized_groups = (
        len(set.intersection(set(user_groups), set(existing_groups))) > 0
    )

    return existing_groups_exist and not authorized_groups
