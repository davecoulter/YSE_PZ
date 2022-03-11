from astropy.io.votable import parse
from astropy.table import unique
import numpy as np
import warnings, os, requests, sys
import io
from datetime import datetime

warnings.filterwarnings("ignore")


class chandraImages:
    def __init__(self, ra, dec, obj):
        # Transient information/search criteria
        self.ra = ra
        self.dec = dec
        self.object = obj
        self.radius = 0.2

        # Information pulled from Chandra archive
        self.obstable = None
        self.obsids = []
        self.targnames = []
        self.targ_ras = []
        self.targ_decs = []
        self.exp_times = []
        self.obs_dates = []
        self.jpegs = []
        self.images = []
        self.n_obsid = 0
        self.total_exp = 0

    def search_chandra_database(self):
        u = "https://cxcfps.cfa.harvard.edu/cgi-bin/cda/footprint/get_vo_table.pl?pos={0},{1}&size={2}"
        url = u.format(self.ra, self.dec, self.radius)

        url += "&inst=ACIS-I,ACIS-S"
        url += "&grating=NONE"

        r = requests.get(url)
        if r.status_code != 200:
            return
        f = io.BytesIO(r.text.encode())
        votable = parse(f)
        tbdata = votable.get_first_table().to_table()
        if len(tbdata) > 0:
            table = unique(tbdata, keys="ObsId")

            self.total_exp = np.sum(table["Exposure"])
            self.obsids = table["ObsId"]
            self.targnames = table["target_name"]
            self.n_obsid = len(table)
            self.targ_ras = table["RA"]
            self.targ_decs = table["Dec"]
            self.exp_times = table["Exposure"]
            self.obs_dates = table["obs_date"]
            self.jpegs = table["preview_uri"]
            self.images = table["full_uri"]


## TEST TEST TEST
if __name__ == "__main__":
    chandra = chandraImages(161.3379417, -4.3380028, "Object")
    chandra.search_chandra_database()
    print(
        "I found",
        chandra.n_obsid,
        "Chandra images of",
        chandra.object,
        "located at coordinates",
        chandra.ra,
        chandra.dec,
    )
    print("Total exposure time is:", chandra.total_exp, "ks")
    print(chandra.images)
    print(chandra.jpegs)
