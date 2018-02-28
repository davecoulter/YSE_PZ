import requests,math,sys
import numpy as np
from astroquery.mast import Observations
from astropy.time import Time
from io import BytesIO
from scipy import misc
from PIL import Image
from datetime import datetime

# Uses references to astroquery.mast fields: https://mast.stsci.edu/api/v0/_c_a_o_mfields.html

class hstImages():
	def __init__(self,ra,dec,obj):
		# Transient information/search criteria
		self.ra=ra
		self.dec=dec
		self.object=obj
		self.radius=0.0001

		## Selection criteria
		self.minexp=160
		self.allowed_detector=['WFPC2/WFC','PC/WFC','ACS/WFC','ACS/HRC','ACS/SBC','WFC3/UVIS','WFC3/IR']
		self.badfilter=['DETECTION']
		self.collection=['HLA','HST']

		# Information pulled from MAST
		self.obstable=None
		self.Nimages=0

		# Storing statistics for each image
		self.filtlist=[]
		self.detlist=[]
		self.jdlist=[]
		self.obsid=[]
		self.jpglist=[]
		self.jpgsize=100

	def getObstable(self):
		self.obstable=Observations.query_region(str(self.ra)+" "+str(self.dec),radius=str(self.radius)+" deg")
		detmasks=[self.obstable['instrument_name'] == name for name in self.allowed_detector]
		filmasks=[self.obstable['filters'] != bad for bad in self.badfilter]
		expmasks=[self.obstable['t_exptime'] >= self.minexp]
		colmasks=[self.obstable['obs_collection'] == coll for coll in self.collection]
		good=[all(l) for l in list(zip(\
			[any(l) for l in list(map(list,zip(*detmasks)))],\
			[any(l) for l in list(map(list,zip(*colmasks)))],\
			[any(l) for l in list(map(list,zip(*expmasks)))],\
			[any(l) for l in list(map(list,zip(*filmasks)))]))]

		self.obstable=self.obstable[good]

		self.Nimages=len(self.obstable)
		self.filtlist=self.obstable['filters']
		self.detlist=self.obstable['instrument_name']
		self.obsid=self.obstable['obs_id']
		self.jdlist=self.obstable['t_min']+2400000.5

	def getJPGurl(self):
		if (self.Nimages == 0):
			print("There are no HST images!!!")
			return(0)

		prefix="https://hla.stsci.edu/cgi-bin/fitscut.cgi?red="
		suffix=";size=256&amp;format=jpg&amp;config=ops&amp;asinh=1&amp;autoscale=90"
		rastring=";RA="+str(self.ra)+"&amp"
		decstring=";DEC="+str(self.dec)+"&amp"
		for obsid in self.obsid:
			idstring=obsid+"&amp"
			url=prefix+idstring+rastring+decstring+suffix
			self.jpglist.append(url)
			#date=Time(jd,format='jd').datetime.strftime("%Y%m%d")


## TEST TEST TEST
if __name__=='__main__':
	startTime = datetime.now()
	if (len(sys.argv) < 3):
		print("Must define RA and DEC in command line!!!")
		sys.exit(1)

	ra=float(sys.argv[1])
	dec=float(sys.argv[2])
	hst=hstImages(ra,dec,'Object')
	hst.getObstable()
	hst.getJPGurl()
	print("I found",hst.Nimages,"HST images of",hst.object,"located at coordinates",hst.ra,hst.dec)
	print("The cut out images have the following URLs:")
	for jpg in hst.jpglist:
		print(jpg)
	print("Run time was: ",(datetime.now() - startTime).total_seconds(),"seconds")
	
