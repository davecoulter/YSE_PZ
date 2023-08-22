""" This module will specify the tags 
to be used for CHIME/FRB transients.  This 
code may move to chime_ffff_pz """

# "Unbiased" survey
blind_survey = dict(
    name='CHIME-Blind',
    version='1.0',
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    max_EBV=0.3,
    min_POx=0.9,
    Prob=0.3,
    label=['Stripe 82'],
    )

# High DM
highDM_survey = dict(
    name='CHIME-HighDM',
    version='1.0',
    max_EBV=0.3,
    min_DM=1000.,
    )

# Repeater
repeater_survey = dict(
    name='CHIME-Repeater',
    version='1.0',
    )


def set_from_instance(instance):
    """ Set tags from an instance (usually an FRBTransient)

    Eventually this will loop through all of the
    possible CHIME tags and set them

    Args:
        instance (FRBTransient): FRBTransient instance

    Returns:
        list: list of CHIME tags for this instance
    """

    tags = []

    # ###################################
    # Blind?
    flag_blind = False
    for ra_rng, dec_rng, label in zip(
        blind_survey['ra_rngs'], 
        blind_survey['dec_rngs'], 
        blind_survey['label']):
        # Need be in any one region
        if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
            instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
            flag_blind = True
    # Test for E(B-V)
    if instance.mw_ebv > blind_survey['max_EBV']:
        flag_blind = False

    # Test for Stars

    # P(O|x) ??  No!
    
    # Finish
    if flag_blind:
        tags.append(blind_survey['name'])

    # ###################################
    # High DM?
    if instance.DM > highDM_survey['min_DM'] and (
        instance.mw_ebv < blind_survey['max_EBV']):
        tags.append(highDM_survey['name'])
    
    # ###################################
    if instance.repeater:
        tags.append(repeater_survey['name'])

    # Need something
    if len(tags) == 0:
        tags = ['CHIME-Unknown']

    # Return
    return tags