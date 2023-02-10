#!/usr/bin/env python
# D. Jones - 8/9/22
"""script for adding new YSE fields via the YSE-PZ API.
Unlike existing utilities, this takes exact pointings
for each field (one at a time) and assigns those to an
MSB"""

# python YSE_App/yse_utils/add_yse_fields.py -s YSE_PZ/settings.ini --name=298.A --ra=01:59:49.157 --dec=-17:03:00 --instrument=GPC2

import argparse
import configparser
import requests
from requests.auth import HTTPBasicAuth
from astropy.coordinates import SkyCoord
import astropy.units as u

class add_yse_fields:
    def __init__(self):
        pass

    def add_args(self, parser=None, usage=None, config=None):

        if parser == None:
            parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")

        parser.add_argument('-s','--settingsfile', default=None, type=str,
                            help='settings file (login/password info)')
        parser.add_argument('-n','--name', default=None, type=str,
                            help='field name, format should be <number>.<letter>')
        parser.add_argument('-r','--ra', default=None, type=str,
                            help='field RA (decimal or sexigesimal)')
        parser.add_argument('-d','--dec', default=None, type=str,
                            help='field Dec (decimal or sexigesimal)')
        parser.add_argument('-i','--instrument', default=None, type=str,
                            help='instrument (GPC1 or GPC2)')

        if config:
            parser.add_argument('--dblogin', default=config.get('main','dblogin'), type=str,
                                help='gmail login (default=%default)')
            parser.add_argument('--dbpassword', default=config.get('main','dbpassword'), type=str,
                                help='gmail password (default=%default)')
            parser.add_argument('--dbemailpassword', default=config.get('main','dbemailpassword'), type=str,
                                help='gmail password (default=%default)')
            parser.add_argument('--dburl', default=config.get('main','dburl'), type=str,
                                help='base URL to POST/GET,PUT to/from a database (default=%default)')
        
        return parser

    def main(self):
        
        # check name format
        if '.' not in self.options.name and len(self.options.name.split('.')[-1]) > 1:
            raise RuntimeError('invalid field name format')
        if 'P2.' not in self.options.name and self.options.instrument == 'GPC2':
            raise RuntimeError(f"if instrument is GPC2, field must have 'P2.' at the end of numeric field ID")

        # see if MSB exists; if it doesn't, create a new MSB
        msb_name = self.options.name.split('.')[0]
        rmsb = requests.get(
            url=f'{self.options.dburl}surveyfieldmsbs/?name={msb_name}',
            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        if not rmsb.status_code == 200:
                raise RuntimeError('MSB query failed')
        rmsb = rmsb.json()['results']
            
        # which group is the YSE group?  There must be a better way to do this....
        ryse = requests.get(
            url=f'{self.options.dburl}observationgroups/?name=YSE',
            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        yse_group = ryse['results'][0]['url']

        rinst = requests.get(
            url=f'{self.options.dburl}instruments/?name={self.options.instrument}',
            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()
        instrument = rinst['results'][0]['url']

        
        if not len(rmsb):
        
            msb_dict = {'obs_group':yse_group,
                        'name':self.options.name.split('.')[0],
                        'active':0}
            rmsb = requests.post(
                url='%ssurveyfieldmsbs/'%self.options.dburl,json=msb_dict,
                auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
            if not rmsb.status_code == 200 and not rmsb.status_code == 201:
                raise RuntimeError('MSB was not added successfully')
            rmsb = rmsb.json()
        else:
            rmsb = rmsb[0]    
            
        # we'll use this URL to patch the MSB with new filters
        msb_id = rmsb['id']
            
        # see if the survey field exists in the database already
        rfield = requests.get(
            url=f'%ssurveyfields/?field_id={self.options.name}'%self.options.dburl,
            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword)).json()

        if len(rfield['results']):
            # if it exists, make sure it's associated with the MSB
            field_in_msb = False
            for field in rmsb['survey_fields']:
                if field['field_id'] == self.options.name:
                    field_in_msb = True
            if field_in_msb:
                print(f'field {self.options.name} exists and is already associated with MSB {msb_name}')
                return
            
            # if field is not in the MSB, we need to add it
            print(f'field {self.options.name} exists but is not associated with MSB {msb_name}')
            print('adding it now...')
            survey_field_list = [{'id':rfield['results'][0]['url'].split('/')[-2]}]

            if len(rmsb['survey_fields']):
                survey_field_list += [{'id':sf['id']} for sf in rmsb['survey_fields'] \
                                      if sf['id'] != rfield['results'][0]['url'].split('/')[-2]]

            rmsb_add = requests.put(url=f'{self.options.dburl}surveyfieldmsbs/{msb_id}/',
                                    json={'obs_group':yse_group,'name':msb_name,
                                          'survey_fields':survey_field_list},
                                    auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
            if not rmsb_add.status_code == 200:
                raise RuntimeError('field was not associated with MSB successfully')

            return

        # now parse the coordinates of the new field
        try:
            ra,dec = float(self.options.ra),float(self.options.dec)
            sc = SkyCoord(ra,dec,unit=u.deg)
        except:
            sc = SkyCoord(self.options.ra,self.options.dec,unit=(u.hour,u.deg))
        
        # if field does not exist, we need to create it and add it to the MSB
        field_dict = {'obs_group':yse_group,
                      'instrument':instrument,
                      'field_id':self.options.name,
                      'cadence':3.0,
                      'ztf_field_id':msb_name.replace('P2',''),
                      'ra_cen':sc.ra.deg,
                      'dec_cen':sc.dec.deg,
                      'width_deg':3.1,
                      'height_deg':3.1}

        rfield = requests.post(
            url=f'{self.options.dburl}surveyfields/',json=field_dict,
            auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        if not rfield.status_code == 201:
            raise RuntimeError('field was not added successfully')
        rfield = rfield.json()

        # add to the MSB
        survey_field_list = [{'id':rfield['url'].split('/')[-2]}]
        if len(rmsb['survey_fields']):
            survey_field_list += [{'id':sf['id']} for sf in rmsb['survey_fields'] \
                if sf['id'] != rfield['url'].split('/')[-2]]
            #survey_field_list = [{'id':sf['url'].split('/')[-2]} for sf in rmsb.json()['results'][0]['survey_fields']]
            
        rmsb_add = requests.put(url=f'{self.options.dburl}surveyfieldmsbs/{msb_id}/',
                                json={'obs_group':yse_group,'name':msb_name,
                                      'survey_fields':survey_field_list},
                                auth=HTTPBasicAuth(self.options.dblogin,self.options.dbpassword))
        if not rmsb_add.status_code == 200:
            raise RuntimeError('field was not associated with MSB successfully')


        print(f'successfully added field {self.options.name} at coords {sc.ra.deg,sc.dec.deg}')
        
        
if __name__ == "__main__":
    ayf = add_yse_fields()

    # read args
    parser = ayf.add_args(usage='')
    args = parser.parse_args()
    if args.settingsfile:
        config = configparser.ConfigParser()
        config.read(args.settingsfile)
    else: config=None
    parser = ayf.add_args(usage='',config=config)
    args = parser.parse_args()
    ayf.options = args

    ayf.main()
    print('success!')
