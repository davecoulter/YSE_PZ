#!/usr/bin/env python
import requests
import urllib
import json
import time
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import astropy.table as at
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
import numpy as np
import coreapi
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
import argparse
import configparser
import os
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from io import open as iopen
import datetime
import dateutil
from django.db.models import Q
from YSE_App.models import Transient, TransientTag
import sys

from string import ascii_lowercase
import itertools
from YSE_App.common.utilities import getRADecBox

def iter_all_strings():
	for size in itertools.count(1):
		for s in itertools.product(ascii_lowercase, repeat=size):
			yield "".join(s)

#psst_image_url = "https://star.pst.qub.ac.uk/sne/ps13pi/site_media/images/data/ps13pi"
#yse_image_url = "https://star.pst.qub.ac.uk/sne/ps1yse/site_media/images/data/ps1yse"
psst_image_url = "https://psweb.mp.qub.ac.uk/sne/ps13pi/site_media/images/data/ps13pi"
yse_image_url = "https://psweb.mp.qub.ac.uk/sne/ps1yse/site_media/images/data/ps1yse"

try:
  from dustmaps.sfd import SFDQuery
  sfd = SFDQuery()
except:
  raise RuntimeError("""can\'t import dust maps

run:
import dustmaps
import dustmaps.sfd
dustmaps.sfd.fetch()""")

def fluxToMicroJansky(adu, exptime, zp):
	factor = 10**(-0.4*(zp-23.9))
	uJy = adu/exptime*factor
	return uJy

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

class QUB(CronJobBase):

	RUN_EVERY_MINS = 120

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.QUB_data.QUB'

	def do(self):

		usagestring = "TNS_Synopsis.py <options>"

		tstart = time.time()

		# read in the options from the param file and the command line
		# some convoluted syntax here, making it so param file is not required

		parser = self.add_options(usage=usagestring)
		options,  args = parser.parse_known_args()

		config = configparser.ConfigParser()
		config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
		parser = self.add_options(usage=usagestring,config=config)
		options,  args = parser.parse_known_args()
		self.options = options
		#tnsproc.hostmatchrad = options.hostmatchrad

		try:
			nsn = self.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "QUB Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients from PSST in QUB_data.py\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

		print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


	def add_options(self, parser=None, usage=None, config=None):
		import argparse
		if parser == None:
			parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

		# The basics
		parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_argument('--clobber', default=False, action="store_true",
						  help='clobber output file')
		parser.add_argument('-s','--settingsfile', default=None, type=str,
						  help='settings file (login/password info)')
		parser.add_argument('--status', default='New', type=str,
						  help='transient status to enter in YS_PZ')
		parser.add_argument('--max_days', default=7, type=float,
						  help='grab photometry/objects from the last x days')

		if config:
			parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
							  help='database password, if post=True (default=%default)')
			parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
							  help='email password, if post=True (default=%default)')
			parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
							  help='URL to POST transients to a database (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')
			parser.add_argument('--STATIC', default=config.get('site_settings','STATIC'), type=str,
							  help='static directory (default=%default)')
			parser.add_argument('--qubuser', default=config.get('main','qubuser'), type=str,
							  help='QUB database username (default=%default)')
			parser.add_argument('--qubpass', default=config.get('main','qubpass'), type=str,
							  help='QUB database password (default=%default)')
			parser.add_argument('--psstlink_summary', default=config.get('main','psstlink_summary'), type=str,
							  help='PSST summary CSV (default=%default)')
			parser.add_argument('--psstlink_lc', default=config.get('main','psstlink_lc'), type=str,
							  help='PSST lightcurve CSV (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')

			
			parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
							  help='SMTP login (default=%default)')
			parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
							  help='SMTP host (default=%default)')
			parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
							  help='SMTP port (default=%default)')

			parser.add_argument('--max_days', default=config.get('main','max_days_qub'), type=float,
								help='grab photometry/objects from the last x days')

		else:
			pass


		return(parser)

	def main(self):

		# grab CSV files
		r = requests.get(url=self.options.psstlink_summary,
						 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
		if r.status_code != 200: raise RuntimeError('problem accessing summary link %s'%self.options.yselink_summary)
		summary = at.Table.read(r.text, format='ascii.csv', delimiter='|')

		r = requests.get(url=self.options.psstlink_lc,
						 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
		if r.status_code != 200: raise RuntimeError('problem accessing lc link %s'%self.options.yselink_summary)
		lc = at.Table.read(r.text, format='ascii.csv', delimiter='|')

		nsn = 0
		nsn_single = 25


		nowmjd = Time.now().mjd
		summary_upload = summary[nowmjd - summary['mjd_obs'] < self.options.max_days]

		while nsn_single == 25:
			transientdict,nsn_single = self.parse_data(summary_upload,lc,transient_idx=nsn,max_transients=25)
			print('uploading %i transients'%nsn_single)
			self.send_data(transientdict)
			self.copy_stamps(transientdict)
			nsn += 25
		
	def parse_data(self,summary,lc,transient_idx=0,max_transients=None):
		# today's date
		nowmjd = Time.now().mjd
		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0

		for i,s in enumerate(summary[transient_idx:transient_idx+max_transients]):
			
			sc = SkyCoord(s['ra_psf'],s['dec_psf'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))

			iLC = (lc['ps1_designation'] == s['ps1_designation']) & (nowmjd - lc['mjd_obs'] < self.options.max_days)

			if nowmjd - Time('%s 00:00:00'%s['followup_flag_date'],format='iso',scale='utc').mjd > self.options.max_days:
				status = 'Ignore'
			else:
				status = self.options.status

			tdict = {'name':s['ps1_designation'],
					 'ra':s['ra_psf'],
					 'dec':s['dec_psf'],
					 'obs_group':'PSST',
					 'postage_stamp_file':'%s/%s/%s.jpeg'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['target']),
					 'postage_stamp_ref':'%s/%s/%s.jpeg'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['ref']),
					 'postage_stamp_diff':'%s/%s/%s.jpeg'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['diff']),
					 'postage_stamp_file_fits':'%s/%s/%s.fits'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['target']),
					 'postage_stamp_ref_fits':'%s/%s/%s.fits'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['ref']),
					 'postage_stamp_diff_fits':'%s/%s/%s.fits'%(s['ps1_designation'],s['target'].split('_')[1].split('.')[0],s['diff']),
					 'status':status,
					 #'host':s['host'],
					 'tags':['PSST'],
					 'disc_date':s['followup_flag_date'],
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
			for j,l in enumerate(lc[iLC][np.argsort(lc['mjd_obs'][iLC])]):
				if j == 0 and np.abs(date_to_mjd(s['followup_flag_date'])-l['mjd_obs']) < 1: disc_point = 1
				else: disc_point = 0

				flux = 10**(-0.4*(l['cal_psf_mag']-27.5))
				flux_err = np.log(10)*0.4*flux*l['psf_inst_mag_sig']
				if type(l['psf_inst_mag_sig']) == np.ma.core.MaskedConstant:
					mag_err = 0
					flux_err = 0
				else:
					mag_err = l['psf_inst_mag_sig']

				phot_upload_dict = {'obs_date':mjd_to_date(l['mjd_obs']),
									'band':l['filter'],
									'groups':[],
									'mag':l['cal_psf_mag'],
									'mag_err':mag_err,
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

			photometrydict_ztf = self.getZTFPhotometry(s['ra_psf'],s['dec_psf'])
			if photometrydict_ztf is not None:
				PhotUploadAll['ZTF'] = photometrydict_ztf
			
			nsn += 1

		return transientdict,nsn

	def getZTFPhotometry(self,ra,dec):

		ztfurl = '%s/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(
			self.options.ztfurl,ra,dec)
		client = coreapi.Client()
		schema = client.get(ztfurl)
		if 'results' in schema.keys():
			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":self.options.clobber}
			photometrydict = {'instrument':'ZTF-Cam',
							  'obs_group':'ZTF',
							  'photdata':{}}

			for i in range(len(schema['results'])):
				phot = schema['results'][i]['candidate']
				if phot['isdiffpos'] == 'f':
					continue
				PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
								  'band':'%s-ZTF'%phot['filter'],
								  'groups':[]}
				PhotUploadDict['mag'] = phot['magpsf']
				PhotUploadDict['mag_err'] = phot['sigmapsf']
				PhotUploadDict['flux'] = None
				PhotUploadDict['flux_err'] = None
				PhotUploadDict['data_quality'] = 0
				PhotUploadDict['forced'] = None
				PhotUploadDict['flux_zero_point'] = None
				PhotUploadDict['discovery_point'] = 0
				PhotUploadDict['diffim'] = 1

				photometrydict['photdata']['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict

			return photometrydict

		else: return None

	
	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True
		self.UploadTransients(TransientUploadDict)

	def copy_stamps(self,transientdict):
		try:
			if not djangoSettings.DEBUG: basedir = "%sYSE_App/images/stamps"%(djangoSettings.STATIC_ROOT)
			else: basedir = "%s/YSE_App%sYSE_App/images/stamps"%(djangoSettings.BASE_DIR,self.options.STATIC)
			for k in transientdict.keys():
				if k == 'noupdatestatus': continue
				if k == 'TNS': continue
				if not os.path.exists("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref']))):
					os.makedirs("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref'])))

					# only download the files if the directory didn't exist before now.	 AKA, don't
					# continuously grab new stamps
					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_ref'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_diff'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_file'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_ref_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_diff_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits'])):
						r = requests.get(
							"%s/%s"%(psst_image_url,transientdict[k]['postage_stamp_file_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits']), 'wb') as fout:
							fout.write(r.content)

		except Exception as e:
			print(e)
						
	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		r = requests.post(url = url, data = json.dumps(TransientUploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

		try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		except: print(r.text)
		print("Process done.")

class YSE(CronJobBase):

	RUN_EVERY_MINS = 30

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.QUB_data.YSE'

	def do(self):

		print("starting YSE ingest at {}".format(datetime.datetime.now().isoformat()))
		usagestring = "TNS_Synopsis.py <options>"

		tstart = time.time()

		# read in the options from the param file and the command line
		# some convoluted syntax here, making it so param file is not required
		try:
			parser = self.add_options(usage=usagestring)
			options,  args = parser.parse_known_args()

			config = configparser.ConfigParser()
			config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
			parser = self.add_options(usage=usagestring,config=config)
			options,  args = parser.parse_known_args()
			self.options = options

			nsn = self.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "QUB Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients from YSE in QUB_data.py\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

		print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


	def add_options(self, parser=None, usage=None, config=None):
		import argparse
		if parser == None:
			parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

		# The basics
		parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_argument('--clobber', default=False, action="store_true",
						  help='clobber output file')
		parser.add_argument('-s','--settingsfile', default=None, type=str,
						  help='settings file (login/password info)')
		parser.add_argument('--status', default='New', type=str,
						  help='transient status to enter in YS_PZ')

		if config:
			parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
							  help='database password, if post=True (default=%default)')
			parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
							  help='email password, if post=True (default=%default)')
			parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
							  help='URL to POST transients to a database (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')
			parser.add_argument('--STATIC', default=config.get('site_settings','STATIC'), type=str,
							  help='static directory (default=%default)')
			parser.add_argument('--qubuser', default=config.get('main','qubuser'), type=str,
							  help='QUB database username (default=%default)')
			parser.add_argument('--qubpass', default=config.get('main','qubpass'), type=str,
							  help='QUB database password (default=%default)')
			parser.add_argument('--yselink_summary', default=config.get('main','yselink_summary'), type=str,
							  help='YSE summary CSV (default=%default)')
			parser.add_argument('--yselink_lc', default=config.get('main','yselink_lc'), type=str,
							  help='YSE lightcurve CSV (default=%default)')
			parser.add_argument('--yselink_genericsummary', default=config.get('main','yselink_genericsummary'), type=str,
							  help='YSE summary CSV for possible candidates (default=%default)')
			parser.add_argument('--yselink_genericlc', default=config.get('main','yselink_genericlc'), type=str,
							  help='YSE lightcurve CSV for possible candidates (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')

			
			parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
							  help='SMTP login (default=%default)')
			parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
							  help='SMTP host (default=%default)')
			parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
							  help='SMTP port (default=%default)')

			parser.add_argument('--max_days', default=config.get('main','max_days_yse'), type=float,
								help='grab photometry/objects from the last x days')

		else:
			pass


		return(parser)

	def main(self):

		# get things with YSE Forced flag but no YSE flag
		urlbase = self.options.dburl.replace('/api/','')
		querytitle = 'YSE forced photometry for non-YSE, non-Antares transients'
		r = requests.get('%s/query_api/%s/'%(urlbase,urllib.parse.quote(querytitle)),
						 auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
		data = json.loads(r.text)
		
		nsn = 0
		for yselink_summary, yselink_lc, namecol in zip([self.options.yselink_summary,self.options.yselink_genericsummary],
														[self.options.yselink_lc,self.options.yselink_genericlc],
														['ps1_designation','local_designation']):
			# grab CSV files
			r = requests.get(url=yselink_summary,
							 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
			#import pdb; pdb.set_trace()
			if r.status_code != 200: raise RuntimeError('problem accessing summary link %s'%self.options.yselink_summary)
			try: summary = at.Table.read(r.text, format='ascii', delimiter='|')
			except: continue
			
			r = requests.get(url=yselink_lc,
							 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
			if r.status_code != 200: raise RuntimeError('problem accessing lc link %s'%self.options.yselink_summary)
			try: lc = at.Table.read(r.text, format='ascii', delimiter='|')
			except: continue

			nsn = 0
			nsn_single = 25

			scall = SkyCoord(summary['ra_psf'],summary['dec_psf'],unit=u.deg)
			iSummary = np.array([],dtype=int)
			for d in data['transients']:
				sc = SkyCoord(d['ra'],d['dec'],unit=u.deg)
				sep = sc.separation(scall).arcsec
				if np.min(sep) < 5:
					iSummary = np.append(iSummary,np.where(sep < 5)[0])
			
			nowmjd = Time.now().mjd
			#summary = summary[nowmjd - summary['mjd_obs'] < self.options.max_days]
			iSummary = np.append(iSummary,np.where(nowmjd - summary['mjd_obs'] < self.options.max_days)[0])
			summary_upload = summary[iSummary]
			while nsn_single == 25:
				transientdict,nsn_single = self.parse_data(summary_upload,lc,transient_idx=nsn,max_transients=25)
				print('uploading %i transients'%nsn_single)
				self.send_data(transientdict)
				self.copy_stamps(transientdict)
				nsn += 25

		return nsn
		
	def parse_data(self,summary,lc,transient_idx=0,max_transients=None):
		# today's date
		nowmjd = Time.now().mjd

		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0

		for i,s in enumerate(summary[transient_idx:transient_idx+max_transients]):

			r = requests.get(url='https://psweb.mp.qub.ac.uk/sne/ps1yse/psdb/lightcurveforced/%s'%s['id'])
			#r = requests.get(url='https://star.pst.qub.ac.uk/sne/ps1yse/psdb/lightcurveforced/%s'%s['id'])

			if r.status_code != 200: raise RuntimeError('problem accessing lc link %s'%self.options.yselink_summary)
			try:
				lc_forced = at.Table.read(r.text, format='ascii', delimiter=' ')
				if len(lc_forced): has_forced_phot = True
				else: has_forced_phot = False
			except:
				has_forced_phot = False


			sc = SkyCoord(s['ra_psf'],s['dec_psf'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))

			iLC = (lc['local_designation'] == s['local_designation']) & (nowmjd - lc['mjd_obs'] < self.options.max_days)

			if nowmjd - Time('%s 00:00:00'%s['followup_flag_date'],format='iso',scale='utc').mjd > self.options.max_days+7:
				status = 'Ignore'
			else:
				status = self.options.status

			if type(s['target']) == np.ma.core.MaskedConstant:
				postage_stamp_file = ''
				postage_stamp_ref = ''
				postage_stamp_diff = ''
				postage_stamp_file_fits = ''
				postage_stamp_ref_fits = ''
				postage_stamp_diff_fits = ''
			else:
				postage_stamp_file = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['target'])
				postage_stamp_ref = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['ref'])
				postage_stamp_diff = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['diff'])
				postage_stamp_file_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['target'])
				postage_stamp_ref_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['ref'])
				postage_stamp_diff_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['diff'])

			if type(s['sherlock_specz']) == np.ma.core.MaskedConstant:
				redshift = None
			else:
				redshift = s['sherlock_specz']

			if type(s['sherlock_object_id']) == np.ma.core.MaskedConstant:
				hostdict = {}
			else:
				hostdict = {'name':s['sherlock_object_id'][:64],
							'ra':s['sherlock_host_ra'],
							'dec':s['sherlock_host_dec'],
							'redshift':redshift}
			if type(s['rb_factor_image']) == np.ma.core.MaskedConstant:
				rb_factor = None
			else:
				rb_factor = s['rb_factor_image']

			tdict = {'name':s['local_designation'],
					 'ra':s['ra_psf'],
					 'dec':s['dec_psf'],
					 'obs_group':'YSE',
					 'postage_stamp_file':postage_stamp_file,
					 'postage_stamp_ref':postage_stamp_ref,
					 'postage_stamp_diff':postage_stamp_diff,
					 'postage_stamp_file_fits':postage_stamp_file_fits,
					 'postage_stamp_ref_fits':postage_stamp_ref_fits,
					 'postage_stamp_diff_fits':postage_stamp_diff_fits,
					 'status':status,
					 'context_class':s['sherlockClassification'].replace('UNCLEAR','Unknown'),
					 'host':hostdict,
					 'tags':['YSE'],
					 'disc_date':s['followup_flag_date'],
					 'mw_ebv':mw_ebv,
					 'point_source_probability':ps_prob,
					 'real_bogus_score':rb_factor}

			obj += [s['local_designation']]
			ra += [s['ra_psf']]
			dec += [s['dec_psf']]

			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":self.options.clobber}
			photometrydict = {'instrument':'GPC1',
							  'obs_group':'YSE',
							  'photdata':{}}
			if has_forced_phot:
				for j,lf in enumerate(lc_forced[np.argsort(lc_forced['mjd'])]):
					if j == 0 and np.abs(date_to_mjd(s['followup_flag_date'])-lf['mjd']) < 1: disc_point = 1
					else: disc_point = 0

					if lf['cal_psf_mag'] == 'None':
						forced_mag,forced_mag_err = None,None
					else:
						forced_mag,forced_mag_err = lf['cal_psf_mag'],lf['psf_inst_mag_sig']

					# forced photometry
					phot_upload_dict = {'obs_date':mjd_to_date(lf['mjd']),
										'band':lf['filter'],
										'groups':['YSE'],
										'mag':forced_mag,
										'mag_err':forced_mag_err,
										'flux':fluxToMicroJansky(lf['psf_inst_flux'],27.0,lf['zero_pt'])*10**(0.4*(27.5-23.9)),
										'flux_err':fluxToMicroJansky(lf['psf_inst_flux_sig'],27.0,lf['zero_pt'])*10**(0.4*(27.5-23.9)),
										'data_quality':0,
										'forced':1,
										'flux_zero_point':27.5,
										'discovery_point':disc_point,
										'diffim':1}
					photometrydict['photdata']['%s_%i'%(mjd_to_date(lf['mjd']),j)] = phot_upload_dict


			for j,l in enumerate(lc[iLC][np.argsort(lc['mjd_obs'][iLC])]):
				if has_forced_phot and np.min(np.abs(lc_forced['mjd']-l['mjd_obs'])) < 0.01: continue
				if j == 0 and np.abs(date_to_mjd(s['followup_flag_date'])-l['mjd_obs']) < 1: disc_point = 1
				else: disc_point = 0

				flux = 10**(-0.4*(l['cal_psf_mag']-27.5))
				flux_err = np.log(10)*0.4*flux*l['psf_inst_mag_sig']
				if type(l['psf_inst_mag_sig']) == np.ma.core.MaskedConstant:
					mag_err = 0
					flux_err = 0
				else:
					mag_err = l['psf_inst_mag_sig']

				# unforced photometry
				phot_upload_dict = {'obs_date':mjd_to_date(l['mjd_obs']),
									'band':l['filter'],
									'groups':'YSE',
									'mag':l['cal_psf_mag'],
									'mag_err':mag_err,
									'flux':flux,
									'flux_err':flux_err,
									'data_quality':0,
									'forced':0,
									'flux_zero_point':27.5,
									'discovery_point':disc_point,
									'diffim':1}

				photometrydict['photdata']['%s_%i'%(mjd_to_date(l['mjd_obs']),j)] = phot_upload_dict

			PhotUploadAll['PS1'] = photometrydict
			transientdict[s['local_designation']] = tdict
			transientdict[s['local_designation']]['transientphotometry'] = PhotUploadAll

			photometrydict_ztf = self.getZTFPhotometry(s['ra_psf'],s['dec_psf'])
			if photometrydict_ztf is not None:
				PhotUploadAll['ZTF'] = photometrydict_ztf

			nsn += 1

		return transientdict,nsn

	def getZTFPhotometry(self,ra,dec):

		ztfurl = '%s/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(
			self.options.ztfurl,ra,dec)
		client = coreapi.Client()
		schema = client.get(ztfurl)
		if 'results' in schema.keys():
			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":False}
			photometrydict = {'instrument':'ZTF-Cam',
							  'obs_group':'ZTF',
							  'photdata':{}}

			for i in range(len(schema['results'])):
				phot = schema['results'][i]['candidate']
				if phot['isdiffpos'] == 'f':
					continue
				PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
								  'band':'%s-ZTF'%phot['filter'],
								  'groups':[]}
				PhotUploadDict['mag'] = phot['magpsf']
				PhotUploadDict['mag_err'] = phot['sigmapsf']
				PhotUploadDict['flux'] = None
				PhotUploadDict['flux_err'] = None
				PhotUploadDict['data_quality'] = 0
				PhotUploadDict['forced'] = None
				PhotUploadDict['flux_zero_point'] = None
				PhotUploadDict['discovery_point'] = 0
				PhotUploadDict['diffim'] = 1

				photometrydict['photdata']['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict

			return photometrydict

		else: return None

	
	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True
		self.UploadTransients(TransientUploadDict)

	def copy_stamps(self,transientdict):
		try:
			if not djangoSettings.DEBUG: basedir = "%sYSE_App/images/stamps"%(djangoSettings.STATIC_ROOT)
			else: basedir = "%s/YSE_App%sYSE_App/images/stamps"%(djangoSettings.BASE_DIR,self.options.STATIC)
			for k in transientdict.keys():
				if k == 'noupdatestatus': continue
				if k == 'TNS': continue
				if not os.path.exists("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref']))):
					os.makedirs("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref'])))

					# only download the files if the directory didn't exist before now.	 AKA, don't
					# continuously grab new stamps
					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_ref'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_diff'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_file'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_ref_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_diff_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_file_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits']), 'wb') as fout:
							fout.write(r.content)

		except Exception as e:
			print(e)

	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		try:
			r = requests.post(url = url, data = json.dumps(TransientUploadDict),
							  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword),
							  timeout=60)
			try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
			except: print(r.text)
			print("Process done.")

		except Exception as e:
			print("Error: %s"%e)

def get_next_name(current_name,ttype='Stack',year=None):
	start = False
	current_str = current_name.replace('YSE%s%s'%(ttype,year),'')
	for s in itertools.islice(iter_all_strings(), 20000):
		if start == True:
			next_name = 'YSE%s%s%s'%(ttype,year,s)
			break
		if current_str == s:
			start = True
	try: return next_name
	except:
		print('Error : next_name is not defined on string %s!'%s)
		raise RuntimeError('Error : next_name is not defined on string %s!'%s)

class YSE_Stack(CronJobBase):

	RUN_EVERY_MINS = 30

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.QUB_data.YSE_Stack'

	def do(self):

		print("starting YSE ingest at {}".format(datetime.datetime.now().isoformat()))
		usagestring = "TNS_Synopsis.py <options>"

		tstart = time.time()

		# read in the options from the param file and the command line
		# some convoluted syntax here, making it so param file is not required
		try:
			parser = self.add_options(usage=usagestring)
			options,  args = parser.parse_known_args()

			config = configparser.ConfigParser()
			config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
			parser = self.add_options(usage=usagestring,config=config)
			options,  args = parser.parse_known_args()
			self.options = options

			nsn = self.main()
		except Exception as e:
			print(e)
			exc_type, exc_obj, exc_tb = sys.exc_info()
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "QUB Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients from YSE in QUB_data.py\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

		print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))


	def add_options(self, parser=None, usage=None, config=None):
		import argparse
		if parser == None:
			parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

		# The basics
		parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_argument('--clobber', default=False, action="store_true",
						  help='clobber output file')
		parser.add_argument('-s','--settingsfile', default=None, type=str,
						  help='settings file (login/password info)')
		parser.add_argument('--status', default='New', type=str,
						  help='transient status to enter in YS_PZ')

		if config:
			parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
							  help='database password, if post=True (default=%default)')
			parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
								help='email password, if post=True (default=%default)')
			parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
							  help='URL to POST transients to a database (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')
			parser.add_argument('--STATIC', default=config.get('site_settings','STATIC'), type=str,
							  help='static directory (default=%default)')
			parser.add_argument('--qubuser', default=config.get('main','qubuser'), type=str,
							  help='QUB database username (default=%default)')
			parser.add_argument('--qubpass', default=config.get('main','qubpass'), type=str,
							  help='QUB database password (default=%default)')
			parser.add_argument('--yselink_stacksummary', default=config.get('main','yselink_stacksummary'), type=str,
							  help='YSE summary CSV for possible candidates (default=%default)')
			parser.add_argument('--yselink_stacklc', default=config.get('main','yselink_stacklc'), type=str,
							  help='YSE lightcurve CSV for possible candidates (default=%default)')
			parser.add_argument('--yselink_agnsummary', default=config.get('main','yselink_agnsummary'), type=str,
							  help='YSE summary CSV for possible candidates (default=%default)')
			parser.add_argument('--yselink_agnlc', default=config.get('main','yselink_agnlc'), type=str,
							  help='YSE lightcurve CSV for possible candidates (default=%default)')
			parser.add_argument('--ztfurl', default=config.get('main','ztfurl'), type=str,
							  help='ZTF URL (default=%default)')
			parser.add_argument('--max_days_ysestacklc', default=config.get('main','max_days_ysestacklc'), type=float,
							  help='maximum days to look back for lightcurves (default=%default)')
			parser.add_argument('--max_days_yseignore', default=config.get('main','max_days_ysestackignore'), type=float,
							  help='maximum days to look back for lightcurves (default=%default)')
			parser.add_argument('--max_days_yseagnlc', default=config.get('main','max_days_yseagnlc'), type=float,
							  help='maximum days to look back for lightcurves (default=%default)')
			parser.add_argument('--max_days_yseagnignore', default=config.get('main','max_days_yseagnignore'), type=float,
							  help='maximum days to look back for lightcurves (default=%default)')
			
			parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
							  help='SMTP login (default=%default)')
			parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
							  help='SMTP host (default=%default)')
			parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
							  help='SMTP port (default=%default)')
		else:
			pass


		return(parser)

	def main(self):

		nsn = 0
		
		# grab CSV files
		for summarylink,lclink,naming in zip([self.options.yselink_stacksummary,self.options.yselink_agnsummary],
											 [self.options.yselink_stacklc,self.options.yselink_agnlc],
											 ['stack','agn']):

			if naming == 'stack':
				latest_stacked_transients = Transient.objects.filter(tags__name='YSE Stack').order_by('-created_date')
				year = latest_stacked_transients[0].created_date.year
				if len(latest_stacked_transients):
					stacked_name = latest_stacked_transients[0].name
					self.next_name = get_next_name(stacked_name,ttype='Stack',year=year)
				else:
					self.next_name = 'YSEStack%sa'%year
			else:
				latest_agn = Transient.objects.filter(tags__name='YSE AGN').order_by('-created_date')
				year = latest_agn[0].created_date.year
				if len(latest_agn):
					agn_name = latest_agn[0].name
					self.next_name = get_next_name(agn_name,ttype='AGN',year=year)
				else:
					self.next_name = 'YSEAGN%sa'%year
			
			r = requests.get(url=summarylink,
							 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))

			if r.status_code != 200: raise RuntimeError('problem accessing summary link %s'%summarylink)
			summary = at.Table.read(r.text, format='ascii', delimiter='|')


			r = requests.get(url=lclink,
							 auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
			if r.status_code != 200: raise RuntimeError('problem accessing lc link %s'%lclink)
			lc = at.Table.read(r.text, format='ascii', delimiter='|')

			nsn = 0
			nsn_single = 25

			nowmjd = Time.now().mjd
			if naming == 'stack': summary_upload = summary[nowmjd - summary['mjd_obs'] < self.options.max_days_ysestacklc]
			else: summary_upload = summary[nowmjd - summary['mjd_obs'] < self.options.max_days_yseagnlc]
			# important to sort by flag date for a halfway sensible naming scheme
			summary_upload = summary_upload[np.argsort(date_to_mjd(summary_upload['followup_flag_date']))]
			print('%i transients to upload!'%len(summary_upload))
			while nsn_single == 25:
				transientdict,nsn_single = self.parse_data(
					summary_upload,lc,transient_idx=nsn,max_transients=25,naming_convention=naming)
				print('uploading %i transients'%nsn_single)
				self.send_data(transientdict)
				self.copy_stamps(transientdict)
				nsn += 25
		
		return nsn
		
	def parse_data(self,summary,lc,transient_idx=0,max_transients=None,naming_convention='stack'):
		# today's date
		nowmjd = Time.now().mjd

		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0
		#ysetag = TransientTag.objects.get(name='YSE')
		#yseforcedtag = TransientTag.objects.get(name='YSE Forced Phot')
		if naming_convention == 'stack': ysestacktag = TransientTag.objects.get(name='YSE Stack')
		elif naming_convention == 'agn': ysestacktag = TransientTag.objects.get(name='YSE AGN')
		else: raise RuntimeError('unknown naming convention')
		for i,s in enumerate(summary[transient_idx:transient_idx+max_transients]):
			# check RA/dec
			ramin,ramax,decmin,decmax = getRADecBox(s['ra_psf'],s['dec_psf'],size=0.00042)
			dbtransient = Transient.objects.filter(
				Q(ra__gt=ramin) & Q(ra__lt=ramax) & Q(dec__gt=decmin) & Q(dec__lt=decmax) &
				Q(disc_date__gte=dateutil.parser.parse(s['followup_flag_date'])-datetime.timedelta(365)) &
				Q(disc_date__lte=dateutil.parser.parse(s['followup_flag_date'])+datetime.timedelta(365))).\
				filter(~Q(tags=ysestacktag))
			if len(dbtransient):
				nsn += 1
				continue
			dbstacktransient = Transient.objects.filter(
				Q(ra__gt=ramin) & Q(ra__lt=ramax) & Q(dec__gt=decmin) & Q(dec__lt=decmax) &
				Q(disc_date__gte=dateutil.parser.parse(s['followup_flag_date'])-datetime.timedelta(365)) &
				Q(disc_date__lte=dateutil.parser.parse(s['followup_flag_date'])+datetime.timedelta(365))).\
				filter(Q(tags=ysestacktag))
			if len(dbstacktransient): stackname = dbstacktransient[0].name
			else: stackname = None

			if naming_convention == 'stack':
				#r = requests.get(url='https://star.pst.qub.ac.uk/sne/ps1ysestack/psdb/lightcurveforced/%s'%s['id'])
				r = requests.get(url='https://psweb.mp.qub.ac.uk/sne/ps1ysestack/psdb/lightcurveforced/%s'%s['id'])
			else:
				#r = requests.get(url='https://star.pst.qub.ac.uk/sne/ps1yse/psdb/lightcurveforced/%s'%s['id'])
				r = requests.get(url='https://psweb.mp.qub.ac.uk/sne/ps1yse/psdb/lightcurveforced/%s'%s['id'])
				
			if r.status_code != 200: raise RuntimeError('problem accessing forcedphot link %s')
			try:
				lc_forced = at.Table.read(r.text, format='ascii', delimiter=' ')
				if len(lc_forced): has_forced_phot = True
				else: has_forced_phot = False
			except:
				has_forced_phot = False


			sc = SkyCoord(s['ra_psf'],s['dec_psf'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))
			iLC = (lc['transient_object_id'] == s['id']) #& (nowmjd - lc['mjd_obs'] < self.options.max_days_ysestacklc)

			if naming_convention == 'stack':
				if nowmjd - Time('%s 00:00:00'%s['followup_flag_date'],format='iso',scale='utc').mjd > self.options.max_days_yseignore:
					status = 'Ignore'
				else:
					status = self.options.status
			else:
				if nowmjd - Time('%s 00:00:00'%s['followup_flag_date'],format='iso',scale='utc').mjd > self.options.max_days_yseagnignore:
					status = 'Ignore'
				else:
					status = self.options.status

					
			if type(s['target']) == np.ma.core.MaskedConstant:
				postage_stamp_file = ''
				postage_stamp_ref = ''
				postage_stamp_diff = ''
				postage_stamp_file_fits = ''
				postage_stamp_ref_fits = ''
				postage_stamp_diff_fits = ''
			else:
				postage_stamp_file = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['target'])
				postage_stamp_ref = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['ref'])
				postage_stamp_diff = '%s/%s/%s.jpeg'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['diff'])
				postage_stamp_file_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['target'])
				postage_stamp_ref_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['ref'])
				postage_stamp_diff_fits = '%s/%s/%s.fits'%(s['local_designation'],s['target'].split('_')[1].split('.')[0],s['diff'])

			if type(s['sherlock_specz']) == np.ma.core.MaskedConstant:
				redshift = None
			else:
				redshift = s['sherlock_specz']

			if type(s['sherlock_object_id']) == np.ma.core.MaskedConstant:
				hostdict = {}
			else:
				hostdict = {'name':s['sherlock_object_id'][:64],
							'ra':s['sherlock_host_ra'],
							'dec':s['sherlock_host_dec'],
							'redshift':redshift}
			if type(s['rb_factor_image']) == np.ma.core.MaskedConstant:
				rb_factor = None
			else:
				rb_factor = s['rb_factor_image']

			if stackname: name = stackname[:]
			else:
				name = self.next_name[:]
				year = dateutil.parser.parse(s['followup_flag_date']).year
				if naming_convention == 'stack':
					if str(year) not in self.next_name: self.next_name = 'YSEStack%sa'%str(year)
					else: self.next_name = get_next_name(self.next_name,ttype='Stack',year=year)
				else:
					if str(year) not in self.next_name: self.next_name = 'YSEAGN%sa'%str(year)
					else: self.next_name = get_next_name(self.next_name,ttype='AGN',year=year)
				
			tdict = {'name':name,
					 'ra':s['ra_psf'],
					 'dec':s['dec_psf'],
					 'obs_group':'YSE',
					 'postage_stamp_file':postage_stamp_file,
					 'postage_stamp_ref':postage_stamp_ref,
					 'postage_stamp_diff':postage_stamp_diff,
					 'postage_stamp_file_fits':postage_stamp_file_fits,
					 'postage_stamp_ref_fits':postage_stamp_ref_fits,
					 'postage_stamp_diff_fits':postage_stamp_diff_fits,
					 'status':status,
					 'context_class':s['sherlockClassification'].replace('UNCLEAR','Unknown'),
					 'host':hostdict,
					 'disc_date':s['followup_flag_date'],
					 'mw_ebv':mw_ebv,
					 'point_source_probability':ps_prob,
					 'real_bogus_score':rb_factor}
			if naming_convention == 'stack': tdict['tags'] = ['YSE Stack']
			elif naming_convention == 'agn': tdict['tags'] = ['YSE AGN']
			
			obj += [s['local_designation']]
			ra += [s['ra_psf']]
			dec += [s['dec_psf']]


			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":self.options.clobber}
			photometrydict = {'instrument':'GPC1',
							  'obs_group':'YSE',
							  'photdata':{}}
			if has_forced_phot:
				for j,lf in enumerate(lc_forced[np.argsort(lc_forced['mjd'])]):
					if j == 0 and np.abs(date_to_mjd(s['followup_flag_date'])-lf['mjd']) < 1: disc_point = 1
					else: disc_point = 0

					if lf['cal_psf_mag'] == 'None':
						forced_mag,forced_mag_err = None,None
					else:
						forced_mag,forced_mag_err = lf['cal_psf_mag'],lf['psf_inst_mag_sig']

					# forced photometry
					phot_upload_dict = {'obs_date':mjd_to_date(lf['mjd']),
										'band':lf['filter'],
										'groups':['YSE'],
										'mag':forced_mag,
										'mag_err':forced_mag_err,
										'flux':fluxToMicroJansky(lf['psf_inst_flux'],27.0,lf['zero_pt'])*10**(0.4*(27.5-23.9)),
										'flux_err':fluxToMicroJansky(lf['psf_inst_flux_sig'],27.0,lf['zero_pt'])*10**(0.4*(27.5-23.9)),
										'data_quality':0,
										'forced':1,
										'flux_zero_point':27.5,
										'discovery_point':disc_point,
										'diffim':1}
					photometrydict['photdata']['%s_%i'%(mjd_to_date(lf['mjd']),j)] = phot_upload_dict



			for j,l in enumerate(lc[iLC][np.argsort(lc['mjd_obs'][iLC])]):
				if has_forced_phot and np.min(np.abs(lc_forced['mjd']-l['mjd_obs'])) < 0.01: continue
				if j == 0 and np.abs(date_to_mjd(s['followup_flag_date'])-l['mjd_obs']) < 1: disc_point = 1
				else: disc_point = 0

				flux = 10**(-0.4*(l['cal_psf_mag']-27.5))
				flux_err = np.log(10)*0.4*flux*l['psf_inst_mag_sig']
				if type(l['psf_inst_mag_sig']) == np.ma.core.MaskedConstant:
					mag_err = 0
					flux_err = 0
				else:
					mag_err = l['psf_inst_mag_sig']

				# unforced photometry
				phot_upload_dict = {'obs_date':mjd_to_date(l['mjd_obs']),
									'band':l['filter'],
									'groups':'YSE',
									'mag':l['cal_psf_mag'],
									'mag_err':mag_err,
									'flux':flux,
									'flux_err':flux_err,
									'data_quality':0,
									'forced':0,
									'flux_zero_point':27.5,
									'discovery_point':disc_point,
									'diffim':1}

				photometrydict['photdata']['%s_%i'%(mjd_to_date(l['mjd_obs']),j)] = phot_upload_dict

			PhotUploadAll['PS1'] = photometrydict
			transientdict[tdict['name']] = tdict
			transientdict[tdict['name']]['transientphotometry'] = PhotUploadAll

			photometrydict_ztf = self.getZTFPhotometry(s['ra_psf'],s['dec_psf'])
			if photometrydict_ztf is not None:
				PhotUploadAll['ZTF'] = photometrydict_ztf

			nsn += 1

		return transientdict,nsn

	def getZTFPhotometry(self,ra,dec):

		ztfurl = '%s/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(
			self.options.ztfurl,ra,dec)
		client = coreapi.Client()
		schema = client.get(ztfurl)
		if 'results' in schema.keys():
			PhotUploadAll = {"mjdmatchmin":0.01,
							 "clobber":False}
			photometrydict = {'instrument':'ZTF-Cam',
							  'obs_group':'ZTF',
							  'photdata':{}}

			for i in range(len(schema['results'])):
				phot = schema['results'][i]['candidate']
				if phot['isdiffpos'] == 'f':
					continue
				PhotUploadDict = {'obs_date':jd_to_date(phot['jd']),
								  'band':'%s-ZTF'%phot['filter'],
								  'groups':[]}
				PhotUploadDict['mag'] = phot['magpsf']
				PhotUploadDict['mag_err'] = phot['sigmapsf']
				PhotUploadDict['flux'] = None
				PhotUploadDict['flux_err'] = None
				PhotUploadDict['data_quality'] = 0
				PhotUploadDict['forced'] = None
				PhotUploadDict['flux_zero_point'] = None
				PhotUploadDict['discovery_point'] = 0
				PhotUploadDict['diffim'] = 1

				photometrydict['photdata']['%s_%i'%(jd_to_date(phot['jd']),i)] = PhotUploadDict

			return photometrydict

		else: return None

	
	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True
		self.UploadTransients(TransientUploadDict)

	def copy_stamps(self,transientdict):
		try:
			if not djangoSettings.DEBUG: basedir = "%sYSE_App/images/stamps"%(djangoSettings.STATIC_ROOT)
			else: basedir = "%s/YSE_App%sYSE_App/images/stamps"%(djangoSettings.BASE_DIR,self.options.STATIC)
			for k in transientdict.keys():
				if k == 'noupdatestatus': continue
				if k == 'TNS': continue
				if not os.path.exists("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref']))):
					os.makedirs("%s/%s"%(basedir,os.path.dirname(transientdict[k]['postage_stamp_ref'])))

					# only download the files if the directory didn't exist before now.	 AKA, don't
					# continuously grab new stamps
					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_ref'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_diff'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_file'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_ref_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_ref_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_diff_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_diff_fits']), 'wb') as fout:
							fout.write(r.content)

					if not os.path.exists("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits'])):
						r = requests.get(
							"%s/%s"%(yse_image_url,transientdict[k]['postage_stamp_file_fits'].split('/',1)[-1]),
							auth=HTTPBasicAuth(self.options.qubuser,self.options.qubpass))
						with iopen("%s/%s"%(basedir,transientdict[k]['postage_stamp_file_fits']), 'wb') as fout:
							fout.write(r.content)

		except Exception as e:
			print(e)

	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		try:
			r = requests.post(url = url, data = json.dumps(TransientUploadDict),
							  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword),
							  timeout=60)
			try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
			except: print(r.text)
			print("Process done.")

		except Exception as e:
			print("Error: %s"%e)

			
class YSE_Weekly(CronJobBase):

	RUN_EVERY_MINS = 30

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.QUB_data.YSE'

	def do(self):

		print("starting YSE ingest at {}".format(datetime.datetime.now().isoformat()))
		usagestring = "TNS_Synopsis.py <options>"

		tstart = time.time()

		# read in the options from the param file and the command line
		# some convoluted syntax here, making it so param file is not required
		try:
			ys = YSE()
			parser = ys.add_options(usage=usagestring)
			options,  args = parser.parse_known_args()

			config = configparser.ConfigParser()
			config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
			parser = ys.add_options(usage=usagestring,config=config)
			options,  args = parser.parse_known_args()
			ys.options = options
			ys.options.max_days = 7
			
			nsn = ys.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "YSE Weekly Updates Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload weekly transients from YSE in QUB_data.py\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

		print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

			
class CheckDuplicates(CronJobBase):
	
	RUN_EVERY_MINS = 30

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.QUB_data.CheckDuplicates'

	def do(self):

		print("starting duplicate check at {}".format(datetime.datetime.now().isoformat()))

		tstart = time.time()

		# read in the options from the param file and the command line
		# some convoluted syntax here, making it so param file is not required
		try:
			nsn = self.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "Duplicate Check Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients from YSE in QUB_data.py\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

		print('Checking duplicates took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

	def main(self):
		from YSE_App.models import Transient
		# 10HYSEkcp
		
		transients = Transient.objects.filter(created_date__gt=datetime.datetime.now()-datetime.timedelta(1)).filter(name__startswith='10')
		for t in transients:
			ramin,ramax,decmin,decmax = getRADecBox(t.ra,t.dec,size=0.00042)
			dups = Transient.objects.filter(Q(ra__gt=ramin) & Q(ra__lt=ramax) &
											Q(dec__gt=decmin) & Q(dec__lt=decmax) &
											Q(disc_date__gte=t.disc_date-datetime.timedelta(365)))
			if len(dups) > 1:
				print('deleting transient %s'%t.name)
				t.delete()
		return len(transients)
	
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

	import argparse
	import configparser

	usagestring = "TNS_Synopsis.py <options>"

	tstart = time.time()
	qub = QUB()

	# read in the options from the param file and the command line
	# some convoluted syntax here, making it so param file is not required
	parser = qub.add_options(usage=usagestring)
	options,  args = parser.parse_known_args()
	if options.settingsfile:
		config = configparser.ConfigParser()
		config.read(options.settingsfile)
	else: config=None
	parser = qub.add_options(usage=usagestring,config=config)
	options,  args = parser.parse_known_args()
	qub.options = options
	#tnsproc.hostmatchrad = options.hostmatchrad

	try:
		nsn = qub.main()
	except Exception as e:
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
				  options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

	print('QUB -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))
