.. _adding_data:

*********************
Adding Data to YSE-PZ
*********************

Adding data to YSE-PZ can be done in a variety of ways.
For the most part, it is done by setting up a variety of
cron jobs through django-crons that regularly search for
and ingest data from a variety of sources.

This section gives a basic overview of how to write a
YSE-PZ cron job and the data format(s) that YSE-PZ
expects for uploads.  I will create an example of a basic photometric
upload script for this tutorial.


Writing a Django Cron
=====================

The details of using the `django-cron <https://django-cron.readthedocs.io/en/latest/index.html>`_ package are given in their documentation.  A short summary is given below.

Each YSE-PZ cron will be written inside a CronJobBase class structure, for example ::

  from django_cron import CronJobBase, Schedule

  class PhotometryUploads(CronJobBase):

      RUN_EVERY_MINS = 120

      schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
      code = 'YSE_App.data_ingest.Photometry.PhotometryUpload'

      def do(self):
      	  try:
	      self.do_phot_upload()
	      print('successful upload!')
	  except Exception as e:
	      print("Error: %s"%e)


The code URL links to our test script (`PhotometryUploadExample.py`), located in the
directory :code:`YSE_App/data_ingest` (not in the Git repository, but the full code is at
the bottom of this page).  This is currently set to run every two hours
but typically I don't pay attention to this scheduling criterion and instead
set this in the definition of the cron itself (see below).  The :code:`code` line
above, which basically gives import instructions, should be added to
YSE_PZ/settings.py::

  CRON_CLASSES = ['YSE_App.data_ingest.PhotometryUploadExample.PhotometryUploads']

The actual code that gets run is in the :code:`do()` function.  Note that the code
will crash without raising an error, so it's important to spit out a "success"
message at the end so that you know whether the code completed.  I also write a
try/except loop that emails me if the code crashes, but I will neglect that
for simplicity here::

      def do(self):

          self.do_phot_upload()

	  print('successful upload!')

Once the cron script has been written, write a bash script that can be executed
in a cronjob and that uses the basic django-cron syntax::

  #!/bin/bash
  source /data/yse_pz/yse_virtual/bin/activate # activates conda environment on ziggy
  python /data/yse_pz/YSE_PZ/manage.py runcrons YSE_App.data_ingest.PhotometryUploadExample.PhotometryUploads --force
  echo "============"

use :code:`crontab -e` at the terminal (on any computer that
stays on all the time) to create the cron and pipe the output to a log file::

  */30 * * * * /home/djones/photometry.bash >> /home/djones/cron_run_photometry.log 2>&1



Adding Photometry to YSE-PZ
===========================

All transients or other data are uploaded to YSE-PZ via a JSON dictionary that mimics
the data model of YSE-PZ itself.  To explore the data model itself, use the
`SQL Explorer <https://ziggy.ucolick.org/yse/explorer/play/>_` with the :code:`Show Schema`
button to see the various model tables.  For the photometry test case, I will go through
the (linked) Transient, TransientStatus, TransientTags, TransientPhotometry, TransientPhotData
tables and how to construct a dictionary that creates or updates a transient with a reasonable
set of photometric information.  The basic overview of these tables in the data model are given in the
:ref:`queries`.

First, we have to ingest some photometric data - in this case I'll query `MARS <https://mars.lco.global/>_` for
ZTF photometry of SN 2019np at RA,Dec = (157.3415000,29.5106667) (a nice nearby SN Ia)::

  # all the imports we need for the full code
  from django_cron import CronJobBase, Schedule
  import coreapi
  from astropy.time import Time
  import json
  import numpy as np
  import requests
  from requests.auth import HTTPBasicAuth

  def jd_to_date(jd):
      time = Time(jd,scale='utc',format='jd')
      return time.isot

  def query_mars(ra,dec):
      marsurl = 'https://mars.lco.global/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(ra,dec)
      client = coreapi.Client()
      schema = client.get(marsurl)
      if 'results' in schema.keys():
	  obs_date,mag,mag_err,band = [],[],[],[]
	  for i in range(len(schema['results'])):
	      phot = schema['results'][i]['candidate']
	      if phot['isdiffpos'] == 'f': # this is bad photometry
		  continue
	      mag += [phot['magpsf']]
	      mag_err += [phot['sigmapsf']]
	      obs_date += [jd_to_date(phot['jd'])]
	      band += ['%s-ZTF'%phot['filter']]
	  return np.array(obs_date),np.array(mag),np.array(mag_err),np.array(band)
      else: return [],[],[],[]

The next step is to translate magnitudes and magnitude uncertainties into YSE-PZ format
while giving YSE-PZ the necessary metadata to track instruments, filters, etc etc.  To
make this conversion, YSE-PZ needs to know the names of instruments and filters that are
already defined in the database.  To learn this information, go back to the SQL explorer
playground and run a quick query on the PhotometricBand model.::

  SELECT p.name, i.name
  FROM YSE_App_photometricband p
  INNER JOIN YSE_App_instrument i on p.instrument_id = i.id
  WHERE i.name != 'Unknown'

Scrolling through this list (neglecting the "Unknown" instruments, which should be avoided when possible),
you can see that the filters g-ZTF and r-ZTF associated with instrument ZTF-Cam are the ones that should
be used.  Once we know this information, we're ready to build the dictionary from the top down.


Building the Transient Upload Dictionary
----------------------------------------

We will build a dictionary starting with the Transient object, then linking to a Photometry dictionary,
and then a TransientPhotData dictionary.  First, the dictionary of all transients::

  # initial key telling it not to override the existing status of this transient
  # assuming it exists
  TransientUploadDict = {'noupdatestatus':True}
  TransientUploadDict['2019np'] = {
    'name':'2019np',
    'ra':157.3415000,
    'dec':29.5106667,
    'obs_group':'Unknown', # obs_group and status are required keys for any *new* transients, but not for existing transients
    'status':'Ignore'
    }

For each transient you want to upload, add a dictionary key and a dictionary for each transient.
To see all possible keys that can be specified, run a query in SQL explorer::

  SELECT * FROM YSE_App_transient LIMIT 10

To link foreign keys, YSE-PZ will link using the "name" field of the linked model.  "status" or "obs_group",
for example, need to be set to the name of an existing TransientStatus or ObservationGroup model, respectively.
Again, SQL explorer queries can tell you what the options are for these foreign keys.

Next, link to a TransientPhotometry model.  The TransientPhotometry model is basically a "header"-type
object that contains a couple instructional keys::

  PhotUploadAll = {"mjdmatchmin":0.01,
		   "clobber":False}
  PhotUploadAll["ZTF"] = {'instrument':'ZTF-Cam', # the name of the key "ZTF" doesn't matter, it's just for bookkeeping
                          'obs_group':'ZTF'}

First, the "mjdmatchmin" key tells the YSE-PZ API the MJD separation at which two photometry points should be considered the same.
Though this might not always be the right setting for very fast-cadence observations, my default is usually 0.01 days.
Second, the "clobber" key uses the "mjdmatchmin" criteria to decide whether or not to overwrite observations in the same
filter, on the same instrument, taken at the same time, with a tolerance of deltaMJD < mjdmatchmin.

Finally, the TransientPhotData dictionary is built from the ZTF observations, with a separate dictionary for each
photometric observation (as each is a separate SQL database entry)::

  obs_date,mag,mag_err,band = query_mars(157.3415000,29.5106667)
  PhotDataDict = {}
  PhotUploadAll["ZTF"]["photdata"] = {}
  i = 0
  for o,m,me,b in zip(obs_date,mag,mag_err,band):
      PhotDataDict = {'obs_date':o,
		      'mag':m,
		      'mag_err':me,
		      'band':b,
		      'data_quality':0, # good data
		      'diffim':1, # difference imaging measurement
		       # these next fields have to be included because of the way code is written but can be mostly ignored
		      'flux':None,
		      'flux_err':None,
		      'flux_zero_point':None,
		      'forced':0,
		      'discovery_point':0
      }

      PhotUploadAll["ZTF"]["photdata"][i] = PhotDataDict
      i += 1


Finally, combine the dictionaries and send everything to the API::

  def UploadTransients(self,TransientUploadDict):

      url = '%s'%self.options.dburl.replace('/api','/add_transient')
      try:
          r = requests.post(
	    url = url, data = json.dumps(TransientUploadDict),
	    auth=HTTPBasicAuth(mylogin,mypassword),
	    timeout=60)
	  try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
	  except: print(r.text)
	  print("Process done.")

      except Exception as e:
          print("Error: %s"%e)


  TransientUploadDict['2019np']['transientphotometry'] = PhotUploadAll

  UploadTransients(TransientUploadDict)

Your YSE-PZ login and password can be used for the :code:`mylogin` and
:code:`mypassword` fields.


The Final Code
--------------

Putting all these pieces together, we've now built a cron job that will regularly upload
ZTF photometry for SN 2019np!  The full code is below::

  from django_cron import CronJobBase, Schedule
  import coreapi
  from astropy.time import Time
  import json
  import numpy as np
  import requests
  from requests.auth import HTTPBasicAuth

  def jd_to_date(jd):
	  time = Time(jd,scale='utc',format='jd')
	  return time.isot

  def query_mars(ra,dec):
      marsurl = 'https://mars.lco.global/?format=json&sort_value=jd&sort_order=desc&cone=%.7f%%2C%.7f%%2C0.0014'%(ra,dec)
      client = coreapi.Client()
      schema = client.get(marsurl)
      if 'results' in schema.keys():
	  obs_date,mag,mag_err,band = [],[],[],[]
	  for i in range(len(schema['results'])):
	      phot = schema['results'][i]['candidate']
	      if phot['isdiffpos'] == 'f': # this is bad photometry
		  continue
	      mag += [phot['magpsf']]
	      mag_err += [phot['sigmapsf']]
	      obs_date += [jd_to_date(phot['jd'])]
	      band += ['%s-ZTF'%phot['filter']]
	  return np.array(obs_date),np.array(mag),np.array(mag_err),np.array(band)
      else: return [],[],[],[]

  class PhotometryUploads(CronJobBase):

      RUN_EVERY_MINS = 120

      schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
      code = 'YSE_App.data_ingest.Photometry.PhotometryUpload'

      def do(self):

	  try:
	      self.do_phot_upload()
	      print('successful upload!')
	  except Exception as e:
	      print("Error: %s"%e)


      def do_phot_upload(self):

	  # write out the transient dictionary
	  # initial key telling it not to override the existing status of this transient
	  # assuming it exists
	  TransientUploadDict = {'noupdatestatus':True}
	  TransientUploadDict['2019np'] = {
	      'name':'2019np',
	      'ra':157.3415000,
	      'dec':29.5106667,
	      'obs_group':'Unknown', # obs_group and status are required keys for any *new* transients, but not for existing transients
	      'status':'Ignore'
	  }

	  # set up the photometry upload dictionary
	  PhotUploadAll = {"mjdmatchmin":0.01,
			   "clobber":True}
	  PhotUploadAll["ZTF"] = {'instrument':'ZTF-Cam', # the name of the key "ZTF" doesn't matter, it's just for bookkeeping
				  'obs_group':'ZTF'}

	  # convert the photometric data
	  obs_date,mag,mag_err,band = query_mars(157.3415000,29.5106667)
	  PhotDataDict = {}
	  PhotUploadAll["ZTF"]["photdata"] = {}
	  i = 0
	  for o,m,me,b in zip(obs_date,mag,mag_err,band):
	      PhotDataDict = {'obs_date':o,
			      'mag':m,
			      'mag_err':me,
			      'band':b,
			      'data_quality':0, # good data
			      'diffim':1, # difference imaging measurement
			       # these next fields have to be included because of the way code is written but can be mostly ignored
			      'flux':None,
			      'flux_err':None,
			      'flux_zero_point':None,
			      'forced':0,
			      'discovery_point':0
	      }

	      PhotUploadAll["ZTF"]["photdata"][i] = PhotDataDict
	      i += 1

	  TransientUploadDict['2019np']['transientphotometry'] = PhotUploadAll

	  self.UploadTransients(TransientUploadDict)

      def UploadTransients(self,TransientUploadDict):

	  url = 'https://ziggy.ucolick.org/yse/add_transient/'
	  try:
	      r = requests.post(
	      url = url, data = json.dumps(TransientUploadDict),
		  auth=HTTPBasicAuth(mylogin,mypassword),
		  timeout=60)
	      try: print('YSE_PZ says: %s'%json.loads(r.text)['message'])
	      except: print(r.text)
	      print("Process done.")

	  except Exception as e:
	      print("Error: %s"%e)
