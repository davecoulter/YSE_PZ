""" Code related to FRB tags """

from YSE_App.chime import tags as chime_tags

def find_tags(frb):

    # CHIME?
    if frb.frb_survey.name == 'CHIME/FRB':
        return chime_tags.set_from_instance(frb)

    return []

def values_from_tags(frb, key:str):

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
