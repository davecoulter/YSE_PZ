from django.db import models

from YSE_App.models.base import BaseModel
from YSE_App import models as yse_models

class FRBGalaxy(BaseModel):
    ### Entity relationships ###
    # Optional
    #morphology = models.ForeignKey(HostMorphology, null=True, blank=True, on_delete=models.SET_NULL)

    ### Properties ###
    # Required
    ra = models.FloatField()
    dec = models.FloatField()
    # J2000 name
    name = models.CharField(max_length=64, unique=True)
    # Source of the host, e.g. PS1
    source = models.CharField(max_length=64)

    # Optional
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)

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
        """ Return the filter and magnitude for the host

        First preference is given to 'r/R' band
        Then, anything goes..
        """
        pdict = self.phot_dict
        if len(pdict) == 0:
            return 'None'
        # Take first 'r/R'-band if we have it
        for inst_key in pdict.keys():
            for ifilter in pdict[inst_key].keys():
                if ifilter[-1] in ['r', 'R']:
                    return ifilter, '%.2f'%(pdict[inst_key][ifilter])

        # Take the first one we have
        inst_key = list(pdict.keys())[0]
        ifilter = pdict[inst_key].keys()[0]
        return ifilter, '%.2f'%(pdict[inst_key][ifilter])

    def POxString(self):
        """ Return the P_Ox for the host
        """
        if self.P_Ox is None:
            return 'None'
        else:
            return '%.2f'%(self.P_Ox)

    @property
    def P_Ox(self):
        """ Grab the P_Ox from the PATH table, if it exists

        Returns:
            float: P_Ox or None

        """
        path = Path.objects.filter(galaxy_name=self.name)
        if len(path) == 1:
            return path[0].P_Ox
        else:
            return None

    @property
    def phot_dict(self):
        """ Grab the photometry for the host, if it exists

        Returns:
            dict: photometry dictionary or None

        """
        pdict = {}
        for phot in yse_models.HostPhotometry.objects.filter(host=self):
            top_key = f'{phot.instrument}'
            pdict[top_key] = {}
            for phot_data in yse_models.HostPhotData.objects.filter(photometry=phot):
                pdict[top_key][phot_data.band.name] = phot_data.mag
        return pdict

class Path(BaseModel):

    ### Properties ###
    # Required
    P_Ox = models.FloatField()
    transient_name = models.CharField(max_length=64)
    # Candidate name
    galaxy_name = models.CharField(max_length=64)

    def __str__(self):
        return f'Path: {self.transient_name}, {self.galaxy_name}, {self.P_Ox}'   

    @property
    def galaxy(self):
        return FRBGalaxy.objects.get(name=self.galaxy_name)