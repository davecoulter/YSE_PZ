from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings
#from YSE_App.common.utilities import GetSexigesimalString
#from YSE_App.common.alert import IsK2Pixel, SendTransientAlert
#from YSE_App.common.thacher_transient_search import thacher_transient_search
#from YSE_App.common.tess_obs import tess_obs
#from YSE_App.common.utilities import date_to_mjd
#from YSE_App import *

#from .models import *
#from .serializers import *
import datetime

import numpy as np
import pandas as pd
import os
import pickle

import sys

from sklearn.ensemble import RandomForestRegressor
from SciServer import Authentication, CasJobs

#import last because something else uses 'Q'

class YSE(CronJobBase):

	RUN_EVERY_MINS = 0.1

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.Photo_Z.YSE'

	def do(self,user='awe2',password='StandardPassword',search=1,path_to_model='%s/RF_model.sav'%djangoSettings.STATIC_ROOT):
		"""
		Predicts photometric redshifts from RA and DEC points in SDSS

		An outline of the algorithem is:

		first pull from SDSS u,g,r,i,z magnitudes from SDSS; 
			should be able to handle a list/array of RA and DEC

		place u,g,r,i,z into a vector, append the derived information into the data array

		predict the information from the model

		return the predictions in the same order to the user

		inputs:
			Ra: list or array of len N, right ascensions of target galaxies in decimal degrees
			Dec: list or array of len N, declination of target galaxies in decimal degrees
			search: float, arcmin tolerance to search for the object in SDSS Catalogue
			path_to_model: str, filepath to saved model for prediction
		
		Returns:
			predictions: array of len N, photometric redshift of input galaxy

		"""

		try:
			nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
			from django.db.models import Q #HAS To Remain Here, I dunno why
			print('Entered the photo_z cron')		
			#save time b/c the other cron jobs print a time for completion

			transients = (Transient.objects.filter(Q(host__photo_z__isnull=True) & Q(host__isnull=False)))

			#print('Number of test transients:', len(transients))
			RA=[] #Needs to be list b/c don't know how many hosts are None
			DEC=[]
			outer_mask = [] #create an integer index mask that we will place values into because some hosts dont have a RA and DEC assigned 
			transients_withhost = []
			
			for i,transient_obj in enumerate(transients):
				if transient_obj.host != None:
					RA.append(transient_obj.host.ra)
					DEC.append(transient_obj.host.dec)
					outer_mask.append(i) #provides integer index mask

			outer_mask = np.array(outer_mask) #make that an array

			N_outer = len(transients) #gives size of returned array

			Ra = np.array(RA)
			Dec = np.array(DEC)

			N = len(Ra)#gives size of query array
			Q = N//1000#decompose the length of transients needing classification

			if N%1000 != 0: 
				Q=Q+1 #catch remainder and start a new batch
			total_job = [] #store all pandas job dataframes
			for j in range(Q): #iterate over batches
				if j == (Q-1):
					Ra_batch = Ra[j*1000:((j+1)*1000 + N%1000)] #grab batch remainder
					Dec_batch = Dec[j*1000:((j+1)*1000 + N%1000)]
				else:
					Ra_batch = Ra[j*1000:(j+1)*1000] #other wise grab batch of 1000
					Dec_batch = Dec[j*1000:(j+1)*1000]

				hold=[] #a list for holding the strings that I want to place into an sql query
				for val in range(len(Ra_batch)):
					string = '({},{},{}),|'.format(str(val),str(Ra[val]),str(Dec[val]))
					hold.append(string)

				#Now construct the full query
				sql = "CREATE TABLE #UPLOAD(|id INT PRIMARY KEY,|up_ra FLOAT,|up_dec FLOAT|)|INSERT INTO #UPLOAD|	VALUES|"
				for data in hold:
					sql = sql + data
				#there is a comma that needs to be deleted from the last entry for syntax to work
				sql = sql[0:(len(sql)-2)] + '|'
				#append the rest to it
				sql = sql + "SELECT|p.u,p.g,p.r,p.i,p.z|FROM #UPLOAD as U|OUTER APPLY dbo.fGetNearestObjEq((U.up_ra),(U.up_dec),{}) as N|LEFT JOIN Galaxy AS p ON N.objid=p.objid".format(str(search))
				#change all | to new line: when we change to Unix system will need to change this new line 
				sql = sql.replace('|','\n')
				#login, change to some other credentials later
				Authentication.login('awe2','StandardPassword')
				job = CasJobs.executeQuery(sql,'DR15','pandas') #this lines sends and retrieves the result
				print('Query {} of {} complete'.format(j+1,Q))
				job['u-g']= job['u'].values - job['g'].values
				job['g-r']= job['g'].values - job['r'].values
				job['r-i']= job['r'].values - job['i'].values
				job['i-z']= job['i'].values - job['z'].values
				job['u_over_z']= job['u'].values / job['z'].values
				total_job.append(job)

			print('left the query loop')
			query_result = pd.concat(total_job)
			#now feed to a RF model for prediction
			X = query_result.values
			#load the model, will need to change the path later
			model = pickle.load(open(path_to_model, 'rb'))
			#Need to deal with NANs now since many objects are outside the SDSS footprint, later models will learn to deal with this
			#ideas: need to retain a mask of where the nans are in the row
			mask = np.invert((query_result.isna().any(1).values)) #true was inside SDSS footprint
			#also will want this mask in indices so we can insert the predicted data correctly
			indices=[]
			for i,val in enumerate(mask):
				if val == True:
					indices.append(i)
			predictions = model.predict((X[mask,:]))
			#make nan array with size of what user asked for
			return_me = np.ones(N)*np.nan
			#now replace nan with the predictions in order
			return_me[indices] = predictions
			#something is wrong here!, line works inside a try statement but not outside. raises no error for some reason...?
			return_me_outer = np.ones(N_outer) * np.nan
			return_me_outer[outer_mask] = return_me
			#print('debug: made it here')
			print('time taken:', datetime.datetime.utcnow() - nowdate)
			print('uploading now')
			tz,mpz = [],[]
			for t,pz in zip(transients,return_me):
				if pz != pz: continue
				#print('1')
				host = t.host
				#print('2')
				#import pdb; pdb.set_trace()
				host.photo_z = pz
				#print('3')
				host.save()
				#print('4')
				tz += [host.redshift]
				mpz += [pz]
			plt.plot(tz,mpz,'.')
			plt.savefig('test.png')

			print('time taken with upload:', datetime.datetime.utcnow() - nowdate)
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print("""Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
			#html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
			#sendemail(from_addr, user.email, subject, html_msg,
			#		  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
