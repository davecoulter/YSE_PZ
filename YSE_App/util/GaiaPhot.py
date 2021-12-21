import pandas as pd
import datetime
import numpy as np

def get_gaia_list(look_back_days):
    gaia_list = pd.read_csv('http://gsaweb.ast.cam.ac.uk/alerts/alerts.csv')
    datelist = np.array([(datetime.datetime.now()-datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')).\
                         total_seconds()/86400 for date in a[' Date'].values])
    index = datelist<look_back_days
    targets = gaia_list[index]
    return targets

def get_gaia_phot(name, targets):
    index = (targets[' TNSid']=='AT'+name) | (targets[' TNSid']=='SN'+name) 
    if sum(index) >0:
        gaia_name = targets[index]['#Name'].values[0]
        data = pd.read_csv('http://gsaweb.ast.cam.ac.uk/alerts/alert/'+gaia_name+'/lightcurve.csv/')
        return data
    else:
        return 
