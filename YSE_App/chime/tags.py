""" Specify CHIME Tags """

blind_survey = dict(
    name='CHIME-Blind',
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    label=['Stripe 82'],
    )

def set_from_instance(instance):
    # Blind?
    tags = []
    for ra_rng, dec_rng, label in zip(
        blind_survey['ra_rngs'], 
        blind_survey['dec_rngs'], 
        blind_survey['label']):
        if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
            instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
            tags.append(blind_survey['name'])

    return tags