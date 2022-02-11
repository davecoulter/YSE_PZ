.. _queries:

***************************
Working with the YSE-PZ API
***************************

This is a quick overview of adding or getting data using the YSE-PZ django rest framework API.

Finding the correct API link
============================

All of the YSE-PZ models accessible through the API can be seen at `<http://127.0.0.1:8000/api>`_.  Clicking on
each link will list the available model fields that can be queried.  Different models have filter syntax
that allows you to query on various fields, but this is pretty sporadic.  Below is a list of model fields
that can be queried on.  These are defined using :code:`django_filters.FilterSet` models
in :code:`YSE_App/api_views.py`::

  SurveyField
  - field_id
  - obs_group
  SurveyFieldMSB
  - name
  - active
  SurveyObservation
  - status_in
  - obs_mjd_gte
  - obs_mjd_lte
  - mjd_requested_gte
  - mjd_requested_lte
  - survey_field
  - obs_group
  - ra_gt
  - ra_lt
  - dec_gt
  - dec_lt
  Transient
  - created_date_gte
  - modified_date_gte
  - status_in
  - ra_gte
  - ra_lte
  - dec_gte
  - dec_lte
  - tag_in
  - name
  ClassicalResource
  - instrument_name
  
Queries through a Web Browser
=============================

The above filters can be used to get information through the API.  For example,
say that you'd like to see the available information for SN 2018gv::

  http://127.0.0.1:8000/api/transients/?name=2018gv

This works because the API has a :code:`name` filter defined above.  From there,
you can alter the data for this transient through the POST web form on the page.

Say you'd like to find every transient with a right ascension between 0 and 1
degrees, and with a status of :code:`Following`.  The link would be::

  http://127.0.0.1:8000/api/transients/?ra_gte=0&ra_lte=1&status_in=Following
  
Queries using the Python Requests Module
----------------------------------------

The python requests module is the easiest way to interact with the database through python.

A Simple GET Script
-------------------

Let's get the list of fields from the Young Supernova Experiment that are currently being observed (marked as "active")::

  import requests
  from requests.auth import HTTPBasicAuth
  data = requests.get('http://127.0.0.1:8000/api/surveyfieldmsbs/?active=1',
                      auth=HTTPBasicAuth(login,password)).json()
  field_list = [data['results'][i]['name'] for i in range(len(data['results']))]
  
A Simple POST Script
--------------------

Let's add a classical observing date::

  import requests
  from requests.auth import HTTPBasicAuth
  import json
  
  # first, we need to locate a classical resource
  # let's just grab a recent Shane night
  data = requests.get('http://127.0.0.1:8000/api/classicalresources/?telescope_name=Shane',
                      auth=HTTPBasicAuth(login,password)).json()
  resource_url = data['results'][0]['url']

  # now we can add a resource
  # classicalnighttypes/3 in this case is a "full" night, you can grab this info with a similar GET as above
  # and just choosing a random obs date
  ObsDateInfo = {"resource": resource_url,
                 "night_type": "http://127.0.0.1:8000/api/classicalnighttypes/3/",
                 "obs_date": "2022-02-15T00:00:00"}
  r = requests.post('http://127.0.0.1:8000/api/classicalobservingdates/',
                    json=ObsDateInfo,auth=HTTPBasicAuth(login,password))
  
  
