import requests
import time
import imaplib
import socket
import ssl
import getpass
import pprint
import email
import re
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from enum import Enum
from astroquery.ned import Ned
import astropy.units as u
from astropy import coordinates
import numpy as np
from astroquery.irsa_dust import IrsaDust
import datetime
import json
import os
from astropy.coordinates import SkyCoord
from astropy.coordinates import ICRS, Galactic, FK4, FK5
from astropy.time import Time
import coreapi
import wget
from urllib.parse import unquote

reg_obj = b"https://wis-tns.weizmann.ac.il/object/(\w+)"
# reg_ra = b"\d{4}\w+\sRA[\=a-zA-Z\<\>\" ]+(\d{2}:\d{2}:\d{2}\.\d+)"
# reg_dec = b"DEC[\=a-zA-Z\<\>\" ]+((?:\+|\-)\d{2}:\d{2}:\d{2}\.\d+)\,\s\w+"

reg_ra = b'\>\sRA[\=\*a-zA-Z\<\>" ]+(\d{2}:\d{2}:\d{2}\.\d+)'
reg_dec = b'DEC[\=\*a-zA-Z\<\>" ]+((?:\+|\-)\d{2}:\d{2}:\d{2}\.\d+)\<\/em\>\,'

photkeydict = {
    "magflux": "Mag. / Flux",
    "magfluxerr": "Err",
    "obsdate": "Obs-date",
    "maglim": "Lim. Mag./Flux",
    "unit": "Units",
    "filter": "Filter",
    "inst": "Tel / Inst",
    "remarks": "Remarks",
    "obsgroup": "Assoc. Groups",
    "specfile": "Spectrum ascii file",
}


def try_parse_float(s):
    try:
        test = float(s)
        return True
    except ValueError:
        return False


class phot_row:
    def __init__(self, rowResultSet):

        self.ID = None
        self.Obs_date = None
        self.Mag_Flux = None
        self.Err = None
        self.Lim_Mag_Flux = None
        self.Units = None
        self.Filter = None
        self.Tel_Inst = None
        self.Exp_time = None
        self.Observers = None
        self.Remarks = None

        tds = rowResultSet.find_all("td")

        if len(tds) > 0:
            self.ID = tds[0].text
            self.Obs_date = (
                datetime.datetime.strptime(tds[1].text, "%Y-%m-%d %H:%M:%S")
                if tds[1].text != ""
                else None
            )
            self.Mag_Flux = float(tds[2].text) if tds[2].text != "" else None
            self.Err = float(tds[3].text) if tds[3].text != "" else None
            self.Lim_Mag_Flux = float(tds[4].text) if tds[4].text != "" else None
            self.Units = tds[5].text
            self.Filter = tds[6].text
            self.Tel_Inst = tds[7].text
            self.Exp_time = tds[8].text
            self.Observers = tds[9].text
            self.Remarks = tds[10].text


class ned_row:
    def __init__(self, detail_url, obj_name, ra, dec, object_type, z, separation):
        self.detail_url = detail_url
        self.obj_name = obj_name
        self.ra = ra
        self.dec = dec
        self.object_type = object_type
        self.z = z
        self.separation = separation


class tns_obj:
    def __init__(
        self,
        name,
        tns_url,
        internal_name,
        event_type,
        ra,
        dec,
        ebv,
        z,
        tns_host,
        tns_host_z,
        ned_nearest_host,
        ned_nearest_z,
        ned_nearest_sep,
        discovery_date,
        phot_rows,
        disc_mag,
    ):

        self.Name = name
        self.TNS_URL = tns_url
        self.Internal_Name = internal_name
        self.Event_Type = (
            event_type if (event_type != "---" and event_type != "") else "Untyped"
        )
        self.Ra = ra
        self.Dec = dec
        self.EBV = ebv  # np.asarray([float(e) for e in ebv])
        self.Z = float(z) if (z != "---" and z != "") else -1
        self.TNS_Host = tns_host
        self.TNS_Host_Z = (
            float(tns_host_z) if (tns_host_z != "---" and tns_host_z != "") else -1
        )
        self.NED_Nearest_host = ned_nearest_host
        self.NED_Nearest_z = np.asarray([round(float(hz), 3) for hz in ned_nearest_z])
        self.NED_Nearest_sep = np.asarray([float(s) for s in ned_nearest_sep])
        self.Discovery_Date = datetime.datetime.strptime(
            discovery_date, "%Y-%m-%d %H:%M:%S"
        )
        self.Photometry = phot_rows
        self.Disc_Mag = float(disc_mag)

        dec_deg = float(dec[:3])
        self.Survey = "FOUNDATION" if dec_deg > -30 else "SWOPE"

        # Get the last photometry row that has the remark "Last non detection". If this doens't exist, just get the
        # last photometry row.

    def last_nondetection(self):
        ln_dates = [p for p in self.Photometry if "Last non detection" in p.Remarks]
        if ln_dates is None or len(ln_dates) == 0:
            ln_dates = self.Photometry

        lnd = ln_dates[-1].Obs_date
        days = (datetime.datetime.today() - lnd).days

        return (lnd, days)

    def build_comments(self):

        comments = []
        lnd = self.last_nondetection()

        # .decode("utf-8")
        if not np.any([(h == self.TNS_Host) for h in self.NED_Nearest_host]):
            comments.append("-TNS and NED hosts disagree.")

        if not (
            np.any(self.NED_Nearest_z == self.TNS_Host_Z)
            or np.any(self.NED_Nearest_z == self.Z)
        ):
            comments.append("-TNS and NED z disagree.")

        if lnd[1] >= 17 and lnd[1] <= 20:
            comments.append("-Last non-detection questionable.")

        return comments

    def validate(self):

        bad_reasons = []

        # Last non-detection check
        lnd = self.last_nondetection()
        good_lnd = lnd[1] <= 20

        # Reddening check
        good_r = (
            self.A_v is not None and len(self.A_v) > 0 and not np.any(self.A_v >= 0.5)
        )

        # Host check - exists?
        good_h = (self.TNS_Host != "") or (
            self.NED_Nearest_host is not None or len(self.NED_Nearest_host) > 0
        )

        # Z check - either obj z, host z, or NED z exists and is in range
        good_obj_z = False
        good_TNS_host_z = False
        good_NED_z = False

        # if obj_z is present, it trumps the rest of the checks.
        #  if good, stop checks
        #  if bad, stop checks and report
        #
        # if obj_z is missing, check host_z
        # 	if host_z is present, it trumps the rest of checks
        # 	  if good, stop checks
        # 	  if bad, stop checks and report
        #
        # if NED_z is present,
        # 	if bad, report
        # *If any z is less than 0.015, mark as questionable. Might be close enough

        obj_z_present = self.Z is not None and self.Z != "" and self.Z != -1
        tns_host_z_present = (
            self.TNS_Host_Z is not None
            and self.TNS_Host_Z != ""
            and self.TNS_Host_Z != -1
        )

        if obj_z_present:
            good_obj_z = self.Z >= 0.015 and self.Z <= 0.08

        if tns_host_z_present:
            good_TNS_host_z = self.TNS_Host_Z >= 0.015 and self.TNS_Host_Z <= 0.08

        good_NED_z = np.any(
            [(nedz >= 0.015 and nedz <= 0.08) for nedz in self.NED_Nearest_z]
        )

        # Questionable if too low of z, or LND same as discovery date
        questionable = (
            (self.Z > 0.0 and self.Z < 0.015)
            or (self.TNS_Host_Z > 0.0 and self.TNS_Host_Z < 0.015)
            or np.any([(nedz < 0.015) for nedz in self.NED_Nearest_z])
            or lnd[1] == 0
        )

        good_z = good_obj_z or good_TNS_host_z or good_NED_z

        # check obj type - either unspecified of SN Ia
        good_type = (
            self.Event_Type == ""
            or self.Event_Type == "Untyped"
            or self.Event_Type == "SN Ia"
        )

        # ---- Checks ---- #
        if not good_lnd:
            bad_reasons.append("-Last non-detection too long: %s" % lnd[1])

        if not good_r:
            av = -1
            if len(self.A_v) > 0:
                av = self.A_v[0]
            bad_reasons.append("-Reddening too high or not available; a_v = %s" % av)

        if not good_h:
            bad_reasons.append("-No host in TNS or NED")

        if obj_z_present:
            if not good_obj_z:
                bad_reasons.append("-Bad TNS Object z: %s" % self.Z)
        else:
            if tns_host_z_present:
                if not good_TNS_host_z:
                    bad_reasons.append(
                        "-No TNS Object z & bad TNS Host z: %s" % self.TNS_Host_Z
                    )
            else:
                if not good_NED_z:
                    bad_reasons.append("-No TNS Object or Host z, no good NED z")

        if not good_type:
            bad_reasons.append("-Object not 'Untyped' or 'SN Ia'")

        valid = good_lnd and good_r and good_h and good_z and good_type

        status = "Questionable"
        if not questionable:
            if valid:
                status = "True"
            else:
                status = "False"

        return (status, bad_reasons)


def WriteLine(f, text, em):
    line = text
    if em and text != "":
        line = "*" + text + "*"

    f.write(line + "\n")


def WriteOutput(tns_objs):
    today = datetime.datetime.today().strftime("%Y%m%d_%H%M")
    fname1 = "TNS_Report_%s.txt" % today

    with open(fname1, "w") as f:
        for i in range(len(tns_objs)):

            sindex = np.argsort(tns_objs[i].NED_Nearest_sep)
            val = tns_objs[i].validate()
            em = val[0] == "True" or val[0] == "Questionable"

            WriteLine(f, "--------------------------------------------------------", em)
            WriteLine(f, ("Valid?: %s" % val[0]), em)
            WriteLine(f, "Reason(s):", em)
            [WriteLine(f, r, em) for r in val[1]]
            WriteLine(f, ("Survey: %s" % tns_objs[i].Survey), em)
            WriteLine(
                f, ("Name: %s (%s)" % (tns_objs[i].Name, tns_objs[i].TNS_URL)), em
            )
            WriteLine(f, ("Internal Name: %s" % tns_objs[i].Internal_Name), em)
            WriteLine(f, ("Type: %s" % tns_objs[i].Event_Type), em)
            WriteLine(f, ("Dec: %s" % tns_objs[i].Dec), em)
            WriteLine(f, ("Host (via TNS): %s" % tns_objs[i].TNS_Host), em)
            WriteLine(f, ("Object z (via TNS): %s" % tns_objs[i].Z), em)
            WriteLine(f, ("Host z (via TNS): %s" % tns_objs[i].TNS_Host_Z), em)
            WriteLine(f, ("Disc. Date: %s" % tns_objs[i].Discovery_Date), em)

            lnd = tns_objs[i].last_nondetection()
            WriteLine(f, ("Last non-detection: %s" % lnd[0]), em)
            WriteLine(f, ("Last non-detection days: %s" % lnd[1]), em)
            WriteLine(f, ("Disc. Mag: %s" % tns_objs[i].Disc_Mag), em)
            WriteLine(f, "", em)
            WriteLine(f, "--NED info--", em)
            if len(tns_objs[i].NED_Nearest_host) > 0:
                for j in range(len(tns_objs[i].NED_Nearest_host)):

                    formatted_text = (
                        "NED Host: %s; Separation [arcmin]: %s; a_v: %s; z: %s"
                        % (
                            tns_objs[i].NED_Nearest_host[sindex[j]],  # .decode("utf-8")
                            tns_objs[i].NED_Nearest_sep[sindex[j]],
                            tns_objs[i].A_v[sindex[j]],
                            tns_objs[i].NED_Nearest_z[sindex[j]],
                        )
                    )
                    WriteLine(f, formatted_text, em)
            WriteLine(f, "", em)
            WriteLine(f, "Comment(s):", em)
            [WriteLine(f, c, em) for c in tns_objs[i].build_comments()]

    with open("TNS_Outputs.txt", "w") as t_o:
        t_o.write(fname1)


class DBOps:
    def __init__(self):
        pass

    def init_params(self):
        self.dblogin = self.options.dblogin
        self.dbpassword = self.options.dbpassword
        self.dburl = self.options.dburl
        self.baseposturl = "http --ignore-stdin -a %s:%s POST %s" % (
            self.dblogin,
            self.dbpassword,
            self.dburl,
        )
        self.basegeturl = "http --ignore-stdin -a %s:%s GET %s" % (
            self.dblogin,
            self.dbpassword,
            self.dburl,
        )
        self.baseputurl = "http --ignore-stdin -a %s:%s PUT %s" % (
            self.dblogin,
            self.dbpassword,
            self.dburl,
        )
        self.basegetobjurl = "http --ignore-stdin -a %s:%s GET " % (
            self.dblogin,
            self.dbpassword,
        )

    def add_options(self, parser=None, usage=None, config=None):
        import optparse

        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

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

        if config:
            parser.add_option(
                "--login",
                default=config.get("main", "login"),
                type="string",
                help="gmail login (default=%default)",
            )
            parser.add_option(
                "--password",
                default=config.get("main", "password"),
                type="string",
                help="gmail password (default=%default)",
            )

            parser.add_option(
                "--dblogin",
                default=config.get("main", "dblogin"),
                type="string",
                help="gmail login (default=%default)",
            )
            parser.add_option(
                "--dbpassword",
                default=config.get("main", "dbpassword"),
                type="string",
                help="gmail password (default=%default)",
            )
            parser.add_option(
                "--dburl",
                default=config.get("main", "dburl"),
                type="string",
                help="base URL to POST/GET,PUT to/from a database (default=%default)",
            )
            parser.add_option(
                "--transientapi",
                default=config.get("main", "transientapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--internalsurveyapi",
                default=config.get("main", "internalsurveyapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--transientclassesapi",
                default=config.get("main", "transientclassesapi"),
                type="string",
                help="URL to POST transients classes to a database (default=%default)",
            )
            parser.add_option(
                "--hostapi",
                default=config.get("main", "hostapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--photometryapi",
                default=config.get("main", "photometryapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--photdataapi",
                default=config.get("main", "photdataapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--hostphotometryapi",
                default=config.get("main", "hostphotometryapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--hostphotdataapi",
                default=config.get("main", "hostphotdataapi"),
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--obs_groupapi",
                default=config.get("main", "obs_groupapi"),
                type="string",
                help="URL to POST group to a database (default=%default)",
            )
            parser.add_option(
                "--statusapi",
                default=config.get("main", "statusapi"),
                type="string",
                help="URL to POST status to a database (default=%default)",
            )
            parser.add_option(
                "--instrumentapi",
                default=config.get("main", "instrumentapi"),
                type="string",
                help="URL to POST instrument to a database (default=%default)",
            )
            parser.add_option(
                "--bandapi",
                default=config.get("main", "bandapi"),
                type="string",
                help="URL to POST band to a database (default=%default)",
            )
            parser.add_option(
                "--observatoryapi",
                default=config.get("main", "observatoryapi"),
                type="string",
                help="URL to POST observatory to a database (default=%default)",
            )
            parser.add_option(
                "--telescopeapi",
                default=config.get("main", "telescopeapi"),
                type="string",
                help="URL to POST telescope to a database (default=%default)",
            )

            return parser

    def post_object_to_DB(self, table, objectdict, return_full=False):
        cmd = "%s%s " % (self.baseposturl, self.options.__dict__["%sapi" % table])
        for k, v in zip(objectdict.keys(), objectdict.values()):
            if "<url>" not in str(v):
                if k != "tags" and k != "groups":
                    cmd += '%s="%s" ' % (k, v)
                else:
                    cmd += "%s:=[] " % (k)
            else:
                cmd += '%s="%s%s%s/" ' % (
                    k,
                    self.dburl,
                    self.options.__dict__["%sapi" % k],
                    v.split("/")[1],
                )

        objectdata = runDBcommand(cmd)

        if type(objectdata) != list and "url" not in objectdata:
            print(cmd)
            print(objectdata)
            raise RuntimeError("Error : failure adding object")
        if return_full:
            return objectdata
        else:
            return objectdata["url"]

    def put_object_to_DB(self, table, objectdict, objectid, return_full=False):
        cmd = "%s PUT %s " % (self.baseputurl.split("PUT")[0], objectid)
        for k, v in zip(objectdict.keys(), objectdict.values()):
            if "<url>" not in str(v):
                if k != "tags" and k != "groups":
                    cmd += '%s="%s" ' % (k, v)
                else:
                    cmd += "%s:=[] " % k
            else:
                cmd += '%s="%s%s%s/" ' % (
                    k,
                    self.dburl,
                    self.options.__dict__["%sapi" % k],
                    v.split("/")[1],
                )
        objectdata = runDBcommand(cmd)

        if type(objectdata) != list and "url" not in objectdata:
            print("cmd %s failed")
            print(objectdata)
            raise RuntimeError("Error : failure adding object")
        if return_full:
            return objectdata
        else:
            return objectdata["url"]

    def patch_object_to_DB(self, table, objectdict, objectid, return_full=False):
        cmd = "%s PATCH %s " % (self.baseputurl.split("PUT")[0], objectid)
        for k, v in zip(objectdict.keys(), objectdict.values()):
            if "<url>" not in str(v):
                if k != "tags" and k != "groups":
                    cmd += '%s="%s" ' % (k, v)
                else:
                    cmd += "%s:=[] " % k
            else:
                cmd += '%s="%s%s%s/" ' % (
                    k,
                    self.dburl,
                    self.options.__dict__["%sapi" % k],
                    v.split("/")[1],
                )
        objectdata = runDBcommand(cmd)

        if type(objectdata) != list and "url" not in objectdata:
            print("cmd %s failed")
            print(objectdata)
            raise RuntimeError("Error : failure adding object")
        if return_full:
            return objectdata
        else:
            return objectdata["url"]

    def get_ID_from_DB(self, tablename, fieldname, debug=False):

        if debug:
            tstart = time.time()
        auth = coreapi.auth.BasicAuthentication(
            username=self.dblogin, password=self.dbpassword
        )
        client = coreapi.Client(auth=auth)
        try:
            schema = client.get("%s%s?limit=100000" % (self.dburl, tablename))
        except:
            raise RuntimeError("Error : couldn't get schema!")

        idlist, namelist = [], []
        for i in range(len(schema["results"])):
            namelist += [schema["results"][i]["name"].lower()]
            idlist += [schema["results"][i]["url"]]

        if debug:
            print("GET took %.1f seconds" % (time.time() - tstart))
        if fieldname.lower() not in namelist:
            return None

        return np.array(idlist)[np.where(np.array(namelist) == fieldname.lower())][0]

    def get_band_from_DB(self, fieldname, instrumentid, debug=False):

        tablename = "photometricbands"

        if debug:
            tstart = time.time()
        auth = coreapi.auth.BasicAuthentication(
            username=self.dblogin, password=self.dbpassword
        )
        client = coreapi.Client(auth=auth)
        try:
            schema = client.get("%s%s?limit=100000" % (self.dburl, tablename))
        except:
            raise RuntimeError("Error : couldn't get schema!")

        idlist, namelist, instlist = [], [], []
        for i in range(len(schema["results"])):
            namelist += [schema["results"][i]["name"]]
            idlist += [schema["results"][i]["url"]]
            instlist += [schema["results"][i]["instrument"]]

        if debug:
            print("GET took %.1f seconds" % (time.time() - tstart))

        if not len(
            np.where(
                (np.array(namelist) == fieldname) & (np.array(instlist) == instrumentid)
            )[0]
        ):
            return None

        return np.array(idlist)[
            np.where(
                (np.array(namelist) == fieldname) & (np.array(instlist) == instrumentid)
            )
        ][0]

    def get_transient_from_DB(self, fieldname, debug=False):

        if debug:
            tstart = time.time()
        tablename = "transients"
        auth = coreapi.auth.BasicAuthentication(
            username=self.dblogin, password=self.dbpassword
        )
        client = coreapi.Client(auth=auth)
        try:
            schema = client.get(
                "%s%s" % (self.dburl.replace("/api", "/get_transient"), fieldname)
            )
        except:
            raise RuntimeError("Error : couldn't get schema!")

        if not schema["transient"]:
            return None

        return schema["transient"]["url"]

    def add_phot_to_DB(self, PhotUploadAll):

        print("Adding Photometry")

        import requests
        from requests.auth import HTTPBasicAuth

        url = "%s" % db.dburl.replace("/api", "/add_transient_phot")
        r = requests.post(
            url=url,
            data=json.dumps(PhotUploadAll),
            auth=HTTPBasicAuth(db.dblogin, db.dbpassword),
        )

        print("YSE_PZ says: %s" % json.loads(r.text)["message"])

    def get_host_from_DB(self, hostname, hostra, hostdec, matchrad=0.0008, debug=False):

        if debug:
            tstart = time.time()
        tablename = "hosts"
        auth = coreapi.auth.BasicAuthentication(
            username=self.dblogin, password=self.dbpassword
        )
        client = coreapi.Client(auth=auth)
        try:
            schema = client.get(
                "%s%.7f/%.7f/%.4f/"
                % (self.dburl.replace("/api", "/get_host"), hostra, hostdec, matchrad)
            )
        except:
            raise RuntimeError("Error : couldn't get schema!")

        if not len(schema["host candidates"]):
            return None

        seplist = []
        for i in range(len(schema["host candidates"])):
            seplist += [schema["host candidates"][i]["host_sep"]]
        minsep = np.where(seplist == np.min(seplist))[0].astype(int)
        if len(minsep) > 1:
            minsep = [minsep[0]]

        return "%s%s/%s/" % (
            self.dburl,
            tablename,
            schema["host candidates"][minsep[0]]["host_id"],
        )

    def get_key_from_object(self, objid, fieldname):
        cmd = "%s%s?limit=100000" % (self.basegetobjurl, objid)
        output = os.popen(cmd).read()
        try:
            data = json.loads(output)
        except:
            print(cmd)
            print(os.popen(cmd).read())
            raise RuntimeError("Error : cmd output not in JSON format")

        if fieldname in data:
            val = data[fieldname]
            return val
        else:
            return None


class processTNS:
    def __init__(self):
        self.verbose = None

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

        if config:
            parser.add_option(
                "--login",
                default=config.get("main", "login"),
                type="string",
                help="gmail login (default=%default)",
            )
            parser.add_option(
                "--password",
                default=config.get("main", "password"),
                type="string",
                help="gmail password (default=%default)",
            )
            parser.add_option(
                "--dblogin",
                default=config.get("main", "dblogin"),
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
                "--hostmatchrad",
                default=config.get("main", "hostmatchrad"),
                type="float",
                help="matching radius for hosts (arcmin) (default=%default)",
            )

        else:
            parser.add_option(
                "--login",
                default="",
                type="string",
                help="gmail login (default=%default)",
            )
            parser.add_option(
                "--password",
                default="",
                type="string",
                help="gmail password (default=%default)",
            )
            parser.add_option(
                "--dblogin",
                default="",
                type="string",
                help="database login, if post=True (default=%default)",
            )
            parser.add_option(
                "--dbpassword",
                default="",
                type="string",
                help="database password, if post=True (default=%default)",
            )
            parser.add_option(
                "--url",
                default="",
                type="string",
                help="URL to POST transients to a database (default=%default)",
            )
            parser.add_option(
                "--hostmatchrad",
                default=0.001,
                type="float",
                help="matching radius for hosts (arcmin) (default=%default)",
            )

        return parser

    def ProcessTNSEmails(self, post=True, posturl=None, db=None):
        body = ""
        html = ""
        tns_objs = []
        radius = 5  # arcminutes

        ########################################################
        # Get All Email
        ########################################################
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)  # , ssl_context=ctx

        ## NOTE: This is not the way to do this. You will want to implement an industry-standard login step ##
        mail.login(self.login, self.password)
        mail.select("TNS", readonly=False)
        retcode, msg_ids_bytes = mail.search(None, "(UNSEEN)")
        msg_ids = msg_ids_bytes[0].decode("utf-8").split(" ")

        try:
            if retcode != "OK" or msg_ids[0] == "":
                raise ValueError("No messages")

        except ValueError as err:
            print("%s. Exiting..." % err.args)
            mail.close()
            mail.logout()
            del mail
            print("Process done.")
            return

        for i in range(len(msg_ids)):
            ########################################################
            # Iterate Over Email
            ########################################################
            typ, data = mail.fetch(msg_ids[i], "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            # Mark messages as "Unseen"
            # result, wdata = mail.store(msg_ids[i], '-FLAGS', '\Seen')

            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))

                    # skip any text/plain (txt) attachments
                    if (
                        ctype == "text/plain" or ctype == "text/html"
                    ) and "attachment" not in cdispo:
                        body = part.get_payload(decode=True)  # decode
                        # body = part.get_payload()#[0]._payload.encode('utf-8')
                        break
                        # not multipart - i.e. plain text, no attachments, keeping fingers crossed
            else:
                body = msg.get_payload(decode=True)

            objs = re.findall(reg_obj, body)
            print(objs)
            ras = re.findall(reg_ra, body)
            print(ras)
            decs = re.findall(reg_dec, body)
            print(decs)

            try:
                ########################################################
                # For Item in Email, Get TNS
                ########################################################

                for j in range(len(objs)):
                    print(
                        "Object: %s\nRA: %s\nDEC: %s"
                        % (
                            objs[j].decode("utf-8"),
                            ras[j].decode("utf-8"),
                            decs[j].decode("utf-8"),
                        )
                    )

                    # Get TNS page
                    int_name = ""
                    evt_type = ""
                    evt_z = ""
                    host_name = ""
                    host_redshift = ""
                    ned_url = ""

                    tns_url = "https://wis-tns.weizmann.ac.il/object/" + objs[j].decode(
                        "utf-8"
                    )
                    print(tns_url)

                    tstart = time.time()
                    try:
                        response = requests.get(tns_url, timeout=20)
                        html = response.content
                    except:
                        print("trying again")
                        response = requests.get(tns_url, timeout=20)
                        html = response.content

                    soup = BeautifulSoup(html, "lxml")

                    # Get Internal Name, Type, Disc. Date, Disc. Mag, Redshift, Host Name, Host Redshift, NED URL
                    int_name = soup.find(
                        "td", attrs={"class": "cell-internal_name"}
                    ).text
                    evt_type = (
                        soup.find("div", attrs={"class": "field-type"})
                        .find("div")
                        .find("b")
                        .text
                    )
                    evt_type = evt_type  # .replace(' ','')
                    disc_date = (
                        soup.find("div", attrs={"class": "field field-discoverydate"})
                        .find("div")
                        .find("b")
                        .text
                    )
                    disc_mag = (
                        soup.find("div", attrs={"class": "field field-discoverymag"})
                        .find("div")
                        .find("b")
                        .text
                    )
                    try:
                        source_group = (
                            soup.find(
                                "div", attrs={"class": "field field-source_group_name"}
                            )
                            .find("div")
                            .find("b")
                            .text
                        )
                    except AttributeError:
                        source_group = "Unknown"
                    try:
                        disc_filter = soup.find(
                            "td", attrs={"cell": "cell-filter_name"}
                        ).text
                    except AttributeError:
                        disc_filter = "Unknown"
                    if "-" in disc_filter:
                        disc_instrument = disc_filter.split("-")[1]
                    else:
                        disc_instrument = "Unknown"

                    # lets pull the photometry
                    nondetectmaglim = None
                    nondetectdate = None
                    nondetectfilt = None
                    tmag, tmagerr, tflux, tfluxerr, tfilt, tinst, tobsdate = (
                        np.array([]),
                        np.array([]),
                        np.array([]),
                        np.array([]),
                        np.array([]),
                        np.array([]),
                        np.array([]),
                    )
                    try:
                        tables = soup.find_all(
                            "table", attrs={"class": "photometry-results-table"}
                        )
                        for table in tables:
                            data = []
                            table_body = table.find("tbody")
                            header = table.find("thead")
                            headcols = header.find_all("th")
                            header = np.array([ele.text.strip() for ele in headcols])
                            # header.append([ele for ele in headcols if ele])
                            rows = table_body.find_all("tr")

                            for row in rows:
                                cols = row.find_all("td")
                                data.append([ele.text.strip() for ele in cols])

                            for datarow in data:
                                datarow = np.array(datarow)
                                if photkeydict["unit"] in header:
                                    if (
                                        "mag"
                                        in datarow[header == photkeydict["unit"]][
                                            0
                                        ].lower()
                                    ):
                                        if photkeydict["magflux"] in header:
                                            tmag = np.append(
                                                tmag,
                                                datarow[
                                                    header == photkeydict["magflux"]
                                                ],
                                            )
                                            tflux = np.append(tflux, "")
                                        else:
                                            tmag = np.append(tmag, "")
                                            tflux = np.append(tflux, "")
                                        if photkeydict["magfluxerr"] in header:
                                            tmagerr = np.append(
                                                tmagerr,
                                                datarow[
                                                    header == photkeydict["magfluxerr"]
                                                ],
                                            )
                                            tfluxerr = np.append(tfluxerr, "")
                                        else:
                                            tmagerr = np.append(tmagerr, None)
                                            tfluxerr = np.append(tfluxerr, "")
                                    elif (
                                        "flux"
                                        in datarow[header == photkeydict["unit"]][
                                            0
                                        ].lower()
                                    ):
                                        if photkeydict["magflux"] in header:
                                            tflux = np.append(
                                                tflux,
                                                datarow[
                                                    header == photkeydict["magflux"]
                                                ],
                                            )
                                            tmag = np.append(tmag, "")
                                        else:
                                            tflux = np.append(tflux, "")
                                            tmag = np.append(tmag, "")
                                        if photkeydict["magfluxerr"] in header:
                                            tfluxerr = np.append(
                                                tfluxerr,
                                                datarow[
                                                    header == photkeydict["magfluxerr"]
                                                ],
                                            )
                                            tmagerr = np.append(tmagerr, "")
                                        else:
                                            tfluxerr = np.append(tfluxerr, None)
                                            tmagerr = np.append(tmagerr, "")
                                if photkeydict["filter"] in header:
                                    tfilt = np.append(
                                        tfilt, datarow[header == photkeydict["filter"]]
                                    )
                                if photkeydict["inst"] in header:
                                    tinst = np.append(
                                        tinst,
                                        datarow[header == photkeydict["inst"]][0].split(
                                            "_"
                                        )[1],
                                    )
                                if photkeydict["obsdate"] in header:
                                    tobsdate = np.append(
                                        tobsdate,
                                        datarow[header == photkeydict["obsdate"]],
                                    )
                                if (
                                    photkeydict["remarks"] in header
                                    and photkeydict["maglim"] in header
                                ):
                                    if (
                                        "last"
                                        in datarow[header == photkeydict["remarks"]][
                                            0
                                        ].lower()
                                        and "non"
                                        in datarow[header == photkeydict["remarks"]][
                                            0
                                        ].lower()
                                        and "detection"
                                        in datarow[header == photkeydict["remarks"]][
                                            0
                                        ].lower()
                                    ):
                                        nondetectmaglim = datarow[
                                            header == photkeydict["maglim"]
                                        ][0]
                                        nondetectdate = datarow[
                                            header == photkeydict["obsdate"]
                                        ][0]
                                        nondetectfilt = datarow[
                                            header == photkeydict["filter"]
                                        ][0]

                                        # set the discovery flag
                        disc_flag = np.zeros(len(tmag))
                        iMagsExist = np.where(tmag != "")[0]
                        if len(tmag) and len(iMagsExist) == 1:
                            disc_flag[np.where(tmag != "")] = 1
                        elif len(iMagsExist) > 1:
                            mjd = np.zeros(len(iMagsExist))
                            for d in range(len(mjd)):
                                mjd[d] = date_to_mjd(tobsdate[d])
                            iMinMJD = np.where(mjd == np.min(mjd))[0]
                            if len(iMinMJD) > 1:
                                iMinMJD = [iMinMJD[0]]
                            for im, iim in zip(iMagsExist, range(len(iMagsExist))):
                                if len(iMinMJD) and iim == iMinMJD[0]:
                                    disc_flag[im] = 1

                    except:
                        print("Error : couldn't get photometry!!!")

                    evt_z = (
                        soup.find("div", attrs={"class": "field-redshift"})
                        .find("div")
                        .find("b")
                        .text
                    )

                    hn_div = soup.find("div", attrs={"class": "field-hostname"})
                    if hn_div is not None:
                        host_name = hn_div.find("div").find("b").text

                    z_div = soup.find("div", attrs={"class": "field-host_redshift"})
                    if z_div is not None:
                        host_redshift = z_div.find("div").find("b").text

                    ned_url = soup.find(
                        "div", attrs={"class": "additional-links clearfix"}
                    ).find("a")["href"]

                    # Get photometry records
                    table = soup.findAll(
                        "table", attrs={"class": "photometry-results-table"}
                    )
                    prs = []
                    for k in range(len(table)):

                        table_body = table[k].find("tbody")
                        rows = table_body.find_all("tr")
                        print(type(rows))

                        for l in range(len(rows)):
                            prs.append(phot_row(rows[l]))

                            ########################################################
                            # For Item in Email, Get NED
                            ########################################################
                    ra_j = ras[j].decode("utf-8")
                    dec_j = decs[j].decode("utf-8")

                    co = coordinates.SkyCoord(
                        ra=ra_j,
                        dec=dec_j,
                        unit=(u.hour, u.deg),
                        frame="fk4",
                        equinox="J2000.0",
                    )
                    dust_table_l = IrsaDust.get_query_table(co)
                    ebv = dust_table_l["ext SandF mean"][0]
                    ned_region_table = None

                    gal_candidates = 0
                    radius = 5
                    while radius < 11 and gal_candidates < 21:
                        try:
                            print("Radius: %s" % radius)
                            ned_region_table = Ned.query_region(
                                co, radius=radius * u.arcmin, equinox="J2000.0"
                            )
                            gal_candidates = len(ned_region_table)
                            radius += 1
                            print("Result length: %s" % gal_candidates)
                        except Exception as e:
                            radius += 1
                            print("NED exception: %s" % e.args)

                    galaxy_names = []
                    galaxy_zs = []
                    galaxy_seps = []
                    galaxies_with_z = []
                    galaxy_ras = []
                    galaxy_decs = []
                    galaxy_mags = []
                    if ned_region_table is not None:
                        print("NED Matches: %s" % len(ned_region_table))

                        galaxy_candidates = np.asarray(
                            [
                                entry.decode("utf-8")
                                for entry in ned_region_table["Type"]
                            ]
                        )
                        galaxies_indices = np.where(galaxy_candidates == "G")
                        galaxies = ned_region_table[galaxies_indices]

                        print("Galaxy Candidates: %s" % len(galaxies))

                        # Get Galaxy name, z, separation for each galaxy with z
                        for l in range(len(galaxies)):
                            if isinstance(galaxies[l]["Redshift"], float):
                                galaxies_with_z.append(galaxies[l])
                                galaxy_names.append(galaxies[l]["Object Name"])
                                galaxy_zs.append(galaxies[l]["Redshift"])
                                galaxy_seps.append(galaxies[l]["Distance (arcmin)"])
                                galaxy_ras.append(galaxies[l]["RA(deg)"])
                                galaxy_decs.append(galaxies[l]["DEC(deg)"])
                                galaxy_mags.append(galaxies[l]["Magnitude and Filter"])

                        print("Galaxies with z: %s" % len(galaxies_with_z))
                        # Get Dust in LoS for each galaxy with z
                        if len(galaxies_with_z) > 0:
                            for l in range(len(galaxies_with_z)):
                                co_l = coordinates.SkyCoord(
                                    ra=galaxies_with_z[l]["RA(deg)"],
                                    dec=galaxies_with_z[l]["DEC(deg)"],
                                    unit=(u.deg, u.deg),
                                    frame="fk4",
                                    equinox="J2000.0",
                                )

                        else:
                            print("No NED Galaxy hosts with z")

                    tns_objs.append(
                        tns_obj(
                            name=objs[j].decode("utf-8"),
                            tns_url=tns_url,
                            internal_name=int_name,
                            event_type=evt_type,
                            ra=ras[j].decode("utf-8"),
                            dec=decs[j].decode("utf-8"),
                            ebv=ebv,
                            z=evt_z,
                            tns_host=host_name,
                            tns_host_z=host_redshift,
                            ned_nearest_host=galaxy_names,
                            ned_nearest_z=galaxy_zs,
                            ned_nearest_sep=galaxy_seps,
                            discovery_date=disc_date,
                            phot_rows=prs,
                            disc_mag=disc_mag,
                        )
                    )

                    if post:
                        snid = objs[j].decode("utf-8")
                        # if source_group doesn't exist, we need to add it
                        obsgroupid = db.get_ID_from_DB(
                            "observationgroups", source_group
                        )
                        if not obsgroupid:
                            obsgroupid = db.get_ID_from_DB(
                                "observationgroups", "Unknown"
                            )  # db.post_object_to_DB('observationgroup',{'name':source_group})

                            # get the status
                        statusid = db.get_ID_from_DB("transientstatuses", self.status)
                        if not statusid:
                            raise RuntimeError("Error : not all statuses are defined")

                        # put in the hosts
                        hostcoords = ""
                        hosturl = ""
                        ned_mag = ""
                        galaxy_z_times_seps = np.array(galaxy_seps) * np.array(
                            galaxy_zs
                        )
                        for z, name, ra, dec, sep, mag, gzs in zip(
                            galaxy_zs,
                            galaxy_names,
                            galaxy_ras,
                            galaxy_decs,
                            galaxy_seps,
                            galaxy_mags,
                            galaxy_z_times_seps,
                        ):
                            if gzs == np.min(galaxy_z_times_seps):
                                hostdict = {
                                    "name": name,
                                    "ra": ra,
                                    "dec": dec,
                                    "redshift": z,
                                }
                                hosturl = db.get_host_from_DB(
                                    name, ra, dec, self.hostmatchrad
                                )
                                if not hosturl:
                                    print("Adding new host!")
                                    hostoutput = db.post_object_to_DB(
                                        "host", hostdict, return_full=True
                                    )
                                    hosturl = hostoutput["url"]
                                    hostexists = False
                                else:
                                    print(
                                        "Host at coord RA,DEC=%.7f,%.7f already exists in DB"
                                        % (ra, dec)
                                    )
                                    hostexists = True
                                ned_mag = mag

                            hostcoords += "ra=%.7f, dec=%.7f\n" % (ra, dec)

                            # put in the spec type
                        eventid = db.get_ID_from_DB("transientclasses", evt_type)
                        if not eventid:
                            eventid = db.get_ID_from_DB(
                                "transientclasses", "Unknown"
                            )  # db.post_object_to_DB('transientclasses',{'name':evt_type})

                            # first check if already exists
                        dbid = db.get_transient_from_DB(snid)
                        k2id = db.get_ID_from_DB("internalsurveys", "K2")
                        # then POST or PUT, depending
                        # put in main transient
                        sc = SkyCoord(
                            ras[j].decode("utf-8"),
                            decs[j].decode("utf-8"),
                            FK5,
                            unit=(u.hourangle, u.deg),
                        )
                        db.options.best_spec_classapi = db.options.transientclassesapi

                        newobjdict = {
                            "name": objs[j].decode("utf-8"),
                            "ra": sc.ra.deg,
                            "dec": sc.dec.deg,
                            "obs_group": obsgroupid,
                            "host": hosturl,
                            "candidate_hosts": hostcoords,
                            "best_spec_class": eventid,
                            "TNS_spec_class": evt_type,
                            "mw_ebv": ebv,
                            "disc_date": disc_date.replace(" ", "T"),
                            "tags": [],
                            "groups": [],
                        }
                        if nondetectdate:
                            newobjdict["non_detect_date"] = nondetectdate.replace(
                                " ", "T"
                            )
                        if nondetectmaglim:
                            newobjdict["non_detect_limit"] = nondetectmaglim
                        if evt_z and evt_z != "---":
                            newobjdict["redshift"] = float(evt_z)
                        if nondetectfilt:
                            nondetectid = db.get_ID_from_DB(
                                "photometricbands", nondetectfilt
                            )
                            if nondetectid:
                                newobjdict["non_detect_filter"] = nondetectid

                        if dbid:
                            # if the status is ignore, we're going to promote this to new
                            status_getid = db.get_key_from_object(dbid, "status")
                            statusname = db.get_key_from_object(status_getid, "name")
                            if statusname == "Ignore":
                                newobjdict["status"] = statusid
                            transientid = db.patch_object_to_DB(
                                "transient", newobjdict, dbid
                            )
                        else:
                            newobjdict["status"] = statusid
                            transientid = db.post_object_to_DB("transient", newobjdict)

                            # add the photometry
                        for ins in np.unique(tinst):

                            transientdict = {
                                "obs_group": source_group,
                                "status": self.status,
                                "name": objs[j].decode("utf-8"),
                                "ra": sc.ra.deg,
                                "dec": sc.dec.deg,
                                "groups": [],
                            }

                            photdict = {
                                "instrument": ins,
                                "obs_group": source_group,
                                "transient": objs[j].decode("utf-8"),
                                "groups": [],
                            }

                            PhotUploadAll = {
                                "transient": transientdict,
                                "photheader": photdict,
                            }
                            try:
                                for f, k in zip(
                                    np.unique(tfilt), range(len(np.unique(tfilt)))
                                ):
                                    # put in the photometry

                                    for m, me, flx, fe, od, df in zip(
                                        tmag[(f == tfilt) & (ins == tinst)],
                                        tmagerr[(f == tfilt) & (ins == tinst)],
                                        tflux[(f == tfilt) & (ins == tinst)],
                                        tfluxerr[(f == tfilt) & (ins == tinst)],
                                        tobsdate[(f == tfilt) & (ins == tinst)],
                                        disc_flag[(f == tfilt) & (ins == tinst)],
                                    ):
                                        if not m and not me and not flx and not fe:
                                            continue
                                        # TODO: compare od to disc_date.replace(' ','T')
                                        # if they're close or equal?  Set discovery flag
                                        PhotUploadDict = {
                                            "obs_date": od.replace(" ", "T"),
                                            "band": f,
                                            "groups": [],
                                        }
                                        if m:
                                            PhotUploadDict["mag"] = m
                                        else:
                                            PhotUploadDict["mag"] = None
                                        if me:
                                            PhotUploadDict["mag_err"] = me
                                        else:
                                            PhotUploadDict["mag_err"] = None
                                        if flx:
                                            PhotUploadDict["flux"] = flx
                                        else:
                                            PhotUploadDict["flux"] = None
                                        if fe:
                                            PhotUploadDict["flux_err"] = fe
                                        else:
                                            PhotUploadDict["flux_err"] = None
                                        if df:
                                            PhotUploadDict["discovery_point"] = 1
                                        else:
                                            PhotUploadDict["discovery_point"] = 0
                                        PhotUploadDict["data_quality"] = 0
                                        PhotUploadDict["forced"] = None
                                        PhotUploadDict["flux_zero_point"] = None

                                        PhotUploadAll[
                                            "%s_%i" % (od.replace(" ", "T"), k)
                                        ] = PhotUploadDict

                                PhotUploadAll["header"] = {
                                    "clobber": True,
                                    "mjdmatchmin": 0.01,
                                }
                                db.add_phot_to_DB(PhotUploadAll)
                            except:
                                print("Error adding photometry!!")

                                # put in the galaxy photometry, if the host wasn't already in the DB
                            if ned_mag and not hostexists:
                                try:
                                    unknowninstid = db.get_ID_from_DB(
                                        "instruments", "Unknown"
                                    )
                                    unknowngroupid = db.get_ID_from_DB(
                                        "observationgroups", "NED"
                                    )
                                    if not unknowngroupid:
                                        unknowngroupid = db.get_ID_from_DB(
                                            "observationgroups", "Unknown"
                                        )
                                    unknownbandid = db.get_ID_from_DB(
                                        "photometricbands", "Unknown"
                                    )

                                    hostphottabledict = {
                                        "host": hosturl,
                                        "obs_group": unknowngroupid,
                                        "instrument": unknowninstid,
                                        "groups": [],
                                    }
                                    hostphottableid = db.post_object_to_DB(
                                        "hostphotometry", hostphottabledict
                                    )

                                    # put in the photometry
                                    hostphotdatadict = {
                                        "obs_date": disc_date.replace(
                                            " ", "T"
                                        ),  #'2000-01-01 00:00:00',
                                        "mag": ned_mag.decode("utf-8")[:-1],
                                        "band": unknownbandid,
                                        "photometry": hostphottableid,
                                        "groups": [],
                                    }
                                    hostphotdataid = db.post_object_to_DB(
                                        "hostphotdata", hostphotdatadict
                                    )
                                except:
                                    print("getting host mag failed")

                        try:
                            specinst, specobsdate, specobsgroup, specfiles = (
                                np.array([]),
                                np.array([]),
                                np.array([]),
                                np.array([]),
                            )

                            tables = soup.find_all(
                                "table", attrs={"class": "class-results-table"}
                            )
                            for table in tables:
                                data = []
                                table_body = table.find("tbody")
                                header = table.find("thead")
                                headcols = header.find_all("th")
                                header = np.array(
                                    [ele.text.strip() for ele in headcols]
                                )
                                # header.append([ele for ele in headcols if ele])
                                rows = table_body.find_all("tr")
                                for row in rows:
                                    cols = row.find_all("td")
                                    data.append([ele.text.strip() for ele in cols])

                                for datarow in data:
                                    datarow = np.array(datarow)
                                    if photkeydict["specfile"] not in header:
                                        continue
                                    if photkeydict["inst"] in header:
                                        print(datarow[header == photkeydict["inst"]])
                                        specinst = np.append(
                                            specinst,
                                            datarow[header == photkeydict["inst"]][0]
                                            .split("/")[1]
                                            .replace(" ", ""),
                                        )
                                    if "Obs-date (UT)" in header:
                                        specobsdate = np.append(
                                            specobsdate,
                                            datarow[header == "Obs-date (UT)"][0],
                                        )
                                    if photkeydict["obsgroup"] in header:
                                        specobsgroup = np.append(
                                            specobsgroup,
                                            datarow[header == photkeydict["obsgroup"]][
                                                0
                                            ],
                                        )
                                    if photkeydict["specfile"] in header:
                                        specfile = datarow[
                                            header == photkeydict["specfile"]
                                        ][0].encode("utf-8")
                                        reg_specfile = b'<a href=".*%s"' % specfile
                                        asciifile = re.findall(reg_specfile, html)
                                        finalspec = (
                                            asciifile[0]
                                            .decode("utf-8")
                                            .replace('<a href="', "")
                                            .replace('"', "")
                                        )
                                        specfiles = np.append(specfiles, finalspec)
                            if len(specfiles):
                                sc = SkyCoord(
                                    ras[j].decode("utf-8"),
                                    decs[j].decode("utf-8"),
                                    FK5,
                                    unit=(u.hourangle, u.deg),
                                )
                                for s, si, so, sog in zip(
                                    specfiles, specinst, specobsdate, specobsgroup
                                ):
                                    os.system(
                                        "rm %s spec_tns_upload.txt" % s.split("/")[-1]
                                    )
                                    dlfile = wget.download(unquote(s))
                                    fout = open("spec_tns_upload.txt", "w")
                                    print("# wavelength flux", file=fout)
                                    print(
                                        "# snid %s" % objs[j].decode("utf-8"), file=fout
                                    )
                                    print("# ra %s" % sc.ra.deg, file=fout)
                                    print("# dec %s" % sc.dec.deg, file=fout)
                                    print("# instrument %s" % si, file=fout)
                                    print(
                                        "# obs_date %s" % so.replace(" ", "T"),
                                        file=fout,
                                    )
                                    print("# obs_group %s" % sog, file=fout)
                                    fin = open(dlfile, "r")
                                    for line in fin:
                                        print(line.replace("\n", ""), file=fout)
                                    fout.close()
                                    print("uploading TNS spectrum...")
                                    os.system(
                                        "uploadTransientData.py -i %s --spectrum -e -s %s"
                                        % ("spec_tns_upload.txt", self.settingsfile)
                                    )
                                    os.system(
                                        "rm %s spec_tns_upload.txt" % s.split("/")[-1]
                                    )
                        except:
                            print("Error : couldn't get spectra!!!")

                            # Mark messages as "Seen"
                result, wdata = mail.store(msg_ids[i], "+FLAGS", "\\Seen")

            except:
                for j in range(len(objs)):
                    print("Something went wrong!!!	Sticking to basic info only")
                    print(
                        "Object: %s\nRA: %s\nDEC: %s"
                        % (
                            objs[j].decode("utf-8"),
                            ras[j].decode("utf-8"),
                            decs[j].decode("utf-8"),
                        )
                    )

                    snid = objs[j].decode("utf-8")
                    # if source_group doesn't exist, we need to add it
                    source_group = "Unknown"
                    obsgroupid = db.get_ID_from_DB("observationgroups", source_group)
                    if not obsgroupid:
                        obsgroupid = db.get_ID_from_DB(
                            "observationgroups", "Unknown"
                        )  # db.post_object_to_DB('observationgroup',{'name':source_group})

                        # get the status
                    statusid = db.get_ID_from_DB("transientstatuses", self.status)
                    if not statusid:
                        raise RuntimeError("Error : not all statuses are defined")

                    dbid = db.get_ID_from_DB("transients", snid)
                    k2id = db.get_ID_from_DB("internalsurveys", "K2")
                    # then POST or PUT, depending
                    # put in main transient
                    sc = SkyCoord(
                        ras[j].decode("utf-8"),
                        decs[j].decode("utf-8"),
                        FK5,
                        unit=(u.hourangle, u.deg),
                    )
                    db.options.best_spec_classapi = db.options.transientclassesapi
                    newobjdict = {
                        "name": objs[j].decode("utf-8"),
                        "ra": sc.ra.deg,
                        "dec": sc.dec.deg,
                        "status": statusid,
                        "obs_group": obsgroupid,
                        "tags": [],
                        "groups": [],
                    }

                    if dbid:
                        transientid = db.patch_object_to_DB(
                            "transient", newobjdict, dbid
                        )
                    else:
                        transientid = db.post_object_to_DB("transient", newobjdict)

                        # WriteOutput(tns_objs)
        print("Process done.")

    def getIDfromName(self, tablename, fieldname):
        cmd = "http --ignore-stdin -a %s:%s GET %s%s" % (
            self.dblogin,
            self.dbpassword,
            self.dburl,
            tablename,
        )
        output = os.popen(cmd).read()
        data = json.loads(output)

        idlist, namelist = [], []
        for i in range(len(data)):
            namelist += [data[i]["name"]]
            idlist += [data[i]["url"]]

        if fieldname not in namelist:
            return None

        return np.array(idlist)[np.where(np.array(namelist) == fieldname)][0]


def date_to_mjd(obs_date):
    time = Time(obs_date, scale="utc")
    return time.mjd


def runDBcommand(cmd):
    try:
        tstart = time.time()
        while time.time() - tstart < 20:
            return json.loads(os.popen(cmd).read())
    except:
        print(os.popen(cmd).read())
        raise RuntimeError("Error : cmd %s failed!!" % cmd)


if __name__ == "__main__":
    # execute only if run as a script

    import optparse
    import configparser

    usagestring = "TNS_Synopsis.py <options>"

    tstart = time.time()
    tnsproc = processTNS()

    # read in the options from the param file and the command line
    # some convoluted syntax here, making it so param file is not required
    parser = tnsproc.add_options(usage=usagestring)
    options, args = parser.parse_args()
    if options.settingsfile:
        config = configparser.ConfigParser()
        config.read(options.settingsfile)
    else:
        config = None
    parser = tnsproc.add_options(usage=usagestring, config=config)
    options, args = parser.parse_args()
    tnsproc.hostmatchrad = options.hostmatchrad

    db = DBOps()
    parser = db.add_options(usage=usagestring, config=config)
    options, args = parser.parse_args()
    db.options = options
    db.init_params()

    tnsproc.login = options.login
    tnsproc.password = options.password
    tnsproc.dblogin = options.dblogin
    tnsproc.dbpassword = options.dbpassword
    tnsproc.dburl = options.dburl
    tnsproc.status = options.status
    tnsproc.settingsfile = options.settingsfile

    tnsproc.ProcessTNSEmails(post=True, db=db)
    print("TNS -> YSE_PZ took %.1f seconds" % (time.time() - tstart))
