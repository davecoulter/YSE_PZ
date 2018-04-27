#!/usr/bin/env python
# D. Jones - 12/2/17
# python uploadTransientData.py -i foundlc/GPC1v3_F15atz.snana.dat -f -e -s ../../YSE_PZ/settings.ini

import os
import json
import urllib.request
import ast
from astropy.time import Time
import numpy as np
import coreapi

class upload():
	def __init__(self):
		pass
	def add_options(self, parser=None, usage=None, config=None):
		import optparse
		if parser == None:
			parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

		parser.add_option('-s','--settingsfile', default=None, type="string",
						  help='settings file (login/password info)')
			
		# The basics
		parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_option('--clobber', default=False, action="store_true",
						  help='clobber output file')

		parser.add_option('-i','--inputfile', default=None, type="string",
						  help='input file ')
		parser.add_option('--trid', default=None, type="string",
						  help='transient ID')
		parser.add_option('--status', default='Following', type="string",
						  help='transient status (new, follow, etc')
		parser.add_option('--obsgroup', default='Foundation', type="string",
						  help='group who observed this transient')
		parser.add_option('--inputformat', default='snana', type="string",
						  help="input file format, can be 'basic' or 'snana' (photometry only) ")
		parser.add_option('--instrument', default='GPC1', type="string",
						  help="instrument name")
		parser.add_option('-u','--useheader', default=False, action="store_true",
						  help="if set, grab keys from the file header and try to POST to db")
		parser.add_option('-f','--foundationdefaults', default=False, action="store_true",
						  help="use default settings for foundation")
		parser.add_option('-e','--onlyexisting', default=False, action="store_true",
						  help="only add light curves for existing objects")
		parser.add_option('-m','--mjdmatchmin', default=0.05, type="float",
						  help="""if clobber flag not set, photometric observation with MJD separation 
less than this, in the same filter/instrument are treated as the same data.	 Allows updates to the photometry""")

		
		return(parser)

	def uploadHeader(self,sn,db=None):
		# first figure out the status and obs_group foreign keys
		statusid = db.get_ID_from_DB('transientstatuses',self.options.status)
		obsid = db.get_ID_from_DB('observationgroups',self.options.obsgroup)
		if not obsid or not statusid: raise RuntimeError('Error : obsgroup or status not found in DB!')

		transgetcmd = "http -a %s:%s GET %s/transients/"%(
			self.options.login,self.options.password,self.options.postURL)
		if 'OTHERID' in sn.__dict__.keys():
			transid = getIDfromName(transgetcmd,sn.OTHERID)
			transname = sn.OTHERID
		else:
			transid = getIDfromName(transgetcmd,sn.SNID)
			transname = sn.SNID
			
		if not transid:
			if type(sn.RA) == float:
				# upload the basic transient data
				basicdatacmd = "http -a %s:%s POST %s/transients/ name='%s' ra='%s' dec='%s' status='%s' obs_group=%s"%(
					self.options.login,self.options.password,self.options.postURL,transname,float(sn.RA),float(sn.DECL),
					statusid,obsid)
			else:
				basicdatacmd = "http -a %s:%s POST %s/transients/ name='%s' ra='%s' dec='%s' status='%s' obs_group=%s"%(
					self.options.login,self.options.password,self.options.postURL,transname,sn.RA.split()[0],sn.DECL.split()[0],
					statusid,obsid)
		#else:
		#	basicdatacmd = "http -a %s:%s PATCH %s/transients/%s/ name='%s' ra='%s' dec='%s' status=%s obs_group=%s"%(
		#		self.options.login,self.options.password,self.options.postURL,transid,transname,sn.RA.split()[0],sn.DECL.split()[0],
		#		statusid,obsid)

		output = os.popen(basicdatacmd).read()
		basictrans = json.loads(output)
		transid = basictrans['url']
		
		return(transid)
		
	def uploadSNANAPhotometry(self,db=None):
		import snana
		sn = snana.SuperNova(self.options.inputfile)
		if self.options.foundationdefaults:
			sn.SNID = sn.otherID[2:]
		transid = db.get_transient_from_DB(sn.SNID)
		if self.options.onlyexisting and not transid:
			print('Object %s not found!	 Trying %s'%(sn.SNID,sn.otherID))
			sn.SNID = sn.otherID
			transid = db.get_transient_from_DB(sn.SNID)
			if self.options.onlyexisting and not transid:
				print('Object %s not found!	 Returning'%sn.SNID)
				return()
		print('uploading object %s'%sn.SNID)
		
		if self.options.useheader:
			transid = self.uploadHeader(sn)			
			transname = sn.SNID
		else:
			transid = db.get_transient_from_DB(sn.SNID)
			transname = sn.SNID
			
		# create photometry object, if it doesn't exist
		photheaderdata = db.get_objects_from_DB('photometry')
		if type(sn.RA) == float:
			self.parsePhotHeaderData(photheaderdata,transname,sn.RA,sn.DECL,db=db)
		else:
			self.parsePhotHeaderData(photheaderdata,transname,sn.RA.split()[0],sn.DECL.split()[0],db=db)
		# get the filter IDs
		
		# upload the photometry
		for mjd,flux,fluxerr,mag,magerr,flt in zip(
				sn.MJD,sn.FLUXCAL,sn.FLUXCALERR,sn.MAG,sn.MAGERR,sn.FLT):

			obsdate = Time(mjd,format='mjd').isot
			bandid = db.getBandfromDB('band',flt,self.instid)
			if not bandid:
				raise RuntimeError('Error : band %s is not defined in the DB!!'%flt)
			
			PhotUploadDict = {'obs_date':obsdate,
							  'flux':flux,
							  'flux_err':fluxerr,
							  'photometry':self.photdataid,
							  'forced':1,
							  'dq':1,
							  'band':bandid,
							  'flux_zero_point':27.5,
							  'groups':[]}
			
			if flux > 0:
				PhotUploadDict['mag'] = mag
				PhotUploadDict['mag_err'] = magerr

			if 'SEARCH_PEAKMJD' in sn.__dict__.keys() and np.abs(mjd - sn.SEARCH_PEAKMJD) < 0.5:
				PhotUploadDict['discovery_point'] = 1
				
			if not transid:
				photdata = db.post_object_to_DB('photdata',PhotUploadDict)
			else:
				# if the transient is already in the DB, we need to check for photometry
				# and avoid duplicate epochs
				photepochs = db.get_objects_from_DB('photdata')
				closeID = None
				for p in photepochs:
					pmjd = Time(p['obs_date'],format='isot').mjd
					if p['photometry'] == self.photdataid and np.abs(pmjd - mjd) < self.options.mjdmatchmin and p['band'] == bandid:
						closeID = p['url']
						break
				if closeID and self.options.clobber:
					photdata = db.patch_object_to_DB('photdata',PhotUploadDict,closeID)
				elif closeID and not self.options.clobber:
					print('data point at MJD %i exists!	 not clobbering'%pmjd)
				else:
					photdata = db.post_object_to_DB('photdata',PhotUploadDict)
								
	def parsePhotHeaderData(self,photheaderdata,snid,ra,dec,db=None):

		# if no photometry header, then create one
		self.instid = db.get_ID_from_DB('instruments',self.options.instrument)
		if not self.instid:
			self.instid = db.get_ID_from_DB('instruments','Unknown')
		self.obsgroupid = db.get_ID_from_DB('observationgroups',self.options.obsgroup)
		if not self.obsgroupid:
			self.obsgroupid = db.get_ID_from_DB('observationgroups','Unknown')
		self.snidid = db.get_transient_from_DB(snid)

		inDB = False
		if type(photheaderdata) == list or not self.snidid:
			self.photdataid = db.getPhotObjfromDB(
				'photometry',self.snidid,self.instid,self.obsgroupid)
			if self.photdataid: inDB = True
			
		if not inDB:

			if not self.snidid:
				postdict = {'obs_group':self.obsgroupid,
							'status':db.get_ID_from_DB('transientstatuses',self.options.status),
							'name':snid,
							'ra':ra,
							'dec':dec,
							'groups':[]}
				self.snidid = db.post_object_to_DB('transient',postdict)

			photpostdict = {'instrument':self.instid,
							'obs_group':self.obsgroupid,
							'transient':self.snidid,
							'groups':[]}
			self.photdataid = db.post_object_to_DB('photometry',photpostdict)

			
	def uploadBasicPhotometry(self):
		from txtobj import txtobj

	def uploadBasicSpectrum(self):
		from txtobj import txtobj

def runDBcommand(cmd):
	try:
		return(json.loads(os.popen(cmd).read()))
	except:
		import pdb; pdb.set_trace()
		raise RuntimeError('Error : cmd %s failed!!'%cmd)
	

class DBOps():
	def __init__(self):
		pass

	def init_params(self):
		self.dblogin = self.options.dblogin
		self.dbpassword = self.options.dbpassword
		self.dburl = self.options.dburl
		self.baseposturl = "http --ignore-stdin -a %s:%s POST %s"%(self.dblogin,self.dbpassword,self.dburl)
		self.basegeturl = "http --ignore-stdin -a %s:%s GET %s"%(self.dblogin,self.dbpassword,self.dburl)
		self.baseputurl = "http --ignore-stdin -a %s:%s PUT %s"%(self.dblogin,self.dbpassword,self.dburl)
		self.basegetobjurl = "http --ignore-stdin -a %s:%s GET "%(self.dblogin,self.dbpassword)
	
	def add_options(self, parser=None, usage=None, config=None):
		import optparse
		if parser == None:
			parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

		parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_option('--clobber', default=False, action="store_true",
						  help='clobber output file')
		parser.add_option('-i','--inputfile', default=None, type="string",
						  help='input file ')
		parser.add_option('-p','--photometry', default=False, action="store_true",
						  help='input file is photometry')
		parser.add_option('--spectrum', default=False, action="store_true",
						  help='input file is a spectrum')
		
		parser.add_option('-s','--settingsfile', default=None, type="string",
						  help='settings file (login/password info)')
		parser.add_option('-f','--foundationdefaults', default=False, action="store_true",
						  help="use default settings for foundation")
		parser.add_option('-e','--onlyexisting', default=False, action="store_true",
						  help="only add light curves for existing objects")
		
		if config:
			parser.add_option('--login', default=config.get('main','login'), type="string",
							  help='gmail login (default=%default)')
			parser.add_option('--password', default=config.get('main','password'), type="string",
							  help='gmail password (default=%default)')

			parser.add_option('--dblogin', default=config.get('main','dblogin'), type="string",
							  help='gmail login (default=%default)')
			parser.add_option('--dbpassword', default=config.get('main','dbpassword'), type="string",
							  help='gmail password (default=%default)')
			parser.add_option('--dburl', default=config.get('main','dburl'), type="string",
							  help='base URL to POST/GET,PUT to/from a database (default=%default)')
			parser.add_option('--transientapi', default=config.get('main','transientapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--internalsurveyapi', default=config.get('main','internalsurveyapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--transientclassesapi', default=config.get('main','transientclassesapi'), type="string",
							  help='URL to POST transients classes to a database (default=%default)')
			parser.add_option('--hostapi', default=config.get('main','hostapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--photometryapi', default=config.get('main','photometryapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--photdataapi', default=config.get('main','photdataapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--hostphotometryapi', default=config.get('main','hostphotometryapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--hostphotdataapi', default=config.get('main','hostphotdataapi'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--obs_groupapi', default=config.get('main','obs_groupapi'), type="string",
							  help='URL to POST group to a database (default=%default)')
			parser.add_option('--statusapi', default=config.get('main','statusapi'), type="string",
							  help='URL to POST status to a database (default=%default)')
			parser.add_option('--instrumentapi', default=config.get('main','instrumentapi'), type="string",
							  help='URL to POST instrument to a database (default=%default)')
			parser.add_option('--bandapi', default=config.get('main','bandapi'), type="string",
							  help='URL to POST band to a database (default=%default)')
			parser.add_option('--observatoryapi', default=config.get('main','observatoryapi'), type="string",
							  help='URL to POST observatory to a database (default=%default)')
			parser.add_option('--telescopeapi', default=config.get('main','telescopeapi'), type="string",
							  help='URL to POST telescope to a database (default=%default)')

			return(parser)
			
	def post_object_to_DB(self,table,objectdict,return_full=False):
		cmd = '%s%s '%(self.baseposturl,self.options.__dict__['%sapi'%table])
		for k,v in zip(objectdict.keys(),objectdict.values()):
			if '<url>' not in str(v):
				if k != 'tags' and k != 'groups':
					cmd += '%s="%s" '%(k,v)
				else:
					cmd += '%s:=[] '%(k)
			else:
				cmd += '%s="%s%s%s/" '%(k,self.dburl,self.options.__dict__['%sapi'%k],v.split('/')[1])

		objectdata = runDBcommand(cmd)

		if type(objectdata) != list and 'url' not in objectdata:
			print(cmd)
			print(objectdata)
			raise RuntimeError('Error : failure adding object')
		if return_full:
			return(objectdata)
		else:
			return(objectdata['url'])

	def put_object_to_DB(self,table,objectdict,objectid,return_full=False):
		cmd = '%s PUT %s '%(self.baseputurl.split('PUT')[0],objectid)
		for k,v in zip(objectdict.keys(),objectdict.values()):
			if '<url>' not in str(v):
				if k != 'tags' and k != 'groups':
					cmd += '%s="%s" '%(k,v)
				else:
					cmd += '%s:=[] '%k
			else:
				cmd += '%s="%s%s%s/" '%(k,self.dburl,self.options.__dict__['%sapi'%k],v.split('/')[1])

		objectdata = runDBcommand(cmd)

		if type(objectdata) != list and 'url' not in objectdata:
			print('cmd %s failed'%cmd)
			print(objectdata)
			raise RuntimeError('Error : failure adding object')
		if return_full:
			return(objectdata)
		else:
			return(objectdata['url'])

	def patch_object_to_DB(self,table,objectdict,objectid,return_full=False):
		cmd = '%s PATCH %s '%(self.baseputurl.split('PUT')[0],objectid)
		for k,v in zip(objectdict.keys(),objectdict.values()):
			if '<url>' not in str(v):
				cmd += '%s="%s" '%(k,v)
			else:
				cmd += '%s="%s%s%s/" '%(k,self.dburl,self.options.__dict__['%sapi'%k],v.split('/')[1])
		objectdata = runDBcommand(cmd)

		if type(objectdata) != list and 'url' not in objectdata:
			print('cmd %s failed'%cmd)
			print(objectdata)
			raise RuntimeError('Error : failure adding object')
		if return_full:
			return(objectdata)
		else:
			return(objectdata['url'])

	def get_objects_from_DB(self,table):
		cmd = '%s%s '%(self.basegeturl,self.options.__dict__['%sapi'%table])
		objectdata = runDBcommand(cmd)

		if 'results' not in objectdata or type(objectdata['results']) != list and 'url' not in objectdata['results'][0]:
			print(cmd)
			print(objectdata)
			raise RuntimeError('Error : failure adding object')
		else:
			return(objectdata['results'])


	def get_ID_from_DB(self,tablename,fieldname,debug=False):

		if debug: tstart = time.time()
		auth = coreapi.auth.BasicAuthentication(
			username=self.dblogin,
			password=self.dbpassword,
		)
		client = coreapi.Client(auth=auth)
		try:
			schema = client.get('%s%s'%(self.dburl,tablename))
		except:
			raise RuntimeError('Error : couldn\'t get schema!')

		idlist,namelist = [],[]
		for i in range(len(schema['results'])):
			namelist += [schema['results'][i]['name']]
			idlist += [schema['results'][i]['url']]

		if debug:
			print('GET took %.1f seconds'%(time.time()-tstart))

		if fieldname not in namelist: return(None)

		return(np.array(idlist)[np.where(np.array(namelist) == fieldname)][0])

	def get_transient_from_DB(self,fieldname,debug=False):

		if debug: tstart = time.time()
		tablename = 'transients'
		auth = coreapi.auth.BasicAuthentication(
			username=self.dblogin,
			password=self.dbpassword,
		)
		client = coreapi.Client(auth=auth)
		try:
			schema = client.get('%s%s'%(self.dburl.replace('/api','/get_transient'),fieldname))
		except:
			raise RuntimeError('Error : couldn\'t get schema!')

		if not schema['transient']:
			return None

		return(schema['transient']['url'])
	
	def get_key_from_object(self,objid,fieldname):
		cmd = '%s%s'%(self.basegetobjurl,objid)
		output = os.popen(cmd).read()
		try:
			data = json.loads(output)
		except:
			print(cmd)
			print(os.popen(cmd).read())
			raise RuntimeError('Error : cmd output not in JSON format')

		if fieldname in data:
			val = data[fieldname]
			return(val)
		else: return(None)

	def getPhotObjfromDB(self,table,transient,instrument,obsgroup):
		cmd = '%s%s '%(self.basegeturl,self.options.__dict__['%sapi'%table])
		output = os.popen(cmd).read()
		data = json.loads(output)

		translist,instlist,obsgrouplist,idlist = [],[],[],[]
		for i in range(len(data['results'])):
			obsgrouplist += [data['results'][i]['obs_group']]
			instlist += [data['results'][i]['instrument']]
			translist += [data['results'][i]['transient']]
			idlist += [data['results'][i]['url']]

		if obsgroup not in obsgrouplist or instrument not in instlist or transient not in translist:
			return(None)
		iObs = np.where((np.array(translist) == transient) &
						(np.array(instlist) == instrument) &
						(np.array(obsgrouplist) == obsgroup))[0]
		if not len(iObs): return(None)

		return(np.array(idlist)[iObs][0])

				
	def getBandfromDB(self,table,fieldname,instrument):
		cmd = '%s%s '%(self.basegeturl,self.options.__dict__['%sapi'%table])
		output = os.popen(cmd).read()
		data = json.loads(output)

		idlist,namelist,instlist = [],[],[]
		for i in range(len(data['results'])):
			namelist += [data['results'][i]['name']]
			idlist += [data['results'][i]['url']]
			instlist += [data['results'][i]['instrument']]

		if fieldname not in namelist or instrument not in instlist: return(None)

		return(np.array(idlist)[np.where((np.array(namelist) == fieldname) &
										 (np.array(instlist) == instrument))][0])

		
if __name__ == "__main__":

	# execute only if run as a script

	import optparse
	import configparser

	usagestring='uploadData.py [options]'
	upl = upload()

	# read in the options from the param file and the command line
	# some convoluted syntax here, making it so param file is not required
	parser = upl.add_options(usage=usagestring)
	options,  args = parser.parse_args()
	if options.settingsfile:
		config = configparser.ConfigParser()
		config.read(options.settingsfile)
	else: config=None
	parser = upl.add_options(usage=usagestring,config=config)
	options,  args = parser.parse_args()

	db = DBOps()
	if config:
		parser = db.add_options(usage=usagestring,config=config)
		dboptions,	args = parser.parse_args()
		db.options = dboptions
	db.init_params()
		

	upl.options = options
	
	if options.inputformat == 'basic':
		upl.uploadBasicPhotometry(db=db)
	elif options.inputformat == 'snana':
		upl.uploadSNANAPhotometry(db=db)
	else:
		raise RuntimeError('Error : input option not found')
