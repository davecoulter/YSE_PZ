""" Code related to FRB tags """

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
    # Hiding here to avoid circular import (I hope)
    from YSE_App.models import FRBSampleCriteria

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
        if sample.name in tag_names and getattr(sample,key) is not None:
            values.append(getattr(sample,key))

    return values
