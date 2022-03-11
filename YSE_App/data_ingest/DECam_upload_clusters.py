#!/usr/bin/env python
import configparser
import os
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html.parser import HTMLParser
from io import open as iopen

import astropy.table as at
import astropy.units as u
import dateutil.parser
import requests
from astro_ghost.ghostHelperFunctions import *
from astropy.coordinates import SkyCoord
from bs4 import BeautifulSoup
from django.conf import settings as djangoSettings
from django_cron import CronJobBase
from django_cron import Schedule
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth

from YSE_App.util.TNS_Synopsis import mastrequests
# from YSE_App.data_ingest.TNS_uploads import get_ps_score

try:
    from astro_ghost.photoz_helper import calc_photoz
except:
    pass
import datetime
import json
from astropy.time import Time

_base_url = "https://stsci-transients.stsci.edu"

try:
    from dustmaps.sfd import SFDQuery

    sfd = SFDQuery()
except:
    raise RuntimeError(
        """can\'t import dust maps
run:
import dustmaps
import dustmaps.sfd
dustmaps.sfd.fetch()"""
    )


def mjd_to_date(obs_mjd):
    time = Time(obs_mjd, scale="utc", format="mjd")
    return time.isot


def get_ps_score(RA, DEC):
    """Get ps1 star/galaxy score from MAST. Provide RA and DEC in degrees.
    Returns an empty string if no match is found witing 3 arcsec.
    """
    # get the WSID and password if not already defined
    # get your WSID by going to https://mastweb.stsci.edu/ps1casjobs/changedetails.aspx after you login to Casjobs.

    os.environ["CASJOBS_WSID"] = str(1_862_226_089)
    os.environ["CASJOBS_PW"] = "tr4nsientsP!z"
    query = """select top 1 p.ps_score
    from pointsource_magnitudes_view as p
    inner join fGetNearbyObjEq(%.5f, %.5f, 0.05) nb on p.objid=nb.objid
    """ % (
        RA,
        DEC,
    )

    jobs = mastrequests.MastCasJobs(context="HLSP_PS1_PSC")
    results = jobs.quick(query, task_name="python cross-match")

    output = results.split("\n")[1]
    if not output:
        output = None
    else:
        output = round(float(output), 3)
        print("PS_SCORE: %.3f" % output)

    return output


def sendemail(
    from_addr, to_addr, subject, message, login, password, smtpserver, cc_addr=None
):

    print("Preparing email")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    payload = MIMEText(message, "html")
    msg.attach(payload)

    with smtplib.SMTP(smtpserver) as server:
        try:
            server.starttls()
            server.login(login, password)
            resp = server.sendmail(from_addr, [to_addr], msg.as_string())
            print("Send success")
        except:
            print("Send fail")


def get_clusters(date):

    t = Time(date)
    datestr = t.datetime.strftime("YSE%y%m%d")

    # get DECAM clusters file
    url = "/".join([_base_url, datestr, "sniff", "clusterslist.txt"])
    r = requests.get(url)
    if r.status_code == 200:
        data = r.text
        files = r.text.split("\n")
        output = []
        for f in files:
            # Get rid of formatting codes
            out = f.replace("\x1b[38;5;34m", "")
            out = out.replace("[0m", "")
            output.append(out)

        return output

    return []


def download_and_parse_cluster_file(clusterfile, date):
    t = Time(date)
    datestr = t.datetime.strftime("YSE%y%m%d")

    # get DECAM clusters file
    url = "/".join([_base_url, datestr, "sniff", clusterfile])

    print(f"Getting clusters file {url}")

    r = requests.get(url)
    if r.status_code == 200:
        file_id = 0

        output = {"files": None, "candidates": None, "photometry": None}
        table = None
        for line in r.text.split("\n"):
            if line.startswith("#"):
                if table:
                    if file_id == 1:
                        output["files"] = table
                        cols = line.replace("#", "").split()
                        table = at.Table(names=cols, dtype=["S200"] * len(cols))
                    elif file_id == 2:
                        output["candidates"] = table
                        cols = line.replace("#", "").split()
                        table = at.Table(names=cols, dtype=["S200"] * len(cols))
                else:
                    cols = line.replace("#", "").split()
                    table = at.Table(names=cols, dtype=["S200"] * len(cols))
                file_id += 1
            else:
                if line.split():
                    table.add_row(line.split())

        output["photometry"] = table

        return output


def get_candidate_photometry(candnum, clusterfile, date):
    # Get base path of clustersfile
    path, filename = os.path.split(clusterfile)

    field = path.split("_")[0]
    chip = path.split("/")[-1]
    num = clusterfile.split(".")[1]

    forced_file = "{0}_{1}.{2}/{0}_{1}.{2}_cand{3}.forced.difflc.txt".format(
        field, chip, num, candnum
    )

    t = Time(date)
    datestr = t.datetime.strftime("YSE%y%m%d")

    # get DECAM clusters file
    url = "/".join([_base_url, datestr, "sniff", path, forced_file])
    r = requests.get(url)

    if r.status_code == 200:
        table = None
        for i, line in enumerate(r.text.split("\n")):
            if i == 0:
                cols = line.replace("#", "").split()
                table = at.Table(names=cols, dtype=["S200"] * len(cols))
            else:
                if line.split():
                    table.add_row(line.split())
        return table
    else:
        return None


class DECam_clusters(CronJobBase):

    RUN_EVERY_MINS = 120

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.DECam_upload.DECam"

    def do(self):
        usagestring = "DECam_clusters_upload.py date <options>"
        tstart = time.time()

        # read in the options from the param file and the command line
        # some convoluted syntax here, making it so param file is not required

        parser = self.add_options(usage=usagestring)
        options, args = parser.parse_known_args()

        config = configparser.ConfigParser()
        config.read("%s/settings.ini" % djangoSettings.PROJECT_DIR)
        parser = self.add_options(usage=usagestring, config=config)
        options, args = parser.parse_known_args()
        self.options = options

        try:
            nsn = self.main()
        except Exception as e:
            print(e)
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "QUB Transient Upload Failure"
            print("Sending error email")
            html_msg = (
                "Alert : YSE_PZ Failed to upload transients from PSST in QUB_data.py\n"
            )
            html_msg += "Error : %s"
            sendemail(
                from_addr,
                options.dbemail,
                subject,
                html_msg % (e),
                options.SMTP_LOGIN,
                options.dbemailpassword,
                smtpserver,
            )

        print(
            "QUB -> YSE_PZ took %.1f seconds for %i transients"
            % (time.time() - tstart, nsn)
        )

    def add_options(self, parser=None, usage=None, config=None):
        import argparse

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument(
            "-v", "--verbose", action="count", dest="verbose", default=1
        )
        parser.add_argument(
            "--clobber", default=False, action="store_true", help="clobber output file"
        )
        parser.add_argument(
            "-s",
            "--settingsfile",
            default=None,
            type=str,
            help="settings file (login/password info)",
        )
        parser.add_argument(
            "--status",
            default="New",
            type=str,
            help="transient status to enter in YS_PZ",
        )
        parser.add_argument(
            "--max_days",
            default=7,
            type=float,
            help="grab photometry/objects from the last x days",
        )

        if config:
            parser.add_argument(
                "--dblogin",
                default=config.get("main", "dblogin"),
                type=str,
                help="database login, if post=True (default=%default)",
            )
            parser.add_argument(
                "--dbemail",
                default=config.get("main", "dbemail"),
                type=str,
                help="database login, if post=True (default=%default)",
            )
            parser.add_argument(
                "--dbpassword",
                default=config.get("main", "dbpassword"),
                type=str,
                help="database password, if post=True (default=%default)",
            )
            parser.add_argument(
                "--dbemailpassword",
                default=config.get("main", "dbemailpassword"),
                type=str,
                help="email password, if post=True (default=%default)",
            )
            parser.add_argument(
                "--dburl",
                default=config.get("main", "dburl"),
                type=str,
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_argument(
                "--ztfurl",
                default=config.get("main", "ztfurl"),
                type=str,
                help="ZTF URL (default=%default)",
            )
            parser.add_argument(
                "--STATIC",
                default=config.get("site_settings", "STATIC"),
                type=str,
                help="static directory (default=%default)",
            )

            parser.add_argument(
                "--SMTP_LOGIN",
                default=config.get("SMTP_provider", "SMTP_LOGIN"),
                type=str,
                help="SMTP login (default=%default)",
            )
            parser.add_argument(
                "--SMTP_HOST",
                default=config.get("SMTP_provider", "SMTP_HOST"),
                type=str,
                help="SMTP host (default=%default)",
            )
            parser.add_argument(
                "--SMTP_PORT",
                default=config.get("SMTP_provider", "SMTP_PORT"),
                type=str,
                help="SMTP port (default=%default)",
            )

            parser.add_argument(
                "--max_decam_days",
                default=config.get("main", "max_days_decam"),
                type=float,
                help="grab photometry/objects from the last x days",
            )

        else:
            pass

        return parser

    def getGHOSTData(self, sc, ghost_host):
        hostdict = {}
        hostcoords = ""
        hostdict = {
            "name": ghost_host["objName"].to_numpy()[0],
            "ra": ghost_host["raMean"].to_numpy()[0],
            "dec": ghost_host["decMean"].to_numpy()[0],
        }

        hostcoords = f"ra={hostdict['ra']:.7f}, dec={hostdict['dec']:.7f}\n"
        if "photo_z" in ghost_host.keys():
            hostdict["photo_z_internal"] = ghost_host["photo_z"].to_numpy()[0]
        if (
            "NED_redshift" in ghost_host.keys()
            and ghost_host["NED_redshift"].to_numpy()[0]
            == ghost_host["NED_redshift"].to_numpy()[0]
        ):
            hostdict["redshift"] = ghost_host["NED_redshift"].to_numpy()[0]

        if "photo_z_internal" in hostdict.keys():
            if hostdict["photo_z_internal"] != hostdict["photo_z_internal"]:
                hostdict["photo_z_internal"] = None

        return hostdict, hostcoords

    def main(self):
        date = datetime.datetime.now() - datetime.timedelta(self.options.max_decam_days)

        # let's grab the most recent phot. data for each transient
        # if the DECam data on the sniff pages doesn't have more recent
        # data, hopefully we can assume things are up to date
        tr = requests.get(
            f"{self.options.dburl.replace('/api','')}query_api/DECAT_transients_mags/",
            auth=HTTPBasicAuth(self.options.dblogin, self.options.dbpassword),
        )
        etdata = tr.json()["transients"]
        etdict = {}
        ra = []
        dec = []
        dict_names = np.array([])
        for et in etdata:
            etdict[et["name"]] = et
            ra += [et["ra"]]
            dec += [et["dec"]]
            dict_names = np.append(dict_names, et["name"])
        scexisting = SkyCoord(ra, dec, unit=u.deg)

        # prelims
        transientdict = {}
        if not os.path.exists("database/GHOST.csv"):
            getGHOST(real=True, verbose=True)

        nowdate = datetime.datetime.now()
        numdays = (datetime.datetime.now() - date).days
        date_list = [nowdate - datetime.timedelta(days=x) for x in range(numdays)]
        count = 0
        transientdict = {}
        for mydate in date_list:
            clusters = get_clusters(mydate.isoformat())

            if not clusters:
                continue

            for clusterfile in clusters:
                if not clusterfile:
                    continue
                clustersdata = download_and_parse_cluster_file(
                    clusterfile, mydate.isoformat()
                )
                if not clustersdata:
                    continue

                for row in clustersdata["candidates"]:
                    if row["ysename"] != "-":
                        lcdata = get_candidate_photometry(
                            row["ID"], clusterfile, mydate.isoformat()
                        )

                        if not lcdata:
                            continue
                        lcdata["flux_c"] = lcdata["flux_c"].astype(float)
                        lcdata["dflux_c"] = lcdata["dflux_c"].astype(float)
                        lcdata["ZPTMAG_c"] = lcdata["ZPTMAG_c"].astype(float)
                        lcdata["MJD"] = lcdata["MJD"].astype(float)

                        # get RA/Dec
                        ra = lcdata["ra"][0]
                        dec = lcdata["dec"][0]
                        tname = row["ysename"]
                        print(f"trying to upload data for transient {tname}")

                        transient_exists = False
                        sc = None
                        if tname in etdict.keys():
                            transient_exists = True
                            dict_name = tname[:]
                        else:
                            sc = SkyCoord([ra], [dec], unit=(u.hour, u.deg))
                            sep_arcsec = scexisting.separation(sc).arcsec
                            if np.min(sep_arcsec) < 2:
                                transient_exists = True
                                dict_name = dict_names[
                                    sep_arcsec == np.min(sep_arcsec)
                                ][0]
                                print(
                                    f"transient {tname} is called {dict_name} on YSE-PZ!"
                                )
                        if transient_exists:
                            print(
                                f"transient {tname} is already on YSE-PZ!  I will ignore metadata queries"
                            )

                        if not transient_exists:
                            # some metadata
                            sc = SkyCoord([ra], [dec], unit=(u.hour, u.deg))
                            mw_ebv = float("%.3f" % (sfd(sc[0]) * 0.86))
                            try:
                                ps_prob = get_ps_score(sc[0].ra.deg, sc[0].dec.deg)
                            except:
                                ps_prob = None

                            # run GHOST
                            # import pdb; pdb.set_trace()
                            try:
                                ghost_hosts = getTransientHosts(
                                    ["tmp" + candid],
                                    [SkyCoord(ra, dec, unit=(u.hour, u.deg))],
                                    verbose=True,
                                    starcut="gentle",
                                    ascentMatch=False,
                                )
                                ghost_hosts = calc_photoz(ghost_hosts)
                            except:
                                ghost_hosts = None

                            if ghost_hosts is not None:
                                ghost_host = ghost_hosts[
                                    ghost_hosts["TransientName"] == candid
                                ]
                                if not len(ghost_host):
                                    ghost_host = None
                            else:
                                ghost_host = None
                        else:
                            ghost_host = None

                        # is the most recent photometry greater than what exists on YSE-PZ?
                        if transient_exists:
                            tdate = dateutil.parser.parse(
                                mjd_to_date(np.max(lcdata["MJD"]))
                            )
                            ysedate = dateutil.parser.parse(
                                etdict[dict_name]["obs_date"]
                            )
                            if ysedate < tdate + datetime.timedelta(0.1):
                                print(
                                    f"the latest data for transient {tname} already exists on YSE-PZ!  skipping..."
                                )
                                continue

                        # get photometry
                        tdict = {
                            "name": tname,
                            "ra": sc[0].ra.deg,
                            "dec": sc[0].dec.deg,
                            "obs_group": "YSE",
                            "status": self.options.status,
                            #'disc_date':None,
                            "mw_ebv": mw_ebv,
                            "point_source_probability": ps_prob,
                            "tags": ["DECAT"],
                        }
                        if not transient_exists:
                            tdict["point_source_probability"] = ps_prob

                        if ghost_host is not None:
                            hostdict, hostcoords = self.getGHOSTData(sc, ghost_host)
                            tdict["host"] = hostdict
                            tdict["candidate_hosts"] = hostcoords

                        PhotUploadAll = {
                            "mjdmatchmin": 0.01,
                            "clobber": self.options.clobber,
                        }
                        photometrydict = {
                            "instrument": "DECam",
                            "obs_group": "YSE",
                            "photdata": {},
                        }

                        for j, lc in enumerate(lcdata):

                            try:
                                mag = float(lc["m"])
                                mag_err = float(lc["dm"])
                            except:
                                mag = None
                                mag_err = None

                            phot_upload_dict = {
                                "obs_date": mjd_to_date(lc["MJD"]),
                                "band": lc["filt"],
                                "groups": ["YSE"],
                                "mag": mag,
                                "mag_err": mag_err,
                                "flux": lc["flux_c"]
                                * 10 ** (0.4 * (27.5 - lc["ZPTMAG_c"])),
                                "flux_err": lc["dflux_c"]
                                * 10 ** (0.4 * (27.5 - lc["ZPTMAG_c"])),
                                "data_quality": 0,
                                "forced": 1,
                                "discovery_point": 0,
                                "flux_zero_point": 27.5,
                                "diffim": 1,
                            }

                            photometrydict["photdata"][
                                "%s_%i" % (mjd_to_date(lc["MJD"]), j)
                            ] = phot_upload_dict

                        PhotUploadAll["DECam"] = photometrydict
                        transientdict[tname] = tdict
                        transientdict[tname]["transientphotometry"] = PhotUploadAll
                        count += 1

                        if not count % 10:
                            # do the uploads
                            self.send_data(transientdict)
                            transientdict = {}

        self.send_data(transientdict)

    def send_data(self, TransientUploadDict):

        TransientUploadDict["noupdatestatus"] = True
        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self, TransientUploadDict):

        url = "%s" % self.options.dburl.replace("/api", "/add_transient")
        try:
            r = requests.post(
                url=url,
                data=json.dumps(TransientUploadDict),
                auth=HTTPBasicAuth(self.options.dblogin, self.options.dbpassword),
                timeout=60,
            )
            try:
                print("YSE_PZ says: %s" % json.loads(r.text)["message"])
            except:
                print(r.text)
            print("Process done.")

        except Exception as e:
            print("Error: %s" % e)
