#!/usr/bin/env python

from YSE_App.common import mast_query,chandra_query,spitzer_query
from YSE_App.models import *

def main():

    transients = Transient.objects.filter(has_hst__isnull=True).filter(name__startswith='2019').filter(TNS_spec_class__isnull=False)
    
    for t in transients:
        try:
            if t.has_hst is None:
                hst=mast_query.hstImages(t.ra,t.dec,'Object')
                hst.getObstable()
                if hst.Nimages > 0:
                    t.has_hst = True
                else:
                    t.has_hst = False
                t.save()
        except: pass

        try:
            if t.has_jwst is None:
                jwst = mast_query.jwstImages(t.ra, t.dec, 'Object')
                jwst.getObstable()
                if jwst.Nimages > 0:
                    t.has_jwst = True
                else:
                    t.has_jwst = False
                t.save()
        except: pass

        try:
            if t.has_chandra is None:
                chr=chandra_query.chandraImages(t.ra,t.dec,'Object')
                chr.search_chandra_database()
                if chr.n_obsid > 0:
                    t.has_chandra = True
                else:
                    t.has_chandra = False
                t.save()
        except: pass

        try:
            if t.has_spitzer is None:
                if spitzer_query.get_bool_from_coord(t.ra,t.dec):
                    t.has_spitzer = True
                else:
                    t.has_spitzer = False
                t.save()
        except: pass

if __name__ == "__main__":
    main()
