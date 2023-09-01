""" This module will specify the tags 
to be used for CHIME/FRB transients.  This 
code may move to chime_ffff_pz """

# "Unbiased" survey
blind_survey = dict(
    name='CHIME-Blind',
    version='1.0',
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    label=['Stripe 82'],
    )

def set_from_instance(instance):
    """ Set tags from an instance (usually an FRBTransient)

    Eventually this will loop through all of the
    possible CHIME tags and set them

    Args:
        instance (FRBTransient): FRBTransient instance

    Returns:
        list: list of CHIME tags
    """

    # Blind?
    tags = []
    for ra_rng, dec_rng, label in zip(
        blind_survey['ra_rngs'], 
        blind_survey['dec_rngs'], 
        blind_survey['label']):
        if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
            instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
            tags.append(blind_survey['name'])

    if len(tags) == 0:
        tags = ['CHIME-Unknown']
    return tags