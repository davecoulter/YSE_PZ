#! python 
#
# Grab ZTF forced photometry on a field
#
# M.C. Stroh & Wynn Jacobson-Galan
#
#

import argparse
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from datetime import datetime
import email
import imaplib
import numpy as np
import os
import pandas as pd
import random
import re
import shutil
import string
import subprocess
import sys
import time
import traceback
from django.conf import settings as djangoSettings

import matplotlib
matplotlib.use('AGG') # This makes it run faster, comment out for interactive plotting
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore") # We'll get warnings from log10 when there are non-detections


#
# Generic ZTF webdav login
#
_ztfuser = "ztffps"
_ztfinfo = "dontgocrazy!"

def random_log_file_name(log_file_dir='/tmp'):

    log_file_name = None
    while log_file_name is None or os.path.exists(log_file_name):
        log_file_name = f"{log_file_dir}/forced_phot_out/ztffp_%s.txt"%''.join([random.choice(string.ascii_uppercase + string.digits) for i in range(10)])
        #random.choices(string.ascii_uppercase + string.digits, k=10))
    
    return log_file_name



def download_ztf_url(url, verbose=True):

    wget_command = "wget --http-user=%s --http-password=%s -O %s \"%s\""%(
        _ztfuser,_ztfinfo,url.split('/')[-1],url)

    if verbose:
        print("Downloading file...")
        print('\t' + wget_command)
    p = subprocess.Popen(wget_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()

    #os.system(wget_command)
    return url.split('/')[-1]



def match_ztf_message(job_info, message_body, message_time_epoch):

    match = False

    #
    # Only continue if the message was received AFTER the job was submitted
    #
    #if message_time_epoch < job_info['cdatetime'].to_list()[0]:

    #    return match


    message_lines = message_body.splitlines()

    for line in message_lines:
        if re.search("reqid", line):

            inputs = line.split('(')[-1]

            # Two ways
            # Processing has completed for reqid=XXXX ()
            test_ra = inputs.split('ra=')[-1].split(',')[0]
            test_decl = inputs.split('dec=')[-1].split(')')[0]
            if re.search('minJD', line) and re.search('maxJD', line):
                test_minjd = inputs.split('minJD=')[-1].split(',')[0]
                test_maxjd = inputs.split('maxJD=')[-1].split(',')[0]
            else:
                test_minjd = inputs.split('startJD=')[-1].split(',')[0]
                test_maxjd = inputs.split('endJD=')[-1].split(',')[0]
                
            # Call this a match only if parameters match
            if np.format_float_positional(float(test_ra), precision=6, pad_right=6).replace(' ','0') == job_info['ra'].to_list()[0] and \
               np.format_float_positional(float(test_decl), precision=6, pad_right=6).replace(' ','0') == job_info['dec'].to_list()[0] and \
               np.format_float_positional(float(test_minjd), precision=6, pad_right=6).replace(' ','0') == job_info['jdstart'].to_list()[0] and \
               np.format_float_positional(float(test_maxjd), precision=6, pad_right=6).replace(' ','0') == job_info['jdend'].to_list()[0]:

               match = True

    #import pdb; pdb.set_trace()

    return match



def read_job_log(file_name):

    job_info = pd.read_html(file_name)[0]
    job_info['ra'] = np.format_float_positional(float(job_info['ra'].to_list()[0]), precision=6, pad_right=6).replace(' ','0')
    job_info['dec'] = np.format_float_positional(float(job_info['dec'].to_list()[0]), precision=6, pad_right=6).replace(' ','0')
    job_info['jdstart'] = np.format_float_positional(float(job_info['jdstart'].to_list()[0]), precision=6, pad_right=6).replace(' ','0')
    job_info['jdend'] = np.format_float_positional(float(job_info['jdend'].to_list()[0]), precision=6, pad_right=6).replace(' ','0')
    job_info['isostart'] = Time(float(job_info['jdstart'].to_list()[0]), format='jd', scale='utc').iso
    job_info['isoend'] = Time(float(job_info['jdend'].to_list()[0]), format='jd', scale='utc').iso
    job_info['ctime'] = os.path.getctime(file_name) - time.localtime().tm_gmtoff
    job_info['cdatetime'] = datetime.fromtimestamp(os.path.getctime(file_name))

    return job_info


class ZTF_Forced_Phot:

    def __init__(self,ztf_email_address=None,ztf_email_password=None,
                 ztf_email_imapserver=None,ztf_user_address=None,
                 ztf_user_password=None):

        #
        # Import ZTF email user information
        #
        if ztf_email_address is None: self._ztffp_email_address = os.environ["ztf_email_address"]
        else: self._ztffp_email_address = ztf_email_address
        
        if ztf_email_password is None: self._ztffp_email_password = os.environ["ztf_email_password"]
        else: self._ztffp_email_password = ztf_email_password

        if ztf_email_imapserver is None: self._ztffp_email_server = os.environ["ztf_email_imapserver"]
        else: self._ztffp_email_server = ztf_email_imapserver

        if ztf_user_address is None: self._ztffp_user_address = os.environ["ztf_user_address"]
        else: self._ztffp_user_address = ztf_user_address

        if ztf_user_password is None: self._ztffp_user_password = os.environ["ztf_user_password"]
        else: self._ztffp_user_password = ztf_user_password

    
    #
    # Look for email to download data products
    # 
    def query_ztf_email(self,log_file_name, source_name=None, verbose=True):


        downloaded_file_names = None

        if not os.path.exists(log_file_name):

            print("%s does not exist."%log_file_name)
            return -1


        # Interpret the request sent to the ZTF forced photometry server
        job_info = read_job_log(log_file_name)


        try:

            imap = imaplib.IMAP4_SSL(self._ztffp_email_server)
            imap.login(self._ztffp_email_address, self._ztffp_email_password)

            status, messages = imap.select("INBOX")
            processing_match = False
            # if it's not in the first 100 messages, then I don't care
            for i in range(int(messages[0]), 0, -1)[0:100]:
                if processing_match:
                    break

                # Fetch the email message by ID
                res, msg = imap.fetch(str(i), "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        # Parse a bytes email into a message object
                        msg = email.message_from_bytes(response[1])
                        # decode the email subject
                        sender, encoding = email.header.decode_header(msg.get("From"))[0]

                        if not isinstance(sender, bytes) and re.search("ztfpo@ipac\.caltech\.edu", sender):


                            #
                            # Get message body
                            #
                            content_type = msg.get_content_type()
                            body = msg.get_payload(decode=True).decode()

                            this_date = msg['Date']
                            this_date_tuple = email.utils.parsedate_tz(msg['Date'])
                            local_date = datetime.fromtimestamp(email.utils.mktime_tz(this_date_tuple))


                            #
                            # Check if this is the correct one
                            #
                            if content_type=="text/plain":
                                processing_match = match_ztf_message(job_info, body, local_date)
                                subject, encoding = email.header.decode_header(msg.get("Subject"))[0]

                                if processing_match:

                                    # Grab the appropriate URLs
                                    lc_url = 'https' + (body.split('_lc.txt')[0] + '_lc.txt').split('https')[-1]
                                    log_url = 'https' + (body.split('_log.txt')[0] + '_log.txt').split('https')[-1]


                                    # Download each file
                                    lc_initial_file_name = download_ztf_url(lc_url, verbose=verbose)
                                    log_initial_file_name = download_ztf_url(log_url, verbose=verbose)


                                    # Rename
                                    if source_name is None:
                                        downloaded_file_names = [lc_initial_file_name, log_initial_file_name]
                                    else:
                                        lc_final_name = source_name.replace(' ','')+"_"+lc_initial_file_name.split('_')[-1]
                                        log_final_name = source_name.replace(' ','')+"_"+log_initial_file_name.split('_')[-1]
                                        #import pdb; pdb.set_trace()
                                        #
                                        os.rename(lc_initial_file_name, lc_final_name)
                                        os.rename(log_initial_file_name, log_final_name)
                                        downloaded_file_names = [lc_final_name, log_final_name]

            imap.close()
            imap.logout()


        # Connection could be broken
        except Exception as e:
            pass

        if downloaded_file_names is not None:

            for file_name in downloaded_file_names:
                if verbose:
                    print("Downloaded: %s"%file_name)

        return downloaded_file_names




    def ztf_forced_photometry(self,ra, decl, jdstart=None, jdend=None, days=60, send=True, verbose=True):


        #
        # Set dates
        #
        if jdend is None:

            jdend = Time(datetime.utcnow(), scale='utc').jd


        if jdstart is None:

            jdstart = jdend - days



        if ra is not None and decl is not None:

            # Check if ra is a decimal
            try:
                # These will trigger the exception if they aren't float
                float(ra)
                float(decl)
                skycoord = SkyCoord(ra, decl, frame='icrs', unit='deg')

            # Else assume sexagesimal
            except Exception:
                skycoord = SkyCoord(ra, decl, frame='icrs', unit=(u.hourangle, u.deg))


            # Convert to string to keep same precision. This will make matching easier in the case of submitting multiple jobs.
            jdend_str = np.format_float_positional(float(jdend), precision=6)
            jdstart_str = np.format_float_positional(float(jdstart), precision=6)
            ra_str = np.format_float_positional(float(skycoord.ra.deg), precision=6)
            decl_str = np.format_float_positional(float(skycoord.dec.deg), precision=6)


            log_file_name = random_log_file_name(log_file_dir=djangoSettings.ZTFTMPDIR) # Unique file name

            if verbose:
                print("Sending ZTF request for (R.A.,Decl)=(%s,%s)"%(ra,decl))

            wget_command = "wget --http-user=%s --http-passwd=%s -O %s \"https://ztfweb.ipac.caltech.edu/cgi-bin/requestForcedPhotometry.cgi?"%(_ztfuser,_ztfinfo,log_file_name) + \
                           "ra=%s&"%ra_str + \
                           "dec=%s&"%decl_str + \
                           "jdstart=%s&"%jdstart_str +\
                           "jdend=%s&"%jdend_str + \
                           "email=%s&userpass=%s\""%(self._ztffp_user_address,self._ztffp_user_password)
            if verbose:
                print(wget_command)

            if send:

                p = subprocess.Popen(wget_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                stdout, stderr = p.communicate()

                #if verbose:
                #    print(stdout.decode('utf-8'))

            os.chmod(log_file_name,0o0777)

            return log_file_name


        else:

            #if verbose:
            raise RuntimeError("Missing necessary R.A. or declination.")
            #return None



    def plot_ztf_fp(self,lc_file_name, file_format='.png', threshold=3.0, upperlimit=5.0, verbose=False):

        # Color mapping for figures
        filter_colors = {'ZTF_g': 'g', 'ZTF_r': 'r', 'ZTF_i': 'darkorange'}


        # Use default naming convention
        plot_file_name = lc_file_name.replace('.txt', '.png')

        try:
            ztf_fp_df = pd.read_csv(lc_file_name, delimiter=' ', comment='#')
        except:
            if verbose:
                print("Empty ZTF light curve file (%s). Check the log file."%lc_file_name)
            return

        # Rename columns due to mix of , and ' ' separations in the files
        new_cols = dict()
        for col in ztf_fp_df.columns:
            new_cols[col] = col.replace(',','')

        # Make a clean version
        ztf_fp_df.rename(columns=new_cols, inplace=True)
        ztf_fp_df.drop(columns=['Unnamed: 0'], inplace=True)

        #
        # Create additional columns with useful calculations
        #
        ztf_fp_df['mjd_midpoint'] = ztf_fp_df['jd'] - 2400000.5 - ztf_fp_df['exptime']/2./86400. # Do it all at once here
        ztf_fp_df['fp_mag'] = ztf_fp_df['zpdiff'] - 2.5*np.log10(ztf_fp_df['forcediffimflux'])
        ztf_fp_df['fp_mag_unc'] = 1.0857 * ztf_fp_df['forcediffimfluxunc']/ztf_fp_df['forcediffimflux']
        ztf_fp_df['fp_ul'] = ztf_fp_df['zpdiff'] - 2.5*np.log10(upperlimit * ztf_fp_df['forcediffimfluxunc'])


        fig = plt.figure(figsize=(12,6))

        # Iterate over filters
        for ztf_filter in set(ztf_fp_df['filter']):

            filter_df = ztf_fp_df[ztf_fp_df['filter']==ztf_filter]

            # Upper limit df
            ul_filter_df = filter_df[filter_df.forcediffimflux/filter_df.forcediffimfluxunc < threshold]

            # Detections df
            detection_filter_df = filter_df[filter_df.forcediffimflux/filter_df.forcediffimfluxunc >= threshold]

            if verbose:
                print("%s: %s detections and %s upper limits."%(ztf_filter,detection_filter_df.shape[0],ul_filter_df.shape[0]))

            # Plot detections
            plt.plot(detection_filter_df.mjd_midpoint, detection_filter_df.fp_mag, color=filter_colors[ztf_filter], marker='o', linestyle='', zorder=3)
            plt.errorbar(detection_filter_df.mjd_midpoint, detection_filter_df.fp_mag, yerr=detection_filter_df.fp_mag_unc, color=filter_colors[ztf_filter], linestyle='', zorder=1)

            # Plot non-detections
            plt.plot(ul_filter_df.mjd_midpoint, ul_filter_df.fp_mag, color=filter_colors[ztf_filter], marker='v', linestyle='', zorder=2)


        # Final touches
        plt.gca().invert_yaxis()
        plt.grid(True)
        plt.tick_params(bottom=True, top=True, left=True, right=True, direction='in', labelsize='18', grid_linestyle=':')
        plt.ylabel('ZTF FP (Mag.)', fontsize='20')
        plt.xlabel('Time (MJD)', fontsize='20')
        plt.tight_layout()

        output_file_name = lc_file_name.rsplit('.', 1)[0] + file_format
        fig.savefig(output_file_name)
        plt.close(fig)

        return output_file_name

    # Same as run_ztf_fp but just checks the email
    def get_ztf_fp(self,log_file_name, directory_path='.',
                   source_name='temp',verbose=False):


        # Download via email
        downloaded_file_names = None
        time_start_seconds = time.time()

        downloaded_file_names = self.query_ztf_email(log_file_name, source_name=source_name, verbose=verbose)

        if downloaded_file_names == -1:
            if verbose:
                print("%s was not found."%log_file_name)
            return None

        #
        # Clean-up
        #
        output_directory = ("%s/%s"%(directory_path,source_name)).replace('//','/')

        # Trim potential extra '/'
        if output_directory[-1:]=='/':
            output_directory = output_directory[:-1]

        # Create directory
        if not os.path.exists(output_directory):
            if verbose:
                print("Creating %s"%output_directory)

            os.makedirs(output_directory,mode=0o0777)
            try:
                os.chmod(output_directory,mode=0o0777)
            except: pass
        #
        # Move all files to this location
        #

        # Wget log file
        #output_files = list()
        #if log_file_name is not None and os.path.exists(log_file_name):
        #    shutil.move(log_file_name, "%s/%s"%(output_directory,log_file_name))
        #    if verbose:
        #        print("%sZTF wget log: %s/%s"%(' '*5,output_directory,log_file_name))
        #    output_files.append("%s/%s"%(output_directory,log_file_name))


        # Downloaded files
        output_files = []
        if isinstance(downloaded_file_names, list):
            for downloaded_file_name in downloaded_file_names:
                if os.path.exists(downloaded_file_name):
                    shutil.move(downloaded_file_name, "%s/%s"%(output_directory,downloaded_file_name))

                    if verbose:
                        print("%sZTF downloaded file: %s/%s"%(' '*5,output_directory,downloaded_file_name))
                    output_files.append("%s/%s"%(output_directory,downloaded_file_name))


        if len(output_files)==0 or isinstance(output_files, list)==False:
            output_files = None


        # Useful for automation
        return output_files

        

    # Wrap the main code in a wrapper function so that other python code can call this.
    def run_ztf_fp(self,all_jd=False, days=60, decl=None, directory_path='.',
                   do_plot=True, emailcheck=20, fivemindelay=60, jdend=None, 
                   jdstart=None, logfile=None, mjdend=None, mjdstart=None, 
                   plotfile=None, ra=None, skip_clean=False, source_name='temp',
                   verbose=False):


        #
        # Exit early if no sufficient conditions given to run
        #
        run = False
        if (ra is not None and decl is not None) or (logfile is not None) or (plotfile is not None):
            run = True


        # Go home early
        if run==False:
            print("Insufficient parameters given to run.")
            return


        #
        # Change necessary variables based on what was provided
        #

        # Override jd values if mjd arguments are supplied
        if mjdstart is not None:
            jdstart = mjdstart + 2400000.5
        if mjdend is not None:
            jdend = mjdend + 2400000.5


        # Set to full ZTF range
        if all_jd:
            jdstart = 2458194.5
            jdend = Time(datetime.utcnow(), scale='utc').jd


        log_file_name = None
        if logfile is None and plotfile is None:

            log_file_name = self.ztf_forced_photometry(ra=ra, decl=decl, jdstart=jdstart, jdend=jdend, days=days)

        else:

            log_file_name = logfile
            plot_file_name = plotfile


        if log_file_name is not None:

            # Download via email
            downloaded_file_names = None
            time_start_seconds = time.time()
            if emailcheck > 0:
                while downloaded_file_names is None:

                    if time.time() - time_start_seconds < emailcheck:
                        if verbose:
                            print("Waiting for the email (rechecking every %s seconds)."%emailcheck)

                    downloaded_file_names = self.query_ztf_email(log_file_name, source_name=source_name, verbose=verbose)
                    if downloaded_file_names == -1:
                        if verbose:
                            print("%s was not found."%log_file_name)
                    elif downloaded_file_names is None:
                        if emailcheck < fivemindelay and time.time() - time_start_seconds > 600: # After 5 minutes, change to checking every 1 minute
                            emailcheck = fivemindelay
                            if verbose:
                                print("Changing to re-checking every %s seconds."%emailcheck)
                        time.sleep(emailcheck)
            else:
                output_directory = ("%s/%s"%(directory_path,source_name)).replace('//','/')
                if not os.path.exists(output_directory):
                    if verbose:
                        print("Creating %s"%output_directory)
                    os.makedirs(output_directory)

                shutil.move(log_file_name, "%s/%s"%(output_directory,log_file_name.split('/')[-1]))
                return "%s/%s"%(output_directory,log_file_name.split('/')[-1])

        else:
            downloaded_file_names = [plot_file_name] 


        if downloaded_file_names is not None and downloaded_file_names[0] is not None:

            # Open LC file and plot it
            if do_plot:
                figure_file_name = plot_ztf_fp(downloaded_file_names[0], verbose=verbose)
            else:
                figure_file_name = None


        #
        # Clean-up
        #
        if skip_clean==False:
            output_directory = ("%s/%s"%(directory_path,source_name)).replace('//','/')
            # Trim potential extra '/'
            if output_directory[-1:]=='/':
                output_directory = output_directory[:-1]

            # Create directory
            if not os.path.exists(output_directory):
                if verbose:
                    print("Creating %s"%output_directory)
                os.makedirs(output_directory,mode=0o0775)


            #
            # Move all files to this location
            #

            # Wget log file
            output_files = list()
            if log_file_name is not None and os.path.exists(log_file_name):
                shutil.move(log_file_name, "%s/%s"%(output_directory,log_file_name))
                if verbose:
                    print("%sZTF wget log: %s/%s"%(' '*5,output_directory,log_file_name))
                output_files.append("%s/%s"%(output_directory,log_file_name))


            # Downloaded files
            if isinstance(downloaded_file_names, list):
                for downloaded_file_name in downloaded_file_names:
                    if os.path.exists(downloaded_file_name):
                        shutil.move(downloaded_file_name, "%s/%s"%(output_directory,downloaded_file_name))
                        if verbose:
                            print("%sZTF downloaded file: %s/%s"%(' '*5,output_directory,downloaded_file_name))
                        output_files.append("%s/%s"%(output_directory,downloaded_file_name))


            # Figure
            if figure_file_name is not None and os.path.exists(figure_file_name):
                shutil.move(figure_file_name, "%s/%s"%(output_directory,figure_file_name))
                if verbose:
                    print("%sZTF figure: %s/%s"%(' '*5,output_directory,figure_file_name))
                output_files.append("%s/%s"%(output_directory,figure_file_name))

        if len(output_files)==0 or isinstance(output_files, list)==False:
            output_files = None


        # Useful for automation
        return output_files



    def main(self):

        # First 'fix' possible negative declinations which argparse can't handle on its own
        for i, arg in enumerate(sys.argv):
            if (arg[0] == '-') and arg[1].isdigit(): sys.argv[i] = ' ' + arg

        # Initialize argument parser.
        parser = argparse.ArgumentParser(prog="ztf_fp.py <ra> <decl>", description='Grab ZTF forced photometry on the given location.', formatter_class=argparse.RawTextHelpFormatter)

        # Necessary arguments
        parser.add_argument('ra', type=str, nargs='?', default=None,
                       help="Right ascension of the target. Can be provided in DDD.ddd or HH:MM:SS.ss formats.")
        parser.add_argument('decl', type=str, nargs='?', default=None,
                       help="Declination of the target. Can be provided in +/-DDD.ddd or DD:MM:SS.ss formats.")
        # OR (query has already been sent)
        parser.add_argument('-logfile', metavar='logfile', type=str, nargs='?', default=None, 
                       help='Log file to process instead of submitting a new job.')
        # OR (option to only build light curve)
        parser.add_argument('-plotfile', metavar='plotfile', type=str, nargs='?', default=None, 
                       help='Light curve file to plot instead of submitting and downloading a new job.')


        # Additional arguments we can use
        parser.add_argument('-source_name', metavar='source_name', type=str, nargs='?', default='temp_source', 
                       help='Source name that will be used to name output files.')    
        parser.add_argument('-mjdstart', metavar='mjdstart', type=float, nargs='?', default=None, 
                       help='Start of date range for forced photometry query. Overrides -jdstart.')    
        parser.add_argument('-mjdend', metavar='mjdend', type=float, nargs='?', default=None, 
                       help='End of date range for forced photometry query. Overrides -jdstop')
        parser.add_argument('-jdstart', metavar='jdstart', type=float, nargs='?', default=None, 
                       help='Start of date range for forced photometry query.')    
        parser.add_argument('-jdend', metavar='jdend', type=float, nargs='?', default=None, 
                       help='End of date range for forced photometry query.')
        parser.add_argument('-ztf_all_jd', action='store_true', dest='all_jd',
                       help='Use the full range of ZTF public dates.')
        parser.set_defaults(all_jd=False)
        parser.add_argument('-days', metavar='days', type=int, nargs='?', default=60, 
                       help='Number of days prior to jdend to query (or number of days prior to today if jdend is not given).')    
        parser.add_argument('-emailcheck', metavar='emailcheck', type=float, nargs='?', default=20, 
                       help='How often to recheck your email for the ZTF results.')
        parser.add_argument('-skip_clean', action='store_false', dest='skip_clean',
                       help='After completion skip placing all output files in the same directory.')
        parser.set_defaults(skip_clean=False)
        parser.add_argument('-directory_path', metavar='directory_path', type=str, nargs='?', default='.', 
                       help='Path to directory for clean-up. Requires -directory option.') 
        parser.add_argument('-fivemindelay', metavar='fivemindelay', type=float, nargs='?', default=60, 
                       help='How often (in seconds) to query the email after 5 minutes have elapsed.')    
        parser.add_argument('-skip_plot', action='store_false', dest='do_plot',
                       help='Skip making the plot. Useful for automated and batch use cases, or if user wants to use their personal plotting code.')
        parser.set_defaults(do_plot=True)



        try:
            # Validate inputs
            args = parser.parse_args()
            run = True

        except Exception:

            run = False


        # Don't go further if there were problems with arguments or inputs
        if run:

            run_ztf_fp(**vars(args), verbose=True)


if __name__ == "__main__":
    ztf = ZTF_Forced_Phot()
    ztf.main()

