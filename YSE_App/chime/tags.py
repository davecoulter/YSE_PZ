""" This module will specify the tags 
to be used for CHIME/FRB transients.  This 
code may move to chime_ffff_pz 

Better -- it should become part of the database
 and therefore a Django model

THIS HAS BEEN DEPRECATED!

"""

# "Unbiased" sample
blind_sample = dict(
    name='CHIME-Blind',
    version='0.1',
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    max_EBV=0.3,
    mr_max=24.5,     # Faintest magnitude to try spectroscopy
    max_P_Ux=0.5,    # Host is considered unseen if P(U|x) is greater than this
    min_POx=0.0,    # Minimum P(O|x) to consider (of top 2)
    end_date='2030-12-31', # Not implemented yet
    prob=0.3,
    label=['Stripe 82'],
    )

# High DM (notional)
highDM_sample = dict(
    name='CHIME-HighDM',
    version='0.1',
    max_EBV=0.3,
    min_DM=1000.,
    max_P_Ux=0.5,    # Host is considered unseen if P(U|x) is greater than this
    mr_max=24.5,   # Faintest magnitude to try spectroscopy
    prob=0.8,
    )

# Repeater (notional)
repeater_sample = dict(
    name='CHIME-Repeater',
    version='0.1',
    prob=0.8,
    mr_max=24.5,   # Faintest magnitude to try spectroscopy
    )

# KKO
kko_sample = dict(
    name='CHIME-KKO',
    version='0.1',
    max_EBV=0.3,     #
    mr_max=23.,      # Faintest magnitude to try spectroscopy -- not implemented
    min_POx=0.9,     # Minimum P(O|x) to consider (of top 2)
    max_P_Ux=0.5,    # Host is considered unseen if P(U|x) is greater than this
    prob=0.8,
    )

# Bright FRBs
bright_sample = dict(
    name='CHIME-Bright',
    version='0.1',
    max_EBV=0.3,     #
    mr_max=22.,      # Faintest magnitude to try spectroscopy -- not implemented
    min_POx=0.9,     # Minimum P(O|x) to consider (of top 2)
    max_P_Ux=0.5,    # Host is considered unseen if P(U|x) is greater than this
    prob=0.8,
    )

all_samples = [blind_sample, highDM_sample, repeater_sample, kko_sample, bright_sample]


def set_from_instance(instance):
    """ Set tags from an instance (usually an FRBTransient)

    Eventually this will loop through all of the
    possible CHIME tags and set them

    Actually, this is likely to be deprecated and the user
    will be forced to set the Tag at ingestion

    Args:
        instance (FRBTransient): FRBTransient instance

    Returns:
        list: list of CHIME tags for this instance
    """

    tags = []

    # ###################################
    # Blind?
    flag_blind = False
    for ra_rng, dec_rng, _ in zip(
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