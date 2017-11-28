#!/usr/bin/env python
# D. Jones - 11/27/17
from __future__ import print_function
import sys
import os
from astropy.io import fits
from astropy import wcs
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.coordinates import ICRS, Galactic, FK4, FK5
from astropy.stats import sigma_clipped_stats
import numpy as np
from photutils import CircularAperture,aperture_photometry
import pylab as plt

class finder():
    def __init__(self):
        pass
        
    def add_options(self, parser=None, usage=None, config=None):
        import optparse
        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_option('--clobber', default=False, action="store_true",
                          help='clobber output file')
        parser.add_option('--finderSizeArcmin', default=4, type="float",
                              help='size of finder chart box in arcmin (default=%default)')
        parser.add_option('--finderMaxSizeArcmin', default=5, type="float",
                              help='max size of finder chart box in arcmin, used if offset stars cannot be found (default=%default)')
        parser.add_option('--maxOffsetStarMag', default=19, type="float",
                          help='maximum magnitude of offset star (default=%default)')
        parser.add_option('--numOffsetStar', default=3, type="int",
                          help='max number of offset stars (default=%default)')
        parser.add_option('--finderFilt', default='r', type="string",
                          help='image filter for finder chart (default=%default)')
        parser.add_option('-o','--outputFinderFileName', default=None, type="string",
                          help='output filename for finder chart (default=%default)')
        parser.add_option('-f','--outputOffsetFileName', default=None, type="string",
                          help='output filename for finder chart (default=%default)')
        parser.add_option('-s','--snid', default=None, type="string",
                          help='Object name - optional (default=%default)')
        parser.add_option('-r','--ra', default=None, type="string",
                          help='RA of target (default=%default)')
        parser.add_option('-d','--dec', default=None, type="string",
                          help='Dec of target (default=%default)')

        return(parser)
            
    def mkChart(self,ra,dec,outfile):

        if ':' in ra and ':' in dec:
            sc = SkyCoord("%s %s"%(ra,dec),FK5,unit=(u.hourangle,u.deg))
            self.options.ra = sc.ra.deg
            self.options.dec = sc.dec.deg
            ra,dec = sc.ra.deg,sc.dec.deg
        else:
            ra,dec = float(ra),float(dec)
            self.options.ra = float(ra); self.options.dec = float(dec)
            
        finderim = panstamps_lite(ra,dec,options.finderFilt,options.finderSizeArcmin,outfile)
        if not finderim:
            finderim = getDSSImage(ra,dec,options.finderFilt,options.finderSizeArcmin,outfile)
            if not finderim: raise RuntimeError('Error : problem retrieving FITS image of field!')
            
        xpos,ypos,ra,dec,mag,raoff,decoff = self.getOffsetStarsWrap(finderim)

        self.mkPlot(finderim,xpos,ypos,ra,dec,mag,raoff,decoff,outfile)
        os.system('rm %s'%finderim)
        return()
        
    def mkPlot(self,finderim,xpos,ypos,ra,dec,mag,raoff,decoff,outfile):
        ax = plt.axes([0.2,0.3,0.6,0.6])
        ax.set_xticks([])
        ax.set_yticks([])
        
        imdata = fits.getdata(finderim)
        imshape = np.shape(imdata)
        from matplotlib.colors import LogNorm
        plt.imshow(imdata,cmap='gray_r',norm=LogNorm(vmin=self.skystd))

        if self.options.outputOffsetFileName:
            fout = open(self.options.outputOffsetFileName,'w')
            print('# ID RA Dec RA_off Dec_off Mag',file=fout)
        
        colors = ['C0','C1','C2','C3','C4','C5']
        ybase = -0.15; count = 0
        for x,y,r,d,m,ro,do,i,clr in zip(xpos,ypos,ra,dec,mag,raoff,decoff,range(1,len(xpos)+1),colors):
            ax.plot(x,y,'+',ms=30,color=clr)
            ax.text(x-80,y+100,i,fontsize=15,color=clr,bbox={'alpha':0.3,'edgecolor':'1.0','facecolor':'1.0'})

            sc = SkyCoord(r,d,unit=u.deg)
            ax.text(0.5,ybase-count*0.15,r"""%i: $\alpha$=%02i:%02i:%02.3f $\delta$=%02i:%02i:%02.3f mag=%.3f
            RA (to targ): %.3f E, Dec (to targ): %.3f N"""%(i,sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2],
                                                            sc.dec.dms[0],np.abs(sc.dec.dms[1]),
                                                            np.abs(sc.dec.dms[2]),m,ro.arcsec,do.arcsec),
                    fontsize=10,ha='center',transform=ax.transAxes,bbox={'alpha':1.0,'edgecolor':'1.0','facecolor':'1.0'})
            if self.options.outputOffsetFileName:
                print("%s_S%i %02i:%02i:%02.3f %02i:%02i:%02.3f %.3f %.3f %.3f"%(self.options.snid,
                                                                                 i,sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2],
                                                                                 sc.dec.dms[0],np.abs(sc.dec.dms[1]),
                                                                                 np.abs(sc.dec.dms[2]),ro.arcsec,do.arcsec,m),
                      file=fout)
            count += 1
        if self.options.outputOffsetFileName: fout.close()
        ax.plot(imshape[1]/2.,imshape[0]/2.,'+',ms=100,color='r')

        sc = SkyCoord(self.options.ra,self.options.dec,unit=u.deg)
        ax.set_title(r'ID: %s, $\alpha$ = %02i:%02i:%02.3f $\delta$ = %02i:%02i:%02.3f'%(
            self.options.snid,sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2],
            sc.dec.dms[0],np.abs(sc.dec.dms[1]),np.abs(sc.dec.dms[2])))
        plt.savefig(outfile)
        return()

    def getOffsetStarsWrap(self,finderim,PS1=True):
        xpos,ypos,ralist,declist,mag,raofflist,decofflist = \
            self.getOffsetStars(finderim,PS1=PS1,roundlo=-0.1,roundhi=0.1)
        if xpos is None:
            print('getOffsetStars failed!  Relaxing roundness limit and trying again')
            xpos,ypos,ralist,declist,mag,raofflist,decofflist = \
                self.getOffsetStars(finderim,PS1=PS1,roundlo=-1.0,roundhi=1.0)
            if xpos is None:
                raise RuntimeError('Error : no offset stars found!')
        return(xpos,ypos,ralist,declist,mag,raofflist,decofflist)
        
    def getOffsetStars(self,finderim,PS1=True,roundlo=-1.0,roundhi=1.0):

        imdata = fits.getdata(finderim)
        hdr = fits.getheader(finderim)
        ImWCS = wcs.WCS(hdr)
        
        # use detection/findstars from photutils to get stars
        from photutils import DAOStarFinder
        mean, median, std = sigma_clipped_stats(imdata, sigma=3.0, iters=5)
        self.skystd = std
        daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std, roundlo=roundlo, roundhi=roundhi)
        sources = daofind(imdata - median)

        positions = []
        for x,y in zip(sources['xcentroid'],sources['ycentroid']):
            positions += [(x,y)]
        
        ap = CircularAperture(positions,
                              r=10)
        skysubim = imdata-median
        #err = calc_total_error(skysubim, std, 1.0)
        phot_table = aperture_photometry(skysubim, ap)#, error=err)
        
        # check mags with aperture photometry
        if PS1:
            zpt = 25+2.5*np.log10(hdr['EXPTIME'])
        else:
            zpt = 28.0 + np.log10 (hdr['EXPOSURE']/60.) * 2.5

        mag = -2.5*np.log10(phot_table['aperture_sum']) + zpt
        imshape = np.shape(imdata)
        iGood = np.where((mag < self.options.maxOffsetStarMag) & (sources['xcentroid'] > 10) &
                         (sources['xcentroid'] < imshape[1]-10) & (sources['ycentroid'] > 10) &
                         (sources['ycentroid'] < imshape[0]-10))[0]

        if not len(iGood):
            print('Error : no good offset stars found')
            return(None,None,None,None,None,None,None)
        iBright = iGood[np.argsort(mag[iGood])]
        xpos,ypos = sources['xcentroid'][iBright][0:self.options.numOffsetStar],\
                    sources['ycentroid'][iBright][0:self.options.numOffsetStar]
        mag = mag[iBright][0:self.options.numOffsetStar]
        
        # get ra, dec offsets
        objcoord = SkyCoord(self.options.ra,self.options.dec,unit=u.deg)
        ralist,declist,raofflist,decofflist,maglist = [],[],[],[],[]
        for x,y in zip(xpos,ypos):
            ra,dec = ImWCS.wcs_pix2world([(x,y)],0)[0]
            ralist += [ra]; declist += [dec]
            offcoord = SkyCoord(ra,dec,unit=u.deg)
            dra, ddec = offcoord.spherical_offsets_to(objcoord)
            raofflist += [dra.to(u.arcsec)]
            decofflist += [ddec.to(u.arcsec)]

        return(xpos,ypos,ralist,declist,mag,raofflist,decofflist)

def panstamps_lite(ra,dec,filt,size,outfile):
    import requests
    import wget
    import time
    import re
    
    pos = """%(ra)s %(dec)s""" % locals()


    try:
        response = requests.get(
            url="http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts",
            params={
                "pos": pos,
                "filter": filt,
                "filetypes": "stack",
                "size": size*60*4,
                "output_size": size*60*4,
                "verbose": "0",
                "autoscale": "99.500000",
                "catlist": "",
            },
        )
    except requests.exceptions.RequestException:
        print('HTTP Request failed')
        
    reFitscutouts = re.compile(
            r"""<th>(?P<imagetype>\w+)\s+(?P<skycellid>\d+.\d+)\s+(?P<ffilter>[\w\\]+)(\s+(?P<mjd>\d+\.\d+))?<br.*?href="(http:)?//plpsipp1v.*?Display</a>.*?Fits cutout" href="(?P<fiturl>(http:)?//plpsipp1v.*?\.fits)".*?</th>""", re.I)

    if sys.version_info[0] < 3:
        thisIter = reFitscutouts.finditer(response.content)
    else:
        thisIter = reFitscutouts.finditer(response.content.decode('utf-8'))

    stackFitsUrls = []
    for item in thisIter:
        imagetype = item.group("imagetype")
        skycellid = item.group("skycellid")
        ffilter = item.group("ffilter")
        fiturl = 'http://plpsipp1v.stsci.edu%s'%item.group("fiturl")
        if fiturl[0:5] != "http:":
            fiturl = "http:" + fiturl
            mjd = item.group("mjd")
        stackFitsUrls.append(fiturl)

    for s in stackFitsUrls:
        s = s.replace('plpsipp1v.stsci.edu//','')
        if not os.path.dirname(outfile):
            outdlfile = '%.7f_%.7f_%s.PS1.fits'%(ra,dec,time.time())
        else:
            outdlfile = '%s/%.7f_%.7f_%s.PS1.fits'%(os.path.dirname(outfile),ra,dec,time.time())
        dlfile = wget.download(s,out=outdlfile)
        break

    if os.path.exists(dlfile):
        return(dlfile)
    else: return(None)

def getDSSImage(ra,dec,filt,size,outfile):
    QueryURL="http://archive.eso.org/dss/dss/image?ra=%s&dec=%s&x=4&y=4&Sky-Survey=2r&mime-type=download-fits"%(ra,dec)
    outdlfile = '%s/%.7f_%.7f_%s.DSS.fits'%(os.path.dirname(outfile),ra,dec,time.time())
    dlfile = wget.download(fitsurl,out=outdlfile)

    if os.path.exists(dlfile):
        return(dlfile)
    else: return(None)
    
if __name__ == "__main__":

    import os
    import optparse

    useagestring='mkFinderChart.py [options]'
    find = finder()
    parser = find.add_options(usage=useagestring)
    options,  args = parser.parse_args()
    find.options = options
    
    find.mkChart(options.ra,options.dec,options.outputFinderFileName)
