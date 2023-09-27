""" Utilities related to FFFF-PZ """

from django.core.exceptions import ObjectDoesNotExist

def add_or_grab_obj(iclass, uni_fields:dict, extra_fields:dict, user=None):
    """ Convenience utility to add/grab an object in the DB

    Args:
        iclass (django model): Model to add/grab
        uni_fields (dict): 
            dict of fields that uniquely identify the object
        extra_fields (dict): 
            dict of additional fields to add to the object if it is created
        user (django user object, optional): user object. Defaults to None.

    Returns:
        django instance: Object either grabbed or added to the DB
    """
    try:
        obj = iclass.objects.get(**uni_fields)
    except ObjectDoesNotExist:
        # Merge
        all_fields = uni_fields.copy()
        all_fields.update(extra_fields)
        # Add user?
        if user is not None:
            all_fields['created_by'] = user
            all_fields['modified_by'] = user
        obj = iclass(**all_fields)
        obj.save()
        print("Object created")
    else:
        print("Object existed, returning it")
    # Return
    return obj
