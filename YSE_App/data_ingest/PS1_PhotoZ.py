from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings

import datetime
import numpy as np
import pandas as pd
import os

import sys
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

from astropy.io import ascii
from astropy.table import Table

import re
import pylab
import json
import requests

try: # Python 3.x
    from urllib.parse import quote as urlencode
    from urllib.request import urlretrieve
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode
    from urllib import urlretrieve

try: # Python 3.x
    import http.client as httplib 
except ImportError:  # Python 2.x
    import httplib 
    
import sfdmap #https://github.com/kbarbary/sfdmap

from photoz_helper import photo_z_cone

class YSE(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.PS1_PhotoZ.YSE'
    
    def do(self):
        try:
            nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
            from django.db.models import Q #HAS To Remain Here, I dunno why
            print('Entered the photo_z Pan-Starrs cron')        
            #save time b/c the other cron jobs print a time for completion
                
            #m = sfdmap.SFDMap(mapdir=djangoSettings.STATIC_ROOT+'/sfddata-master')
            model_filepath = os.path.join(djangoSettings.STATIC_ROOT,'MLP_lupton.hdf5')
            
            transients = Transient.objects.filter(Q(host__isnull=False))

            mymodel = tf.keras.models.load_model(model_filepath,custom_objects={'LeakyReLU':tf.keras.layers.LeakyReLU})
        
            RA = [T.host.ra for T in transients]
            DEC = [T.host.dec for T in transients]
            
            data = []
            print('made it to the cone search step')
            for i,ra,dec in zip(range(len(RA)),RA,DEC):    
                X = photo_z_cone(ra,dec,search=10.0,sfddata_path=djangoSettings.STATIC_ROOT+'/sfddata-master') #given ra return X
                data.append(X.astype(np.float32).reshape(31))
                print(i)
                if i >5:
                    break #debug
            #turn that into a numpy array
            data = np.array(data)
            transients = transients[0:len(data)] #debug
            mask = np.logical_not(np.any(np.isnan(data),axis=1))
            #now evaluate in bulk
            posterior = mymodel(data[mask],training=False).numpy()
            ####Now define some stuff I forgot about
            NB_BINS=360
            ZMIN=0.0
            ZMAX=1.0
            BINS_SIZE = (ZMAX-ZMIN)/NB_BINS
            range_z = np.linspace(ZMIN,ZMAX, NB_BINS+1)[:NB_BINS]
            print('mask: ',mask)
            point_estimates = np.sum(range_z*posterior,1)
            error = np.ones(len(point_estimates))
            for i in range(len(point_estimates)):
                error[i] = np.std(np.random.choice(a=range_z,size=1000,p=posterior[i,:]/np.sum(posterior[i,:]),replace=True)) #this could be parallized i'm sure
            j=0 #skip masked transients
            for i,T in enumerate(transients):
                if not(mask[i]): #skip over hosts we couldnt find
            	    continue
            	
                #T = transient_dictionary[value]
                #if not(T.host.photo_z_lutpon):
                if True:
                    print(point_estimates[j])
                    print(error[j])
                    T.host.photo_z_lupton = point_estimates[j]
                    T.host.photo_z_err_lupton = error[j]
                    j+=1

                    #T.host.save() #takes a long time and then my query needs to be reset which is also a long time
    
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""PS Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
            #html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            #sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
YSE_instance = YSE()
YSE_instance.do()
