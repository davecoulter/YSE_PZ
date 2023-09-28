from autoslug import AutoSlugField
from auditlog.registry import auditlog

from django.db import models
from django.dispatch import receiver

import numpy as np

from YSE_App.models.base import BaseModel
from YSE_App.models import *  # Avoids circular import
from YSE_App.models.enum_models import *
from YSE_App.models.tag_models import *
from YSE_App.chime import tags as chime_tags
from YSE_App.common.utilities import GetSexigesimalString, getSeparation
from YSE_App.models.frbgalaxy_models import FRBGalaxy

from YSE_App import frb_tags
from YSE_App import frb_status
from YSE_App import frb_utils

from astropy.coordinates import SkyCoord
from astroquery import irsa_dust

class FRBTransient(BaseModel):
    """ FRBTransient model

    Based on Transient, this is the primary model for 
    all the FRBs in FFFF-PZ
    """

    ### Entity relationships ###
    # Required

    # Describes at what stage of follow-up an FRB is at
    status = models.ForeignKey(TransientStatus, models.SET(get_sentinel_transientstatus))
    # Provides the name of the FRB survey from which it originated
    frb_survey = models.ForeignKey(FRBSurvey, on_delete=models.CASCADE)

    ### Properties ###
    # Required
    # TNS name;  must be unique
    name = models.CharField(max_length=64, unique=True)
    # RA in deg
    ra = models.FloatField()
    # Dec in deg
    dec = models.FloatField()
    # Dispersion Measure
    DM = models.FloatField()

    # Optional
    # Error in RA in deg
    ra_err = models.FloatField(null=True, blank=True)
    # Error in Dec in deg
    dec_err = models.FloatField(null=True, blank=True)
    # Error in ellipse in deg
    a_err = models.FloatField(null=True, blank=True)
    # Error in ellipse in deg
    b_err = models.FloatField(null=True, blank=True)
    # PA of the ellipse
    theta = models.FloatField(null=True, blank=True)
    # Localization file
    localization_file = models.CharField(max_length=64, null=True, blank=True)

    # Repeater?
    repeater = models.BooleanField(default=False, blank=True)
    # Rotation measure
    RM = models.FloatField(null=True, blank=True)
    # S.N
    s2n = models.FloatField(null=True, blank=True)

    # Host -- defined as the Highest P(O|x) candidate
    #   set in YSE_App.galaxies.path.ingest_path_results()
    host = models.ForeignKey(
        FRBGalaxy, null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='frb') # Needs to be here for backwards compatibility

    # All candidates ingested into the DB during PATH analysis
    candidates = models.ManyToManyField(
        FRBGalaxy, blank=True, 
        related_name='frb_candidates')

    # Path Unseen probability
    P_Ux = models.FloatField(null=True, blank=True)

    # Galactic E(B-V) -- taken from Irsa at creation
    mw_ebv = models.FloatField(null=True, blank=True)

    # Redshift, derived from host
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)

    # FRB Tags
    frb_tags = models.ManyToManyField(FRBTag, blank=True)

    slug = AutoSlugField(null=True, default=None, unique=True, populate_from='name')

    # The String methods are for viewing
    def CoordString(self):
        return GetSexigesimalString(self.ra, self.dec)

    def RADecimalString(self):
        return '%.7f'%(self.ra)

    def DecDecimalString(self):
        return '%.7f'%(self.dec)

    def DMString(self):
        return '%.1f'%(self.DM)

    def StatusString(self):
        return self.status.name

    def FRBSurveyString(self):
        return self.frb_survey.name

    def FRBTagsString(self):
        tags = [tag.name for tag in self.frb_tags.all()]
        if len(tags) > 0:
            return ','.join(tags)
        else:
            return ''

    def HostString(self):
        if self.host:
            return self.host.name
        else:
            return ''

    def HostPOxString(self):
        if self.host:
            return self.host.POxString()
        else:
            return ''

    def FRBSurveyString(self):
        return self.frb_survey.name
    
    def FRBFollowUpResourcesString(self):
        resources = FRBFollowUpResource.objects.filter(transient=self)
        if resources.count() > 0:
            resouce_list = [r.name for r in resources]
            # TODO -- Turn this into URLs
            resouce_names = ','.join(resouce_list)
            return resouce_names
        else:
            return ''

    def Separation(self):
        host = FRBGalaxy.objects.get(pk=self.host_id)
        return '%.2f'%getSeparation(self.ra,self.dec,host.ra,host.dec)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

    def get_Path_values(self):
        """ Grab lists of the PATH values and candidate galaxies

        Returns:
            tuple: (list, list) of PATH values and candidate galaxies
        """
        path_values, galaxies = [], []
        # Loop on the filtered table
        if Path.objects.filter(transient=self).count() > 0:
            for p in Path.objects.filter(transient=self):
                path_values.append(p.P_Ox)
                galaxies.append(p.galaxy)
        return path_values, galaxies

    def sum_top_two_PATH(self):
        path_values, _ = self.get_Path_values()
        if len(path_values) == 0:
            return 0.
        elif len(path_values) == 1:
            return path_values[0]
        else:
            path_values = np.array(path_values)
            argsrt = np.argsort(path_values)
            path_values = path_values[argsrt]
            return np,sum(path_values[-2:])

    @property
    def best_Path_galaxy(self):
        """ Return the galaxy with the highest P(O|x) value

        Returns:
            FRBGalaxy: Galaxy with the highest P(O|x) value or None
        """
        path_values, galaxies = self.get_Path_values()
        if len(galaxies) > 0:
            imax = np.argmax(path_values)
            return galaxies[imax]
        else:
            return None

auditlog.register(FRBTransient)

@receiver(models.signals.post_save, sender=FRBTransient)
def execute_after_save(sender, instance, created, *args, **kwargs):

    # Add a few bits and pieces including tags
    if created:

        # Galactic E(B-V) -- Needs to come before tagging
        c = SkyCoord(ra=instance.ra, dec=instance.dec, unit='deg')
        # TODO 
        #  PUT THIS BACK!!
        #instance.mw_ebv = irsa_dust.IrsaDust.get_query_table(c)['ext SandF mean'][0]
        instance.mw_ebv = 0.

        # CHIME FRB items
        tags = frb_tags.find_tags(instance)
        if len(tags) > 0:

            # Add tags
            for tag_name in tags:
                # Add the tag if it doesn't exist
                frb_tag = frb_utils.add_or_grab_obj(
                    FRBTag, dict(name=tag_name), {}, instance.created_by)
                # Record
                instance.frb_tags.add(frb_tag)
            
            ## Set status to PublicPATH unless we are only CHIME-Unknown
            #tag_names = [tag.name for tag in instance.frb_tags.all()]
            #if len(tag_names) == 1 and tag_names[0] == 'CHIME-Unknown':
            #    pass
            #else:
            #    instance.status = TransientStatus.objects.get(name='PublicPATH')

        # Set status
        frb_status.set_status(instance)

        # Save
        instance.save()

class Path(BaseModel):
    """ django model for PATH table

    Each PATH posterior value P(O|x) is for an FRB-Galaxy pairing
    which are required properties

    Requires an FRBTransient and FRBGalaxy pairing

    """

    ### Properties ###
    # Required 

    # Transient 
    transient = models.ForeignKey(FRBTransient, on_delete=models.CASCADE)
    # PATH P(O|x) value
    P_Ox = models.FloatField()
    # Candidate name
    galaxy = models.ForeignKey(FRBGalaxy, on_delete=models.CASCADE)

    # Optional

    # Vetted? If true, a human has confirmed the results are valid
    vetted = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f'Path: {self.transient.name}, {self.galaxy.name}, {self.P_Ox}, {self.vetted}'   
