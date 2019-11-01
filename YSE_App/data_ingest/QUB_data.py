#!/usr/bin/env python
import requests
import json
import time
from requests.auth import HTTPBasicAuth
import astropy.table as at
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
import numpy as np
import coreapi

try:
  from dustmaps.sfd import SFDQuery
  sfd = SFDQuery()
except:
  raise RuntimeError("""can\'t import dust maps

run:
import dustmaps
import dustmaps.sfd
dustmaps.sfd.fetch()""")

def getRADecBox(ra,dec,size=None):
	RAboxsize = DECboxsize = size

	# get the maximum 1.0/cos(DEC) term: used for RA cut
	minDec = dec-0.5*DECboxsize
	if minDec<=-90.0:minDec=-89.9
	maxDec = dec+0.5*DECboxsize
	if maxDec>=90.0:maxDec=89.9

	invcosdec = max(1.0/np.cos(dec*np.pi/180.0),
					1.0/np.cos(minDec  *np.pi/180.0),
					1.0/np.cos(maxDec  *np.pi/180.0))

	ramin = ra-0.5*RAboxsize*invcosdec
	ramax = ra+0.5*RAboxsize*invcosdec
	decmin = dec-0.5*DECboxsize
	decmax = dec+0.5*DECboxsize

	if ra<0.0: ra+=360.0
	if ra>=360.0: ra-=360.0

	if ramin!=None:
		if (ra-ramin)<-180:
			ramin-=360.0
			ramax-=360.0
		elif (ra-ramin)>180:
			ramin+=360.0
			ramax+=360.0
	return(ramin,ramax,decmin,decmax)


def get_ps_score(RA, DEC):
	'''Get ps1 star/galaxy score from MAST. Provide RA and DEC in degrees.
	Returns an empty string if no match is found witing 3 arcsec.
	'''
	# get the WSID and password if not already defined
	# get your WSID by going to https://mastweb.stsci.edu/ps1casjobs/changedetails.aspx after you login to Casjobs.

	os.environ['CASJOBS_WSID'] = str(1862226089)
	os.environ['CASJOBS_PW'] = 'tr4nsientsP!z'
	query = """select top 1 p.ps_score
	from pointsource_magnitudes_view as p
	inner join fGetNearbyObjEq(%.5f, %.5f, 0.05) nb on p.objid=nb.objid
	""" %(RA, DEC)

	jobs = mastrequests.MastCasJobs(context="HLSP_PS1_PSC")
	results = jobs.quick(query, task_name="python cross-match")

	output = results.split('\n')[1]
	if not output:
		output = None
	else:
		output = round(float(output), 3)
		print('PS_SCORE: %.3f' %output)

	return output

class QUB:
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
		parser.add_option('-s','--settingsfile', default=None, type="string",
						  help='settings file (login/password info)')
		parser.add_option('--status', default='New', type="string",
						  help='transient status to enter in YS_PZ')
		parser.add_option('--max_days', default=7, type="float",
						  help='grab photometry/objects from the last x days')

		if config:
			parser.add_option('--dblogin', default=config.get('main','dblogin'), type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbemail', default=config.get('main','dbemail'), type="string",
							  help='database login, if post=True (default=%default)')
			parser.add_option('--dbpassword', default=config.get('main','dbpassword'), type="string",
							  help='database password, if post=True (default=%default)')
			parser.add_option('--dburl', default=config.get('main','dburl'), type="string",
							  help='URL to POST transients to a database (default=%default)')
			parser.add_option('--ztfurl', default=config.get('main','ztfurl'), type="string",
							  help='ZTF URL (default=%default)')
			parser.add_option('--qubuser', default=config.get('main','qubuser'), type="string",
							  help='QUB database username (default=%default)')
			parser.add_option('--qubpass', default=config.get('main','qubpass'), type="string",
							  help='QUB database password (default=%default)')
			parser.add_option('--psstlink_summary', default=config.get('main','psstlink_summary'), type="string",
							  help='PSST summary CSV (default=%default)')
			parser.add_option('--psstlink_lc', default=config.get('main','psstlink_lc'), type="string",
							  help='PSST lightcurve CSV (default=%default)')
			parser.add_option('--ztfurl', default=config.get('main','ztfurl'), type="string",
							  help='ZTF URL (default=%default)')

			
			parser.add_option('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type="string",
							  help='SMTP login (default=%default)')
			parser.add_option('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type="string",
							  help='SMTP host (default=%default)')
			parser.add_option('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type="string",
							  help='SMTP port (default=%default)')
		else:
			pass


		return(parser)

	def main(self):
		transientdict,nsn = self.parse_data()
		self.send_data(transientdict)
		return nsn
		
	def parse_data(self):
		# today's date
		nowmjd = Time.now().mjd
		
		# grab CSV files
		r = requests.get(url=self.options.psstlink_summary,
						 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
		if r.status_code != 200: raise RuntimeError('problem accessing summary link %s'%self.options.psstlink_summary)
		summary = at.Table.read(r.text, format='ascii', delimiter='|')

		r = requests.get(url=self.options.psstlink_lc,
						 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
		if r.status_code != 200: raise RuntimeError('problem accessing lc link %s'%self.options.psstlink_summary)
		lc = at.Table.read(r.text, format='ascii', delimiter='|')

		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0
		for i,s in enumerate(summary):
			if nowmjd - s['mjd_obs'] > self.options.max_days: continue
			if nsn > 100: break
			#if nsn < 20:
			#	nsn += 1
			#	continue
			
			sc = SkyCoord(s['ra_psf'],s['dec_psf'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))

			iLC = (lc['ps1_designation'] == s['ps1_designation']) & (nowmjd - lc['mjd_obs'] < self.options.max_days)
			tdict = {'name':s['ps1_designation'],
					 'ra':s['ra_psf'],
					 'dec':s['dec_psf'],
					 'obs_group':'PSST',
					 'status':self.options.status,
					 #'best_spec_class':s['context_classification'],
					 #'host':s['host'],
					 'tags':['PSST'],
					 'disc_date':mjd_to_date(s['mjd_obs']),
					 'mw_ebv':mw_ebv,
					 'point_source_probability':ps_prob}
			obj += [s['ps1_designation']]
			ra += [s['ra_psf']]
			dec += [s['dec_psf']]

			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":self.options.clobber}
			photometrydict = {'instrument':'GPC1',
							  'obs_group':'PSST',
							  'photdata':{}}
			for j,l in enumerate(lc[iLC]):
				if j == 0: disc_point = 1
				else: disc_point = 0

				flux = 10**(0.4*(l['cal_psf_mag']-27.5))
				flux_err = np.log(10)*0.4*flux*l['psf_inst_mag_sig']

				phot_upload_dict = {'obs_date':mjd_to_date(l['mjd_obs']),
									'band':l['filter'],
									'groups':[],
									'mag':l['cal_psf_mag'],
									'mag_err':l['psf_inst_mag_sig'],
									'flux':flux,
									'flux_err':flux_err,
									'data_quality':0,
									'forced':0,
									'flux_zero_point':27.5,
									'discovery_point':disc_point,
									'diffim':1}

				photometrydict['photdata']['%s_%i'%(mjd_to_date(l['mjd_obs']),j)] = phot_upload_dict

			PhotUploadAll['PS1'] = photometrydict
			transientdict[s['ps1_designation']] = tdict
			transientdict[s['ps1_designation']]['transientphotometry'] = PhotUploadAll
			#import pdb; pdb.set_trace()
			nsn += 1
			#transientdict = self.getZTFPhotometry(transientdict,s['ra_psf'],s['dec_psf'])
			
			#transientdict['transientphotometry'] = photometrydict
		#import pdb; pdb.set_trace()
		#scall = SkyCoord(ra,dec,unit=u.deg) #summary['ra_psf'],summary['dec_psf']
		#transientdict = self.getZTFPhotometry(transientdict,obj,scall)
		#import pdb; pdb.set_trace()
		return transientdict,nsn

	#def getZTFPhotometry(self,transientdict,ra,dec):
	#	nowjd = Time.now().jd
	#	nowmjd = Time.now().mjd

	#	ramin,ramax,decmin,decmax = getRADecBox(ra,dec,size=0.00042)
		
	#	antares_query = {
	#		"query": {
	#			"bool": {
	#				"must": [
	#					{
	#						"range": {
	#							"mjd": {
	#								"gte": nowmjd-7,
	#								"lte": nowmjd+1,
	#							}
	#						}
	#					},
	#					{
	#						"range": {
	#							"ra": {
	#								"gte": ramin,
	#								"lte": ramax,
	#							}
	#						}
	#					},
	#					{
	#						"range": {
	#							"dec": {
	#								"gte": decmin,
	#								"lte": decmax,
	#							}
	#						}
	#					}
    #
	#				]
    #
    #				}
#				}
#			}
#		query_test = {
#			"query": {
#				"bool": {
#					"must": [
#						{
#							"range": {
#								"ra": {
#									"gte": 109.9,
#									"lte": 110.1,
#								}
#							}
#						},
#						{
#							"range": {
#								"properties.ztf_rb": {
#									"gte": 0.9,
#								}
#							}
#						}
#					]
#				}
#			}
#		}
#		
#		from antares_client.search import search
#		import time
#		tstart = time.time()
#		print('starting query')
#		result_set = search(antares_query)
#		print('query took %i seconds'%(time.time()-tstart))
#		import pdb; pdb.set_trace()
#		#antares = 
#		
#		ztfurl = '%s/?format=json&sort_value=jd&sort_order=desc&jd_gt=%i&limit=1000'%(
#			self.options.ztfurl,nowjd-self.options.max_days)
#		client = coreapi.Client()
#		schema = client.get(ztfurl)
#		photometrydict = {}
#		if 'results' in schema.keys():
#			import pdb; pdb.set_trace()
#			for i in range(len(schema['results'])):
#				
#				sc = SkyCoord(schema['results'][i]['candidate']['ra'],schema['results'][i]['candidate']['dec'],unit=u.deg)
#				sep = sc.separation(scall)
#				if np.min(sep.arcsec) > 2: continue
#				import pdb; pdb.set_trace()
#				transient = obj[sep == np.min(sep)]
#				if transient not in photometrydict.keys(): photometrydict[transient] = {}
#				
#				phot = schema['results'][i]['candidate']
#				if phot['isdiffpos'] == 'f':
#					continue
#				PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
#								  'band':'%s-ZTF'%phot['filter'],
#								  'groups':[]}
#				PhotUploadDict['mag'] = phot['magap']
#				PhotUploadDict['mag_err'] = phot['sigmagap']
#				PhotUploadDict['flux'] = None
#				PhotUploadDict['flux_err'] = None
#				PhotUploadDict['data_quality'] = 0
#				PhotUploadDict['forced'] = None
#				PhotUploadDict['flux_zero_point'] = None
#				PhotUploadDict['discovery_point'] = 0
#				PhotUploadDict['diffim'] = 1
#
#				photometrydict[transient]['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict
#
#			for transient in photometrydict.keys():
#				photometrydict = {'instrument':'ZTF-Cam',
#								  'obs_group':'ZTF',
#								  'photdata':{}}
#				transientdict[transient]['transientphotometry']['ZTF'] = photometrydict
#				for k in photometrydict[transient].keys():
#					transientdict[transient]['transientphotometry']['ZTF']['photdata'][k] = photometrydict[transient][k]
#			#transientdict[transient]['transientphotometry']['ZTF'] = photometrydict
#			return transientdict
#
#		else: return None

	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True #self.options.noupdatestatus
		self.UploadTransients(TransientUploadDict)

	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		r = requests.post(url = url, data = json.dumps(TransientUploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

		try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		except: print(r.text)
		print("Process done.")
	
def jd_to_date(jd):
	time = Time(jd,scale='utc',format='jd')
	return time.isot

def date_to_mjd(obs_date):
	time = Time(obs_date,scale='utc')
	return time.mjd

def mjd_to_date(obs_mjd):
	time = Time(obs_mjd,scale='utc',format='mjd')
	return time.isot


def fetch(url):
	urlresponse = None
	count = 0
	while not urlresponse and count < 3:
		try:
			urlresponse = urllib.request.urlopen(url).read()
			return url, urlresponse
		except Exception as e:
			pass
		count += 1

	print('URL %s failed after 3 tries'%(url))
	return url, None

def run_parallel_in_threads(target, args_list):
	result = queue.Queue()
	# wrapper to collect return value in a Queue
	def task_wrapper(*args):
		result.put(target(*args))
	threads = [threading.Thread(target=task_wrapper, args=args) for args in args_list]
	for t in threads:
		t.start()
	for t in threads:
		t.join()
	return result


def sendemail(from_addr, to_addr,
			subject, message,
			login, password, smtpserver, cc_addr=None):

	print("Preparing email")

	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = from_addr
	msg['To'] = to_addr
	payload = MIMEText(message, 'html')
	msg.attach(payload)

	with smtplib.SMTP(smtpserver) as server:
		try:
			server.starttls()
			server.login(login, password)
			resp = server.sendmail(from_addr, [to_addr], msg.as_string())
			print("Send success")
		except:
			print("Send fail")

def format_to_json(source):
	# change data to json format and return
	parsed=json.loads(source,object_pairs_hook=OrderedDict)
	#result=json.dumps(parsed,indent=4)
	return parsed #result

def get(url,json_list,api_key):
	try:
		# url for get obj
		get_url=url+'/object'
		# change json_list to json format
		json_file=OrderedDict(json_list)
		# construct the list of (key,value) pairs
		get_data=[('api_key',(None, api_key)),
				  ('data',(None,json.dumps(json_file)))]
		# get obj using request module
		response=requests.post(get_url, files=get_data)
		return response
	except Exception as e:
		return [None,'Error message : \n'+str(e)]

	
if __name__ == """__main__""":

	import optparse
	import configparser

	usagestring = "TNS_Synopsis.py <options>"

	tstart = time.time()
	qub = QUB()

	# read in the options from the param file and the command line
	# some convoluted syntax here, making it so param file is not required
	parser = qub.add_options(usage=usagestring)
	options,  args = parser.parse_args()
	if options.settingsfile:
		config = configparser.ConfigParser()
		config.read(options.settingsfile)
	else: config=None
	parser = qub.add_options(usage=usagestring,config=config)
	options,  args = parser.parse_args()
	qub.options = options
	#tnsproc.hostmatchrad = options.hostmatchrad
	
	if "hi": #try:
		nsn = qub.main()
	else: #except Exception as e:
		nsn = 0
		from django.conf import settings as djangoSettings
		smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
		from_addr = "%s@gmail.com" % options.SMTP_LOGIN
		subject = "QUB Transient Upload Failure"
		print("Sending error email")
		html_msg = "Alert : YSE_PZ Failed to upload transients\n"
		html_msg += "Error : %s"
		sendemail(from_addr, options.dbemail, subject,
				  html_msg%(e),
				  options.SMTP_LOGIN, options.dbpassword, smtpserver)

	print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))
