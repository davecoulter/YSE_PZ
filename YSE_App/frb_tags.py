""" Code related to FRB tags """

from YSE_App.chime import tags as chime_tags

def find_tags(frb):
    """ Grab possible tags for an FRB instance

    Args:
        frb (FRBTransient): FRBTransient instance

    Returns:
        list: list of tags
    """

    # CHIME?
    if frb.frb_survey.name == 'CHIME/FRB':
        return chime_tags.set_from_instance(frb)

    return []

def values_from_tags(frb, key:str):
    """ Grab a list of values for a given key from the tags
      of a given FRB

    Args:
        frb (FRBTransient): FRBTransient instance
        key (str): key to grab

    Returns:
        list: list of values for the key;  can be empty
    """

    # Prep
    tag_names = [frb_tag.name for frb_tag in frb.frb_tags.all()]

    # Get all of the values in a list
    values = []

    if frb.frb_survey.name == 'CHIME/FRB':
        # Loop through 
        for sample in chime_tags.all_samples:
            if sample['name'] in tag_names and key in sample.keys():
                values.append(sample[key])

    return values
