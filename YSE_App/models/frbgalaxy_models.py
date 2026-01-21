from django.db import models

from YSE_App.models.base import BaseModel
from YSE_App import models as yse_models
#from YSE_App.models.frbtransient_models import FRBTransient
from YSE_App.common.utilities import GetSexigesimalString 

class FRBGalaxy(BaseModel):
    """django model for FRB host galaxy candidates
    (and the assigned host too)

    Primary model of FFFF-PZ

    These will almost always (maybe always) be candidates
    for FRB hosts

    """
    ### Entity relationships ###
    # Optional
    #morphology = models.ForeignKey(HostMorphology, null=True, blank=True, on_delete=models.SET_NULL)

    ### Properties ###
    # Required
    ra = models.FloatField()
    dec = models.FloatField()
    # J2000 name with format specified by YSE_App.common.utilities.getGalaxyname()
    name = models.CharField(max_length=64, unique=True)
    # Source of the galaxy, e.g. PS1
    source = models.CharField(max_length=64)

    # Optional

    # Redshift
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)
    # Qualty of the redshift
    #   1: 100% secure
    redshift_quality = models.IntegerField(null=True, blank=True)
    # Source of the redshift
    #   private,SDSS,DESI, etc.
    redshift_source = models.CharField(max_length=64, blank=True)

    photoz = models.FloatField(null=True, blank=True)
    photoz_err = models.FloatField(null=True, blank=True)
    photoz_source = models.CharField(max_length=64, blank=True)


    # Angular size (in arcsec; typically half-light radius)
    ang_size = models.FloatField(null=True, blank=True)

    def GalaxyString(self):
        ra_str, dec_str = GetSexigesimalString(self.ra, self.dec)

        if self.name:
            return "Galaxy: %s; (%s, %s)" % (self.name, ra_str, dec_str)
        else:
            return "Galaxy: (%s, %s)" % (ra_str, dec_str)

    def NameString(self):
        ra_str, dec_str = GetSexigesimalString(self.ra, self.dec)
        return f'J{ra_str}{dec_str}'.replace(':', '')

    def CoordString(self):
        return GetSexigesimalString(self.ra, self.dec)

    def RADecimalString(self):
        return '%.7f'%(self.ra)

    def DecDecimalString(self):
        return '%.7f'%(self.dec)

    def __str__(self):
        return self.GalaxyString()

    def natural_key(self):
        return self.GalaxyString()

    def FilterMagString(self):
        """ Return the filter and magnitude for the galaxy (for viewing)

        First preference is given to 'r/R' band
        Then, anything goes..

        Returns:
            str, str: filter and magnitude for the galaxy
        """
        pdict = self.phot_dict
        if len(pdict) == 0:
            return 'None'
        # Take first 'r/R'-band if we have it
        for inst_key in pdict.keys():
            for ifilter in pdict[inst_key].keys():
                if ifilter[-1] in ['r', 'R']:
                    return f'{inst_key}-{ifilter}', '%.2f'%(pdict[inst_key][ifilter])

        # Take the first one we have
        inst_key = list(pdict.keys())[0]
        ifilter = pdict[inst_key].keys()[0]
        return f'{inst_key}-{ifilter}', '%.2f'%(pdict[inst_key][ifilter])

    def POxString(self):
        """ Return the P_Ox for the galaxy as a string (for viewing)
        """
        if self.P_Ox is None:
            return 'None'
        else:
            return '%.2f'%(self.P_Ox)

    def MagString(self):
        """ Return the path_mag for the galaxy as a string (for viewing)
        """
        if self.P_Ox is None:
            return ''
        else:
            return '%.1f'%(self.path_mag)

    def zString(self):
        """ Return the redshift for the galaxy as a string (for viewing)
        """
        if self.redshift is None:
            return 'None'
        else:
            return '%.4f'%(self.redshift)

    def zSource(self):
        """ Return the redshift source for the galaxy as a string (for viewing)
        """
        if self.redshift_source is None:
            return 'None'
        else:
            return self.redshift_source

    def zQualString(self):
        """ Return the redshift quality for the galaxy as a string (for viewing)
        """
        if self.redshift_quality is None:
            return 'None'
        else:
            return f'{self.redshift_quality}'
        
    def photozString(self):
        """ Return the photometric redshift for the galaxy as a string (for viewing)
        """
        if self.photoz is None:
            return 'None'
        else:
            return '%.2f'%(self.photoz)

    

    @property
    def path_mag(self):
        """ Magnitude used for PATH analysis 

        Returns:
            float or None: PATH magnitude or None

        """
        path = yse_models.Path.objects.filter(galaxy=self)
        if len(path) == 1:
            band = path[0].band
            phot = yse_models.GalaxyPhotData.objects.filter(
                photometry__galaxy=self,band=band)
            return phot[0].mag
        else:
            return None

    @property
    def P_Ox(self):
        """ Grab the P_Ox from the PATH table, if it exists

        Returns:
            float: P_Ox or None

        """
        path = yse_models.Path.objects.filter(galaxy=self)
        if len(path) == 1:
            return path[0].P_Ox
        else:
            return None

    @property
    def phot_dict(self):
        """ Grab a dict of photometry for the galaxy, if it exists

        phot[instrument][band] = mag

        Returns:
            dict: photometry dictionary or None

        """
        pdict = {}
        for phot in yse_models.GalaxyPhotometry.objects.filter(galaxy=self):
            top_key = f'{phot.instrument.tel_instr()}'
            pdict[top_key] = {}
            for phot_data in yse_models.GalaxyPhotData.objects.filter(photometry=phot):
                pdict[top_key][phot_data.band.name] = phot_data.mag
        return pdict

