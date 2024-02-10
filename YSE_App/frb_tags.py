""" Code related to FRB tags """

#from YSE_App.chime import tags as chime_tags

from YSE_App.models import FRBSampleCriteria

#def find_tags(frb):
#    """ Grab possible tags for an FRB instance
#
#    Args:
#        frb (FRBTransient): FRBTransient instance
#
#    Returns:
#        list: list of tags
#    """
#
#    # CHIME?
#    if frb.frb_survey.name == 'CHIME/FRB':
#        return chime_tags.set_from_instance(frb)
#
#    return []

def values_from_tags(frb, key:str, debug:bool=False):
    """ Grab a list of values for a given key from the tags
      of a given FRB

    Args:
        frb (FRBTransient): FRBTransient instance
        key (str): key to grab
        debug (bool, optional): Debug flag. Defaults to False.

    Returns:
        list: list of values for the key;  can be empty
    """

    # Prep
    tag_names = [frb_tag.name for frb_tag in frb.frb_tags.all()]
    if debug:
        print(f"tag_names = {tag_names} for {frb.name} and key {key}")

    # Get all samples with the frb survey
    samples = FRBSampleCriteria.objects.filter(
        frb_survey=frb.frb_survey)

    # Loop through 
    values = []
    for sample in samples:
        #if debug and key == 'min_POx':
        #    print(f"{sample['name']} {list(sample.keys())}")
        if sample.name in tag_names and getattr(sample,key) is not None:
            values.append(getattr(sample,key))

    return values
