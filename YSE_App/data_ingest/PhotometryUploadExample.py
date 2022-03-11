from django_cron import CronJobBase, Schedule
import coreapi
from astropy.time import Time
import json
import numpy as np
import requests
from requests.auth import HTTPBasicAuth


def jd_to_date(jd):
    time = Time(jd, scale="utc", format="jd")
    return time.isot


def query_mars(ra, dec):
    marsurl = (
        "https://mars.lco.global/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014"
        % (ra, dec)
    )
    client = coreapi.Client()
    schema = client.get(marsurl)
    if "results" in schema.keys():
        obs_date, mag, mag_err, band = [], [], [], []
        for i in range(len(schema["results"])):
            phot = schema["results"][i]["candidate"]
            if phot["isdiffpos"] == "f":  # this is bad photometry
                continue
            mag += [phot["magpsf"]]
            mag_err += [phot["sigmapsf"]]
            obs_date += [jd_to_date(phot["jd"])]
            band += ["%s-ZTF" % phot["filter"]]
        return np.array(obs_date), np.array(mag), np.array(mag_err), np.array(band)
    else:
        return [], [], [], []


class PhotometryUploads(CronJobBase):

    RUN_EVERY_MINS = 120

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.PhotometryUploadExample.PhotometryUploads"

    def do(self):

        try:
            self.do_phot_upload()
            print("successful upload!")
        except Exception as e:
            print("Error: %s" % e)

    def do_phot_upload(self):

        # write out the transient dictionary
        # initial key telling it not to override the existing status of this transient
        # assuming it exists
        TransientUploadDict = {"noupdatestatus": True}
        TransientUploadDict["2019np"] = {
            "name": "2019np",
            "ra": 157.3415000,
            "dec": 29.5106667,
            "obs_group": "Unknown",  # obs_group and status are required keys for any *new* transients, but not for existing transients
            "status": "Ignore",
        }

        # set up the photometry upload dictionary
        PhotUploadAll = {"mjdmatchmin": 0.01, "clobber": True}
        PhotUploadAll["ZTF"] = {
            "instrument": "ZTF-Cam",  # the name of the key "ZTF" doesn't matter, it's just for bookkeeping
            "obs_group": "ZTF",
        }

        # convert the photometric data
        obs_date, mag, mag_err, band = query_mars(157.3415000, 29.5106667)
        PhotDataDict = {}
        PhotUploadAll["ZTF"]["photdata"] = {}
        i = 0
        for o, m, me, b in zip(obs_date, mag, mag_err, band):
            PhotDataDict = {
                "obs_date": o,
                "mag": m,
                "mag_err": me,
                "band": b,
                "data_quality": 0,  # good data
                "diffim": 1,  # difference imaging measurement
                # these next fields have to be included because of the way code is written but can be mostly ignored
                "flux": None,
                "flux_err": None,
                "flux_zero_point": None,
                "forced": 0,
                "discovery_point": 0,
            }

            PhotUploadAll["ZTF"]["photdata"][i] = PhotDataDict
            i += 1

        TransientUploadDict["2019np"]["transientphotometry"] = PhotUploadAll

        self.UploadTransients(TransientUploadDict)

    def UploadTransients(self, TransientUploadDict):

        url = (
            "https://ziggy.ucolick.org/yse_test/add_transient/"
        )  #''http://127.0.0.1:8000/add_transient/'
        try:
            r = requests.post(
                url=url,
                data=json.dumps(TransientUploadDict),
                auth=HTTPBasicAuth("djones", "BossTent1"),
                timeout=60,
            )
            try:
                print("YSE_PZ says: %s" % json.loads(r.text)["message"])
            except:
                print(r.text)
            print("Process done.")

        except Exception as e:
            print("Error: %s" % e)
