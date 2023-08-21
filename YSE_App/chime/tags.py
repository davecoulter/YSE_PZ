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

# High DM
highDM_survey = dict(
    name='CHIME-HighDM',
    version='1.0',
    min_DM=1000.,
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

    tags = []

    # Blind?
    flag_blind = True
    for ra_rng, dec_rng, label in zip(
        blind_survey['ra_rngs'], 
        blind_survey['dec_rngs'], 
        blind_survey['label']):
        if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
            instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
            pass
        else:
            flag_blind = False
    # Test for E(B-V)
    # Test for Stars
    if flag_blind:
        tags.append(blind_survey['name'])

    # High DM?
    if instance.DM > highDM_survey['min_DM']:
        tags.append(highDM_survey['name'])
    

    if len(tags) == 0:
        tags = ['CHIME-Unknown']
    return tags