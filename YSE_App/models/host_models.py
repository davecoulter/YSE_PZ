from django.db import models
from YSE_App.models.base import *
from YSE_App.models.enum_models import *
from YSE_App.models.photometric_band_models import *
from YSE_App.common.utilities import *
from YSE_App import models as yse_models

class HostSED(BaseModel):
    ### Entity relationships ###
    # Optional
    sed_type = models.ForeignKey(SEDType, null=True, blank=True, on_delete=models.SET_NULL)

    ### Properties ###
    # Optional
    metalicity = models.FloatField(null=True, blank=True)
    metalicity_err = models.FloatField(null=True, blank=True)
    log_SFR = models.FloatField(null=True, blank=True)
    log_SFR_err = models.FloatField(null=True, blank=True)
    log_sSFR = models.FloatField(null=True, blank=True)
    log_sSFR_err = models.FloatField(null=True, blank=True)
    log_mass = models.FloatField(null=True, blank=True)
    log_mass_err = models.FloatField(null=True, blank=True)
    ebv = models.FloatField(null=True, blank=True)
    ebv_err = models.FloatField(null=True, blank=True)
    log_age = models.FloatField(null=True, blank=True)
    log_age_err = models.FloatField(null=True, blank=True)
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)
    fit_chi2 = models.FloatField(null=True, blank=True)
    fit_n = models.IntegerField(null=True, blank=True)
    fit_plot_file = models.TextField(null=True, blank=True)

    def __str__(self):
        name_str = 'HostSED: '
        try:
            name_str += self.sed_type.name
        except NameError:
            name_str += 'Untyped'
        return name_str

    def natural_key(self):
        return self.__str__

class Host(BaseModel):
    ### Entity relationships ###
    # Optional
    host_morphology = models.ForeignKey(HostMorphology, null=True, blank=True, on_delete=models.SET_NULL)
    host_sed = models.ForeignKey(HostSED, null=True, blank=True, on_delete=models.SET_NULL)
    band_sextract = models.ForeignKey(PhotometricBand, null=True, blank=True, on_delete=models.SET_NULL)
    best_spec = models.ForeignKey('HostSpectrum', related_name='+', null=True, blank=True, on_delete=models.SET_NULL)

    ### Properties ###
    # Required
    ra = models.FloatField()
    dec = models.FloatField()
    # J2000 name
    name = models.CharField(max_length=64, unique=True)

    # Optional
    redshift = models.FloatField(null=True, blank=True)
    redshift_err = models.FloatField(null=True, blank=True)
    r_a = models.FloatField(null=True, blank=True)
    r_b = models.FloatField(null=True, blank=True)
    theta = models.FloatField(null=True, blank=True)
    eff_offset = models.FloatField(null=True, blank=True)
    photo_z = models.FloatField(null=True, blank=True)
    photo_z_err = models.FloatField(null=True, blank=True)
    photo_z_internal = models.FloatField(null=True, blank=True)
    photo_z_err_internal = models.FloatField(null=True, blank=True)
    photo_z_PSCNN = models.FloatField(null=True, blank=True)
    photo_z_err_PSCNN = models.FloatField(null=True, blank=True)
    photo_z_source = models.CharField(max_length=64, null=True, blank=True)
    transient_host_rank = models.IntegerField(null=True, blank=True)
    panstarrs_objid = models.BigIntegerField(null=True, blank=True)

    # Angular size (in arcsec; typically half-light radius)
    ang_size = models.FloatField(null=True, blank=True)

    def HostString(self):
        ra_str, dec_str = GetSexigesimalString(self.ra, self.dec)

        if self.name:
            return "Host: %s; (%s, %s)" % (self.name, ra_str, dec_str)
        else:
            return "Host: (%s, %s)" % (ra_str, dec_str)

    def NameString(self):
        ra_str, dec_str = GetSexigesimalString(self.ra, self.dec)
        return f'J{ra_str}{dec_str}'

    def CoordString(self):
        return GetSexigesimalString(self.ra, self.dec)

    def RADecimalString(self):
        return '%.7f'%(self.ra)

    def DecDecimalString(self):
        return '%.7f'%(self.dec)

    def __str__(self):
        return self.HostString()

    def natural_key(self):
        return self.HostString()

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
        path = Path.objects.get(host_name=self.name)
        if len(path) == 1:
            return path[0].P_Ox
        else:
            return None

    @property
    def phot_dict(self):
        pdict = {}
        for phot in yse_models.HostPhotometry.objects.filter(host=self):
            top_key = f'{phot.instrument}'
            pdict[top_key] = {}
            for phot_data in yse_models.HostPhotData.objects.filter(photometry=phot):
                pdict[top_key][phot_data.band.name] = phot_data.mag
        return pdict

# PATH values;  distinct from Host because it is an FRB/Host coupling
class Path(BaseModel):

    ### Properties ###
    # Required
    P_Ox = models.FloatField()
    transient_name = models.CharField(max_length=64)
    # Candidate name
    host_name = models.CharField(max_length=64)

    def __str__(self):
        return f'Path: {self.transient_name}, {self.host_name}, {self.P_Ox}'   

    @property
    def galaxy(self):
        return Host.objects.get(name=self.host_name)