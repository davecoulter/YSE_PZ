from .models import *

def get_recent_phot_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    for p in photometry:
            photdata = TransientPhotData.objects.filter(photometry=p.id).order_by('-obs_date')
            
    return(photdata[0])

def get_first_phot_for_transient(transient_id=None):

    transient = Transient.objects.filter(id=transient_id)
    photometry = TransientPhotometry.objects.filter(transient=transient_id)

    for p in photometry:
            photdata = TransientPhotData.objects.filter(photometry=p.id).order_by('-obs_date')[::-1]
            
    return(photdata[0])
