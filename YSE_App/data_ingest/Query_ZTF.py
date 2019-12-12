#!/usr/bin/env python

import requests
import urllib
from django_cron import CronJobBase, Schedule
from requests.auth import HTTPBasicAuth
from django.conf import settings as djangoSettings
import configparser
import imaplib
import email
from YSE_App.common.utilities import date_to_mjd
from YSE_App.models.survey_models import *
from django.conf import settings as djangoSettings
import json
import re
import datetime
from antares_client.search import search
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
import time
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

query_template = {
    "query": {
        "bool": {
            "must": [
                {
                    "range": {
                        "ra": {
                        },
                    }
                },
                {
                    "range": {
                        "dec": {
                        },
                    }
                },
                {
                    "range": {
                        "properties.ztf_rb": {
                        },
                    }
                },
				{
                    "range": {
                        "properties.ztf_jd": {
                        },
                    }
                },
             ]
        }
    }
}

#				{
#					"match": {
#						"properties.ztf_object_id": "ZTF18abrfjdh"
#					}
#                }


class AntaresZTF(CronJobBase):

	RUN_EVERY_MINS = 0.1

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.Query_ZTF.AntaresZTF'
	
	def do(self):

		tstart = time.time()
		
		parser = self.add_options(usage='')
		options,  args = parser.parse_args()

		config = configparser.ConfigParser()
		config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
		parser = self.add_options(usage='',config=config)
		options,  args = parser.parse_args()
		self.options = options

		try:
			self.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "QUB Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbpassword, smtpserver)

		print('Antares -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

	def main(self):
		
		recentmjd = date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(14))
		survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)
		field_pk = survey_obs.values('survey_field').distinct()
		survey_fields = SurveyField.objects.filter(pk__in = field_pk).select_related()
		
		for s in survey_fields:

			width_corr = 3.1/np.abs(np.cos(s.dec_cen))
			ra_offset = Angle(width_corr/2., unit=u.deg)
			dec_offset = Angle(3.1/2., unit=u.deg)
			sc = SkyCoord(s.ra_cen,s.dec_cen,unit=u.deg)
			ra_min = sc.ra - ra_offset
			ra_max = sc.ra + ra_offset
			dec_min = sc.dec - dec_offset
			dec_max = sc.dec + dec_offset
			
			query = query_template.copy()
			query['query']['bool']['must'][0]['range']['ra']['gte'] = ra_min.deg
			query['query']['bool']['must'][0]['range']['ra']['lte'] = ra_max.deg
			query['query']['bool']['must'][1]['range']['dec']['gte'] = dec_min.deg
			query['query']['bool']['must'][1]['range']['dec']['lte'] = dec_max.deg
			query['query']['bool']['must'][2]['range']['properties.ztf_rb']['gte'] = 0.5
			query['query']['bool']['must'][3]['range']['properties.ztf_jd']['gte'] = recentmjd+2400000.5
			result_set = search(query)

			transientdict,nsn = self.parse_data(result_set)
			print('uploading %i transients'%nsn)
			self.send_data(transientdict)
			
			import pdb; pdb.set_trace()

	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True
		self.UploadTransients(TransientUploadDict)

	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		r = requests.post(url = url, data = json.dumps(TransientUploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

		try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		except: print(r.text)
		print("Process done.")
		
	def parse_data(self,result_set):
		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0
		for i,s in enumerate(result_set):
			
			sc = SkyCoord(s['properties']['ztf_ra'],s['properties']['ztf_dec'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))

			if s['properties']['ztf_object_id'] not in transientdict.keys():
				tdict = {'name':s['properties']['ztf_object_id'],
						 'status':'New',
						 'ra':s['properties']['ztf_ra'],
						 'dec':s['properties']['ztf_dec'],
						 'obs_group':'ZTF',
						 'tags':['ZTF'],
						 'disc_date':mjd_to_date(s['properties']['ztf_jd']-2400000.5),
						 'mw_ebv':mw_ebv,
						 'point_source_probability':ps_prob}
				obj += [s['properties']['ztf_object_id']]
				ra += [s['properties']['ztf_ra']]
				dec += [s['properties']['ztf_dec']]

				PhotUploadAll = {"mjdmatchmin":0.01,
								 "clobber":False}
				photometrydict = {'instrument':'ZTF-Cam',
								  'obs_group':'ZTF',
								  'photdata':{}}

			else:
				tdict = transientdict[s['properties']['ztf_object_id']]
				if s['properties']['ztf_jd']-2400000.5 < date_to_mjd(tdict['disc_date']):
					tdict['disc_date'] = mjd_to_date(s['properties']['ztf_jd']-2400000.5)

				PhotUploadAll = transientdict[s['properties']['ztf_object_id']]['transientphotometry']
				photometrydict = PhotUploadAll['ZTF']
								
			flux = 10**(-0.4*(s['properties']['ztf_magpsf']-27.5))
			flux_err = np.log(10)*0.4*flux*s['properties']['ztf_sigmapsf']

			phot_upload_dict = {'obs_date':mjd_to_date(s['properties']['ztf_jd']-2400000.5),
								'band':'%s-ZTF'%s['properties']['passband'].lower(),
								'groups':[],
								'mag':s['properties']['ztf_magpsf'],
								'mag_err':s['properties']['ztf_sigmapsf'],
								'flux':flux,
								'flux_err':flux_err,
								'data_quality':0,
								'forced':0,
								'flux_zero_point':27.5,
								# might need to fix this later
								'discovery_point':0, #disc_point,
								'diffim':1}
			photometrydict['photdata']['%s_%i'%(mjd_to_date(s['properties']['ztf_jd']-2400000.5),i)] = phot_upload_dict

			PhotUploadAll['ZTF'] = photometrydict
			transientdict[s['properties']['ztf_object_id']] = tdict
			transientdict[s['properties']['ztf_object_id']]['transientphotometry'] = PhotUploadAll

			nsn += 1

			#if s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
			#	import pdb; pdb.set_trace()
			if s['properties']['passband'] == 'R' and s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
				import pdb; pdb.set_trace()
				
		return transientdict,nsn

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

			parser.add_option('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type="string",
							  help='SMTP login (default=%default)')
			parser.add_option('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type="string",
							  help='SMTP host (default=%default)')
			parser.add_option('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type="string",
							  help='SMTP port (default=%default)')

		else:
			pass


		return(parser)
						  
class MARS_ZTF(CronJobBase):

	RUN_EVERY_MINS = 0.1

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.Query_ZTF.MARS_ZTF'
	
	def do(self):

		tstart = time.time()
		
		parser = self.add_options(usage='')
		options,  args = parser.parse_args()
		config = configparser.ConfigParser()
		config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
		parser = self.add_options(usage='',config=config)
		options,  args = parser.parse_args()
		self.options = options

		try:
			self.main()
		except Exception as e:
			print(e)
			nsn = 0
			smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
			from_addr = "%s@gmail.com" % options.SMTP_LOGIN
			subject = "QUB Transient Upload Failure"
			print("Sending error email")
			html_msg = "Alert : YSE_PZ Failed to upload transients\n"
			html_msg += "Error : %s"
			sendemail(from_addr, options.dbemail, subject,
					  html_msg%(e),
					  options.SMTP_LOGIN, options.dbpassword, smtpserver)

		print('Antares -> YSE_PZ took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

	def main(self):
		
		recentmjd = date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(14))
		survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)
		field_pk = survey_obs.values('survey_field').distinct()
		survey_fields = SurveyField.objects.filter(pk__in = field_pk).select_related()
		
		for s in survey_fields:

			width_corr = 3.1/np.abs(np.cos(s.dec_cen))
			ra_offset = Angle(width_corr/2., unit=u.deg)
			dec_offset = Angle(3.1/2., unit=u.deg)
			sc = SkyCoord(s.ra_cen,s.dec_cen,unit=u.deg)
			ra_min = sc.ra - ra_offset
			ra_max = sc.ra + ra_offset
			dec_min = sc.dec - dec_offset
			dec_max = sc.dec + dec_offset
			result_set = []
			for page in range(500):
				print(s,page)
				marsurl = '%s/?format=json&sort_value=jd&sort_order=desc&ra__gt=%.7f&ra__lt=%.7f&dec__gt=%.7f&dec__lt=%.7f&jd__gt=%i&rb__gt=0.5&page=%i'%(
					self.options.ztfurl,ra_min.deg,ra_max.deg,dec_min.deg,dec_max.deg,recentmjd+2400000.5,page+1)
				client = coreapi.Client()
				try:
					schema = client.get(marsurl)
					if 'results' in schema.keys():
						result_set = np.append(result_set,schema['results'])
					else: break
				except: break
				#break

			transientdict,nsn = self.parse_data(result_set,date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(2)))
			print('uploading %i transient detections'%nsn)
			self.send_data(transientdict)
			#import pdb; pdb.set_trace()			
			#import pdb; pdb.set_trace()

	def send_data(self,TransientUploadDict):

		TransientUploadDict['noupdatestatus'] = True
		self.UploadTransients(TransientUploadDict)

	def UploadTransients(self,TransientUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_transient')
		r = requests.post(url = url, data = json.dumps(TransientUploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

		try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		except: print(r.text)
		print("Process done.")
		
	def parse_data(self,result_set,mjdlim):
		transientdict = {}
		obj,ra,dec = [],[],[]
		nsn = 0
		for i,s in enumerate(result_set):
			if s['candidate']['rb'] < 0.5: continue
			sc = SkyCoord(s['candidate']['ra'],s['candidate']['dec'],unit=u.deg)
			try:
				ps_prob = get_ps_score(sc.ra.deg,sc.dec.deg)
			except:
				ps_prob = None

			mw_ebv = float('%.3f'%(sfd(sc)*0.86))

			if s['objectId'] not in transientdict.keys():
				if s['candidate']['jdstarthist']-2400000.5 < mjdlim:
					status = 'Ignore'
				else: status = 'New'

				tdict = {'name':s['objectId'],
						 'status':status,
						 'ra':s['candidate']['ra'],
						 'dec':s['candidate']['dec'],
						 'obs_group':'ZTF',
						 'tags':['ZTF'],
						 'disc_date':mjd_to_date(s['candidate']['jdstarthist']-2400000.5),
						 'mw_ebv':mw_ebv,
						 'point_source_probability':ps_prob}

				PhotUploadAll = {"mjdmatchmin":0.01,
								 "clobber":False}
				photometrydict = {'instrument':'ZTF-Cam',
								  'obs_group':'ZTF',
								  'photdata':{}}

			else:
				tdict = transientdict[s['objectId']]					
				PhotUploadAll = transientdict[s['objectId']]['transientphotometry']
				photometrydict = PhotUploadAll['ZTF']
								
			flux = 10**(-0.4*(s['candidate']['magpsf']-27.5))
			flux_err = np.log(10)*0.4*flux*s['candidate']['sigmapsf']

			phot_upload_dict = {'obs_date':mjd_to_date(s['candidate']['jd']-2400000.5),
								'band':'%s-ZTF'%s['candidate']['filter'].lower(),
								'groups':[],
								'mag':s['candidate']['magpsf'],
								'mag_err':s['candidate']['sigmapsf'],
								'flux':flux,
								'flux_err':flux_err,
								'data_quality':0,
								'forced':0,
								'flux_zero_point':27.5,
								# might need to fix this later
								'discovery_point':0, #disc_point,
								'diffim':1}
			photometrydict['photdata']['%s_%i'%(mjd_to_date(s['candidate']['jd']-2400000.5),i)] = phot_upload_dict

			PhotUploadAll['ZTF'] = photometrydict
			transientdict[s['objectId']] = tdict
			transientdict[s['objectId']]['transientphotometry'] = PhotUploadAll

			nsn += 1

			#if s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
			#	import pdb; pdb.set_trace()
			#if s['candidate']['passband'] == 'R' and s['candidate']['objectId'] == 'ZTF18abrfjdh':
			#	import pdb; pdb.set_trace()

		return transientdict,nsn

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

			parser.add_option('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type="string",
							  help='SMTP login (default=%default)')
			parser.add_option('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type="string",
							  help='SMTP host (default=%default)')
			parser.add_option('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type="string",
							  help='SMTP port (default=%default)')

			parser.add_option('--ztfurl', default=config.get('main','ztfurl'), type="string",
							  help='ZTF URL (default=%default)')
			
		else:
			pass


		return(parser)
						  
