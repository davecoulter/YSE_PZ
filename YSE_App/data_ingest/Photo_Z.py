from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings
import datetime
import numpy as np
import pandas as pd
import os
import pickle
import sys
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
from SciServer import Authentication, CasJobs


#import last because something else uses 'Q'

class YSE(CronJobBase):

	RUN_EVERY_MINS = 10

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.Photo_Z.YSE'

	def do(self,user='awe2',password='StandardPassword',search=1,path_to_model='YSE_App/data_ingest/YSE_DNN_photoZ_model_315.hdf5'):
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

			RA=[] #Needs to be list b/c don't know how many hosts are None
			DEC=[]
			outer_mask = [] #create an integer index mask that we will place values into because some transients don't have a host, even when they make it past the filter????
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
					string = '({},{},{}),|'.format(str(val),str(Ra_batch[val]),str(Dec_batch[val]))
					hold.append(string)

				#Now construct the full query
				sql = "CREATE TABLE #UPLOAD(|id INT PRIMARY KEY,|up_ra FLOAT,|up_dec FLOAT|)|INSERT INTO #UPLOAD|	VALUES|"
				for data in hold:
					sql = sql + data
				#there is a comma that needs to be deleted from the last entry for syntax to work
				sql = sql[0:(len(sql)-2)] + '|'
				#append the rest to it
				sql = sql + "SELECT|p.objID,p.u,p.g,p.r,p.i,p.z,p.extinction_u,p.extinction_g,p.extinction_r,p.extinction_i,p.extinction_z,p.petroRad_u,p.petroRad_g,p.petroRad_r,p.petroRad_i,p.petroRad_z,p.petroR50_r,p.petroR90_r|FROM #UPLOAD as U|OUTER APPLY dbo.fGetNearestObjEq((U.up_ra),(U.up_dec),{}) as N|LEFT JOIN PhotoObjAll AS p ON N.objid=p.objID".format(str(search))
				#change all | to new line: when we change to Unix system will need to change this new line 
				sql = sql.replace('|','\n')
				#login, change to some other credentials later
				Authentication.login('awe2','StandardPassword')
				job = CasJobs.executeQuery(sql,'DR12','pandas') #this line sends and retrieves the result
				
				print('Query {} of {} complete'.format(j+1,Q))
				print(np.shape(job.values))
				job['dered_u'] = job['u'].values - job['extinction_u'].values
				job['dered_g'] = job['g'].values - job['extinction_g'].values
				job['dered_r'] = job['r'].values - job['extinction_r'].values
				job['dered_i'] = job['i'].values - job['extinction_i'].values
				job['dered_z'] = job['z'].values - job['extinction_z'].values
				
				job['u-g']= job['dered_u'].values - job['dered_g'].values
				job['g-r']= job['dered_g'].values - job['dered_r'].values
				job['r-i']= job['dered_r'].values - job['dered_i'].values
				job['i-z']= job['dered_i'].values - job['dered_z'].values
				job['u_over_z']= job['dered_u'].values / job['dered_z'].values
				
				job['C'] = job['petroR90_r'].values/job['petroR50_r'].values
				total_job.append(job)
				#print('length of total job :',len(total_job)) 
			print('left the query loop')
			query_result = pd.concat(total_job)
			#now feed to a RF model for prediction
			#query_result['fake']=np.zeros((len(query_result['dered_u'].values)))
			X = query_result[['dered_u','dered_g','dered_r','dered_i','dered_z','u-g','g-r','r-i','i-z','u_over_z','petroRad_u','petroRad_g','petroRad_r','petroRad_i','petroRad_z','petroR50_r','petroR90_r','C']].values
			#define and load in the model
			def create_model(learning_rate):
    
				model = keras.Sequential([])
				model.add(keras.layers.Dense(input_shape=(18,),units=18,activation=keras.activations.linear)) #tried relu
				#model.add(keras.layers.Dropout(rate=0.1))
				model.add(keras.layers.Dense(units=18,activation=tf.nn.relu)) 
				#model.add(keras.layers.Dropout(rate=0.1))
				model.add(keras.layers.Dense(units=18,activation=tf.nn.relu))
				#model.add(keras.layers.Dropout(rate=0.1))
				model.add(keras.layers.Dense(units=18,activation=tf.nn.relu)) #tf.nn.relu
				#model.add(keras.layers.Dropout(rate=0.1))
				model.add(keras.layers.Dense(units=315,activation=keras.activations.softmax))
				
				#RMS = keras.optimizers.RMSprop(learning_rate=learning_rate)
				adam = keras.optimizers.Adam(lr=learning_rate)
				model.compile(optimizer=adam, loss='categorical_crossentropy') 
				return(model)

			keras.backend.clear_session()
			model = create_model(learning_rate = 1e-3)#couldve been anything for this, just gonna predict
			model.load_weights(path_to_model)
			
			#Need to deal with NANs now since many objects are outside the SDSS footprint, later models will learn to deal with this
			#ideas: need to retain a mask of where the nans are in the row
			mask = np.invert((query_result.isna().any(1).values)) #true was inside SDSS footprint
			#also will want this mask in indices so we can insert the predicted data correctly
			indices=[]
			for i,val in enumerate(mask):
				if val == True:
					indices.append(i)
			
			#predict on data that is not NAN
			predictions = model.predict(X[mask,:], verbose=2)
			np.save('YSE_predictions.npy',predictions)
			n_classes=315
			redshift_bin_middles = np.array(np.array(range(n_classes)) * 0.7/n_classes + 0.7/(n_classes*2))
			def expected_values(Out,bins=redshift_bin_middles):
				Y = np.empty((np.shape(Out)[0]))
				for i in range(np.shape(Out)[0]):
					Y[i] = np.sum(bins * Out[i,:])
				return(Y)
			predictions=expected_values(predictions)
			#print(np.shape(predictions))
			#print(N)
			#make nan array with size of what user asked for
			return_me = np.ones(N)*np.nan
			#now replace nan with the predictions in order
			return_me[indices] = predictions
			return_me_outer = np.ones(N_outer) * np.nan
			return_me_outer[outer_mask] = return_me
			print('time taken:', datetime.datetime.utcnow() - nowdate)
			#print('uploading now')
			tz,mpz = [],[]
			for t,pz in zip(transients,return_me):
				if pz != pz: continue
				host = t.host
				#host.photo_z = pz
				#host.save()
				tz += [host.redshift]
				mpz += [pz]
			plt.plot(tz,mpz,'.',alpha=0.02)
			plt.xlim(-0.01,0.7)
			plt.ylim(-0.01,0.7)
			plt.ylabel('Photo Z')
			plt.xlabel('true Z')
			plt.savefig('test.png')

			print('time taken with upload:', datetime.datetime.utcnow() - nowdate)
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print("""Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
			#html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
			#sendemail(from_addr, user.email, subject, html_msg,
			#		  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
