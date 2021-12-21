#!/usr/bin/env python
# D. Jones - 12/4/17

from .models import *
from .forms import *

def get_all_phot(transient_id=None):
    
    transient = Transient.objects.filter(id=transient_id)
    photometry = Photometry.objects.filter(transient=transient_id)
    photdata = TransientPhotData.objects.filter(photometry=photometry.photometry_id)

    return(photdata)
