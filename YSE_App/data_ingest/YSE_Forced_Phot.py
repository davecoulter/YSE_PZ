#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from astropy.io import fits
import astropy.table as at
from YSE_App.models import *
import datetime
from YSE_App.common.utilities import date_to_mjd
from YSE_App.util.skycells import getskycell
from io import BytesIO
import pylab as plt
from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
import time
import configparser
from lxml import html
import shutil
import tempfile
import os
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re

#bad_flags = ['0x00001000','0x20000000','0x40000000','0x80000000']

default_stamp_header = fits.Header()
default_stamp_header['XTENSION'] = 'BINTABLE'         
default_stamp_header['BITPIX']  = 8
default_stamp_header['NAXIS']   = 2
default_stamp_header['NAXIS1']  = 476
default_stamp_header['NAXIS2']  = 9
default_stamp_header['PCOUNT']  = 0
default_stamp_header['GCOUNT']  = 1
default_stamp_header['TFIELDS'] = 24
default_stamp_header['TTYPE1']  = 'ROWNUM  '
default_stamp_header['TFORM1']  = 'J       '
default_stamp_header['TTYPE2']  = 'PROJECT '
default_stamp_header['TFORM2']  = '16A     '
default_stamp_header['TTYPE3']  = 'SURVEY_NAME'
default_stamp_header['TFORM3']  = '16A     '
default_stamp_header['TTYPE4']  = 'IPP_RELEASE'
default_stamp_header['TFORM4']  = '16A     '
default_stamp_header['TTYPE5']  = 'JOB_TYPE'
default_stamp_header['TFORM5']  = '16A     '
default_stamp_header['TTYPE6']  = 'OPTION_MASK'
default_stamp_header['TFORM6']  = 'J       '
default_stamp_header['TTYPE7']  = 'REQ_TYPE'
default_stamp_header['TFORM7']  = '16A     '
default_stamp_header['TTYPE8']  = 'IMG_TYPE'
default_stamp_header['TFORM8']  = '16A     '
default_stamp_header['TTYPE9']  = 'ID      '
default_stamp_header['TFORM9']  = '16A     '
default_stamp_header['TTYPE10'] = 'TESS_ID '
default_stamp_header['TFORM10'] = '64A     '
default_stamp_header['TTYPE11'] = 'COMPONENT'
default_stamp_header['TFORM11'] = '64A     '
default_stamp_header['TTYPE12'] = 'COORD_MASK'
default_stamp_header['TFORM12'] = 'J       '
default_stamp_header['TTYPE13'] = 'CENTER_X'
default_stamp_header['TFORM13'] = 'D       '
default_stamp_header['TTYPE14'] = 'CENTER_Y'
default_stamp_header['TFORM14'] = 'D       '
default_stamp_header['TTYPE15'] = 'WIDTH   '
default_stamp_header['TFORM15'] = 'D       '
default_stamp_header['TTYPE16'] = 'HEIGHT  '
default_stamp_header['TFORM16'] = 'D       '
default_stamp_header['TTYPE17'] = 'DATA_GROUP'
default_stamp_header['TFORM17'] = '64A     '
default_stamp_header['TTYPE18'] = 'REQFILT '
default_stamp_header['TFORM18'] = '16A     '
default_stamp_header['TTYPE19'] = 'MJD_MIN '
default_stamp_header['TFORM19'] = 'D       '
default_stamp_header['TTYPE20'] = 'MJD_MAX '
default_stamp_header['TFORM20'] = 'D       '
default_stamp_header['TTYPE21'] = 'RUN_TYPE'
default_stamp_header['TFORM21'] = '16A     '
default_stamp_header['TTYPE22'] = 'FWHM_MIN'
default_stamp_header['TFORM22'] = 'D       '
default_stamp_header['TTYPE23'] = 'FWHM_MAX'
default_stamp_header['TFORM23'] = 'D       '
default_stamp_header['TTYPE24'] = 'COMMENT '
default_stamp_header['TFORM24'] = '64A     '
default_stamp_header['EXTNAME'] = 'PS1_PS_REQUEST'
default_stamp_header['REQ_NAME'] = 'yse.meh_stamp_testid200410'
default_stamp_header['EXTVER']  = '2       '
default_stamp_header['ACTION']  = 'PROCESS '
default_stamp_header['EMAIL']   = 'yse@qub.ac.uk'

default_forcedphot_header = fits.Header()
default_forcedphot_header['XTENSION'] = 'BINTABLE'
default_forcedphot_header['BITPIX']   = 8
default_forcedphot_header['NAXIS']    = 2
default_forcedphot_header['NAXIS1']   = 84
default_forcedphot_header['NAXIS2']   = 8
default_forcedphot_header['PCOUNT']   = 0
default_forcedphot_header['GCOUNT']   = 1
default_forcedphot_header['TFIELDS']  = 9
default_forcedphot_header['TTYPE1']   = 'ROWNUM  '
default_forcedphot_header['TFORM1']   = '20A     '
default_forcedphot_header['TTYPE2']   = 'RA1_DEG '
default_forcedphot_header['TFORM2']   = 'D       '
default_forcedphot_header['TTYPE3']   = 'DEC1_DEG'
default_forcedphot_header['TFORM3']   = 'D       '
default_forcedphot_header['TTYPE4']   = 'RA2_DEG '
default_forcedphot_header['TFORM4']   = 'D       '
default_forcedphot_header['TTYPE5']   = 'DEC2_DEG'
default_forcedphot_header['TFORM5']   = 'D       '
default_forcedphot_header['TTYPE6']   = 'FILTER  '
default_forcedphot_header['TFORM6']   = '20A     '
default_forcedphot_header['TTYPE7']   = 'MJD-OBS '
default_forcedphot_header['TFORM7']   = 'D       '
default_forcedphot_header['TTYPE8']   = 'FPA_ID  '
default_forcedphot_header['TFORM8']   = 'J       '
default_forcedphot_header['TTYPE9']   = 'COMPONENT'
default_forcedphot_header['TFORM9']   = '64A     '
default_forcedphot_header['EXTNAME']  = 'MOPS_DETECTABILITY_QUERY'
default_forcedphot_header['QUERY_ID'] = 'yse.meh_det_test200410'
default_forcedphot_header['EXTVER']   = '2       '
default_forcedphot_header['OBSCODE']  = '566     '
default_forcedphot_header['STAGE']    = 'WSdiff  '
default_forcedphot_header['EMAIL']    = 'yse@qub.ac.uk'

from astropy.visualization import PercentileInterval, AsinhStretch
from tendo import singleton

def get_camera(exp_name):
    if re.match('o[0-9][0-9][0-9][0-9]g[0-9][0-9][0-9][0-9]o',exp_name):
        return 'GPC1'
    elif re.match('o[0-9][0-9][0-9][0-9]h[0-9][0-9][0-9][0-9]o',exp_name):
        return 'GPC2'
    else: raise RuntimeError('couldn\'t parse exp name')

def fits_to_png(ff,outfile,log=False):
    plt.clf()
    ax = plt.axes()
    fim = ff[1].data
    # replace NaN values with zero for display
    fim[np.isnan(fim)] = 0.0
    # set contrast to something reasonable
    transform = AsinhStretch() + PercentileInterval(99.5)
    bfim = transform(fim)
    ax.imshow(bfim,cmap="gray",origin="lower")
    circle = plt.Circle((np.shape(fim)[0]/2-1, np.shape(fim)[1]/2-1), 15, color='r',fill=False)
    ax.add_artist(circle)
    plt.gca().set_axis_off()
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                        hspace = 0, wspace = 0)
    plt.margins(0,0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.savefig(outfile,bbox_inches = 'tight',pad_inches = 0)
    
def fluxToMicroJansky(adu, exptime, zp):
    factor = 10**(-0.4*(zp-23.9))
    uJy = adu/exptime*factor
    return uJy

def parse_mdc(mdc_text):

    mdc = {}
    for line in mdc_text.split('\n'):
        if line.startswith('ROWNUM'):
            rownum = int(line.split()[-1])
            mdc[rownum] = {}
        elif line.startswith('ROW'): continue
        elif line.startswith('END'): continue
        elif not line: continue
        else:
            mdc[rownum][line.split()[0]] = line.split()[2]
            
    return mdc
            
class ForcedPhot(CronJobBase):

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhot'

    def __init__(self):
        
        self.debug = False
        if self.debug:
            print('debug mode enabled')
    
    def do(self):
        code = 'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhot'
        
        self.debug = False

        # options
        parser = self.add_options(usage='')
        options,  args = parser.parse_known_args()
        config = configparser.ConfigParser()
        config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
        parser = self.add_options(usage='',config=config)
        options,  args = parser.parse_known_args()
        self.options = options

        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "YSE_PZ Forced Photometry Upload Failure"
        html_msg = "Alert : YSE_PZ Forced Photometry Failed to upload transients in YSE_Forced_Phot.py\n"
        html_msg += "Error : %s"

        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="10")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)        

        try:
            tstart = time.time()

            #nsn = self.doall_main()
            nsn = self.main()
            print('success')
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""Forced phot cron failed with error %s at line number %s"""%(
                e,exc_tb.tb_lineno))
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('YSE_PZ Forced Photometry took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

    def add_options(self, parser=None, usage=None, config=None):
        import argparse
        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
        parser.add_argument('--clobber', default=False, action="store_true",
                          help='clobber output file')
        parser.add_argument('-s','--settingsfile', default=None, type=str,
                          help='settings file (login/password info)')
        parser.add_argument('--max_time_minutes', default=30, type=str,
                          help='look for transients created in the last x minutes (default=%default)')
        parser.add_argument('--max_days_yseimage', default=7, type=str,
                          help='look for YSE survey images in the last x days (default=%default)')
        
        if config:
            parser.add_argument('--STATIC', default=config.get('site_settings','STATIC'), type=str,
                                help='static directory (default=%default)')
            parser.add_argument('--upload', default=config.get('yse','upload'), type=str,
                              help='stamp upload server (default=%default)')
            parser.add_argument('--stamp', default=config.get('yse','stamp'), type=str,
                              help='stamp upload server (default=%default)')
            parser.add_argument('--detectability', default=config.get('yse','detectability'), type=str,
                              help='stamp upload server (default=%default)')
            parser.add_argument('--skycell', default=config.get('yse','skycell'), type=str,
                              help='stamp upload server (default=%default)')
            parser.add_argument('--ifauser', default=config.get('yse','user'), type=str,
                              help='stamp upload server (default=%default)')
            parser.add_argument('--ifapass', default=config.get('yse','pass'), type=str,
                              help='stamp upload server (default=%default)')

            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbemail', default=config.get('main','dbemail'), type=str,
                              help='database login, if post=True (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                              help='database password, if post=True (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                                help='database password, if post=True (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                              help='URL to POST transients to a database (default=%default)')

            parser.add_argument('--SMTP_LOGIN', default=config.get('SMTP_provider','SMTP_LOGIN'), type=str,
                              help='SMTP login (default=%default)')
            parser.add_argument('--SMTP_HOST', default=config.get('SMTP_provider','SMTP_HOST'), type=str,
                              help='SMTP host (default=%default)')
            parser.add_argument('--SMTP_PORT', default=config.get('SMTP_provider','SMTP_PORT'), type=str,
                              help='SMTP port (default=%default)')

        else:
            pass


        return(parser)

    def doall_main(self):
        min_date = datetime.datetime.utcnow() - datetime.timedelta(days=30) #minutes=self.options.max_time_minutes)
        transients = Transient.objects.filter(
            created_date__gte=min_date).filter(~Q(tags__name='YSE') & ~Q(tags__name='YSE Stack')).order_by('-created_date')
        for t in transients:
            print(t.name)
            self.main(transient_name=t.name)
            
    def main(self,transient_name=None,update_forced=False):

        # candidate transients
        min_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=self.options.max_time_minutes)
        nowmjd = date_to_mjd(datetime.datetime.utcnow())
        transient_name='2022ann'; self.options.max_days_yseimage = 120
        if transient_name is None and not update_forced:
            transients = Transient.objects.filter(
                created_date__gte=min_date).filter(~Q(tags__name='YSE') & ~Q(tags__name='YSE Stack')).order_by('-created_date')
        elif update_forced:
            min_date_forcedphot=datetime.datetime.utcnow() - datetime.timedelta(days=7)
            transients = Transient.objects.filter(
                ~Q(tags__name='YSE') &
                ~Q(tags__name='YSE Stack') &
                Q(transientphotometry__transientphotdata__obs_date__gt=min_date_forcedphot) &
                Q(disc_date__gt=datetime.datetime.utcnow() - datetime.timedelta(days=1000))).distinct()
        else:
            transients = Transient.objects.filter(name=transient_name)

        # candidate survey images
        survey_images = SurveyObservation.objects.filter(status__name='Successful').\
            filter(obs_mjd__gt=nowmjd-self.options.max_days_yseimage).filter(diff_id__isnull=False)
        transient_list,ra_list,dec_list,diff_id_list,warp_id_list,mjd_list,filt_list,camera_list = \
            [],[],[],[],[],[],[],[]

        for t in transients:

            sit = survey_images.filter(Q(survey_field__ra_cen__gt=t.ra-1.55) | Q(survey_field__ra_cen__lt=t.ra+1.55) |
                                       Q(survey_field__dec_cen__gt=t.dec-1.55) | Q(survey_field__dec_cen__lt=t.dec+1.55))

            if len(sit):
                sct = SkyCoord(t.ra,t.dec,unit=u.deg)
            for s in sit:
                sc = SkyCoord(s.survey_field.ra_cen,s.survey_field.dec_cen,unit=u.deg)
                if sc.separation(sct).deg < 1.65:
                    transient_list += [t.name]
                    ra_list += [t.ra]
                    dec_list += [t.dec]
                    diff_id_list += [s.diff_id]
                    warp_id_list += [s.warp_id]
                    mjd_list += [s.obs_mjd]
                    filt_list += [s.photometric_band.name]
                    import pdb; pdb.set_trace()
                    camera_list += [get_camera(s.warp_id).lower()] #s.survey_field.instrument.name.lower()]

        nt = len(np.unique(transient_list))
        print('{} transients to upload!'.format(nt))
        if nt == 0: return 0
        print('trying to upload transients:')
        for t in np.unique(transient_list):
            print(t)

        stamp_request_name,skycelldict = self.stamp_request(
            transient_list,ra_list,dec_list,camera_list,diff_id_list,warp_id_list,[])
        print('submitted stamp request {}'.format(stamp_request_name))

        phot_request_names = self.forcedphot_request(
            transient_list,ra_list,dec_list,mjd_list,filt_list,camera_list,diff_id_list,skycelldict)
        print('submitted phot requests:')
        for prn in phot_request_names: print(prn)

        print('jobs were submitted, waiting up to 10 minutes for them to finish')
        # wait until the jobs are done
        jobs_done = False
        tstart = time.time()
        while not jobs_done and time.time()-tstart < 600:
            print('waiting 60 seconds to check status...')
            time.sleep(60)
            done_stamp,success_stamp = self.get_status(stamp_request_name)
            doneall_phot = True
            for phot_request_name in phot_request_names:
                done_phot,success_phot = self.get_status(phot_request_name)
                if not done_phot: doneall_phot = False
            if done_stamp and doneall_phot: jobs_done = True
        
        if not jobs_done:
            raise RuntimeError('job timeout!')
        
        # get the data from the jobs
        img_dict = self.get_stamps(stamp_request_name,transient_list)

        # save to data model
        phot_dict = self.get_phot(phot_request_names,transient_list,ra_list,dec_list,img_dict)
        
        #write the stack jobs
        transient_list,ra_list,dec_list,stack_id_list = [],[],[],[]
        for t in phot_dict.keys():
            for s,r,d in zip(phot_dict[t]['stack_id'],phot_dict[t]['ra'],phot_dict[t]['dec']):
                stack_id_list += [s]
                ra_list += [r]
                dec_list += [d]
                transient_list += [t]
                import pdb; pdb.set_trace()
                camera_list += ['gpc1']
                
        stack_request_name,skycelldict = self.stamp_request(
            transient_list,ra_list,dec_list,camera_list,[],[],stack_id_list,skycelldict=skycelldict)
        print('submitted stack request {}'.format(stack_request_name))
        
        # submit the stack jobs
        tstart = time.time()
        jobs_done = False
        while not jobs_done and time.time()-tstart < 600:
            print('waiting 60 seconds to check status...')
            time.sleep(60)
            done_stamp,success_stamp = self.get_status(stack_request_name)
            if done_stamp: jobs_done = True
        if not success_stamp:
            pass

            #raise RuntimeError('jobs failed!')
        if not jobs_done:
            raise RuntimeError('job timeout!')
        
        # get the data from the stack job
        stack_img_dict = self.get_stamps(stack_request_name,transient_list)

        # save to data model
        self.write_to_db(phot_dict,img_dict,stack_img_dict)

        print('uploaded transients:')
        for t in img_dict.keys():
            print(t)
        return len(list(img_dict.keys()))
        
    def get_images(self,img_dict):

        if not djangoSettings.DEBUG: basedir = "%sYSE_App/images/stamps"%(djangoSettings.STATIC_ROOT)
        else: basedir = "%s/YSE_App%sYSE_App/images/stamps"%(djangoSettings.BASE_DIR,self.options.STATIC)
        for k in img_dict.keys():
            for img_key_in,img_key_out in zip(['warp_image_link','diff_image_link','stack_image_link'],
                                              ['warp_file','diff_file','stack_file']):

                img_dict[k][img_key_out] = []
                img_dict[k][img_key_out+'_png'] = []

                session = requests.Session()
                session.auth = (self.options.ifauser,self.options.ifapass)
                for i in range(len(img_dict[k][img_key_in])):
                    if img_dict[k][img_key_in][i] is None:
                        img_dict[k][img_key_out] += [None]
                        img_dict[k][img_key_out+'_png'] += [None]
                        continue
                    
                    outdir = "%s/%s/%i"%(basedir,k,int(float(img_dict[k]['%s_mjd'%img_key_in.replace('_link','')][i])))
                    
                    if not os.path.exists(outdir):
                        os.makedirs(outdir)

                    filename = img_dict[k][img_key_in][i].split('/')[-1]
                    outfile = "{}/{}".format(outdir,filename)
                    
                    fits_response = session.get(img_dict[k][img_key_in][i],stream=True)
                    with open(outfile,'wb') as fout:
                        shutil.copyfileobj(fits_response.raw, fout)

                    ff = fits.open(outfile)
                    if 'diff' in img_key_in: fits_to_png(ff,outfile.replace('fits','png'),log=False)
                    else: fits_to_png(ff,outfile.replace('fits','png'),log=True)
                    img_dict[k][img_key_out] += [outfile.replace('{}/'.format(basedir),'')]
                    img_dict[k][img_key_out+'_png'] += [outfile.replace('{}/'.format(basedir),'').replace('.fits','.png')]
                    
        return img_dict
                    
    def write_to_db(self,phot_dict,img_dict,stack_img_dict):

        img_dict = self.get_images(img_dict)
        stack_img_dict = self.get_images(stack_img_dict)

        tdict = {}
        for k in img_dict.keys():

            PhotUploadAll = {"mjdmatchmin":0.0001,
                             "clobber":True}
            photometrydict_ps1 = {'instrument':'GPC1',
                                  'obs_group':'YSE',
                                  'photdata':{}}
            photometrydict_ps2 = {'instrument':'GPC2',
                                  'obs_group':'YSE',
                                  'photdata':{}}

            tdict[k] = {'name':k,
                        #'obs_group':'YSE',
                        'tags':['YSE Forced Phot']}

            for i in range(len(img_dict[k]['diff_image_id'])):

                if k in stack_img_dict.keys():
                    stack_file = stack_img_dict[k]['stack_file'][0]
                    stack_png = stack_img_dict[k]['stack_file_png'][0]
                else:
                    stack_file,stack_png = None,None
                    
                if img_dict[k]['diff_image_link'][i] is None: valid_pixels = False
                else: valid_pixels = True
                diffimgdict = {'postage_stamp_file':img_dict[k]['warp_file_png'][i],
                               'postage_stamp_ref':stack_png,
                               'postage_stamp_diff':img_dict[k]['diff_file_png'][i],
                               'postage_stamp_file_fits':img_dict[k]['warp_file_png'][i],
                               'postage_stamp_ref_fits':stack_file,
                               'postage_stamp_diff_fits':img_dict[k]['diff_file'][i],
                               'valid_pixels':valid_pixels}
                
                if k in phot_dict.keys():
                    idx = np.where(img_dict[k]['diff_image_id'][i] == np.array(phot_dict[k]['diff_id']))[0]
                else: idx = None
                if idx is not None and len(idx) and k in phot_dict.keys():
                    idx = idx[0]
                    
                    flux = fluxToMicroJansky(
                        phot_dict[k]['flux'][idx],phot_dict[k]['exptime'][idx],phot_dict[k]['zpt'][idx])*10**(0.4*(27.5-23.9))
                    flux_err = fluxToMicroJansky(phot_dict[k]['flux_err'][idx],phot_dict[k]['exptime'][idx],
                                                 phot_dict[k]['zpt'][idx])*10**(0.4*(27.5-23.9))

                    if flux != flux or flux_err != flux_err:
                        flux,flux_err,mag,mag_err = None,None,None,None
                    elif flux <= 0:
                        mag = None
                        mag_err = None
                    else:
                        mag = -2.5*np.log10(flux)+27.5
                        mag_err = 1.0857*flux_err/flux

                    phot_upload_dict = {'obs_date':mjd_to_date(phot_dict[k]['mjd'][idx]),
                                        'band':phot_dict[k]['filt'][idx],
                                        'groups':'YSE',
                                        'mag':mag,
                                        'mag_err':mag_err,
                                        'flux':flux,
                                        'flux_err':flux_err,
                                        'data_quality':phot_dict[k]['dq'][idx],
                                        'forced':1,
                                        'flux_zero_point':27.5,
                                        'discovery_point':0,
                                        'diffim':1,
                                        'diffimg':diffimgdict}
                else:
                    phot_upload_dict = {'obs_date':mjd_to_date(img_dict[k]['diff_image_mjd'][i]),
                                        'band':img_dict[k]['diff_image_filter'][i],
                                        'groups':'YSE',
                                        'mag':None,
                                        'mag_err':None,
                                        'flux':None,
                                        'flux_err':None,
                                        'data_quality':1,
                                        'forced':None,
                                        'flux_zero_point':27.5,
                                        'discovery_point':0,
                                        'diffim':1,
                                        'diffimg':diffimgdict}
                if 'GPC1' in phot_upload_dict['band']:
                    photometrydict_ps1['photdata']['%s_%i'%(mjd_to_date(img_dict[k]['diff_image_mjd'][i]),i)] = phot_upload_dict
                elif 'GPC2' in phot_upload_dict['band']:
                    photometrydict_ps2['photdata']['%s_%i'%(mjd_to_date(img_dict[k]['diff_image_mjd'][i]),i)] = phot_upload_dict
                else:
                    raise RuntimeError("couldn't figure out the instrument")
                    
            PhotUploadAll['PS1'] = photometrydict_ps1
            PhotUploadAll['PS2'] = photometrydict_ps2
            tdict[k]['transientphotometry'] = PhotUploadAll
        self.send_data(tdict)
        
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
        

    def get_phot(self,request_names,transient_list,transient_ra_list,transient_dec_list,img_dict):
        sct = SkyCoord(transient_ra_list,transient_dec_list,unit=u.deg)
        transient_list = np.array(transient_list)

        phot_dict = {}
        for request_name in request_names:
            phot_link = 'http://datastore.ipp.ifa.hawaii.edu/pstampresults/'
            phot_results_link = '{}/{}/'.format(phot_link,request_name)

            phot_page = requests.get(url=phot_results_link)
            if phot_page.status_code != 200:
                raise RuntimeError('results page {} does not exist'.format(phot_results_link))


            tree = html.fromstring(phot_page.content)
            fitsfiles = tree.xpath('//a/text()')
            for f in fitsfiles:
                if 'detectability' in f:
                    phot_fits_link = '{}/{}/{}'.format(phot_link,request_name,f)
                    fits_response = requests.get(url=phot_fits_link,stream=True)

                    # this is a pain but it seems necessary
                    tmpfits = tempfile.NamedTemporaryFile(delete=False)
                    shutil.copyfileobj(fits_response.raw, tmpfits)
                    tmpfits.close()
                    ff = fits.open(tmpfits.name)
                    os.remove(tmpfits.name)
                    for i in range(len(ff[1].data)):
                        mjd = ff[0].header['MJD-OBS']
                        exptime = ff[0].header['EXPTIME']
                        filt = ff[0].header['FPA.FILTER'].split('.')[0]
                        flux = ff[1].data['PSF_INST_FLUX'][i]
                        flux_err = ff[1].data['PSF_INST_FLUX_SIG'][i]
                        # http://svn.pan-starrs.ifa.hawaii.edu/trac/ipp/browser/trunk/psModules/src/objects/pmSourceMasks.h?order=name
                        # saturated, diff spike, ghost, off chip
                        #bad_flags = ['0x00001000','0x20000000','0x40000000','0x80000000']
                        # saturation, defect
                        #0x00000080, 0x00000800
                        if ff[1].data['PSF_QF'][i] < 0.9 or \
                           (ff[1].data['FLAGS'][i] & 0x00001000) or \
                           (ff[1].data['FLAGS'][i] & 0x20000000) or \
                           (ff[1].data['FLAGS'][i] & 0x40000000) or \
                           (ff[1].data['FLAGS'][i] & 0x80000000) or \
                           (ff[1].data['FLAGS'][i] & 0x00000080) or \
                           (ff[1].data['FLAGS'][i] & 0x00000800): dq = 1
                        else: dq = 0
                        stack_id = ff[0].header['PPSUB.REFERENCE'].split('.')[-3]
                        warp_id = ff[0].header['PPSUB.INPUT'].split('.')[3]
                        ra = ff[1].data['RA_PSF'][i]
                        dec = ff[1].data['DEC_PSF'][i]
                        sc = SkyCoord(ff[1].data['RA_PSF'][i],ff[1].data['DEC_PSF'][i],unit=u.deg)
                        sep = sc.separation(sct).arcsec
                        if np.min(sep) > 2:
                            raise RuntimeError(
                                'couldn\'t find transient match for RA,Dec=%.7f,%.7f'%(
                                    ff[1].data['RA_PSF'][i],ff[1].data['DEC_PSF'][i]))
                        tn = transient_list[sep == np.min(sep)][0]
                        if tn not in phot_dict.keys():
                            phot_dict[tn] = {'mjd':[],
                                             'filt':[],
                                             'flux':[],
                                             'flux_err':[],
                                             'dq':[],
                                             'stack_id':[],
                                             'warp_id':[],
                                             'diff_id':[],
                                             'ra':[],
                                             'dec':[],
                                             'exptime':[],
                                             'zpt':[]}

                        phot_dict[tn]['mjd'] += [mjd]
                        phot_dict[tn]['filt'] += [filt]
                        phot_dict[tn]['flux'] += [flux]
                        phot_dict[tn]['flux_err'] += [flux_err]
                        phot_dict[tn]['dq'] += [dq]
                        phot_dict[tn]['stack_id'] += [stack_id]
                        phot_dict[tn]['warp_id'] += [warp_id]
                        phot_dict[tn]['diff_id'] += [f.split('.')[2]]
                        phot_dict[tn]['ra'] += [ra]
                        phot_dict[tn]['dec'] += [dec]
                        phot_dict[tn]['exptime'] += [exptime]
                        phot_dict[tn]['zpt'] += [ff[0].header['FPA.ZP']]

        return phot_dict

    def get_stamps(self,request_name,transient_list):

        stamp_link = 'http://datastore.ipp.ifa.hawaii.edu/yse-pstamp-results/'
        stamp_results_link = '{}/{}/results.mdc'.format(stamp_link,request_name)
        stamp_fitsfile_link = '{}/{}/'.format(stamp_link,request_name)
        
        stamps_page = requests.get(url=stamp_results_link)
        if stamps_page.status_code != 200:
            raise RuntimeError('results page {} does not exist'.format(stamp_results_link))
        
        mdc_stamps = parse_mdc(stamps_page.text)

        tree = html.fromstring(stamps_page.content)
        fitsfiles = tree.xpath('//a/text()')
        
        image_dict = {}

        for k in mdc_stamps.keys():
            if 'SUCCESS' not in mdc_stamps[k]['ERROR_STR'] and 'NO_VALID_PIXELS' not in mdc_stamps[k]['ERROR_STR'] and\
               'PSTAMP_NO_IMAGE_MATCH' not in mdc_stamps[k]['ERROR_STR']:
                raise RuntimeError('part of job {} failed!'.format(request_name))
            img_name,img_type,transient,mjd,img_id,img_filter = \
                mdc_stamps[k]['IMG_NAME'],mdc_stamps[k]['IMG_TYPE'],mdc_stamps[k]['COMMENT'].split('.')[-1],\
                float(mdc_stamps[k]['MJD_OBS']),mdc_stamps[k]['ID'],mdc_stamps[k]['FILTER'].split('.')[0]
            if transient not in image_dict.keys():
                image_dict[transient] = {'warp_image_link':[],'diff_image_link':[],'stack_image_link':[],
                                         'warp_image_id':[],'diff_image_id':[],'stack_image_id':[],
                                         'warp_image_mjd':[],'diff_image_mjd':[],'stack_image_mjd':[],
                                         'warp_image_filter':[],'diff_image_filter':[],'stack_image_filter':[]}
            if 'NO_VALID_PIXELS' not in mdc_stamps[k]['ERROR_STR'] and 'PSTAMP_NO_IMAGE_MATCH' not in mdc_stamps[k]['ERROR_STR']:
                if img_type == 'warp':
                    image_dict[transient]['warp_image_link'] += ['{}/{}'.format(stamp_fitsfile_link,img_name)]
                    image_dict[transient]['warp_image_id'] += [img_id]
                    image_dict[transient]['warp_image_mjd'] += [mjd]
                    image_dict[transient]['warp_image_filter'] += [img_filter]
                elif img_type == 'diff':
                    image_dict[transient]['diff_image_link'] += ['{}/{}'.format(stamp_fitsfile_link,img_name)]
                    image_dict[transient]['diff_image_id'] += [img_id]
                    image_dict[transient]['diff_image_mjd'] += [mjd]
                    image_dict[transient]['diff_image_filter'] += [img_filter]
                elif img_type == 'stack':
                    image_dict[transient]['stack_image_link'] += ['{}/{}'.format(stamp_fitsfile_link,img_name)]
                    image_dict[transient]['stack_image_id'] += [img_id]
                    image_dict[transient]['stack_image_mjd'] += [mjd]
                    image_dict[transient]['stack_image_filter'] += [img_filter]
                else: raise RuntimeError('image type {} not found'.format(img_type))
            else:
                if img_type == 'warp':
                    image_dict[transient]['warp_image_link'] += [None]
                    image_dict[transient]['warp_image_id'] += [img_id]
                    image_dict[transient]['warp_image_mjd'] += [mjd]
                    image_dict[transient]['warp_image_filter'] += [img_filter]
                elif img_type == 'diff':
                    image_dict[transient]['diff_image_link'] += [None]
                    image_dict[transient]['diff_image_id'] += [img_id]
                    image_dict[transient]['diff_image_mjd'] += [mjd]
                    image_dict[transient]['diff_image_filter'] += [img_filter]
                elif img_type == 'stack':
                    image_dict[transient]['stack_image_link'] += [None]
                    image_dict[transient]['stack_image_id'] += [img_id]
                    image_dict[transient]['stack_image_mjd'] += [mjd]
                    image_dict[transient]['stack_image_filter'] += [img_filter]
                else: raise RuntimeError('image type {} not found'.format(img_type))

        return image_dict

    
    def get_status(self,request_name):
        
        status_link = 'http://pstamp.ipp.ifa.hawaii.edu/status.php'
        session = requests.Session()
        session.auth = (self.options.ifauser,self.options.ifapass)

        page = session.post(status_link)
        page = session.post(status_link)
        
        if page.status_code == 200:
            lines_out = []
            for line in page.text.split('<pre>')[-1].split('\n'):
                if line and '------------------' not in line and '/pre' not in line:
                    lines_out += [line[1:]]
            text = '\n'.join(lines_out)
            tbl = at.Table.read(text,format='ascii',delimiter='|',data_start=1,header_start=0)

            idx = tbl['name'] == request_name
            if not len(tbl[idx]):
                print('warning: could not find request named %s'%request_name)
                return False, False
            if tbl['Completion Time (UTC)'][idx]: done = True
            else: done = False

            if float(tbl['Total Jobs'][idx]) == float(tbl['Successful Jobs'][idx]): success = True
            else:
                success = False
                print('warning: %i of %i jobs failed'%(float(tbl['Total Jobs'][idx])-float(tbl['Successful Jobs'][idx]),float(tbl['Total Jobs'][idx])))
        
        return done,success
        
    def stamp_request(
            self,transient_list,ra_list,dec_list,camera_list,diff_id_list,
            warp_id_list,stack_id_list,width=300,height=300,skycelldict=None):

        assert len(transient_list) == len(warp_id_list) or \
            len(transient_list) == len(diff_id_list) or \
            len(transient_list) == len(stack_id_list)
        
        transient_list,ra_list,dec_list,diff_id_list,warp_id_list,stack_id_list = \
            np.atleast_1d(np.asarray(transient_list)),np.atleast_1d(np.asarray(ra_list)),np.atleast_1d(np.asarray(dec_list)),\
            np.atleast_1d(np.asarray(diff_id_list)),np.atleast_1d(np.asarray(warp_id_list)),np.atleast_1d(np.asarray(stack_id_list))
        
        data = at.Table(names=('ROWNUM', 'PROJECT', 'SURVEY_NAME', 'IPP_RELEASE', 'JOB_TYPE',
                               'OPTION_MASK', 'REQ_TYPE', 'IMG_TYPE', 'ID', 'TESS_ID',
                               'COMPONENT', 'COORD_MASK', 'CENTER_X', 'CENTER_Y', 'WIDTH',
                               'HEIGHT', 'DATA_GROUP', 'REQFILT', 'MJD_MIN', 'MJD_MAX',
                               'RUN_TYPE', 'FWHM_MIN', 'FWHM_MAX', 'COMMENT'),
                        dtype=('>i4','S16','S16','S16','S16','>i4','S16','S16','S16','S64',
                               'S64','>i4','>f8','>f8','>f8','>f8','S64','S16','>f8','>f8',
                               'S16','>f8','>f8','S64'))

        transients_unq,idx = np.unique(transient_list,return_index=True)
        if skycelldict is None:
            skycelldict = {}
            skycells = np.array([])
            for snid,ra,dec in zip(transient_list[idx],ra_list[idx],dec_list[idx]):
                skycells = np.append(skycells,'skycell.'+getskycell(ra,dec)[0])
                skycelldict[snid] = skycells[-1]
        
        count = 1
        for snid,ra,dec,camera,diff_id in \
            zip(transient_list,ra_list,dec_list,camera_list,diff_id_list):
            if diff_id is None: continue
            skycell_str = skycelldict[snid]
            data.add_row((count,camera,'null','null','stamp',2049,'byid','diff',diff_id,'RINGS.V3',
                          skycell_str,2,ra,dec,width,height,'null','null',0,0,'null',0,0,'diff.for.%s'%snid) )
            count += 1
        
        for snid,ra,dec,camera,warp_id in \
            zip(transient_list,ra_list,dec_list,camera_list,warp_id_list):
            if warp_id is None: continue
            skycell_str = skycelldict[snid]
            data.add_row((count,camera,'null','null','stamp',2049,'byid','warp',warp_id,'RINGS.V3',
                          skycell_str,2,ra,dec,width,height,'null','null',0,0,'null',0,0,'warp.for.%s'%snid) )
            count += 1
            
        for snid,ra,dec,camera,stack_id in \
            zip(transient_list,ra_list,dec_list,camera_list,stack_id_list):
            if stack_id is None: continue
            skycell_str = skycelldict[snid]
            data.add_row((count,camera,'null','null','stamp',2049,'byid','stack',stack_id,'RINGS.V3',
                          skycell_str,2,ra,dec,width,height,'null','null',0,0,'null',0,0,'stack.for.%s'%snid) )
            count += 1

        hdr = default_stamp_header.copy()
        request_name = 'YSE-stamp.%i'%(time.time())
        hdr['REQ_NAME'] = request_name
        ff = fits.BinTableHDU(data, header=hdr)

        s = BytesIO()
        ff.writeto(s, overwrite=True)
        if self.debug:
            ff.writeto('stampimg.fits',overwrite=True)

        self.submit_to_ipp(s)
        return request_name,skycelldict

    def forcedphot_request(self,transient_list,ra_list,dec_list,mjd_list,filt_list,camera_list,diff_id_list,skycelldict):

        transient_list,ra_list,dec_list,mjd_list,filt_list,diff_id_list,camera_list = \
            np.atleast_1d(np.asarray(transient_list)),np.atleast_1d(np.asarray(ra_list)),\
            np.atleast_1d(np.asarray(dec_list)),np.atleast_1d(np.asarray(mjd_list)),\
            np.atleast_1d(np.asarray(filt_list)),np.atleast_1d(np.asarray(diff_id_list)),\
            np.atleast_1d(np.asarray(camera_list))
        
        request_names = []
        count = 0
        for snid_unq in np.unique(transient_list):
            data = at.Table(names=('ROWNUM','PROJECT','RA1_DEG','DEC1_DEG','RA2_DEG','DEC2_DEG','FILTER','MJD-OBS','FPA_ID','COMPONENT_ID'),
                            dtype=('S20','S16','>f8','>f8','>f8','>f8','S20','>f8','>i4','S64'))
            for snid,ra,dec,mjd,filt,camera,diff_id in \
                zip(transient_list[transient_list == snid_unq],ra_list[transient_list == snid_unq],dec_list[transient_list == snid_unq],
                    mjd_list[transient_list == snid_unq],filt_list[transient_list == snid_unq],camera_list[transient_list == snid_unq],diff_id_list[transient_list == snid_unq]):
                if diff_id is None or diff_id == 'NULL': continue
                data.add_row(('forcedphot_ysebot_{}'.format(count),camera,ra,dec,ra,dec,filt,mjd,diff_id,skycelldict[snid_unq]) )
                count += 1
                import pdb; pdb.set_trace()
            if len(data) > 0:
                hdr = default_forcedphot_header.copy()
                request_name = 'YSE-phot.%s.%s.%i'%(snid,diff_id,time.time())
                hdr['QUERY_ID'] = request_name
                hdr['EXTNAME'] = 'MOPS_DETECTABILITY_QUERY'
                hdr['EXTVER'] = '2'
                hdr['OBSCODE'] = '566'
                hdr['STAGE'] = 'WSdiff'
                ff = fits.BinTableHDU(data, header=hdr)
                if self.debug:
                    ff.writeto('%s.fits'%request_name, overwrite=True)

                s = BytesIO()
                ff.writeto(s, overwrite=True)

                self.submit_to_ipp(s)
                request_names += [request_name]
            else:
                print('warning : no diff IDs for transient {}'.format(snid_unq))
                
        return request_names

    def retrieve_stamp(self):
        pass

    def retrieve_forcedphot(self):
        pass

    def submit_to_ipp(self,filename_or_obj):

        session = requests.Session()
        session.auth = (self.options.ifauser,self.options.ifapass)
        stampurl = 'http://pstamp.ipp.ifa.hawaii.edu/upload.php'

        # First login. Returns session cookie in response header. Even though status_code=401, it is ok
        page = session.post(stampurl)

        if type(filename_or_obj) == str: files = {'filename':open(filename,'rb')}
        else: files = {'filename':filename_or_obj.getvalue()}
        page = session.post(stampurl, files=files)

class ForcedPhotUpdate(CronJobBase):

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhotUpdate'

    def __init__(self):
        
        self.debug = False
        if self.debug:
            print('debug mode enabled')
    
    def do(self):
        code = 'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhotUpdate'
        
        self.debug = False

        # code options
        fp = ForcedPhot()
        parser = fp.add_options(usage='')
        options,  args = parser.parse_known_args()

        config = configparser.ConfigParser()
        config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
        parser = fp.add_options(usage='',config=config)
        options,  args = parser.parse_known_args()
        fp.options = options

        # in case of code failures
        smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
        from_addr = "%s@gmail.com" % options.SMTP_LOGIN
        subject = "YSE_PZ Forced Photometry Upload Failure"
        html_msg = "Alert : YSE_PZ Forced Photometry Failed to upload transients in YSE_Forced_Phot.py\n"
        html_msg += "Error : %s"
        
        # check for instance of code already running
        try:
            me = singleton.SingleInstance(flavor_id="11")
        except singleton.SingleInstanceException:
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      f"multiple instances of {code} are running",
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)
            sys.exit(1)        

        
        try:
            tstart = time.time()

            nsn = fp.main(update_forced=True)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""Forced phot cron failed with error %s at line number %s"""%(
                e,exc_tb.tb_lineno))
            nsn = 0
            print("Sending error email")
            sendemail(from_addr, options.dbemail, subject,
                      html_msg%(e),
                      options.SMTP_LOGIN, options.dbemailpassword, smtpserver)

        print('YSE_PZ Forced Photometry took %.1f seconds for %i transients'%(time.time()-tstart,nsn))

        
def sendemail(from_addr, to_addr,
              subject, message,
              login, password, smtpserver, cc_addr=None):

    print("Preparing email")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    payload = MIMEText(message, 'html')
    msg.attach(payload)
    
    with smtplib.SMTP(smtpserver) as server:
        try:
            server.starttls()
            server.login(login, password)
            resp = server.sendmail(from_addr, [to_addr], msg.as_string())
            print("Send success")
        except:
            print("Send fail")

        
if __name__ == "__main__":
    fp = ForcedPhot()
    fp.do()
