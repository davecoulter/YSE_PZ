from astropy.io.votable import parse
import numpy as np
import warnings,os,requests,sys
import io
from datetime import datetime
warnings.filterwarnings("ignore")


class chandraImages():
	def __init__(self,ra,dec,obj):
		# Transient information/search criteria
		self.ra=ra
		self.dec=dec
		self.object=obj
		self.radius=0.2
		self.tmpfile="delme.xml"

		## Selection criteria
		self.allowed_detector=['ACIS-I','ACIS-S']

		# Information pulled from Chandra archive
		self.obstable=None
		self.obsids=[]
		self.targnames=[]
		self.targ_ras=[]
		self.targ_decs=[]
		self.exp_times=[]
		self.obs_dates=[]
		self.jpegs=[]
		self.images=[]
		self.n_obsid=0
		self.total_exp=0

	def search_chandra_database(self):
		u="https://cxcfps.cfa.harvard.edu/cgi-bin/cda/footprint/get_vo_table.pl?pos={0},{1}&size={2}"
		url=u.format(self.ra, self.dec, self.radius)

		if self.allowed_detector is not None:
			url += "&inst="
			for i in self.allowed_detector:
				url += ","+i
		url += "&grating=NONE"

		r=requests.get(url)
		if r.status_code!=200:
			print('status message:',r.text)
			raise RuntimeError('ERROR: could not get url %s, status code %d' % (url,r.status_code))
		f=open(self.tmpfile,'w+')
		f.write(r.text)
		f.close()

		votable=parse(self.tmpfile)
		os.remove(self.tmpfile)
		tbdata=votable.get_first_table()
		data=tbdata.array

		mask=np.unique(data['ObsId'],return_index=True)[1]
		uniq_obsid_data=data[mask]
		grmask=uniq_obsid_data['Grating'] == b'NONE'
		uniq_obsid_data=uniq_obsid_data[grmask]

		self.total_exp=np.sum(uniq_obsid_data['Exposure'])
		self.obsids=uniq_obsid_data['ObsId']
		self.targnames=uniq_obsid_data['target_name']
		self.n_obsid=len(uniq_obsid_data)
		self.targ_ras=uniq_obsid_data['RA']
		self.targ_decs=uniq_obsid_data['Dec']
		self.exp_times=uniq_obsid_data['Exposure']
		self.obs_dates=uniq_obsid_data['obs_date']
		self.jpegs=uniq_obsid_data['preview_uri']
		self.images=uniq_obsid_data['full_uri']


## TEST TEST TEST
if __name__=='__main__':
	startTime = datetime.now()
	if (len(sys.argv) < 2):
		print("Usage: python chandra_query.py ra(deg) dec(deg)!!!")
		sys.exit(1)

	ra=float(sys.argv[1])
	dec=float(sys.argv[2])
	chandra=chandraImages(ra,dec,"Object")
	chandra.search_chandra_database()
	print("I found",chandra.n_obsid,"Chandra images of",chandra.object,
		"located at coordinates",chandra.ra,chandra.dec)
	print("Total exposure time is:",chandra.total_exp,"ks")
	print(chandra.images)
	print(chandra.jpegs)
	print("OBS ID/TARGET/RA/DEC/EXPTIME is:")
	for o,l,t,r,d,e in zip(chandra.obsids,
						   chandra.obs_dates,
						   chandra.targnames,
						   chandra.targ_ras,
						   chandra.targ_decs,
						   chandra.exp_times):
		print(o,l,t,r,d,e)
	print("Run time was: ",(datetime.now() - startTime).total_seconds(),"seconds")