#!/usr/bin/env python 
# Python 2/3 compatibility
from __future__ import print_function
import re,sys,string,math,os,types,exceptions,glob
from astropy.table import Table
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import time
import requests
import json
from requests.auth import HTTPBasicAuth
from astropy.time import Time

filtdict = {"THACHER z":'Thacher - Imager - z',
			"THACHER i":'Thacher - Imager - i',
			"THACHER r":'Thacher - Imager - r',
			"THACHER g":'Thacher - Imager - g',
			"THACHER u":'Thacher - Imager - u',
			"ANDICAM K":'ANDICAM - IR - K',
			"ANDICAM H":'ANDICAM - IR - H',
			"ANDICAM J":'ANDICAM - IR - J',
			"ANDICAM U":'ANDICAM - CCD - U',
			"ANDICAM I":'ANDICAM - CCD - I',
			"ANDICAM R":'ANDICAM - CCD - R',
			"ANDICAM V":'ANDICAM - CCD - V',
			"ANDICAM B":'ANDICAM - CCD - B',
			"NICKEL r":"Direct/2Kx2K - r'",
			"NICKEL i":"Direct/2Kx2K - i'",
			"NICKEL B":"Direct/2Kx2K - V",
			"NICKEL V":"Direct/2Kx2K - B",
			"SWOPEDIRECT u":"Direct/4Kx4K - u",
			"SWOPEDIRECT r":"Direct/4Kx4K - r",
			"SWOPEDIRECT i":"Direct/4Kx4K - i",
			"SWOPEDIRECT g":"Direct/4Kx4K - g",
			"SWOPEDIRECT V":"Direct/4Kx4K - V",
			"SWOPEDIRECT B":"Direct/4Kx4K - B'"}

def mjd_to_date(mjd):
	t = Time(mjd, format='mjd')
	return t.fits.replace('(UTC)','').replace('T',' ')
	
def hex2int(val):
	if type(val) is str:   #types.StringType:
		val = int(eval(val))
	return(val)

class GW2YSE:
	def __init__(self):
		pass

	def add_options(self, parser=None, usage=None, config=None):
		import optparse
		if parser == None:
			parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

		parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_option('--clobber', default=False, action="store_true",
						  help='clobber output file')
		parser.add_option('--debug', default=False, action="store_true",
						  help='clobber output file')
		parser.add_option('-s','--settingsfile', default=None, type="string",
						  help='settings file (login/password info)')
		parser.add_option('-i','--inlist', default=None, type="string",
						  help='input list with alerts pages')
		parser.add_option('-o','--outlist', default=None, type="string",
						  help='output list')

		
		if config:
			parser.add_option('--login', default=config.get('main','login'), type="string",
							  help='gmail login (default=%default)')
			parser.add_option('--password', default=config.get('main','password'), type="string",
							  help='gmail password (default=%default)')
			parser.add_option('--dblogin', default=config.get('main','dblogin'), type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbemail', default=config.get('main','dbemail'), type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbpassword', default=config.get('main','dbpassword'), type="string",
							  help='database password, if post=True (default=%default)')
			parser.add_option('--dburl', default=config.get('main','dburl'), type="string",
							  help='URL to POST transients to a database (default=%default)')

		else:
			parser.add_option('--login', default="", type="string",
							  help='gmail login (default=%default)')
			parser.add_option('--password', default="", type="string",
							  help='gmail password (default=%default)')
			parser.add_option('--dblogin', default="", type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbemail', default="", type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbpassword', default="", type="string",
							  help='database password, if post=True (default=%default)')
			parser.add_option('--dburl', default="", type="string",
							  help='URL to POST transients to a database (default=%default)')

		return parser
			
	def getdata(self,listfilename,outfile):
		# put the tools directory into the path
		pyscripts = os.environ['PIPE_PYTHONSCRIPTS']
		sys.path.append(pyscripts+'/tools')
		sys.path.append(pyscripts)
		sys.path.append(os.path.join(pyscripts, os.environ['PIPENAME']))
		sys.path.append(os.path.join(pyscripts, os.environ['PIPE_INSTRUMENT']))

		if not listfilename or not outfile:
			raise RuntimeError('input and output filenames must be set with the -i and -o args!')
		
		import pipeclasses

		if	os.environ['PIPE_INSTRUMENT']=='SWOPEDIRECT':
			import swopealerts as alerts
			temporaryalerts = alerts.swopealertclass()
			alerts = alerts.swopealertclass()
		else:
			error = 'ERROR: PIPE_INSTRUMENT={inst} is not recognized!'
			raise RuntimeError,error.format(inst=os.environ['PIPE_INSTRUMENT'])

		params = pipeclasses.paramfileclass()
		params.loadfile(os.getenv('PIPE_PARAMS'))

		# read the files
		lines=open(listfilename).readlines()

		outfmt = '{field:<8} {candID:<4} {intname:<14} {ra:<14} {dec:<14} {mjd:<12}'
		outfmt += '{dpclass:<12} {filters} {images} \n'
		outlist = [outfmt.format(field='#Field',
								candID='candID',
								intname='Internal Name',
								ra='RA',
								dec='DEC',
								mjd='MJD',
								dpclass='Type',
								filters='Filters',
								images='Images')]

		datadictlist,objs,ras,decs = {},[],[],[]
		for line in lines:
			linebkp = line
			line = line.strip()
			line = re.sub('addevents.py','',line)
			line = re.sub('"','',line)
			line = line.strip()
			print('################################\n###  ADDING %s' % (line))
			m	  = re.search('.*\#(\d+)$',line)
			if m:
				(candID,) = m.groups()
				candID = int(candID)
			else:
				f = open(sys.argv[1]+'.error','aw')
				f.write(linebkp)
				f.close()
				continue

			clusters = parsehtml4cluster(line, params)
			websniff = parsehtml4websniff(line, params)

			filetable = None
			candlist = None
			difflc = None
			with open(clusters, 'r') as f:
				buff = []
				for line in f:
					if line.startswith('#') and len(buff)==0:
						buff.append(line.strip('#').split())
						continue
					elif line.startswith('#') and len(buff)>0:
						# Read out buffer into table
						header = buff[0]
						trans_cols = map(list, zip(*buff[1:]))
						if header[0]=='cmpfile':
							# file table
							filetable = Table(trans_cols, names=header)
						elif (header[0]=='ID' and header[1]=='RAaverage'):
							# candlist
							candlist = Table(trans_cols, names=header)
						elif (header[0]=='ID' and header[1]=='cmpfile'):
							# difflc, only want the one with ID=candID
							if (buff[1][0]==str(candID)):
								difflc = Table(trans_cols, names=header)
								buff = []
								break
						buff = [line.strip('#').split()]
					else:
						buff.append(line.split())
			# If buff is not empty, unfortunately it was the last one
			if len(buff)>0:
				if (buff[0][0]=='ID' and buff[0][1]=='cmpfile'):
					difflc = Table(map(list, zip(*buff[1:])), names=buff[0])

			# Now that we've parsed all the data.  Need to work our way through
			# this convoluted catalog system.  Step 1 is parse RAaverage, DECaverage
			# Get relevent row from candlist
			row = candlist[candlist['ID']==str(candID)]
			RAaverage = str(row['RAaverage'][0])
			DECaverage = str(row['DECaverage'][0])

			# Now get list of cmpfiles for each row in difflc
			files = difflc['cmpfile']

			# Now get filters.	This can be parsed directly from the cmpfiles
			filts = list(set([cmpfile.split('.')[1] for cmpfile in files]))

			# Parse highest S/N candidates and types for each filter in filts
			sn = ['---'] * len(filts)
			types = ['---'] * len(filts)
			for i,filt in enumerate(filts):
				for row in difflc:
					# Ignore wrong filter or negative sources or 0 error
					if (float(row['dflux'])==0.0
						or float(row['flux'])<0
						or '.'+filt+'.' not in row['cmpfile']):
						continue
					else:
						if sn[i] is '---':
							sn[i] = str(float(row['flux'])/float(row['dflux']))
							types[i] = str(row['type'])
						elif float(sn[i])<float(row['flux'])/float(row['dflux']):
							sn[i] = str(float(row['flux'])/float(row['dflux']))
							types[i] = str(row['type'])

			# There is no unique field name column, so we have to parse this from
			# one of the other columns.	 I'm using the FITSNAME here because we
			# always write out fits files with <field>.<filter>.<date>.<id>_...
			fitsname = filetable[filetable['cmpfile']==files[0]]['FITSNAME'][0]
			field = fitsname.split('.')[0]

			# Now glob all 3PS.jpg files for that candID into a comma-separated list
			search = websniff+'/*cand'+str(candID)+'.*3PS.jpg'
			triplets = ','.join(glob.glob(search))

			# Now get all of the MJDs from the filetable
			mjds = [float(filetable[filetable['cmpfile']==file]['MJD'][0])
				for file in files]
			discovery_mjd = np.min(mjds)

			datadict = {}
			datadict['name'] = field+'C'+str(candID).zfill(4)
			sc = SkyCoord(RAaverage,DECaverage,frame="fk5",unit=(u.hourangle,u.deg))
			datadict['ra'] = sc.ra.deg
			datadict['dec'] = sc.dec.deg
			datadict['disc_date'] = mjd_to_date(discovery_mjd)
			datadict['status'] = 'New'
			datadict['obs_group'] = 'SSS'
			datadict['gwcandidate'] = {}
			
			datadict['gwcandidate']['field_name'] = field
			datadict['gwcandidate']['candidate_id'] = candID
			datadict['gwcandidate']['name'] = field+'C'+str(candID).zfill(4)
			datadict['gwcandidate']['websniff_url'] = linebkp.replace('\n','')
			datadict['gwcandidate']['gwcandidateimage'] = {}
			datadict['gwcandidate']['transient'] = field+'C'+str(candID).zfill(4)
			
			for triplet,filt,dpclass in zip(triplets.split(','),filts,types):
				triplet_webaddress = triplet.replace('/web/','/')
				triplet = triplet_webaddress.split('/')
				triplet = "https://ziggy.ucolick.org/gw/" + "/".join(triplet[3:])
				imgdict = {}
				imgdict['dophot_class'] = hex2int(dpclass)
				imgdict['image_filter'] = filtdict['%s %s'%(os.environ['PIPE_INSTRUMENT'],filt)]
				imgdict['image_filename'] = triplet
				imgdict['obs_date'] = mjd_to_date(discovery_mjd)
				imgdict['gw_candidate'] = field+'C'+str(candID).zfill(4)
				datadict['gwcandidate']['gwcandidateimage'][triplet] = imgdict
			datadictlist[field+'C'+str(candID).zfill(4)] = datadict
			
			outlist.append(outfmt.format(field=field,
										 candID=candID,
										 intname=field+'C'+str(candID).zfill(4),
										 ra=RAaverage,
										 dec=DECaverage,
										 mjd=discovery_mjd,
										 dpclass=','.join(types),
										 filters=','.join(filts),
										 images=triplets))
			objs += [field+'C'+str(candID).zfill(4)]
			ras += [sc.ra.deg]
			decs +=[sc.dec.deg]
			
		with open(outfile,'w') as f:
			for line in outlist:
				f.write(line)

		return objs,ras,decs,datadictlist

	def senddata(self,datadictlist,objs,ras,decs,doNED=False):

		if self.debug:
			with open('tmp.json', 'r') as fp:
				datadictlist = json.load(fp)
			objs = ['2018ivcC0072']
			ras = ['40.9135208333']
			decs = ['-0.113786111111']
			self.UploadTransients(datadictlist)
		
			return

		
		assert len(ras) == len(decs)

		if type(ras[0]) == float:
			scall = SkyCoord(ras,decs,frame="fk5",unit=u.deg)
		else:
			scall = SkyCoord(ras,decs,frame="fk5",unit=(u.hourangle,u.deg))

		ebvall,nedtables = [],[]
		ebvtstart = time.time()
		if doNED:
			for sc in scall:
				dust_table_l = IrsaDust.get_query_table(sc)
				ebvall += [dust_table_l['ext SandF mean'][0]]
				try:
					ned_region_table = Ned.query_region(sc, radius=self.nedradius*u.arcmin, equinox='J2000.0')
				except:
					ned_region_table = None
				nedtables += [ned_region_table]
			print('E(B-V)/NED time: %.1f seconds'%(time.time()-ebvtstart))

		for j in range(len(objs)):
			tallstart = time.time()

			obj = objs[j]

			iobj = np.where(obj == np.array(objs))[0]
			if len(iobj) > 1: iobj = int(iobj[0])
			else: iobj = int(iobj)
			
			if doNED: sc,ebv,nedtable = scall[iobj],ebvall[iobj],nedtables[iobj]
			else: sc = scall[iobj]; ebv = None; nedtable = None
			
			print("Object: %s\nRA: %s\nDEC: %s" % (obj,ras[iobj],decs[iobj]))
			
			########################################################
			# For Item in Email, Get NED
			########################################################
			datadictlist[obj]['mw_ebv'] = ebv

			try:
				if doNED:
					hostdict,hostcoords = self.getNEDData(jd,sc,nedtable)
					datadictlist[obj]['host'] = hostdict
					datadictlist[obj]['candidate_hosts'] = hostcoords
			except: pass
			
			try:
				photdict = self.getZTFPhotometry(sc)
				datadictlist[obj]['transientphotometry'] = photdict
			except: photdict = None


		datadictlist['noupdatestatus'] = True
		with open('tmp.json', 'w') as fp:
			json.dump(datadictlist, fp)
		
		self.UploadTransients(datadictlist)
		
		return

				
	def getNEDData(self,jd,sc,ned_table):

		gal_candidates = 0
		radius = 5
		while (radius < 11 and gal_candidates < 21): 
			try:
				print("Radius: %s" % radius)
				gal_candidates = len(ned_table)
				radius += 1
				print("Result length: %s" % gal_candidates)
			except Exception as e:
				radius += 1
				print("NED exception: %s" % e.args)

		galaxy_names = []
		galaxy_zs = []
		galaxy_seps = []
		galaxies_with_z = []
		galaxy_ras = []
		galaxy_decs = []
		galaxy_mags = []
		if ned_table is not None:
			print("NED Matches: %s" % len(ned_table))

			galaxy_candidates = np.asarray([entry.decode("utf-8") for entry in ned_table["Type"]])
			galaxies_indices = np.where(galaxy_candidates == 'G')
			galaxies = ned_table[galaxies_indices]

			print("Galaxy Candidates: %s" % len(galaxies))

			# Get Galaxy name, z, separation for each galaxy with z
			for l in range(len(galaxies)):
				if isinstance(galaxies[l]["Redshift"], float):
					galaxies_with_z.append(galaxies[l])
					galaxy_names.append(galaxies[l]["Object Name"])
					galaxy_zs.append(galaxies[l]["Redshift"])
					galaxy_seps.append(galaxies[l]["Separation"])
					galaxy_ras.append(galaxies[l]["RA"])
					galaxy_decs.append(galaxies[l]["DEC"])
					galaxy_mags.append(galaxies[l]["Magnitude and Filter"])
								
			print("Galaxies with z: %s" % len(galaxies_with_z))
			# Get Dust in LoS for each galaxy with z
			if len(galaxies_with_z) > 0:
				for l in range(len(galaxies_with_z)):
					co_l = coordinates.SkyCoord(ra=galaxies_with_z[l]["RA"], 
												dec=galaxies_with_z[l]["DEC"], 
												unit=(u.deg, u.deg), frame='fk4', equinox='J2000.0')

			else:
				print("No NED Galaxy hosts with z")

		# put in the hosts
		hostcoords = ''; hosturl = ''; ned_mag = ''
		galaxy_z_times_seps = np.array(galaxy_seps)*np.array(np.abs(galaxy_zs))
		hostdict = {}
		for z,name,ra,dec,sep,mag,gzs in zip(galaxy_zs,galaxy_names,galaxy_ras,
											 galaxy_decs,galaxy_seps,galaxy_mags,
											 galaxy_z_times_seps):
			if gzs == np.min(galaxy_z_times_seps):
				hostdict = {'name':name,'ra':ra,'dec':dec,'redshift':z}
				
			hostcoords += 'ra=%.7f, dec=%.7f\n'%(ra,dec)

		return hostdict,hostcoords
	
	def UploadTransients(self,UploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_gw_candidate')
		r = requests.post(url = url, data = json.dumps(UploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
		
		print('YSE_PZ says: %s'%json.loads(r.text)['message'])				
		print("Process done.")

				

def parsehtml4cluster(htmlfilename, params):
	message = 'Parsing html address: {html}'
	print(message.format(html=htmlfilename))
	filename = re.sub('.*\/sniff\/*','',htmlfilename)
	filename = re.sub('\#\d+$','',filename)

	# Hack for Swope
	if os.environ['PIPE_INSTRUMENT']=='SWOPEDIRECT':
		sub = '(http|https)://ziggy.ucolick.org/gw/Swope'
		base = re.sub(sub, '', htmlfilename)
		base = re.sub('\#\d+$','', base)
		base = re.sub('/sniff/\d+/', '', base).split('/')
		clusters = params.get('WORKSPACE_DIR')
		clusters += '/' + base[0] + '/' + base[1] + '/' + base[2] + '.diff.clusters'
		return(clusters)
	else:
		error = 'ERROR: unrecognized PIPE_INSTRUMENT={pipe}'
		print(error.format(pipe=os.environ['PIPE_INSTRUMENT']))
		return('')

def parsehtml4websniff(htmlfilename, params):
	message = 'Parsing html address: {html}'
	print(message.format(html=htmlfilename))
	filename = re.sub('.*\/sniff\/*','',htmlfilename)
	filename = re.sub('\#\d+$','',filename)

	# Hack for Swope
	if os.environ['PIPE_INSTRUMENT']=='SWOPEDIRECT':
		sub = '(http|https)://ziggy.ucolick.org/gw/Swope'
		path = '/data/LCO/Swope/web'
		base = re.sub(sub, path, htmlfilename)
		path,file = os.path.split(base)
		return(path)
	else:
		error = 'ERROR: unrecognized PIPE_INSTRUMENT={pipe}'
		print(error.format(pipe=os.environ['PIPE_INSTRUMENT']))
		return('')

if __name__=='__main__':

	import optparse
	import configparser
	import sys
	
	usagestring = """getevents.py <options>

examples: 

python getevents.py -s settings.ini -i tmp.txt -o out.txt
python getevents.py -s ../../YSE_PZ/settings.ini -i tmp.txt -o out.txt

"""

	gw = GW2YSE()

	# read in the options from the param file and the command line
	# some convoluted syntax here, making it so param file is not required
	parser = gw.add_options(usage=usagestring)
	options,  args = parser.parse_args()
	if options.settingsfile:
		config = configparser.ConfigParser()
		config.read(options.settingsfile)
	else: config=None
	parser = gw.add_options(usage=usagestring,config=config)
	options,  args = parser.parse_args()
	gw.options = options
	gw.debug = options.debug
	
	listfilename = options.inlist
	outfile = options.outlist

	if gw.debug:
		gw.senddata(None,[],[],[])
	else:
		objs,ras,decs,datadictlist = gw.getdata(listfilename,outfile)
		gw.senddata(datadictlist,objs,ras,decs)
