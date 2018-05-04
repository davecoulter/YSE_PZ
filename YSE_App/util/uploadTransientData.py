#!/usr/bin/env python
# D. Jones - 12/2/17
# python uploadTransientData.py -i foundlc/GPC1v3_F15atz.snana.dat -f -e -s ../../YSE_PZ/settings.ini

import os
import json
import urllib.request
import urllib
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
		parser.add_option('--permissionsgroup', default='', type="string",
						  help='group that has permission to view this photometry on YSE_PZ')
		parser.add_option('--inputformat', default='snana', type="string",
						  help="input file format, can be 'basic' or 'snana' (photometry only) ")
		parser.add_option('--instrument', default='GPC1', type="string",
						  help="instrument name")
		parser.add_option('--forcedphot', default=0, type="int",
						  help="set to 1 if forced photometry")
		parser.add_option('-u','--useheader', default=False, action="store_true",
						  help="if set, grab keys from the file header and try to POST to db")
		parser.add_option('-f','--foundationdefaults', default=False, action="store_true",
						  help="use default settings for foundation")
		parser.add_option('-e','--onlyexisting', default=False, action="store_true",
						  help="only add light curves for existing objects")
		parser.add_option('-m','--mjdmatchmin', default=0.05, type="float",
						  help="""if clobber flag not set, photometric observation with MJD separation 
less than this, in the same filter/instrument are treated as the same data.	 Allows updates to the photometry""")
		parser.add_option('--spectrum', default=False, action="store_true",
						  help='input file is a spectrum')
		
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
			if 'otherID' in sn.__dict__.keys():
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
			
		# get dictionaries for transient and photometry
		if type(sn.RA) == float:
			transientdict,photdict = self.parsePhotHeaderData(transname,sn.RA,sn.DECL)
		else:
			transientdict,photdict = self.parsePhotHeaderData(transname,sn.RA.split()[0],sn.DECL.split()[0])
		# get the filter IDs

		PhotUploadAll = {'transient':transientdict,
						 'photheader':photdict}
		
		# upload the photometry
		for mjd,flux,fluxerr,mag,magerr,flt in zip(
				sn.MJD,sn.FLUXCAL,sn.FLUXCALERR,sn.MAG,sn.MAGERR,sn.FLT):

			obsdate = Time(mjd,format='mjd').isot
			
			PhotUploadDict = {'obs_date':obsdate,
							  'flux':flux,
							  'flux_err':fluxerr,
							  'forced':self.options.forcedphot,
							  'dq':1,
							  'band':flt,
							  'flux_zero_point':27.5,
							  'groups':[]}
			
			if flux > 0:
				PhotUploadDict['mag'] = mag
				PhotUploadDict['mag_err'] = magerr
			else:
				PhotUploadDict['mag'] = ''
				PhotUploadDict['mag_err'] = ''
				
			if 'SEARCH_PEAKMJD' in sn.__dict__.keys() and np.abs(mjd - sn.SEARCH_PEAKMJD) < 0.5:
				PhotUploadDict['discovery_point'] = 1
			else:
				PhotUploadDict['discovery_point'] = 0
			PhotUploadAll[obsdate] = PhotUploadDict
			PhotUploadAll['header'] = {'clobber':self.options.clobber,
									   'mjdmatchmin':self.options.mjdmatchmin}
		import requests
		from requests.auth import HTTPBasicAuth
		url = '%s'%db.dburl.replace('/api','/add_transient_phot')
		r = requests.post(url = url, data = json.dumps(PhotUploadAll),
						  auth=HTTPBasicAuth(db.dblogin,db.dbpassword))

		print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		
	def parsePhotHeaderData(self,snid,ra,dec):

		transientdict = {'obs_group':self.options.obsgroup,
						 'status':self.options.status,
						 'name':snid,
						 'ra':ra,
						 'dec':dec,
						 'groups':self.options.permissionsgroup}

		photdict = {'instrument':self.options.instrument,
					'obs_group':self.options.obsgroup,
					'transient':snid,
					'groups':self.options.permissionsgroup}

		return(transientdict,photdict)
			
	def uploadBasicPhotometry(self):
		from txtobj import txtobj

	def uploadBasicSpectrum(self,db=None):

		SpecDictAll = {}
		SpecHeader = {}
		keyslist = ['ra','dec','instrument','rlap','obs_date','redshift',
					'redshift_err','redshift_quality','spectrum_notes',
					'obs_group','groups','spec_phase','snid']
		requiredkeyslist = ['ra','dec','instrument','obs_date','obs_group','snid']
		fin = open(self.options.inputfile)
		count = 0
		for line in fin:
			line = line.replace('\n','')
			if not count: header = np.array(line.replace('# ','').split())
			for key in keyslist:
				if line.lower().startswith('# %s '%key):
					SpecHeader[key] = line.split()[-1]
			count += 1
		fin.close()

		if 'wavelength' not in header or 'flux' not in header:
			raise RuntimeError("""Error : incorrect file format.
			The header should be # wavelength flux fluxerr, with fluxerr optional.""")

		try:
			spc = {}
			spc['wavelength'] = np.loadtxt(self.options.inputfile,unpack=True,usecols=[np.where(header == 'wavelength')[0][0]])
			spc['flux'] = np.loadtxt(self.options.inputfile,unpack=True,usecols=[np.where(header == 'flux')[0][0]])
		except:
			raise RuntimeError("""Error : incorrect file format.
			The header should be # wavelength flux fluxerr, with fluxerr optional.""")

		if 'fluxerr' in header:
			spc['fluxerr'] = np.loadtxt(self.options.inputfile,unpack=True,usecols=[np.where(header == 'fluxerr')[0][0]])
		for key in requiredkeyslist:
			if key not in SpecHeader.keys():
				raise RuntimeError("""Error: required key %s not in spectrum header.
				Format should be
				# key keyval"""%key)			
		for key in keyslist:
			if key not in SpecHeader.keys():
				print('Warning: %s not in spectrum header'%key)
				SpecHeader[key] = None
		SpecHeader['clobber'] = self.options.clobber
		SpecDictAll['header'] = SpecHeader

		SpecDictAll['transient'] = {'name':SpecHeader['snid']}
		
		if 'fluxerr' in spc.keys():
			for w,f,df in zip(spc['wavelength'],spc['flux'],spc['fluxerr']):
				SpecDict = {'wavelength':w,
							'flux':f,
							'flux_err':df}
				SpecDictAll[w] = SpecDict
		else:
			for w,f in zip(spc['wavelength'],spc['flux']):
				SpecDict = {'wavelength':w,
							'flux':f,
							'flux_err':None}
				SpecDictAll[w] = SpecDict
				
		import requests
		from requests.auth import HTTPBasicAuth
		url = '%s'%db.dburl.replace('/api','/add_transient_spec')
		r = requests.post(url = url, data = json.dumps(SpecDictAll),
						  auth=HTTPBasicAuth(db.dblogin,db.dbpassword))

		print('YSE_PZ says: %s'%json.loads(r.text)['message'])

				
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
		parser.add_option('--permissionsgroup', default='', type="string",
						  help='group that has permission to view this photometry on YSE_PZ')
		parser.add_option('--forcedphot', default=0, type="int",
						  help="set to 1 if forced photometry")
		
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

	if options.spectrum:
		upl.uploadBasicSpectrum(db=db)
	elif options.inputformat == 'basic':
		upl.uploadBasicPhotometry(db=db)
	elif options.inputformat == 'snana':
		upl.uploadSNANAPhotometry(db=db)
	else:
		raise RuntimeError('Error : input option not found')
