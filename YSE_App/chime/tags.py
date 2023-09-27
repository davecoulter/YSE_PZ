""" This module will specify the tags 
to be used for CHIME/FRB transients.  This 
code may move to chime_ffff_pz """

# "Unbiased" sample
blind_sample = dict(
    name='CHIME-Blind',
    version='1.0',
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    max_EBV=0.3,
    min_POx=0.9,
    end_date='2030-12-31', # Not implemented yet
    prob=0.3,
    label=['Stripe 82'],
    )

# High DM (notional)
highDM_sample = dict(
    name='CHIME-HighDM',
    version='0.0',
    max_EBV=0.3,
    min_DM=1000.,
    prob=0.8,
    )

# Repeater (notional)
repeater_sample = dict(
    name='CHIME-Repeater',
    version='0.0',
    prob=0.8,
    )

all_samples = [blind_sample, highDM_sample, repeater_sample]


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
        blind_sample['ra_rngs'], 
        blind_sample['dec_rngs'], 
        blind_sample['label']):
        # Need be in any one region
        if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
            instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
            flag_blind = True
    # Test for E(B-V)
    if instance.mw_ebv > blind_sample['max_EBV']:
        flag_blind = False

    # Test for Stars

    # P(O|x) ??  No!
    
    # Finish
    if flag_blind:
        tags.append(blind_sample['name'])

    # ###################################
    # High DM?
    if instance.DM > highDM_sample['min_DM'] and (
        instance.mw_ebv < blind_sample['max_EBV']):
        tags.append(highDM_sample['name'])
    
    # ###################################
    if instance.repeater:
        tags.append(repeater_sample['name'])

    # Need something
    if len(tags) == 0:
        tags = ['CHIME-Unknown']

    # Return
    return tags