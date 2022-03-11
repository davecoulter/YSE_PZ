#!/usr/bin/env python

import requests
import urllib
from django_cron import CronJobBase, Schedule
from requests.auth import HTTPBasicAuth
from django.conf import settings as djangoSettings
import configparser
import imaplib
import email
from YSE_App.common.utilities import date_to_mjd
from YSE_App.models.survey_models import *
from django.conf import settings as djangoSettings
import json
import re
import datetime
from antares_client.search import search
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
import time
import coreapi

# from alerce.api import AlerceAPI
import sys
from astropy.io import fits
import astropy.table as at
from YSE_App.util.skycells import getskycell
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

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

query_template = {
    "query": {
        "bool": {
            "must": [
                {"range": {"ra": {}}},
                {"range": {"dec": {}}},
                {"range": {"properties.ztf_rb": {}}},
                {"range": {"properties.ztf_jd": {}}},
            ]
        }
    }
}

query_test = {
    "query": {
        "bool": {
            "must": [
                {"match": {"properties.ztf_object_id": "ZTF18abrfjdh"}},
                {"range": {"mjd": {"gte": 58798}}},
            ]
        }
    }
}
_allowed_galaxy_catalogs = {
    "sdss_gals": {
        "name_key": "Objid",
        "ra_key": "ra",
        "dec_key": "dec_",
        "redshift_key": "z",
        "priority": 1,
    },
    "ned": {
        "name_key": "sid",
        "ra_key": "RA_deg",
        "dec_key": "DEC_deg",
        "redshift_key": "Redshift_1",
        "priority": 2,
    },
    "veron_agn_qso": {
        "name_key": "sid",
        "ra_key": "RAJ2000",
        "dec_key": "DEJ2000",
        "redshift_key": "z",
        "priority": 3,
    },
    "RC3": {
        "name_key": "id",
        "ra_key": "ra",
        "dec_key": "dec",
        "redshift_key": None,
        "priority": 4,
    },
    "2mass_psc": {
        "name_key": "sid",
        "ra_key": "ra",
        "dec_key": "decl",
        "redshift_key": None,
        "priority": 5,
    },
    "nyu_valueadded_gals": {
        "name_key": "sid",
        "ra_key": "RA",
        "dec_key": "DEC",
        "redshift_key": None,
        "priority": 6,
    },
}
#'french_post_starburst_gals':{'name_key':'Objid','ra_key':'ra','dec_key':dec,'redshift_key':z,'priority':5}}


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


class AntaresZTF(CronJobBase):

    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.Query_ZTF.AntaresZTF"

    def do(self):
        print("running ANTARES query at {}".format(datetime.datetime.now().isoformat()))
        try:
            tstart = time.time()

            parser = self.add_options(usage="")
            options, args = parser.parse_known_args()

            config = configparser.ConfigParser()
            config.read("%s/settings.ini" % djangoSettings.PROJECT_DIR)
            parser = self.add_options(usage="", config=config)
            options, args = parser.parse_known_args()
            self.options = options

            nsn = self.main()
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(
                """Antares cron failed with error %s at line number %s"""
                % (e, exc_tb.tb_lineno)
            )
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "YSE_PZ/ANTARES Transient Upload Failure"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload transients in Query_ZTF.py\n"
            html_msg += """Antares cron failed with error %s at line number %s""" % (
                e,
                exc_tb.tb_lineno,
            )
            sendemail(
                from_addr,
                options.dbemail,
                subject,
                html_msg,
                options.SMTP_LOGIN,
                options.dbemailpassword,
                smtpserver,
            )

        print(
            "Antares -> YSE_PZ took %.1f seconds for %i transients"
            % (time.time() - tstart, nsn)
        )

    def main(self):

        recentmjd = date_to_mjd(
            datetime.datetime.utcnow() - datetime.timedelta(self.options.max_days)
        )
        survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)
        field_pk = survey_obs.values("survey_field").distinct()
        survey_fields = SurveyField.objects.filter(pk__in=field_pk).select_related()
        nsn = 0
        print(survey_fields)
        for s in survey_fields:

            width_corr = 1.55 / np.abs(np.cos(s.dec_cen * np.pi / 180))
            ra_offset = Angle(width_corr / 2.0, unit=u.deg)
            dec_offset = Angle(1.55 / 2.0, unit=u.deg)
            sc = SkyCoord(s.ra_cen, s.dec_cen, unit=u.deg)
            ra_min = sc.ra - ra_offset
            ra_max = sc.ra + ra_offset
            dec_min = sc.dec - dec_offset
            dec_max = sc.dec + dec_offset

            query = query_template.copy()
            query["query"]["bool"]["must"][0]["range"]["ra"]["gte"] = ra_min.deg
            query["query"]["bool"]["must"][0]["range"]["ra"]["lte"] = ra_max.deg
            query["query"]["bool"]["must"][1]["range"]["dec"]["gte"] = dec_min.deg
            query["query"]["bool"]["must"][1]["range"]["dec"]["lte"] = dec_max.deg
            query["query"]["bool"]["must"][2]["range"]["properties.ztf_rb"]["gte"] = 0.5
            query["query"]["bool"]["must"][3]["range"]["properties.ztf_jd"]["gte"] = (
                recentmjd + 2400000.5
            )

            result_set = search(query)

            transientdict, nsn = self.parse_data(result_set)
            print("uploading %i transients" % nsn)
            if nsn > 0:
                self.send_data(transientdict)

        return nsn

    def send_data(self, TransientUploadDict):

        TransientUploadDict["noupdatestatus"] = True
        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self, TransientUploadDict):

        url = "%s" % self.options.dburl.replace("/api", "/add_transient")
        r = requests.post(
            url=url,
            data=json.dumps(TransientUploadDict),
            auth=HTTPBasicAuth(self.options.dblogin, self.options.dbpassword),
        )

        try:
            print("YSE_PZ says: %s" % json.loads(r.text)["message"])
        except:
            print(r.text)
        print("Process done.")

    def parse_data(self, result_set):
        transientdict = {}
        obj, ra, dec = [], [], []
        nsn = 0
        for i, s in enumerate(result_set):
            # if 'astrorapid_skipped' in s['properties'].keys(): continue
            if "streams" not in s.keys() or "yse_candidate_test" not in s["streams"]:
                continue

            # if s['properties']['ztf_object_id'] == 'ZTF20aaykvgb': import pdb; pdb.set_trace()
            # print(s['properties']['snfilter_known_exgal'])
            if s["properties"]["snfilter_known_exgal"] == 1:
                # name, ra, dec, redshift
                # print(s['properties']['ztf_object_id'])
                antareslink = "{}/loci/{}/catalog-matches".format(
                    self.options.antaresapi, s["locus_id"]
                )
                r = requests.get(antareslink)
                data = json.loads(r.text)

                for k in _allowed_galaxy_catalogs.keys():
                    if k in data["result"].keys():
                        hostdict = {
                            "name": k
                            + "_"
                            + str(
                                data["result"][k][0][
                                    _allowed_galaxy_catalogs[k]["name_key"]
                                ]
                            ),
                            "ra": data["result"][k][0][
                                _allowed_galaxy_catalogs[k]["ra_key"]
                            ],
                            "dec": data["result"][k][0][
                                _allowed_galaxy_catalogs[k]["dec_key"]
                            ],
                        }
                        if _allowed_galaxy_catalogs[k]["redshift_key"] is not None:
                            hostdict["redshift"] = data["result"][k][0][
                                _allowed_galaxy_catalogs[k]["redshift_key"]
                            ]

            else:
                hostdict = {}

            sc = SkyCoord(
                s["properties"]["ztf_ra"], s["properties"]["ztf_dec"], unit=u.deg
            )
            try:
                ps_prob = get_ps_score(sc.ra.deg, sc.dec.deg)
            except:
                ps_prob = None

            mw_ebv = float("%.3f" % (sfd(sc) * 0.86))

            if s["properties"]["ztf_object_id"] not in transientdict.keys():
                tdict = {
                    "name": s["properties"]["ztf_object_id"],
                    "status": "New",
                    "ra": s["properties"]["ztf_ra"],
                    "dec": s["properties"]["ztf_dec"],
                    "obs_group": "ZTF",
                    "tags": ["ZTF in YSE Fields"],
                    "disc_date": mjd_to_date(s["properties"]["ztf_jd"] - 2400000.5),
                    "mw_ebv": mw_ebv,
                    "point_source_probability": ps_prob,
                    "host": hostdict,
                }
                obj += [s["properties"]["ztf_object_id"]]
                ra += [s["properties"]["ztf_ra"]]
                dec += [s["properties"]["ztf_dec"]]

                PhotUploadAll = {"mjdmatchmin": 0.01, "clobber": False}
                photometrydict = {
                    "instrument": "ZTF-Cam",
                    "obs_group": "ZTF",
                    "photdata": {},
                }

            else:
                tdict = transientdict[s["properties"]["ztf_object_id"]]
                if s["properties"]["ztf_jd"] - 2400000.5 < date_to_mjd(
                    tdict["disc_date"]
                ):
                    tdict["disc_date"] = mjd_to_date(
                        s["properties"]["ztf_jd"] - 2400000.5
                    )

                PhotUploadAll = transientdict[s["properties"]["ztf_object_id"]][
                    "transientphotometry"
                ]
                photometrydict = PhotUploadAll["ZTF"]

            flux = 10 ** (-0.4 * (s["properties"]["ztf_magpsf"] - 27.5))
            flux_err = np.log(10) * 0.4 * flux * s["properties"]["ztf_sigmapsf"]

            phot_upload_dict = {
                "obs_date": mjd_to_date(s["properties"]["ztf_jd"] - 2400000.5),
                "band": "%s-ZTF" % s["properties"]["passband"].lower(),
                "groups": [],
                "mag": s["properties"]["ztf_magpsf"],
                "mag_err": s["properties"]["ztf_sigmapsf"],
                "flux": flux,
                "flux_err": flux_err,
                "data_quality": 0,
                "forced": 0,
                "flux_zero_point": 27.5,
                # might need to fix this later
                "discovery_point": 0,  # disc_point,
                "diffim": 1,
            }
            photometrydict["photdata"][
                "%s_%i" % (mjd_to_date(s["properties"]["ztf_jd"] - 2400000.5), i)
            ] = phot_upload_dict

            PhotUploadAll["ZTF"] = photometrydict
            transientdict[s["properties"]["ztf_object_id"]] = tdict
            transientdict[s["properties"]["ztf_object_id"]][
                "transientphotometry"
            ] = PhotUploadAll

            nsn += 1

            # if s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
            # 	import pdb; pdb.set_trace()
            # if s['properties']['passband'] == 'R' and s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
            # 	import pdb; pdb.set_trace()

        return transientdict, nsn

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
                help="database password, if post=True (default=%default)",
            )
            parser.add_argument(
                "--dburl",
                default=config.get("main", "dburl"),
                type=str,
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_argument(
                "--antaresapi",
                default=config.get("antares", "antaresapi"),
                type=str,
                help="ANTARES API (default=%default)",
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

        else:
            pass

        return parser


class MARS_ZTF(CronJobBase):

    RUN_EVERY_MINS = 0.1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.Query_ZTF.MARS_ZTF"

    def do(self):

        tstart = time.time()

        parser = self.add_options(usage="")
        options, args = parser.parse_args()
        config = configparser.ConfigParser()
        config.read("%s/settings.ini" % djangoSettings.PROJECT_DIR)
        parser = self.add_options(usage="", config=config)
        options, args = parser.parse_args()
        self.options = options

        try:
            self.main()
        except Exception as e:
            print(e)
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "QUB Transient Upload Failure"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload transients\n"
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
            "Antares -> YSE_PZ took %.1f seconds for %i transients"
            % (time.time() - tstart, nsn)
        )

    def main(self):

        recentmjd = date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(14))
        survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)
        field_pk = survey_obs.values("survey_field").distinct()
        survey_fields = SurveyField.objects.filter(pk__in=field_pk).select_related()

        for s in survey_fields:

            width_corr = 3.1 / np.abs(np.cos(s.dec_cen))
            ra_offset = Angle(width_corr / 2.0, unit=u.deg)
            dec_offset = Angle(3.1 / 2.0, unit=u.deg)
            sc = SkyCoord(s.ra_cen, s.dec_cen, unit=u.deg)
            ra_min = sc.ra - ra_offset
            ra_max = sc.ra + ra_offset
            dec_min = sc.dec - dec_offset
            dec_max = sc.dec + dec_offset
            result_set = []
            for page in range(500):
                print(s, page)
                marsurl = (
                    "%s/?format=json&sort_value=jd&sort_order=desc&ra__gt=%.7f&ra__lt=%.7f&dec__gt=%.7f&dec__lt=%.7f&jd__gt=%i&rb__gt=0.5&page=%i"
                    % (
                        self.options.ztfurl,
                        ra_min.deg,
                        ra_max.deg,
                        dec_min.deg,
                        dec_max.deg,
                        recentmjd + 2400000.5,
                        page + 1,
                    )
                )
                client = coreapi.Client()
                try:
                    schema = client.get(marsurl)
                    if "results" in schema.keys():
                        result_set = np.append(result_set, schema["results"])
                    else:
                        break
                except:
                    break
                # break

            transientdict, nsn = self.parse_data(
                result_set,
                date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(2)),
            )
            print("uploading %i transient detections" % nsn)
            self.send_data(transientdict)
            # import pdb; pdb.set_trace()
            # import pdb; pdb.set_trace()

    def send_data(self, TransientUploadDict):

        TransientUploadDict["noupdatestatus"] = True
        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self, TransientUploadDict):

        url = "%s" % self.options.dburl.replace("/api", "/add_transient")
        r = requests.post(
            url=url,
            data=json.dumps(TransientUploadDict),
            auth=HTTPBasicAuth(self.options.dblogin, self.options.dbemailpassword),
        )

        try:
            print("YSE_PZ says: %s" % json.loads(r.text)["message"])
        except:
            print(r.text)
        print("Process done.")

    def parse_data(self, result_set, mjdlim):
        transientdict = {}
        obj, ra, dec = [], [], []
        nsn = 0
        for i, s in enumerate(result_set):
            if s["candidate"]["rb"] < 0.5:
                continue
            sc = SkyCoord(s["candidate"]["ra"], s["candidate"]["dec"], unit=u.deg)
            try:
                ps_prob = get_ps_score(sc.ra.deg, sc.dec.deg)
            except:
                ps_prob = None

            mw_ebv = float("%.3f" % (sfd(sc) * 0.86))

            if s["objectId"] not in transientdict.keys():
                if s["candidate"]["jdstarthist"] - 2400000.5 < mjdlim:
                    status = "Ignore"
                else:
                    status = "New"

                tdict = {
                    "name": s["objectId"],
                    "status": status,
                    "ra": s["candidate"]["ra"],
                    "dec": s["candidate"]["dec"],
                    "obs_group": "ZTF",
                    "tags": ["ZTF"],
                    "disc_date": mjd_to_date(s["candidate"]["jdstarthist"] - 2400000.5),
                    "mw_ebv": mw_ebv,
                    "point_source_probability": ps_prob,
                }

                PhotUploadAll = {"mjdmatchmin": 0.01, "clobber": False}
                photometrydict = {
                    "instrument": "ZTF-Cam",
                    "obs_group": "ZTF",
                    "photdata": {},
                }

            else:
                tdict = transientdict[s["objectId"]]
                PhotUploadAll = transientdict[s["objectId"]]["transientphotometry"]
                photometrydict = PhotUploadAll["ZTF"]

            flux = 10 ** (-0.4 * (s["candidate"]["magpsf"] - 27.5))
            flux_err = np.log(10) * 0.4 * flux * s["candidate"]["sigmapsf"]

            phot_upload_dict = {
                "obs_date": mjd_to_date(s["candidate"]["jd"] - 2400000.5),
                "band": "%s-ZTF" % s["candidate"]["filter"].lower(),
                "groups": [],
                "mag": s["candidate"]["magpsf"],
                "mag_err": s["candidate"]["sigmapsf"],
                "flux": flux,
                "flux_err": flux_err,
                "data_quality": 0,
                "forced": 0,
                "flux_zero_point": 27.5,
                # might need to fix this later
                "discovery_point": 0,  # disc_point,
                "diffim": 1,
            }
            photometrydict["photdata"][
                "%s_%i" % (mjd_to_date(s["candidate"]["jd"] - 2400000.5), i)
            ] = phot_upload_dict

            PhotUploadAll["ZTF"] = photometrydict
            transientdict[s["objectId"]] = tdict
            transientdict[s["objectId"]]["transientphotometry"] = PhotUploadAll

            nsn += 1

            # if s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
            # 	import pdb; pdb.set_trace()
            # if s['candidate']['passband'] == 'R' and s['candidate']['objectId'] == 'ZTF18abrfjdh':
            # 	import pdb; pdb.set_trace()

        return transientdict, nsn

    def add_options(self, parser=None, usage=None, config=None):
        import optparse

        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

            # The basics
        parser.add_option("-v", "--verbose", action="count", dest="verbose", default=1)
        parser.add_option(
            "--clobber", default=False, action="store_true", help="clobber output file"
        )
        parser.add_option(
            "-s",
            "--settingsfile",
            default=None,
            type="string",
            help="settings file (login/password info)",
        )
        parser.add_option(
            "--status",
            default="New",
            type="string",
            help="transient status to enter in YS_PZ",
        )
        parser.add_option(
            "--max_days",
            default=7,
            type="float",
            help="grab photometry/objects from the last x days",
        )

        if config:
            parser.add_option(
                "--dblogin",
                default=config.get("main", "dblogin"),
                type="string",
                help="database login, if post=True (default=%default)",
            )
            parser.add_option(
                "--dbemail",
                default=config.get("main", "dbemail"),
                type="string",
                help="database login, if post=True (default=%default)",
            )
            parser.add_option(
                "--dbpassword",
                default=config.get("main", "dbpassword"),
                type="string",
                help="database password, if post=True (default=%default)",
            )
            parser.add_option(
                "--dburl",
                default=config.get("main", "dburl"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )

            parser.add_option(
                "--SMTP_LOGIN",
                default=config.get("SMTP_provider", "SMTP_LOGIN"),
                type="string",
                help="SMTP login (default=%default)",
            )
            parser.add_option(
                "--SMTP_HOST",
                default=config.get("SMTP_provider", "SMTP_HOST"),
                type="string",
                help="SMTP host (default=%default)",
            )
            parser.add_option(
                "--SMTP_PORT",
                default=config.get("SMTP_provider", "SMTP_PORT"),
                type="string",
                help="SMTP port (default=%default)",
            )

            parser.add_option(
                "--ztfurl",
                default=config.get("main", "ztfurl"),
                type="string",
                help="ZTF URL (default=%default)",
            )

        else:
            pass

        return parser


class AlerceZTF(CronJobBase):

    RUN_EVERY_MINS = 0.1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.Query_ZTF.AntaresZTF"

    def do(self):

        tstart = time.time()

        parser = self.add_options(usage="")
        options, args = parser.parse_args()

        config = configparser.ConfigParser()
        config.read("%s/settings.ini" % djangoSettings.PROJECT_DIR)
        parser = self.add_options(usage="", config=config)
        options, args = parser.parse_args()
        self.options = options

        try:
            self.main()
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(exc_tb.tb_lineno)
            nsn = 0
            smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
            from_addr = "%s@gmail.com" % options.SMTP_LOGIN
            subject = "QUB Transient Upload Failure"
            print("Sending error email")
            html_msg = "Alert : YSE_PZ Failed to upload transients\n"
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
            "Antares -> YSE_PZ took %.1f seconds for %i transients"
            % (time.time() - tstart, nsn)
        )

    def main(self):

        recentmjd = date_to_mjd(datetime.datetime.utcnow() - datetime.timedelta(7))
        survey_obs = SurveyObservation.objects.filter(obs_mjd__gt=recentmjd)
        field_pk = survey_obs.values("survey_field").distinct()
        survey_fields = SurveyField.objects.filter(pk__in=field_pk).select_related()

        for s in survey_fields:

            sc = SkyCoord(s.ra_cen, s.dec_cen, unit=u.deg)

            total = 10000
            records_per_page = 10000
            page = 1
            sortBy = "firstmjd"
            classearly = 19
            pclassearly = 0.5

            params = {
                # "total": total,
                "records_per_pages": records_per_page,
                "page": page,
                "sortBy": sortBy,
                "query_parameters": {
                    "filters": {"pclassearly": pclassearly, "classearly": classearly},
                    "dates": {
                        "firstmjd": {"min": date_to_mjd(datetime.datetime.utcnow()) - 3}
                    },
                    "coordinates": {
                        "ra": sc.ra.deg,
                        "dec": sc.dec.deg,
                        "sr": 1.65 * 3600,
                    },
                },
            }

            client = AlerceAPI()
            try:
                result_set = client.query(params)  # , format='pandas')
            except:
                continue

            if not len(result_set):
                continue

            transientdict, nsn = self.parse_data(result_set)
            print("uploading %i transients" % nsn)
            self.send_data(transientdict)

    def send_data(self, TransientUploadDict):

        TransientUploadDict["noupdatestatus"] = True
        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self, TransientUploadDict):

        url = "%s" % self.options.dburl.replace("/api", "/add_transient")
        r = requests.post(
            url=url,
            data=json.dumps(TransientUploadDict),
            auth=HTTPBasicAuth(self.options.dblogin, self.options.dbpassword),
        )

        try:
            print("YSE_PZ says: %s" % json.loads(r.text)["message"])
        except:
            print(r.text)
        print("Process done.")

    def parse_data(self, result_set):
        client = AlerceAPI()

        try:
            transientdict = {}
            obj, ra, dec = [], [], []
            nsn = 0
            for i, s in enumerate(result_set):
                print(s["oid"])
                sc = SkyCoord(s["meanra"], s["meandec"], unit=u.deg)
                try:
                    ps_prob = get_ps_score(sc.ra.deg, sc.dec.deg)
                except:
                    ps_prob = None

                mw_ebv = float("%.3f" % (sfd(sc) * 0.86))

                if s["oid"] not in transientdict.keys():
                    tdict = {
                        "name": s["oid"],
                        "status": "New",
                        "ra": s["meanra"],
                        "dec": s["meandec"],
                        "obs_group": "ZTF",
                        "tags": ["ZTF in YSE Fields"],
                        "disc_date": mjd_to_date(s["firstmjd"]),
                        "mw_ebv": mw_ebv,
                        "point_source_probability": ps_prob,
                    }
                    obj += [s["oid"]]
                    ra += [s["meanra"]]
                    dec += [s["meandec"]]

                    PhotUploadAll = {"mjdmatchmin": 0.01, "clobber": False}
                    photometrydict = {
                        "instrument": "ZTF-Cam",
                        "obs_group": "ZTF",
                        "photdata": {},
                    }

                else:
                    tdict = transientdict[s["oid"]]
                    if s["firstmjd"] < date_to_mjd(tdict["disc_date"]):
                        tdict["disc_date"] = mjd_to_date(s["firstmjd"])

                    PhotUploadAll = transientdict[s["oid"]]["transientphotometry"]
                    photometrydict = PhotUploadAll["ZTF"]

                SN_det = client.get_detections(s["oid"])  # , format='pandas')
                filtdict = {1: "g", 2: "r"}
                for p in SN_det:
                    flux = 10 ** (-0.4 * (p["magpsf"] - 27.5))
                    flux_err = np.log(10) * 0.4 * flux * p["sigmapsf"]

                    phot_upload_dict = {
                        "obs_date": mjd_to_date(p["mjd"]),
                        "band": "%s-ZTF" % filtdict[p["fid"]],
                        "groups": [],
                        "mag": p["magpsf"],
                        "mag_err": p["sigmapsf"],
                        "flux": flux,
                        "flux_err": flux_err,
                        "data_quality": 0,
                        "forced": 0,
                        "flux_zero_point": 27.5,
                        # might need to fix this later
                        "discovery_point": 0,  # disc_point,
                        "diffim": 1,
                    }
                    photometrydict["photdata"][
                        "%s_%i" % (mjd_to_date(p["mjd"]), i)
                    ] = phot_upload_dict

                PhotUploadAll["ZTF"] = photometrydict
                transientdict[s["oid"]] = tdict
                transientdict[s["oid"]]["transientphotometry"] = PhotUploadAll

                nsn += 1

                # if s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
                # 	import pdb; pdb.set_trace()
                # if s['properties']['passband'] == 'R' and s['properties']['ztf_object_id'] == 'ZTF18abrfjdh':
                # 	import pdb; pdb.set_trace()
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(exc_tb.tb_lineno)

        print(nsn)
        return transientdict, nsn

    def add_options(self, parser=None, usage=None, config=None):
        import optparse

        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

            # The basics
        parser.add_option("-v", "--verbose", action="count", dest="verbose", default=1)
        parser.add_option(
            "--clobber", default=False, action="store_true", help="clobber output file"
        )
        parser.add_option(
            "-s",
            "--settingsfile",
            default=None,
            type="string",
            help="settings file (login/password info)",
        )
        parser.add_option(
            "--status",
            default="New",
            type="string",
            help="transient status to enter in YS_PZ",
        )
        parser.add_option(
            "--max_days",
            default=7,
            type="float",
            help="grab photometry/objects from the last x days",
        )

        if config:
            parser.add_option(
                "--dblogin",
                default=config.get("main", "dblogin"),
                type="string",
                help="database login, if post=True (default=%default)",
            )
            parser.add_option(
                "--dbemail",
                default=config.get("main", "dbemail"),
                type="string",
                help="database login, if post=True (default=%default)",
            )
            parser.add_option(
                "--dbpassword",
                default=config.get("main", "dbpassword"),
                type="string",
                help="database password, if post=True (default=%default)",
            )
            parser.add_option(
                "--dburl",
                default=config.get("main", "dburl"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )

            parser.add_option(
                "--SMTP_LOGIN",
                default=config.get("SMTP_provider", "SMTP_LOGIN"),
                type="string",
                help="SMTP login (default=%default)",
            )
            parser.add_option(
                "--SMTP_HOST",
                default=config.get("SMTP_provider", "SMTP_HOST"),
                type="string",
                help="SMTP host (default=%default)",
            )
            parser.add_option(
                "--SMTP_PORT",
                default=config.get("SMTP_provider", "SMTP_PORT"),
                type="string",
                help="SMTP port (default=%default)",
            )

        else:
            pass

        return parser
