""" Specify CHIME Surveys """

blind_survey = dict(
    ra_rngs=[[0, 225]],
    dec_rngs=[[-10, 10]],
    label=['Stripe 82'],
    )

def set_from_instance(instance):

   # Blind?
   surveys = []
   for ra_rng, dec_rng, label in zip(
       blind_survey['ra_rngs'], 
       blind_survey['dec_rngs'], 
       blind_survey['label']):
       if instance.ra > ra_rng[0] and instance.ra < ra_rng[1] and \
           instance.dec > dec_rng[0] and instance.dec < dec_rng[1]:
           surveys.append('Blind')

    return surveys