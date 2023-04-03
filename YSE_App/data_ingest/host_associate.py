from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings

import datetime
import numpy as np
import pandas as pd
import os

import sys
import os
import sys
from astro_ghost.PS1QueryFunctions import getAllPostageStamps
from astro_ghost.TNSQueryFunctions import getTNSSpectra
from astro_ghost.NEDQueryFunctions import getNEDSpectra
from astro_ghost.ghostHelperFunctions import *
from astropy.coordinates import SkyCoord
from astropy import units as u
import pandas as pd
from datetime import datetime

from astropy.io import ascii
from astropy.table import Table

def coalesce(iterable):
    for el in iterable:
        if el is not None:
            return el
    return None

class YSE(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.host_associate.YSE'
    
    def do(self):
        try:
            #nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
            from django.db.models import Q #HAS To Remain Here,
            #save time b/c the other cron jobs print a time for completion

            if not os.path.exists(f'{djangoSettings.ghost_path}/database/GHOST.csv'):
                getGHOST(real=True, verbose=False, installpath=djangoSettings.ghost_path)
            #we might reset this once when we update
            
            transients = Transient.objects.filter(~Q(tags__name__in='YSE') &
                                                  Q(host__isnull=False) &
                                                  Q(host__panstarrs_objid__isnull=True))
            #transients = (Transient.objects.filter(Q(host__isnull=False)))
            
            #get rid of objects that have panstarrs_objids already
            #mask=[]
            #for T in transients:
            #    if T.host.panstarrs_objid:
            #        mask.append(False)
            #    else:
            #        mask.append(True)
            
            #reduce transients using the mask
            #transients = [T for i,T in enumerate(transients) if mask[i]]


            #construct a new mask
            mask = []
            for i,T in enumerate(transients):
                if T.host.redshift is not None or T.redshift is not None:
                   redshift = coalesce((T.host.redshift,T.redshift))
                   t_ra = np.pi*T.ra/180
                   t_dec = np.pi*T.dec/180
                   h_ra = np.pi*T.host.ra/180
                   h_dec = np.pi*T.host.dec/180
                   
                   if (np.arccos(np.sin(t_dec)*np.sin(h_dec) + np.cos(t_dec)*np.cos(h_dec)*np.cos(abs(t_ra - h_ra)))*(3e5*redshift/73)/(pow(1.0 + redshift, 2)*1000) ) < 80:
                       mask.append(False)
                   else:
                       mask.append(True)
                       continue
                mask.append(True)
                continue
            
            #reduce transients using the mask
            transients = [T for i,T in enumerate(transients) if mask[i]]
            
            #Now get the coordinates and make up a unique temp name
            #for all the transients in order
            RA = [T.ra for i,T in enumerate(transients)]
            DEC = [T.dec for i,T in enumerate(transients)]
            snCoord = [SkyCoord(ra*u.deg, dec*u.deg, frame='icrs') for ra,dec in zip(RA,DEC)] 
            
            snName = ['SN'+T.name for i,T in enumerate(transients)]
            hosts = getTransientHosts(snName, snCoord, verbose=True, starcut='gentle', ascentMatch=False)
            
            #hosts is a df that may or may not have the hosts, so 
            #we can use the fact that the names are ordered to
            #find which ones we got back, and place them correctly
            for i,T in enumerate(transients):
            
                if len(hosts[hosts['TransientName']=='SN'+str(i)]) ==0:
                    continue

                T.host.ra = hosts[hosts['TransientName']=='SN'+str(i)]['raMean'].values[0]
                T.host.dec = hosts[hosts['TransientName']=='SN'+str(i)]['decMean'].values[0]
                T.host.panstarrs_objid = hosts[hosts['TransientName']=='SN'+str(i)]['objID'].values[0]
                T.host.save()

    
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""GHOST cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
            #html_msg = """host associate cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            #sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
