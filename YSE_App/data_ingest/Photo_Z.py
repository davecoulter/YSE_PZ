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

import SciServer
from SciServer import CasJobs
from SciServer import SkyQuery

def jobDescriber(jobDescription):
    # Prints the results of the CasJobs job status functions in a human-readable manner
    # Input: the python dictionary returned by getJobStatus(jobId) or waitForJob(jobId)
    # Output: prints the dictionary to screen with readable formatting
    import pandas
    
    if (jobDescription["Status"] == 0):
        status_word = 'Ready'
    elif (jobDescription["Status"] == 1):
        status_word = 'Started'
    elif (jobDescription["Status"] == 2):
        status_word = 'Cancelling'
    elif (jobDescription["Status"] == 3):
        status_word = 'Cancelled'
    elif (jobDescription["Status"] == 4):
        status_word = 'Failed'
    elif (jobDescription["Status"] == 5):
        status_word = 'Finished'
    else:
        status_word = 'Status not found!!!!!!!!!'

    print('JobID: ', jobDescription['JobID'])
    print('Status: ', status_word, ' (', jobDescription["Status"],')')
    print('Target (context being searched): ', jobDescription['Target'])
    print('Message: ', jobDescription['Message'])
    print('Created_Table: ', jobDescription['Created_Table'])
    print('Rows: ', jobDescription['Rows'])
    wait = pandas.to_datetime(jobDescription['TimeStart']) - pandas.to_datetime(jobDescription['TimeSubmit'])
    duration = pandas.to_datetime(jobDescription['TimeEnd']) - pandas.to_datetime(jobDescription['TimeStart'])
    print('Wait time: ',wait.seconds,' seconds')
    print('Query duration: ',duration.seconds, 'seconds')

class YSE(CronJobBase):

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.Photo_Z.YSE'

    def do(self,user='awe2',password='StandardPassword',search=1,path_to_model='YSE_DNN_photoZ_model_315.hdf5',debug=True):
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
            
            model_filepath = 'MLP_EBOSS_1.hdf5'
            filter_filepath = 'MLP_EBOSS_BINARY_FILTER.hdf5'
			
			
			
            NB_BINS = 272 #filter has 2, model has 272
            BATCH_SIZE = 64
            ZMIN = 0.0
            ZMAX = 0.6 #filter has 0.8
            BIN_SIZE = (ZMAX - ZMIN) / NB_BINS
            range_z = np.linspace(ZMIN, ZMAX, NB_BINS + 1)[:NB_BINS]
            
            transients = Transient.objects.filter(Q(host__isnull=False) & Q(host__photo_z_internal__isnull=True))
            
            my_index = np.array(range(0,len(transients))) #dummy index used in DF, then used to create a mapping from matched galaxies back to these hosts
               
            transient_dictionary = dict(zip(my_index,transients))
                
            RA = []
            DEC = []
            for i,T in enumerate(transients): #get rid of fake entries
                if T.host.ra and T.host.dec:
                    RA.append(T.host.ra)
                    DEC.append(T.host.dec)
                else:
                    transient_dictionary.pop(i)
                
            DF_pre=pd.DataFrame()
            try: DF_pre['myindex'] = list(transient_dictionary.keys())
            except: import pdb; pdb.set_trace()
            DF_pre['RA'] = RA
            DF_pre['DEC'] = DEC
            
            SciServer.Authentication.login(user,password)
            
            try:
                SciServer.SkyQuery.dropTable('PTable1', datasetName='MyDB')
                SciServer.SkyQuery.dropTable('PTable2', datasetName='MyDB')
            except Exception as e:
                print('tables are not in CAS MyDB, continuing')
                print('if system says table is already in DB, contact Andrew Engel')
                
            SciServer.CasJobs.uploadPandasDataFrameToTable(DF_pre, 'PTable1', context='MyDB')
            
            
            myquery = 'SELECT s.myindex, g.dered_u, g.dered_g, g.dered_r, g.dered_i, g.dered_z, '
            myquery+= 'g.dered_u - g.dered_g as ug, g.dered_u - g.dered_r as ur, g.dered_u - g.dered_i as ui, g.dered_u - g.dered_z as uz, '
            myquery+= 'g.dered_g - g.dered_r as gr, g.dered_g - g.dered_i as gi, g.dered_g - g.dered_z as gz, '
            myquery+= 'g.dered_r - g.dered_i as ri, g.dered_r - g.dered_z as rz, g.dered_i - g.dered_z as iz, '
            myquery+= 'g.dered_u / g.dered_z as u_over_z, g.petroR90_r/g.petroR50_r AS C '
            myquery+= 'INTO MyDB.PTable2 '
            myquery+= 'FROM MyDB.PTable1 s '
            myquery+= 'CROSS APPLY dbo.fGetNearestObjEq(s.RA,s.DEC,1.0/60.0) AS nb '
            myquery+= 'INNER JOIN Galaxy g ON g.objID = nb.objID'

            jobID = CasJobs.submitJob(sql=myquery, context="DR16")

            waited=SciServer.CasJobs.waitForJob(jobId=jobID)
            
            jobDescription = CasJobs.getJobStatus(jobID)
    
            jobDescriber(jobDescription)
            
            PhotoDF = SciServer.SkyQuery.getTable('PTable2', datasetName='MyDB', top=10)

            #change this
            PhotoDF.drop_duplicates(subset='#myindex',inplace=True) #neccessary to patch some bugs
            PhotoDF.dropna(inplace=True)
                        
            cols=['dered_u', 'dered_g', 'dered_r', 'dered_i', 'dered_z', 'ug', 'ur', 'ui', 'uz', 'gr', 'gi', 'gz', 'ri', 'rz', 'iz', 'u_over_z', 'C']
            X = PhotoDF[cols]
            #Z = PhotoDF['REDSHIFT'].values
            INDICES = PhotoDF['#myindex'].values
            X = X.values
            
            def Filter():
                IN = keras.layers.Input((17,))
                dense1 = keras.layers.Dense(20,activation=keras.activations.tanh)(IN) #filter has 20, tanh
                drop1 = keras.layers.Dropout(0.05)(dense1)
                
                dense2 = keras.layers.Dense(20,activation=keras.activations.tanh)(drop1) #filter has 20, tanh
                drop2 = keras.layers.Dropout(0.05)(dense2) #0.1
                
                dense3 = keras.layers.Dense(20,activation=keras.activations.tanh)(drop2) #filter has 20, tanh
                drop3 = keras.layers.Dropout(0.05)(dense3)
                
                dense4 = keras.layers.Dense(20,activation=keras.activations.tanh)(drop3) #filter has 20, tanh
                drop4 = keras.layers.Dropout(0.05)(dense4)#0.1
                
                dense5 = keras.layers.Dense(2,activation=keras.activations.softmax)(drop4) #filter has 2
                
                model = keras.Model(inputs=[IN],outputs=[dense5])
                return(model)
            
            def MLP():
                IN = keras.layers.Input((17,))
                dense1 = keras.layers.Dense(45,activation=keras.activations.relu)(IN) #filter has 20, tanh
                drop1 = keras.layers.Dropout(0.05)(dense1)

                dense2 = keras.layers.Dense(45,activation=keras.activations.relu)(drop1) #filter has 20, tanh
                drop2 = keras.layers.Dropout(0.05)(dense2) #0.1

                dense3 = keras.layers.Dense(45,activation=keras.activations.relu)(drop2) #filter has 20, tanh
                drop3 = keras.layers.Dropout(0.05)(dense3)

                dense4 = keras.layers.Dense(45,activation=keras.activations.relu)(drop3) #filter has 20, tanh
                drop4 = keras.layers.Dropout(0.05)(dense4)#0.1

                dense5 = keras.layers.Dense(NB_BINS,activation=keras.activations.softmax)(drop4) #filter has 2

                model = keras.Model(inputs=[IN],outputs=[dense5])
                return(model)
            
            Filter_model = Filter()
            mymodel = MLP()
            
            Filter_model.load_weights('%s/%s'%(djangoSettings.STATIC_ROOT,filter_filepath))
            
            Filtered = Filter_model.predict(X)
            p = 0.01 #results in 97percent true positives, 95percent true negatives...
            
            mymodel.load_weights('%s/%s'%(djangoSettings.STATIC_ROOT,model_filepath))
            
            posterior = mymodel.predict(X[Filtered[:,1] <= 0.01])
            
            point_estimates = np.sum(range_z*posterior,1)
            
            error=np.ones(len(point_estimates))
            for i in range(len(point_estimates)):
                error[i]=np.std(np.random.choice(a=range_z,size=1000,p=posterior[i,:],replace=True)) #this could be parallized i'm sure
            
            #now figure out which are filtered out, ez work
            all_my_indices = PhotoDF['#myindex'].values
            whats_left = all_my_indices[Filtered[:,1]<=0.01]
                
            #now I have an ordered list of whats_left, which are indices that can be used to match to hosts, and an ordered list of posteriors, 
            #uncertainties, and their point estimates. place them into the model by looping over.
            for i,value in enumerate(whats_left):
                T = transient_dictionary[value]
                T.host.photo_z_internal = point_estimates[i]
                T.host.photo_z_err_internal = error[i]
                #T.host.photo_z_posterior = posterior[i] #Gautham suggested we add it to the host model
                #T.host.photo_z_source = 'YSE internal'
                T.host.save() #takes a long time and then my query needs to be reset which is also a long time
            
            print('time taken with upload:', datetime.datetime.utcnow() - nowdate)
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
            #html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            #sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

#IDK = YSE() #why is this suddenly neccessary???
#IDK.do()
