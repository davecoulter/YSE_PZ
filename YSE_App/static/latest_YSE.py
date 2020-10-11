#!/usr/bin/env python

import requests
import astropy.table as at

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
      <th>Name</th>
      <th>RA</th>
      <th>Dec</th>
      <th>Type</th>
      <th>Redshift</th>
      <th>Host Redshift</th>
      <th>Reporting Group/s</th>
      <th>Discovery Mag</th>
      <th>Discovery Filter</th>
      <th>Discovery Date</th>
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

    csvlink = "https://wis-tns.weizmann.ac.il/search?&discovered_period_value=7&discovered_period_units=days&unclassified_at=0&classified_sne=0&include_frb=0&name=&name_like=0&isTNS_AT=all&public=all&ra=&decl=&radius=&coords_unit=arcsec&reporting_groupid%5B%5D=83&groupid%5B%5D=null&classifier_groupid%5B%5D=null&objtype%5B%5D=null&at_type%5B%5D=null&date_start%5Bdate%5D=&date_end%5Bdate%5D=&discovery_mag_min=&discovery_mag_max=&internal_name=&discoverer=&classifier=&spectra_count=&redshift_min=&redshift_max=&hostname=&ext_catid=&ra_range_min=&ra_range_max=&decl_range_min=&decl_range_max=&discovery_instrument%5B%5D=null&classification_instrument%5B%5D=null&associated_groups%5B%5D=null&at_rep_remarks=&class_rep_remarks=&frb_repeat=all&frb_repeater_of_objid=&frb_measured_redshift=0&frb_dm_range_min=&frb_dm_range_max=&frb_rm_range_min=&frb_rm_range_max=&frb_snr_range_min=&frb_snr_range_max=&frb_flux_range_min=&frb_flux_range_max=&num_page=50&display%5Bredshift%5D=1&display%5Bhostname%5D=1&display%5Bhost_redshift%5D=1&display%5Bsource_group_name%5D=1&display%5Bclassifying_source_group_name%5D=1&display%5Bdiscovering_instrument_name%5D=0&display%5Bclassifing_instrument_name%5D=0&display%5Bprograms_name%5D=0&display%5Binternal_name%5D=1&display%5BisTNS_AT%5D=0&display%5Bpublic%5D=1&display%5Bend_pop_period%5D=0&display%5Bspectra_count%5D=1&display%5Bdiscoverymag%5D=1&display%5Bdiscmagfilter%5D=1&display%5Bdiscoverydate%5D=1&display%5Bdiscoverer%5D=1&display%5Bremarks%5D=0&display%5Bsources%5D=0&display%5Bbibcode%5D=0&display%5Bext_catalogs%5D=0&format=csv"

    response = requests.get(csvlink)
    data = at.Table.read(response.text,format='ascii.csv')

    with open('yse_latest.html','w') as fout:
        print(htmlheader,file=fout)
        for d in data:
            dataline = f"""
<tr>
<td>{d['Name']}</td>
<td>{d['RA']}</td>
<td>{d['DEC']}</td>
<td>{d['Obj. Type']}</td>
<td>{d['Redshift']}</td>
<td>{d['Host Redshift']}</td>
<td>{d['Reporting Group/s']}</td>
<td>{d['Discovery Mag/Flux']}</td>
<td>{d['Discovery Filter']}</td>
<td>{d['Discovery Date (UT)']}</td>
</tr>
"""
            print(dataline,file=fout) 
        print(htmlfooter,file=fout)
    
if __name__ == "__main__":
    main()
