import sys, numpy as np
from astroquery.mast import Observations
from astropy.coordinates import SkyCoord
from astropy.table import Table,unique
from astropy import units as u
from datetime import datetime
from astropy.time import Time

# Uses references to astroquery.mast fields: https://mast.stsci.edu/api/v0/_c_a_o_mfields.html
instrument_defaults = {
        'radius': 1 * u.arcsec,
        'jpg': 'https://hla.stsci.edu/cgi-bin/fitscut.cgi?red={id}'+\
            '&amp;RA={ra}&amp;DEC={dec}&amp;size=256&amp;format=jpg'+\
            '&amp;config=ops&amp;asinh=1&amp;autoscale=90',
        'mask': {'instrument_name': ['WFPC2/WFC','PC/WFC','ACS/WFC','ACS/HRC',
                                     'ACS/SBC','WFC3/UVIS','WFC3/IR'],
                 't_exptime': 40,
                 'obs_collection': ['HST','HLA'],
                 'filters': ['F220W','F250W','F330W','F344N','F435W','F475W',
                      'F550M','F555W','F606W','F625W','F658N','F660N','F660N',
                      'F775W','F814W','F850LP','F892N','F098M','F105W','F110W',
                      'F125W','F126N','F127M','F128N','F130N','F132N','F139M',
                      'F140W','F153M','F160W','F164N','F167N','F200LP','F218W',
                      'F225W','F275W','F280N','F300X','F336W','F343N','F350LP',
                      'F373N','F390M','F390W','F395N','F410M','F438W','F467M',
                      'F469N','F475X','F487N','F502N','F547M','F600LP','F621M',
                      'F625W','F631N','F645N','F656N','F657N','F658N','F665N',
                      'F673N','F680N','F689M','F763M','F845M','F953N','F122M',
                      'F160BW','F185W','F218W','F255W','F300W','F375N','F380W',
                      'F390N','F437N','F439W','F450W','F569W','F588N','F622W',
                      'F631N','F673N','F675W','F702W','F785LP','F791W','F953N',
                      'F1042M','F502N']
                }
}

class hstImages():
    def __init__(self,ra,dec,obj):
        # Transient information/search criteria
        if (':' in str(ra) and ':' in str(dec)):
            self.coord = SkyCoord(ra, dec, unit = (u.hour, u.deg))
        else:
            self.coord = SkyCoord(ra, dec, unit = (u.deg, u.deg))
        self.ra=self.coord.ra.degree
        self.dec=self.coord.dec.degree
        self.obstable = None
        self.object=obj
        self.radius=0.001

        ## Selection criteria
        self.options = instrument_defaults

        self.Nimages = 0
        self.jpglist = []

    def getObstable(self):
        options = self.options
        table=Observations.query_region(self.coord,
            radius=self.options['radius'])

        # HST-specific masks
        filmask = [table['filters'] == good
              for good in options['mask']['filters']]
        filmask = [any(l) for l in list(map(list,zip(*filmask)))]
        expmask = table['t_exptime'] > options['mask']['t_exptime']
        obsmask = [table['obs_collection'] == good
            for good in options['mask']['obs_collection']]
        obsmask = [any(l) for l in list(map(list,zip(*obsmask)))]
        detmask = [table['instrument_name'] == good
            for good in options['mask']['instrument_name']]
        detmask = [any(l) for l in list(map(list,zip(*detmask)))]

        # Construct and apply mask
        mask = [all(l) for l in zip(filmask,expmask,obsmask,detmask)]
        self.obstable = table[mask]

        self.Nimages=0
        if self.obstable:
          if len(self.obstable)>0:

            self.obstable['t_min']=np.around(self.obstable['t_min'], decimals=4)
            self.obstable['t_max']=np.around(self.obstable['t_max'], decimals=4)

            self.obstable.sort('obs_collection')

            self.obstable = unique(self.obstable, keys=['t_min'], keep='last')
            self.obstable = unique(self.obstable, keys=['t_max'], keep='last')

            self.Nimages=len(self.obstable)

    def getJPGurl(self):
        if len(self.obstable) == 0:
            print('There are no HST images!!!')
            return(0)

        url = self.options['jpg']
        for obsid in self.obstable['obs_id']:
            url = self.options['jpg'].format(id=obsid,ra=self.coord.ra.degree,
                dec=self.coord.dec.degree)
            self.jpglist.append(url)

## TEST TEST TEST
if __name__=='__main__':
    startTime = datetime.now()
    hst=hstImages(199.8674542,-13.7236833,'Object')
    hst.getObstable()
    hst.getJPGurl()
    print("I found",hst.Nimages,"HST images of",hst.object,"located at coordinates",hst.ra,hst.dec)
