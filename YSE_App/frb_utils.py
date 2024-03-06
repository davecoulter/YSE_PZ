""" Utilities related to FFFF-PZ """

import pandas
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ForeignKey

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

def addmodify_obj(iclass, data:dict, user): 

    # Grab the meta keys of the class
    keys = [item.name for item in iclass._meta.fields]

    # Resolve any Foreign Keys
    for key in data.keys():
        if key not in keys:
            return 400, f'Bad key: {key}'
        if isinstance(iclass._meta.get_field(key), ForeignKey):
            fkmodel = iclass._meta.get_field(key).remote_field.model
            # Grab it
            fk = fkmodel.objects.filter(name=data[key])
            data[key] = fk[0]

    # Check if the object already exists
    try:
        obj=iclass.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        # It does not exist;  go forth and add it!
        add_or_grab_obj(iclass, data, {}, user)
        return 200, 'Added new object'
    
    # ############################
    # Modify
    data['modified_by'] = user
    # TODO -- do we need this?
    #data['modified_date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for key in data.keys():
        if key in ['name', 'created_by', 'created_date']:
            continue
        try:
            setattr(obj,key,data[key])
        except:
            return 400, f'Bad value for key: {key}'
    iclass.save()
    # Return 
    return 200, 'Modified object'