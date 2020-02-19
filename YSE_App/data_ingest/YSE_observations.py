#!/usr/bin/env python
import requests
import urllib
from django_cron import CronJobBase, Schedule
from requests.auth import HTTPBasicAuth
import configparser
import imaplib
import email
from YSE_App.common.utilities import date_to_mjd
from django.conf import settings as djangoSettings
import json
import re
import numpy as np
import os
from astropy.coordinates import SkyCoord
import astropy.units as u
import sys

def split_band(band,exp_name):
	if re.match('o[0-9][0-9][0-9][0-9]g[0-9][0-9][0-9][0-9]o',exp_name):
		return 'GPC1-%s'%band.split('.')[0]
	elif re.match('o[0-9][0-9][0-9][0-9]h[0-9][0-9][0-9][0-9]o',exp_name):
		return 'GPC2-%s'%band.split('.')[0]
	else: raise RuntimeError('couldn\'t parse exp name')
	
def split_survey_field(survey_field):
	return '.'.join(survey_field.split('.')[1:3])

	
#allowed_keys = ['obs_mjd','survey_field','status','exposure_time',
#				'photometric_band','pos_angle_deg','fwhm','eccentricity',
#				'airmass','image_id']
# email key: (data model key, function name that transforms)
ingest_keys_map = {'exp_name':('image_id',None),
				   'dateobs':('obs_mjd',date_to_mjd),
				   'exp_time':('exposure_time',None),
				   'filter':('photometric_band',split_band),
				   'posang':('pos_angle_deg',None),
				   'airmass':('airmass',None),
				   'fwhm_major':('fwhm_major',None),
				   'eccentricity':('eccentricity',None),
				   'quality':('quality',None),
				   'deteff':('mag_lim',None),
				   'zpt_obs':('zpt_obs',None),
				   'Ngood_diff_skycell':('n_good_skycell',None),
				   'comment':('survey_field',split_survey_field)}

class SurveyObs(CronJobBase):

	RUN_EVERY_MINS = 0.1

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.YSE_observations.SurveyObs'

	def do(self):
		parser = self.add_options(usage='')
		options,  args = parser.parse_known_args()
		try:
			config = configparser.ConfigParser()
			config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)

			parser = self.add_options(usage='',config=config)
			options,  args = parser.parse_known_args()
			self.options = options

			if os.path.exists('%s/surveyfields.txt'%djangoSettings.STATIC_ROOT):
				self.add_survey_fields('%s/surveyfields.txt'%djangoSettings.STATIC_ROOT)
			uploaddict = self.process_emails()
		except Exception as e:
			print(e)
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print('line number %i'%exc_tb.tb_lineno)
			
		if uploaddict is not None: self.upload(uploaddict)
		
	def process_emails(self):

		body = ""
		html = ""
		survey_fields = {}
		
		########################################################
		# Get All Email
		########################################################
		mail =	imaplib.IMAP4_SSL('imap.gmail.com', 993) #, ssl_context=ctx

		## NOTE: This is not the way to do this. You will want to implement an industry-standard login step ##
		mail.login(self.options.SMTP_LOGIN, self.options.SMTP_PASSWORD)
		mail.select('YSE', readonly=False)
		retcode, msg_ids_bytes = mail.search(None, '(UNSEEN)')
		msg_ids = msg_ids_bytes[0].decode("utf-8").split(" ")

		try:
			if retcode != "OK" or msg_ids[0] == "":
				raise ValueError("No messages")

		except ValueError as err:
			print("%s. Exiting..." % err.args)
			mail.close()
			mail.logout()
			del mail
			print("Process done.")
			return None

		objs,ras,decs = [],[],[]
		print('length of msg_ids %s' %len(msg_ids))
		for i in range(len(msg_ids)):
			########################################################
			# Iterate Over Email
			########################################################
			typ, data = mail.fetch(msg_ids[i],'(RFC822)')
			msg = email.message_from_bytes(data[0][1])

			if msg.is_multipart():
				for part in msg.walk():
					ctype = part.get_content_type()
					cdispo = str(part.get('Content-Disposition'))

					# skip any text/plain (txt) attachments
					if (ctype == 'text/plain' or ctype == 'text/html') and 'attachment' not in cdispo:
						body = part.get_payload(decode=True).decode('utf-8')  # decode
						break
			# not multipart - i.e. plain text, no attachments, keeping fingers crossed
			else:
				body = msg.get_payload(decode=True).decode('utf-8')

			header = None
			for line in body.split('\n'):
				lineparts = line.replace('\r','').replace('> ','').split('\t')
				if 'exp_name' in line:
					header = lineparts
				elif 'YSE' in line and header is not None:
					survey_dict = {}
					for h,l in zip(header,lineparts):
						if h in ingest_keys_map.keys():
							if ingest_keys_map[h][1] is None:
								survey_dict[ingest_keys_map[h][0]] = l
							else:
								if ingest_keys_map[h][0] != 'photometric_band':
									survey_dict[ingest_keys_map[h][0]] = ingest_keys_map[h][1](l)
								else:
									survey_dict[ingest_keys_map[h][0]] = ingest_keys_map[h][1](
										l,np.array(lineparts)[np.array(header) == 'exp_name'][0])
					survey_dict['status'] = 'Successful'
					survey_fields[survey_dict['image_id']] = survey_dict

			# Mark messages as "Seen"
			result, wdata = mail.store(msg_ids[i], '+FLAGS', '\\Seen')
		return survey_fields

	def add_survey_fields(self,surveyfile):

		fid,ra,dec = np.loadtxt(surveyfile,unpack=True,dtype=str)
		SurveyUploadDict = {}
		for f,r,d in zip(fid,ra,dec):
			sc = SkyCoord(r,d,unit=(u.hourangle,u.deg))
			SurveyUploadDict[f] = {'obs_group':'YSE',
								   'field_id':f,
								   'cadence':3,
								   'instrument':'GPC1',
								   'ztf_field_id':f.split('.')[0],
								   'ra_cen':sc.ra.deg,
								   'dec_cen':sc.dec.deg,
								   'width_deg':3.1,
								   'height_deg':3.1}
			
		url = '%s'%self.options.dburl.replace('/api','/add_yse_survey_fields')
		r = requests.post(url = url, data = json.dumps(SurveyUploadDict),
						  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
		print('YSE_PZ says: %s'%json.loads(r.text)['message'])
		
	def upload(self,SurveyUploadDict):

		url = '%s'%self.options.dburl.replace('/api','/add_yse_survey_obs')
		try:
			r = requests.post(url = url, data = json.dumps(SurveyUploadDict),
							  auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))

			try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
			except: print(r.text)
		except exception as e: print(e)
		print("upload finished.")
		
	def add_options(self, parser=None, usage=None, config=None):
		import argparse
		if parser == None:
			parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

		# The basics
		parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
		parser.add_argument('--clobber', default=False, action="store_true",
						  help='clobber output file')
		#parser.add_option('-s','--settingsfile', default=None, type=str,
		#				  help='settings file (login/password info)')

		if config:
			parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
							  help='database login, if post=True (default=%default)')
			parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
							  help='database password, if post=True (default=%default)')
			parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
							  help='URL to POST transients to a database (default=%default)')

			parser.add_argument('--SMTP_LOGIN', default=config.get('YSE_SMTP_provider','SMTP_LOGIN'), type=str,
							  help='SMTP login (default=%default)')
			parser.add_argument('--SMTP_PASSWORD', default=config.get('YSE_SMTP_provider','SMTP_PASSWORD'), type=str,
							  help='SMTP password (default=%default)')
			parser.add_argument('--SMTP_HOST', default=config.get('YSE_SMTP_provider','SMTP_HOST'), type=str,
							  help='SMTP host (default=%default)')
			parser.add_argument('--SMTP_PORT', default=config.get('YSE_SMTP_provider','SMTP_PORT'), type=str,
							  help='SMTP port (default=%default)')

		return parser
	
if __name__ == "__main__":
	so = SurveyObs()
	so.do()
