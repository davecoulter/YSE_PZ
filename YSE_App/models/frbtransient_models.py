from autoslug import AutoSlugField
from auditlog.registry import auditlog

from django.db import models

from YSE_App.models.base import BaseModel
#from YSE_App.models.enum_models import FRBSurvey, get_sentinel_transientstatus
#from YSE_App.models.tag_models import FRBTag
from YSE_App.models import *  # Avoids circular import
from YSE_App.chime import tags as chime_tags
from YSE_App.common.utilities import GetSexigesimalString, getSeparation
from YSE_App.models.frbgalaxy_models import FRBGalaxy

class FRBTransient(BaseModel):

    ### Entity relationships ###
    # Required
    status = models.ForeignKey(TransientStatus, models.SET(get_sentinel_transientstatus))
    frb_survey = models.ForeignKey(FRBSurvey, on_delete=models.CASCADE)

    ### Properties ###
    # Required
    # TNS
    name = models.CharField(max_length=64, unique=True)
    ra = models.FloatField()
    dec = models.FloatField()
    # Dispersion Measure
    DM = models.FloatField()

    # Optional
    ra_err = models.FloatField(null=True, blank=True)
    dec_err = models.FloatField(null=True, blank=True)

    # Host and candidates
    # Highest P(O|x) candidate
    host = models.ForeignKey(
        FRBGalaxy, null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='frb') # Needs to be here for backwards compatibility
    # All candidates ingested into the DB
    candidates = models.ManyToManyField(
        FRBGalaxy, blank=True, 
        related_name='frb_candidates')

    # Redshift, derived from host
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)

    # FRB Tags
    frb_tags = models.ManyToManyField(FRBTag, blank=True)

    slug = AutoSlugField(null=True, default=None, unique=True, populate_from='name')

    def CoordString(self):
        return GetSexigesimalString(self.ra, self.dec)

    def RADecimalString(self):
        return '%.7f'%(self.ra)

    def DecDecimalString(self):
        return '%.7f'%(self.dec)

    def Separation(self):
        host = FRBGalaxy.objects.get(pk=self.host_id)
        return '%.2f'%getSeparation(self.ra,self.dec,host.ra,host.dec)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

    def get_Path_values(self):
        path_values, galaxies = [], []
        if Path.objects.filter(transient_name=self.name).count() > 0:
            for p in Path.objects.filter(transient_name=self.name):
                path_values.append(p.P_Ox)
                galaxies.append(FRBGalaxy.objects.get(name=p.galaxy_name))
        return path_values, galaxies

    @property
    def best_Path_galaxy(self):
        path_values, galaxies = self.get_Path_values()
        if len(galaxies) > 0:
            imax = np.argmax(path_values)
            return galaxies[imax]
        else:
            return None

auditlog.register(FRBTransient)

@receiver(models.signals.post_save, sender=FRBTransient)
def execute_after_save(sender, instance, created, *args, **kwargs):

    if created:
        # CHIME FRB
        #from IPython import embed; embed(header="chime_tags_test.py: Transient post_save")
        if instance.context_class.name == 'FRB' and instance.frb_survey.name == 'CHIME':
            tags = chime_tags.set_from_instance(instance)
            frb_tags = [ftag.name for ftag in FRBTag.objects.all()]
            for tag_name in tags:
                # Add the tag if it doesn't exist
                if tag_name not in frb_tags:
                    new_tag = FRBTag(name=tag_name, 
                                     created_by_id=instance.created_by_id,
                                     modified_by_id=instance.modified_by_id)
                    new_tag.save()
                # Record
                frb_tag = FRBTag.objects.get(name=tag_name)
                instance.frb_tags.add(frb_tag)
                print(f"Added FRB tag: {tag_name}")
            
        instance.save()