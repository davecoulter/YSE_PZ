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

# FRB items
from ne2001 import density

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
    # Error in RA in deg (NOT USED)
    ra_err = models.FloatField(null=True, blank=True)
    # Error in Dec in deg (NOT USED)
    dec_err = models.FloatField(null=True, blank=True)
    # Error in ellipse in deg
    a_err = models.FloatField(null=True, blank=True)
    # Error in ellipse in deg
    b_err = models.FloatField(null=True, blank=True)
    # PA of the ellipse
    theta = models.FloatField(null=True, blank=True)
    # Localization file
    localization_file = models.CharField(max_length=64, null=True, blank=True)
    # Event ID
    event_id = models.IntegerField(null=True, blank=True, unique=True)
    # Bright star nearby?
    bright_star = models.BooleanField(default=False, blank=True)

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

    # Galactic DM
    DM_ISM = models.FloatField(null=True, blank=True)

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

    # Localization
    def aerr_DecimalString(self):
        return '%.1f'%(self.a_err*3600) # arcsec

    def berr_DecimalString(self):
        return '%.1f'%(self.b_err*3600) # arcsec

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

    def HostMagString(self):
        if self.host:
            return self.host.MagString()
        else:
            return ''

    def HostzString(self):
        """ Redshift """
        if self.host:
            return self.host.zString()
        else:
            return ''

    def HostzSource(self):
        """ Redshift source """
        if self.host:
            return self.host.zSource()
        else:
            return ''

    def FRBFollowUpResourcesString(self):
        """ Generate a comma-separated list of the FRBFollowUpResources for this transient"""
        from YSE_App.models.frbfollowup_models import FRBFollowUpRequest, FRBFollowUpObservation
        fu_req = FRBFollowUpRequest.objects.filter(transient=self)
        fu_obs = FRBFollowUpObservation.objects.filter(transient=self)
        fu_names = []
        fu_names += [item.ResourceName() for item in fu_req]
        fu_names += [item.ResourceName() for item in fu_obs]

        if len(fu_names) == 0:
            followup_names = 'None'
        else:
            followup_names = ','.join(np.unique(fu_names))
        return followup_names

    def Separation(self):
        host = FRBGalaxy.objects.get(pk=self.host_id)
        return '%.2f'%getSeparation(self.ra,self.dec,host.ra,host.dec)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name


    def calc_DM_ISM(self):
        """ Calcualte DM_ISM from NE2001

        Returns:
            float: DM_ISM in pc/cm^3
        """

        coord = SkyCoord(ra=self.ra, dec=self.dec,
                        unit='deg')
        gcoord = coord.transform_to('galactic')
        l, b = gcoord.l.value, gcoord.b.value
        
        ne = density.ElectronDensity()#**PARAMS)
        ismDM = ne.DM(l, b, 100.)

        return ismDM.value


    def get_Path_values(self):
        """ Grab lists of the PATH values and candidate galaxies

        Returns:
            tuple: (list, list, list) of PATH values and candidate galaxies
                (FRBGalaxy objects) and PATH objects (Path)
                path_values -- PATH P(O|x) values
                galaxies -- FRBGalaxy objects
                path_objs -- Path objects
        """
        path_values, galaxies, path_objs = [], [], []
        # Loop on the filtered table
        if Path.objects.filter(transient=self).count() > 0:
            for p in Path.objects.filter(transient=self):
                path_values.append(p.P_Ox)
                galaxies.append(p.galaxy)
                path_objs.append(p)
        return path_values, galaxies, path_objs

    @property
    def sum_top_two_PATH(self):
        """ Add the top two PATH P(O|x) values for the transient 

        Returns:
            float: 0. if there is no PATH analysis

        """
        path_values, _, _ = self.get_Path_values()
        if len(path_values) == 0:
            return 0.
        elif len(path_values) == 1:
            return path_values[0]
        else:
            path_values = np.array(path_values)
            argsrt = np.argsort(path_values)
            path_values = path_values[argsrt]
            return np.sum(path_values[-2:])

    @property
    def mag_top_two_PATH(self):
        """ PATH mag for the top two PATH P(O|x) values for the transient 

        If there are more than 1, take the top two and 
        return the *brightest* magnitude

        Returns:
            float: 99. if there is no PATH analysis

        """
        path_values, galaxies, path_objs = self.get_Path_values()
        if len(path_values) == 0:
            return 99.
        elif len(path_values) == 1:
            return path_objs[0].galaxy_mag
        else:
            path_values = np.array(path_values)
            argsrt = np.argsort(path_values)
            mags = np.array([obj.galaxy_mag for obj in path_objs])
            # Sort em
            mags = mags[argsrt]
            return np.min(mags)

    @property
    def best_Path_galaxy(self):
        """ Return the galaxy with the highest P(O|x) value

        Returns:
            FRBGalaxy: Galaxy with the highest P(O|x) value or None
        """
        path_values, galaxies, _ = self.get_Path_values()
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
        instance.mw_ebv = irsa_dust.IrsaDust.get_query_table(c)['ext SandF mean'][0]

        # DM ISM
        instance.DM_ISM = instance.calc_DM_ISM()

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

    band = models.ForeignKey(PhotometricBand, blank=True, null=True,
        on_delete=models.SET_NULL)

    # Optional
    # Filter used -- useful for FRB status
    #  Added as optional but should always be present

    # Vetted? If true, a human has confirmed the results are valid
    vetted = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f'Path: {self.transient.name}, {self.galaxy.name}, {self.P_Ox}, {self.vetted}'

    @property
    def galaxy_mag(self):
        from YSE_App.models import GalaxyPhotometry
        from YSE_App.models import GalaxyPhotData

        # Grab the first matching
        gp = GalaxyPhotometry.objects.filter(
            galaxy=self.galaxy, instrument=self.band.instrument)[0]

        # Grab the phot data
        gpd = GalaxyPhotData.objects.get(photometry=gp, band=self.band)

        # Return
        return gpd.mag