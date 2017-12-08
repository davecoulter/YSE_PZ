#!/usr/bin/env python
# D. Jones - 12/2/17

import os
import json
import urllib.request
import ast
from astropy.time import Time
import numpy as np

class upload():
    def __init__(self):
        pass
    def add_options(self, parser=None, usage=None, config=None):
        import optparse
        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_option('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_option('--clobber', default=False, action="store_true",
                          help='clobber output file')
        parser.add_option('-p','--photometry', default=False, action="store_true",
                          help='input file is photometry')
        parser.add_option('-s','--spectrum', default=False, action="store_true",
                          help='input file is a spectrum')
        parser.add_option('-i','--inputfile', default=None, type="string",
                          help='input file ')
        parser.add_option('--trid', default=None, type="string",
                          help='transient ID')
        parser.add_option('--status', default='FollowupFinished', type="string",
                          help='transient status (new, follow, etc')
        parser.add_option('--obsgroup', default='Foundation', type="string",
                          help='group who observed this transient')
        parser.add_option('--inputformat', default='snana', type="string",
                          help="input file format, can be 'basic' or 'snana' (photometry only) ")
        parser.add_option('--instrument', default='GPC1', type="string",
                          help="instrument name")
        parser.add_option('-u','--useheader', default=False, action="store_true",
                          help="if set, grab keys from the file header and try to POST to db")
        parser.add_option('--postURL',default="https://ziggy.ucolick.org/yse_test/api", type="string",
                          help="POST URL root (default=%default)")
        parser.add_option('--user',default="djones", type="string",
                          help="db username (default=%default)")
        parser.add_option('--password',default="BossTent1", type="string",
                          help="db password (default=%default)")
        
        return(parser)

    def uploadHeader(self,sn):
        # first figure out the status and obs_group foreign keys
        statusgetcmd = "http -a %s:%s GET %s/transientstatuses/"%(
            self.options.user,self.options.password,self.options.postURL)
        statusid = getIDfromName(statusgetcmd,self.options.status)
        obsgetcmd = "http -a %s:%s GET %s/observationgroups/"%(
            self.options.user,self.options.password,self.options.postURL)
        obsid = getIDfromName(obsgetcmd,self.options.obsgroup)
        if not obsid or not statusid: raise RuntimeError('Error : obsgroup or status not found in DB!')

        transgetcmd = "http -a %s:%s GET %s/transients/"%(
            self.options.user,self.options.password,self.options.postURL)
        transid = getIDfromName(transgetcmd,sn.SNID)

        if not transid:
            # upload the basic transient data
            basicdatacmd = "http -a %s:%s POST %s/transients/ name='%s' ra='%s' dec='%s' status='%s' obs_group=%s"%(
                self.options.user,self.options.password,self.options.postURL,sn.SNID,sn.RA.split()[0],sn.DECL.split()[0],
                statusid,obsid)
        else:
            basicdatacmd = "http -a %s:%s PUT %s/transients/ name='%s' ra='%s' dec='%s' status=%s obs_group=%s"%(
                self.options.user,self.options.password,self.options.postURL,sn.SNID,sn.RA.split()[0],sn.DECL.split()[0],
                statusid,obsid)

        output = os.popen(basicdatacmd).read()
        basictrans = json.loads(output)
        
    def uploadSNANAPhotometry(self):
        import snana
        sn = snana.SuperNova(self.options.inputfile)

        if self.options.useheader:
            transdata = self.uploadHeader(sn)

        # create photometry object, if it doesn't exist
        getphotcmd = "http -a %s:%s GET %s/transientphotometry/"%(
            self.options.user,self.options.password,self.options.postURL)
        photheaderdata = json.loads(os.popen(getphotcmd).read())
        self.parsePhotHeaderData(photheaderdata,sn.SNID)
        
        # get the filter IDs
        
        # upload the photometry
        for mjd,flux,fluxerr,mag,magerr,flt in zip(sn.MJD,sn.FLUXCAL,sn.FLUXCALERR,sn.MAG,sn.MAGERR,sn.FLT):
            PhotUploadFmt = ["http -a %s:%s %s %s/transientphotdata/ "]
            PhotUploadFmt.append('obs_date="%s" flux=%.4f flux_err=%.4f ')
            PhotUploadFmt.append('photometry=%s ')

            obsdate = Time(mjd,format='mjd').isot
            bandid = self.getBandfromDB('photometricbands',flt,self.instid)
            if flux > 0:
                PhotUploadFmt.append('mag=%.4f mag_err=%.4f forced=1 dq=1 band=%s flux_zero_point=27.5 ')
                PhotUploadFmt = "".join(PhotUploadFmt)
                photcmd = (PhotUploadFmt%(self.options.user,self.options.password,"POST",
                                          self.options.postURL,obsdate,flux,fluxerr,
                                          self.photdataid,mag+27.5,magerr,bandid)).replace('nan','-99')
            else:
                PhotUploadFmt.append('forced=1 dq=1 band=%s flux_zero_point=27.5 ')
                PhotUploadFmt = "".join(PhotUploadFmt)
                photcmd = (PhotUploadFmt%(self.options.user,self.options.password,"POST",
                                          self.options.postURL,obsdate,flux,fluxerr,
                                          self.photdataid,bandid))

            photdata = runDBcommand(photcmd)

    def getPhotObjfromDB(self,tablename,transient,instrument,obsgroup):
        cmd = 'http -a %s:%s GET %s/%s/'%(
            self.options.user,self.options.password,self.options.postURL,tablename)
        output = os.popen(cmd).read()
        data = json.loads(output)

        translist,instlist,obsgrouplist,idlist = [],[],[],[]
        for i in range(len(data)):
            obsgrouplist += [data[i]['obs_group']]
            instlist += [data[i]['instrument']]
            translist += [data[i]['transient']]
            idlist += [data[i]['url']]

        if obsgroup not in obsgrouplist or instrument not in instlist or transient not in translist:
            return(None)

        return(np.array(idlist)[np.where((np.array(translist) == transient) &
                                         (np.array(instlist) == instrument) &
                                         (np.array(obsgrouplist) == obsgroup))][0])

                
    def getBandfromDB(self,tablename,fieldname,instrument):
        cmd = 'http -a %s:%s GET %s/%s/'%(
            self.options.user,self.options.password,self.options.postURL,tablename)
        output = os.popen(cmd).read()
        data = json.loads(output)

        idlist,namelist,instlist = [],[],[]
        for i in range(len(data)):
            namelist += [data[i]['name']]
            idlist += [data[i]['url']]
            instlist += [data[i]['instrument']]

        if fieldname not in namelist or instrument not in instlist: return(None)

        return(np.array(idlist)[np.where((np.array(namelist) == fieldname) &
                                         (np.array(instlist) == instrument))][0])
            
    def getIDfromName(self,tablename,fieldname):
        cmd = 'http -a %s:%s GET %s/%s/'%(
            self.options.user,self.options.password,self.options.postURL,tablename)
        output = os.popen(cmd).read()
        data = json.loads(output)

        idlist,namelist = [],[]
        for i in range(len(data)):
            namelist += [data[i]['name']]
            idlist += [data[i]['url']]

        if fieldname not in namelist: return(None)

        return(np.array(idlist)[np.where(np.array(namelist) == fieldname)][0])
        
    def parsePhotHeaderData(self,photheaderdata,snid):

        # if no photometry header, then create one
        self.instid = getIDfromName('http -a %s:%s GET %s/instruments/'%(
            self.options.user,self.options.password,self.options.postURL),self.options.instrument)
        self.obsgroupid = getIDfromName('http -a %s:%s GET %s/observationgroups/'%(
            self.options.user,self.options.password,self.options.postURL),self.options.obsgroup)
        self.snidid = getIDfromName('http -a %s:%s GET %s/transients/'%(
            self.options.user,self.options.password,self.options.postURL),snid)

        inDB = False
        if type(photheaderdata) == list:
            self.photdataid = self.getPhotObjfromDB(
                'transientphotometry',self.snidid,self.instid,self.obsgroupid)
            if self.photdataid: inDB = True
            
        if not inDB:

            postphotcmd = ["http "]
            postphotcmd.append("-a %s:%s POST %s/transientphotometry/ "%(self.options.user,self.options.password,self.options.postURL))
            postphotcmd.append("instrument=%s "%(instid))
            postphotcmd.append("obs_group='%s' "%(obsgroupid))
            postphotcmd.append("transient='%s' "%(snidid))
            postphotcmd = ''.join(postphotcmd)
            postphotdata = runDBcommand(postphotcmd)

            self.photdataid = postphotdata['url']

            
    def uploadBasicPhotometry(self):
        from txtobj import txtobj

    def uploadBasicSpectrum(self):
        from txtobj import txtobj

def runDBcommand(cmd):
    try:
        return(json.loads(os.popen(cmd).read()))
    except:
        import pdb; pdb.set_trace()
        raise RuntimeError('Error : cmd %s failed!!')
    
def getIDfromName(cmd,name):
    output = os.popen(cmd).read()
    data = json.loads(output)

    idlist,namelist = [],[]
    for i in range(len(data)):
        namelist += [data[i]['name']]
        idlist += [data[i]['url']]

    if name not in namelist: return(None)

    return(np.array(idlist)[np.where(np.array(namelist) == name)][0])
    
if __name__ == "__main__":

    import os
    import optparse

    useagestring='uploadData.py [options]'
    upl = upload()
    parser = upl.add_options(usage=useagestring)
    options,  args = parser.parse_args()
    upl.options = options
    
    if options.photometry and options.inputformat == 'basic':
        upl.uploadBasicPhotometry()
    elif options.photometry and options.inputformat == 'snana':
        upl.uploadSNANAPhotometry()
    elif options.spectrum:
        upl.uploadBasicSpectrum()
    else:
        raise RuntimeError('Error : input option not found')
