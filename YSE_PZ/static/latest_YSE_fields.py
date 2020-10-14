import requests
from requests.auth import HTTPBasicAuth
import datetime
from astropy.time import Time
import json
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

def date_to_mjd(date):
    time = Time(date,scale='utc')
    return time.mjd

def mjd_to_date(mjd):
    time = Time(mjd,format='mjd',scale='utc')
    return time.isot

def GetSexigesimalString(ra_decimal, dec_decimal):
    c = SkyCoord(ra_decimal,dec_decimal,unit=(u.deg, u.deg))
    ra = c.ra.hms
    dec = c.dec.dms

    ra_string = "%02d:%02d:%06.3f" % (ra[0],ra[1],ra[2])
    if dec[0] >= 0:
        dec_string = " %02d:%02d:%06.3f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))
    else:
        dec_string = "%03d:%02d:%06.3f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))

    # Python has a -0.0 object. If the deg is this (because object lies < 60 min south), the string formatter will drop the negative sign
    if c.dec < 0.0 and dec[0] == 0.0:
        dec_string = "-00:%02d:%06.3f" % (np.abs(dec[1]),np.abs(dec[2]))

    return (ra_string, dec_string)

htmlheader = """
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      table {
      border-collapse: collapse;
      border-spacing: 0;
      width: 100%;
      border: 1px solid #ddd;
      }

      th, td {
      text-align: left;
      padding: 16px;
      }

      tr:nth-child(even) {
      background-color: #f2f2f2;
      }
    </style>
  </head>
  <body>
<table class="sortable">
  <thead>
    <tr>
      <th>Field</th>
      <th>RA</th>
      <th>Dec</th>
      <th>Filters</th>
      <th>Date/Time (UT)</th>
      <th>Limiting Mags</th>
    </tr>
  <tbody>
"""

htmlfooter = """
      </tbody>
    </table>
  </body>
</html>

<script src="sorttable.js"></script>
"""

def main():

    nowmjd = date_to_mjd((datetime.datetime.now()+datetime.timedelta(hours=10)).isoformat())
    
    r = requests.get('http://ziggy.ucolick.org/yse/api/surveyobservations/?obs_mjd_gte=%i&limit=1000'%(nowmjd-7),
                     auth=HTTPBasicAuth('djones','BossTent1'))
    data = json.loads(r.text)
    data_results = data['results']
    #import pdb; pdb.set_trace()

    results_dict = {}
    
    field,ra,dec,mjd,maglim,filters = np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([])
    for d in data_results:

        # save the foreign keys when possible
        if d['photometric_band'] not in results_dict.keys():
            photo_results = requests.get(d['photometric_band'],auth=HTTPBasicAuth('djones','BossTent1'))
            p = json.loads(photo_results.text)
            results_dict[d['photometric_band']] = p
        else:
            p = results_dict[d['photometric_band']]
        if d['survey_field'] not in results_dict.keys():
            field_results = requests.get(d['survey_field'],auth=HTTPBasicAuth('djones','BossTent1'))
            f = json.loads(field_results.text)
            results_dict[d['survey_field']] = f
        else:
            f = results_dict[d['survey_field']]
            
        if f['field_id'] in field and len(np.where(np.abs(d['obs_mjd'] - mjd[field == f['field_id']]) < 0.1)[0]):
            iMJDMatch = np.where((field == f['field_id']) & (np.abs(d['obs_mjd'] - mjd) < 0.1))[0][0]
            filt = filters[iMJDMatch]
            if filt == 'z' or p['name'] == 'g' or (p['name'] == 'r' and filt in ['i','z']):
                filters[iMJDMatch] = p['name']+','+filters[iMJDMatch]
            else:
                filters[iMJDMatch] = filters[iMJDMatch][0] + ',' + p['name']
        else:
            field = np.append(field,f['field_id'])
            ra = np.append(ra,f['ra_cen'])
            dec = np.append(dec,f['dec_cen'])
            maglim = np.append(maglim,d['mag_lim'])
            mjd = np.append(mjd,d['obs_mjd'])
            filters = np.append(filters,p['name'])
        #if f['field_id'] == '403.F':
        #    import pdb; pdb.set_trace()

    iSortMJD = np.argsort(mjd)[::-1]
    field,ra,dec,maglim,mjd,filters = \
        field[iSortMJD],ra[iSortMJD],dec[iSortMJD],maglim[iSortMJD],mjd[iSortMJD],filters[iSortMJD]
    
    with open('/data/yse_pz/YSE_PZ/YSE_PZ/static/yse_latest_fields.html','w') as fout:
    #with open('yse_latest_fields.html','w') as fout:
        print(htmlheader,file=fout)

        for f,r,d,mj,m,flt in zip(field,ra,dec,mjd,maglim,filters):

            ra_string,dec_string = GetSexigesimalString(r,d)
            
            dataline = """
<tr>
<td>%s</td>
<td>%s</td>
<td>%s</td>
<td><i>%s</i></td>
<td>%s</td>
<td>%.2f</td>
</tr>
"""%(f,ra_string,dec_string,flt,mjd_to_date(mj).replace('T',' '),m)

            
            print(dataline,file=fout)
        print(htmlfooter,file=fout)


if __name__ == "__main__":
    main()
