#!/usr/bin/env python
# D. Jones - 3/9/21
import argparse
import datetime
import json

import astropy.table as at
import dateutil.parser
import numpy as np
import pandas as pd
import requests
from astropy.time import Time
from requests.auth import HTTPBasicAuth

ysepz_filt_dict = {
    "u": "%s/api/photometricbands/210/",
    "g": "%s/api/photometricbands/211/",
    "r": "%s/api/photometricbands/212/",
    "i": "%s/api/photometricbands/119/",
    "z": "%s/api/photometricbands/120/",
}


def date_to_mjd(date):
    time = Time(date, scale="utc")
    return time.mjd


def parse_qcinv_file(filename):

    qcinv = at.Table(
        names=(
            "expid",
            "ra",
            "dec",
            "ut",
            "fil",
            "time",
            "secz",
            "psf",
            "sky",
            "cloud",
            "teff",
            "Object",
        )
    )

    with open(filename) as fin:
        for line in fin:
            if line.startswith("#"):
                continue
            lineparts = line.split()
            cols = np.append(lineparts[1:12], " ".join(lineparts[12:]))
            qcinv.add_row(cols)

    return qcinv


class DECAM_YSEPZ:
    def __init__(self):
        pass

    def add_args(self, parser=None, usage=None, config=None):
        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        # The basics
        parser.add_argument(
            "-f",
            "--obsfilename",
            type=str,
            default=None,
            help="qinv file from DECam observations",
        )
        parser.add_argument("--yseuser", type=str, default=None, help="YSE username")
        parser.add_argument("--ysepass", type=str, default=None, help="YSE password")
        parser.add_argument(
            "--debug", action="store_true", default=False, help="debug mode"
        )

        return parser

    def upload_transients(self):

        if self.options.debug:
            yseurl = "http://127.0.0.1:8000"
        else:
            yseurl = "https://ziggy.ucolick.org/yse"

        data = pd.read_fwf(self.options.obsfilename)
        # get the full list of DECAT survey fields in YSE-PZ
        fielddata = requests.get(
            url="%s/api/surveyfields/?obs_group=DECAT" % yseurl,
            auth=HTTPBasicAuth(self.options.yseuser, self.options.ysepass),
        ).json()
        existingfields = [f["field_id"] for f in fielddata["results"]]

        field_url_dict = {}
        for field in np.unique(
            data["Object"].values[data["Object"].values == data["Object"].values]
        ):
            if field not in existingfields:
                if field in ["pointing", "MaxVis"]:
                    continue
                if field.startswith("Tile"):
                    continue
                # a bit hacky since tied to specific PKs
                field_add_dict = {
                    "obs_group": "%s/api/observationgroups/86/" % yseurl,
                    "field_id": field,
                    "instrument": "%s/api/instruments/68/" % yseurl,
                    "ra_cen": data["ra"][data["Object"].values == field].values[0],
                    "dec_cen": data["dec"][data["Object"].values == field].values[0],
                    "width_deg": 2.2,
                    "height_deg": 2.2,
                }
                r = requests.post(
                    url="%s/api/surveyfields/" % yseurl,
                    json=field_add_dict,
                    auth=HTTPBasicAuth(self.options.yseuser, self.options.ysepass),
                ).json()
                field_url_dict[field] = r["url"]
            else:
                r = requests.get(
                    url="%s/api/surveyfields/?field_id=%s" % (yseurl, field),
                    auth=HTTPBasicAuth(self.options.yseuser, self.options.ysepass),
                ).json()
                field_url_dict[field] = r["results"][0]["url"]

        # hacky - get the obs date from the filename
        isodate = self.options.obsfilename.split("/")[-1].split(".")[0]
        obsdate_init = dateutil.parser.parse(isodate)
        for i in data.index:
            if data["Object"][i] != data["Object"][i]:
                continue
            if data["Object"][i] in ["pointing", "MaxVis"]:
                continue
            if data["Object"][i].startswith("Tile"):
                continue
            if data["fil"][i] not in ["u", "g", "r", "i", "z"]:
                continue

            if int(data["ut"][i][:2]) > 16:
                obsdate = obsdate_init + datetime.timedelta(days=1)
            else:
                obsdate = obsdate_init + datetime.timedelta(0)

            fulltime = obsdate.isoformat().split("T")[0] + "T" + data["ut"][i] + ":00"
            if "time" in data.keys():
                time, secz = float(data["secz"][i]), float(data["time"][i])
            elif "time secz" in data.keys():
                time, secz = data["time secz"][i].split()
                time, secz = float(time), float(secz)
            if not np.isnan(data["psf"][i]):
                fwhm = data["psf"][i]
            else:
                fwhm = None

            survey_obs_dict = {
                "obs_mjd": date_to_mjd(fulltime),
                "survey_field": field_url_dict[data["Object"][i]],
                "status": "%s/api/taskstatuses/1/" % yseurl,
                "exposure_time": time,
                "photometric_band": ysepz_filt_dict[data["fil"][i]] % yseurl,
                "fwhm_major": fwhm,
                "airmass": secz,
                "image_id": str(data["#expid"][i]),
            }
            # check for duplicates
            r = requests.get(
                url="%s/api/surveyobservations/?survey_field=%s"
                % (yseurl, data["Object"][i]),
                auth=HTTPBasicAuth(self.options.yseuser, self.options.ysepass),
            ).json()
            duplicate = False
            for d in r["results"]:
                if (
                    d["photometric_band"] == survey_obs_dict["photometric_band"]
                    and np.abs(d["obs_mjd"] - survey_obs_dict["obs_mjd"]) < 0.001
                ):
                    duplicate = True
            if duplicate:
                print("warning : duplicate observation found")
                continue

            r = requests.post(
                url="%s/api/surveyobservations/" % yseurl,
                json=survey_obs_dict,
                auth=HTTPBasicAuth(self.options.yseuser, self.options.ysepass),
            )

            if r.status_code != 201:
                raise RuntimeError("failed to add observation!")

        return


if __name__ == "__main__":

    dy = DECAM_YSEPZ()

    parser = dy.add_args()
    args = parser.parse_args()
    dy.options = args
    dy.upload_transients()
