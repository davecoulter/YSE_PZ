from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(TransientHostRank)
admin.site.register(ObservationGroup)
admin.site.register(SEDType)
admin.site.register(HostMorphology)
admin.site.register(Phase)
admin.site.register(TransientClass)
admin.site.register(HostClass)
admin.site.register(Observatory)
admin.site.register(Telescope)
admin.site.register(ObservingNightDates)
admin.site.register(Instrument)
admin.site.register(PhotometricBand)
admin.site.register(Image)
admin.site.register(Transient)
admin.site.register(Host)
admin.site.register(Spectrum)
admin.site.register(Photometry)
admin.site.register(FollowUp)
admin.site.register(InformationSource)
admin.site.register(WebResource)
admin.site.register(Log)
admin.site.register(AlternateTransientNames)
admin.site.register(SpecData)
admin.site.register(HostSED)
