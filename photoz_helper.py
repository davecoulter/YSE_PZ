from astropy.io import ascii
from astropy.table import Table

import sys
import re
import numpy as np
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
    
import pandas as pd
import tensorflow as tf
from tensorflow import keras

import sfdmap

def photo_z_cone(ra,dec,search=5.0,NB_BINS=360,ZMIN=0.0,ZMAX=1.0,sfddata_path='./sfddata-master/'):
    '''
    INPUT:
        ra: degrees
        dec: degrees
        search: arcsec
        
    RETURNS:
        PDFS, point_estimates, objIDs
        
        PDFs: an estimate to the posterior density of probability of redshift, shape [n_returned,360]
        point_estimates: expectation value of redshift shape [n_returned]
        objIDs: the PS1 objIDs of returned items shape [n_returned]
    '''
    m = sfdmap.SFDMap(sfddata_path)
    #First lets define some constants
    b_g = 1.7058474723241624e-09
    b_r = 4.65521985283191e-09
    b_i = 1.2132217745483221e-08
    b_z = 2.013446972858555e-08
    b_y = 5.0575501316874416e-08

    g_mu = 21.92
    r_mu = 20.83
    i_mu = 19.79
    z_mu = 19.24
    y_mu = 18.24

    MEANS = np.array([18.70654578, 17.77948707, 17.34226094, 17.1227873 , 16.92087669,
           19.73947441, 18.89279411, 18.4077393 , 18.1311733 , 17.64741402,
           19.01595669, 18.16447837, 17.73199409, 17.50486095, 17.20389615,
           19.07834251, 18.16996592, 17.71492073, 17.44861273, 17.15508793,
           18.79100201, 17.89569908, 17.45774026, 17.20338482, 16.93640741,
           18.62759241, 17.7453392 , 17.31341498, 17.06194499, 16.79030564,
            0.02543223])

    STDS = np.array([1.7657395 , 1.24853534, 1.08151972, 1.03490545, 0.87252421,
           1.32486758, 0.9222839 , 0.73701807, 0.65002723, 0.41779001,
           1.51554956, 1.05734494, 0.89939638, 0.82754093, 0.63381611,
           1.48411417, 1.05425943, 0.89979008, 0.83934385, 0.64990996,
           1.54735158, 1.10985163, 0.96460099, 0.90685922, 0.74507053,
           1.57813401, 1.14290345, 1.00162105, 0.94634726, 0.80124359,
           0.01687839])
    ra = float(ra)
    dec = float(dec)
    #And define some other stuff from our model training
    BIN_SIZE = (ZMAX - ZMIN) / NB_BINS
    range_z = np.linspace(ZMIN, ZMAX, NB_BINS + 1)[:NB_BINS]
    
    #And now a ton of helper functions...
    def ps1cone(ra,dec,radius,table="mean",release="dr1",format="csv",columns=None,
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs", verbose=False,
               **kw):
        """Do a cone search of the PS1 catalog

        Parameters
        ----------
        ra (float): (degrees) J2000 Right Ascension
        dec (float): (degrees) J2000 Declination
        radius (float): (degrees) Search radius (<= 0.5 degrees)
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        format: csv, votable, json
        columns: list of column names to include (None means use defaults)
        baseurl: base URL for the request
        verbose: print info about request
        **kw: other parameters (e.g., 'nDetections.min':2)
        """

        data = kw.copy()
        data['ra'] = ra
        data['dec'] = dec
        data['radius'] = radius
        return ps1search(table=table,release=release,format=format,columns=columns,
                        baseurl=baseurl, verbose=verbose, **data)


    def ps1search(table="mean",release="dr1",format="csv",columns=None,
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs", verbose=False,
               **kw):
        """Do a general search of the PS1 catalog (possibly without ra/dec/radius)

        Parameters
        ----------
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        format: csv, votable, json
        columns: list of column names to include (None means use defaults)
        baseurl: base URL for the request
        verbose: print info about request
        **kw: other parameters (e.g., 'nDetections.min':2).  Note this is required!
        """

        data = kw.copy()
        if not data:
            raise ValueError("You must specify some parameters for search")
        checklegal(table,release)
        if format not in ("csv","votable","json"):
            raise ValueError("Bad value for format")
        url = "{baseurl}/{release}/{table}.{format}".format(**locals())
        if columns:
            # check that column values are legal
            # create a dictionary to speed this up
            dcols = {}
            for col in ps1metadata(table,release)['name']:
                dcols[col.lower()] = 1
            badcols = []
            for col in columns:
                if col.lower().strip() not in dcols:
                    badcols.append(col)
            if badcols:
                raise ValueError('Some columns not found in table: {}'.format(', '.join(badcols)))
            # two different ways to specify a list of column values in the API
            # data['columns'] = columns
            data['columns'] = '[{}]'.format(','.join(columns))

    # either get or post works
    #    r = requests.post(url, data=data)
        r = requests.get(url, params=data)

        if verbose:
            print(r.url)
        r.raise_for_status()
        if format == "json":
            return r.json()
        else:
            return r.text


    def checklegal(table,release):
        """Checks if this combination of table and release is acceptable

        Raises a VelueError exception if there is problem
        """

        releaselist = ("dr1", "dr2")
        if release not in ("dr1","dr2"):
            raise ValueError("Bad value for release (must be one of {})".format(', '.join(releaselist)))
        if release=="dr1":
            tablelist = ("mean", "stack")
        else:
            tablelist = ("mean", "stack", "detection", "forced_mean")
        if table not in tablelist:
            raise ValueError("Bad value for table (for {} must be one of {})".format(release, ", ".join(tablelist)))


    def ps1metadata(table="mean",release="dr1",
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"):
        """Return metadata for the specified catalog and table

        Parameters
        ----------
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        baseurl: base URL for the request

        Returns an astropy table with columns name, type, description
        """

        checklegal(table,release)
        url = "{baseurl}/{release}/{table}/metadata".format(**locals())
        r = requests.get(url)
        r.raise_for_status()
        v = r.json()
        # convert to astropy table
        tab = Table(rows=[(x['name'],x['type'],x['description']) for x in v],
                   names=('name','type','description'))
        return tab   

    def mastQuery(request):
        """Perform a MAST query.

        Parameters
        ----------
        request (dictionary): The MAST request json object

        Returns head,content where head is the response HTTP headers, and content is the returned data
        """

        server='mast.stsci.edu'

        # Grab Python Version 
        version = ".".join(map(str, sys.version_info[:3]))

        # Create Http Header Variables
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "User-agent":"python-requests/"+version}

        # Encoding the request as a json string
        requestString = json.dumps(request)
        requestString = urlencode(requestString)

        # opening the https connection
        conn = httplib.HTTPSConnection(server)

        # Making the query
        conn.request("POST", "/api/v0/invoke", "request="+requestString, headers)

        # Getting the response
        resp = conn.getresponse()
        head = resp.getheaders()
        content = resp.read().decode('utf-8')

        # Close the https connection
        conn.close()

        return head,content


    def resolve(name):
        """Get the RA and Dec for an object using the MAST name resolver

        Parameters
        ----------
        name (str): Name of object

        Returns RA, Dec tuple with position"""

        resolverRequest = {'service':'Mast.Name.Lookup',
                           'params':{'input':name,
                                     'format':'json'
                                    },
                          }
        headers,resolvedObjectString = mastQuery(resolverRequest)
        resolvedObject = json.loads(resolvedObjectString)
        # The resolver returns a variety of information about the resolved object, 
        # however for our purposes all we need are the RA and Dec
        try:
            objRa = resolvedObject['resolvedCoordinate'][0]['ra']
            objDec = resolvedObject['resolvedCoordinate'][0]['decl']
        except IndexError as e:
            raise ValueError("Unknown object '{}'".format(name))
        return (objRa, objDec)


    def calc_mag(f):
        '''
        Description:
            Calculates the AB magnitude given the flux in Jy

        Usage:
            f: flux in Jy, float or iterable of floats

        References:
            [1] https://iopscience.iop.org/article/10.1088/0004-637X/750/2/99/pdf
                equation 1
        '''
        m = -2.5 * np.log10(f/3631)
        return m



    def convert_flux_to_luptitude(f,b,f_0=3631):
        return -2.5/np.log(10) * (np.arcsinh((f/f_0)/(2*b)) + np.log(b))
    
    radius = search/3600.0 #convert 5 arcsec to degrees
    constraints = {'nDetections.gt':1} #objects with n_detection=1 sometimes just an artifact.

    # strip blanks and weed out blank and commented-out values
    columns ="""objID, raMean, decMean, gFKronFlux, rFKronFlux, iFKronFlux, zFKronFlux, yFKronFlux,
    gFPSFFlux, rFPSFFlux, iFPSFFlux, zFPSFFlux, yFPSFFlux,
    gFApFlux, rFApFlux, iFApFlux, zFApFlux, yFApFlux,
    gFmeanflxR5, rFmeanflxR5, iFmeanflxR5, zFmeanflxR5, yFmeanflxR5,
    gFmeanflxR6, rFmeanflxR6, iFmeanflxR6, zFmeanflxR6, yFmeanflxR6,
    gFmeanflxR7, rFmeanflxR7, iFmeanflxR7, zFmeanflxR7, yFmeanflxR7""".split(',')
    columns = [x.strip() for x in columns]
    columns = [x for x in columns if x and not x.startswith('#')]

    #demand that the photometry is good
    #for column in columns:
    #    constraints[column+'.gt'] = -999

    results = ps1cone(ra,dec,radius,table='forced_mean',release='dr2',columns=columns,verbose=False,**constraints)
    # print first few lines
    lines = results.split('\n')
    if len(lines) > 2:
        values = [line.strip().split(',') for line in lines]
        DF = pd.DataFrame(values[1:-2],columns=values[0])
    else:
        #print('No Matches')
        return np.ones(31)*np.nan

    data_columns = ['gFKronFlux', 'rFKronFlux', 'iFKronFlux', 'zFKronFlux', 'yFKronFlux',
    'gFPSFFlux', 'rFPSFFlux', 'iFPSFFlux', 'zFPSFFlux', 'yFPSFFlux',
    'gFApFlux', 'rFApFlux', 'iFApFlux', 'zFApFlux', 'yFApFlux',
    'gFmeanflxR5', 'rFmeanflxR5', 'iFmeanflxR5', 'zFmeanflxR5', 'yFmeanflxR5',
    'gFmeanflxR6', 'rFmeanflxR6', 'iFmeanflxR6', 'zFmeanflxR6', 'yFmeanflxR6',
    'gFmeanflxR7', 'rFmeanflxR7', 'iFmeanflxR7', 'zFmeanflxR7', 'yFmeanflxR7', 'ebv']
    
    extinction = m.ebv(DF['raMean'].values.astype(np.float32),DF['decMean'].values.astype(np.float32))
    
    DF['ebv'] = list(extinction)
    try:
        closest_return = np.argmin((DF['raMean'].values.astype(np.float32)-ra)**2 + (DF['decMean'].values.astype(np.float32)-dec)**2)
    except ValueError:
        #empty sequence catch. dont know why above isnt catching.
        return np.ones(31)*np.nan
    
    X = DF[data_columns].values.astype(np.float32)
    
    X = X[closest_return:closest_return+1,:] #this keeps 2 dimensional
    
    #convert to luptitudes
    #g
    X[:,[0,5,10,15,20,25]] = convert_flux_to_luptitude(X[:,[0,5,10,15,20,25]],b=b_g)

    #r
    X[:,[1,6,11,16,21,26]] = convert_flux_to_luptitude(X[:,[1,6,11,16,21,26]],b=b_r)

    #i
    X[:,[2,7,12,17,22,27]] = convert_flux_to_luptitude(X[:,[2,7,12,17,22,27]],b=b_i)

    #z
    X[:,[3,8,13,18,23,28]] = convert_flux_to_luptitude(X[:,[3,8,13,18,23,28]],b=b_z)

    #y
    X[:,[4,9,14,19,24,29]] = convert_flux_to_luptitude(X[:,[4,9,14,19,24,29]],b=b_y)
    
    #Noramlize to training data
    X = (X-MEANS)/STDS
    #fix outliers/missing data (but shouldnt exist with forced flux...)
    X[X>20] = 20
    X[X<-20] = -20
    X[np.isnan(X)] = -20
    
    #evaluate using model
    #PDFs = mymodel(X,training=False)
    
    #point_estimates = np.sum(range_z*PDFs,axis=1)
    
    #return PDFs, point_estimates, DF['objID'].values
    return X

