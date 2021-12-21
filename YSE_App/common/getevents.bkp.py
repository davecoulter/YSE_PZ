#!/usr/bin/env python
# Python 2/3 compatibility
from __future__ import print_function
import re,sys,string,math,os,types,exceptions
from astropy.table import Table
import numpy as np

# put the tools directory into the path
pyscripts = os.environ['PIPE_PYTHONSCRIPTS']
sys.path.append(pyscripts+'/tools')
sys.path.append(pyscripts)
sys.path.append(os.path.join(pyscripts, os.environ['PIPENAME']))
sys.path.append(os.path.join(pyscripts, os.environ['PIPE_INSTRUMENT']))

import pipeclasses

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
		parser.add_option('-s','--settingsfile', default=None, type="string",
						  help='settings file (login/password info)')

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

	def getdata(self):
			
		if  os.environ['PIPE_INSTRUMENT']=='SWOPEDIRECT':
			import swopealerts as alerts
			temporaryalerts = alerts.swopealertclass()
			alerts = alerts.swopealertclass()
		else:
			error = 'ERROR: PIPE_INSTRUMENT={inst} is not recognized!'
			raise RuntimeError,error.format(inst=os.environ['PIPE_INSTRUMENT'])

		if (len(sys.argv)!=3):
			usage = 'USAGE: getevents.py websnifflist outlist'
			raise RuntimeError, usage

		listfilename = sys.argv[1]
		outfile = sys.argv[2]
		params = pipeclasses.paramfileclass()
		params.loadfile(os.getenv('PIPE_PARAMS'))

		# read the files
		lines=open(listfilename).readlines()

		outfmt = '{candID:<8} {ra:<14} {dec:<14} {mjd:<12} \n'
		outlist = [outfmt.format(candID='#candID',ra='RA',dec='DEC',mjd='MJD')]
		for line in lines:
			linebkp = line
			line = line.strip()
			line = re.sub('addevents.py','',line)
			line = re.sub('"','',line)
			line = line.strip()
			print('################################\n###  ADDING %s' % (line))
			m     = re.search('.*\#(\d+)$',line)
			if m:
				(candID,) = m.groups()
				candID = int(candID)
			else:
				f = open(sys.argv[1]+'.error','aw')
				f.write(linebkp)
				f.close()
				continue

			clusters = parsehtml4cluster(line, params)

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

			# Now get all of the MJDs from the filetable
			mjds = [float(filetable[filetable['cmpfile']==file]['MJD'][0]) for file in files]
			discovery_mjd = np.min(mjds)

			outlist.append(outfmt.format(candID=candID,
										 ra=RAaverage,
										 dec=DECaverage,
										 mjd=discovery_mjd))

		with open(outfile,'w') as f:
			for line in outlist:
				f.write(line)

	def senddata(self,datadict):

		TransientUploadDict = {}

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

		for j,jd in zip(range(len(objs)),json_data):
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
			if type(jd['data']['reply']['name']) == str:
				jd = jd['data']['reply']
			else:
				jd = None

			transientdict = self.getTNSData(jd,obj,sc,ebv)
			try:
				photdict = self.getZTFPhotometry(sc)
			except: photdict = None

			transientdict['gwcandidate'] = {'field_name':,'candidate_id':,'alt_transient_name':,
								   'transient':obj,'websniff_url':,'dophot_class':}
			transientdict['gwcandidate']['gwcandidateimages'] = {'alt_transient_name':,'image_filename':,'image_filter':}
			
			
			TransientUploadDict[obj] = transientdict

		TransientUploadDict['noupdatestatus'] = self.noupdatestatus
		self.UploadTransients(TransientUploadDict)
		
		return(len(TransientUploadDict))

				

	def UploadTransients(self,UploadDict):

		url = '%s'%self.dburl.replace('/api','/add_gw')
		r = requests.post(url = url, data = json.dumps(TransientUploadDict),
						  auth=HTTPBasicAuth(self.dblogin,self.dbpassword))
		
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
        path = '/data/LCO/Swope/web'
        source_path = params.get('WORKSPACE_DIR')
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

if __name__=='__main__':

	import optparse
	import configparser

	usagestring = "getevents.py <options>"

	gw = GW2YSE()

	# read in the options from the param file and the command line
	# some convoluted syntax here, making it so param file is not required
	parser = getevents.add_options(usage=usagestring)
	options,  args = parser.parse_args()
	if options.settingsfile:
		config = configparser.ConfigParser()
		config.read(options.settingsfile)
	else: config=None
	parser = getevents.add_options(usage=usagestring,config=config)
	options,  args = parser.parse_args()
	gw.options = options

	datadict = gw.getdata()
	gw.senddata(datadict)
