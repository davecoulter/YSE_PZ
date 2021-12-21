#!/usr/bin/env python
from YSE_App.models import *
from django.db.models import Q, Count
from django.contrib.auth.models import User
import coreapi
import requests
import astropy.table as at
from collections import OrderedDict
import json
import dateutil.parser
import numpy as np
import pytz

tnsapi = 'https://www.wis-tns.org/api/get'
tnsapikey = 'ecd2dec8cee4ed72a39fe8467ddd405fec4eef14'

def get(url,json_list,api_key):
    try:
        # url for get obj
        get_url=url+'/object'
        # change json_list to json format
        json_file=OrderedDict(json_list)
        # construct the list of (key,value) pairs
        get_data=[('api_key',(None, api_key)),
                  ('data',(None,json.dumps(json_file)))]
        # get obj using request module
        response=requests.post(get_url, files=get_data)
        return response
    except Exception as e:
        return [None,'Error message : \n'+str(e)]

def format_to_json(source):
    # change data to json format and return
    parsed=json.loads(source,object_pairs_hook=OrderedDict)
    #result=json.dumps(parsed,indent=4)
    return parsed #result


def main(doSpec=False):

    if doSpec:
        # public spectra that shouldn't be public
        tq = Transient.objects.annotate(num_spec=Count('transientspectrum__obs_group')).filter(num_spec__gt=1) #.\
        #                                          filter(Q(transientspectrum__instrument__name='LRIS') |
        #                                                 Q(transientspectrum__instrument__name='KAST') |
        #                                                 Q(transientspectrum__instrument__name='FLOYDS-N') |
        #                                                 Q(transientspectrum__instrument__name='KAST'))
        # now query TNS to see what's public
        for t in tq:
            TNSGetSingle = [("objname",t.name),
                            ("photometry","0"),
                            ("spectra","1")]

            response=get(tnsapi, TNSGetSingle, tnsapikey)
            json_data = format_to_json(response.text)
            if len(json_data['data']['reply']['spectra']) < t.num_spec:
                for spec in TransientSpectrum.objects.filter(transient__name=t.name):
                    spec_is_public = False
                    for tnsspec in json_data['data']['reply']['spectra']:
                        if np.abs((dateutil.parser.parse(tnsspec['obsdate']).replace(tzinfo=pytz.UTC) - spec.obs_date).days) < 1:
                            spec_is_public = True
                    if not spec_is_public:
                        spec.delete()

    # change statuses
    status_ignore = TransientStatus.objects.get(name='Ignore')
    status_watch = TransientStatus.objects.get(name='Watch')
    Transient.objects.filter(status__name='NeedsTemplate').update(status=status_ignore)
    Transient.objects.filter(status__name='FollowupFinished').update(status=status_ignore)
    Transient.objects.filter(status__name='Following').update(status=status_watch)
    Transient.objects.filter(status__name='FollowupRequested').update(status=status_watch)
    Transient.objects.filter(status__name='Interesting').update(status=status_watch)
    
    # ATLAS photometry that shouldn't be public
    tp = TransientPhotometry.objects.filter(instrument__name='ACAM1').annotate(num_phot=Count('transientphotdata__mag')).filter(num_phot__gt=2)
    tp.delete()


    # non-public photometry
    non_public_phot = TransientPhotometry.objects.filter(~Q(groups__name='Public') & ~Q(groups__name__isnull=True))
    non_public_phot.delete()
    phot_ids = non_public_phot.values('id')
    non_public_photdata = TransientPhotData.objects.filter(Q(photometry__id__in=phot_ids))
    non_public_photdata.delete()

    
    # non-public spectra
    non_public_spec = TransientSpectrum.objects.filter(~Q(groups__name='Public') & ~Q(groups__name__isnull=True))
    spec_ids = non_public_spec.values('id')
    non_public_specdata = TransientSpecData.objects.filter(Q(spectrum__id__in=spec_ids))
    non_public_spec.delete()
    non_public_specdata.delete()

    # followup resources
    ClassicalResource.objects.all().delete()
    ToOResource.objects.all().delete()
    QueuedResource.objects.all().delete()
    ClassicalObservingDate.objects.all().delete()
    PrincipalInvestigator.objects.all().delete()
    pi = PrincipalInvestigator.objects.create(
        name='Unknown',created_by=User.objects.get(username='admin'),
        modified_by=User.objects.get(username='admin'))
    
    # followup requests
    TransientFollowup.objects.all().delete()
    HostFollowup.objects.all().delete()
    TransientObservationTask.objects.all().delete()
    HostObservationTask.objects.all().delete()
        
    # on call lists
    OnCallDate.objects.all().delete()
    YSEOnCallDate.objects.all().delete()
        
    # survey observations
    SurveyField.objects.all().delete()
    SurveyFieldMSB.objects.all().delete()
    SurveyObservation.objects.all().delete()
    # and this one isn't actually used
    for c in CanvasFOV.objects.all():
        c.delete()

    # tags
    optional_tags = TransientTag.objects.filter(~Q(name='TESS') & ~Q(name='YSE') & ~Q(name='ZTF in YSE Fields') &
                                                ~Q(name='YSE Forced Phot'))
    optional_tags.delete()

    # GW stuff (barely being used)
    GWCandidate.objects.all().delete()
    GWCandidateImage.objects.all().delete()
        
    # User data
    UserQuery.objects.all().delete()
    UserTelescopeToFollow.objects.all().delete()
    Profile.objects.all().delete()

    # PS1 photometry that shouldn't be public
    tp = TransientPhotometry.objects.filter(instrument__name='GPC1').annotate(num_phot=Count('transientphotdata__mag')).filter(num_phot__gt=2)
    tp.delete()



    # to delete users, we need to modify records of user-modified DB objects: WebAppColor, Unit, DataQuality, Transient
    AlternateTransientNames.objects.all().delete()
    
    WebAppColor.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    WebAppColor.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    Unit.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Unit.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    DataQuality.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    DataQuality.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    Transient.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Transient.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientStatus.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientStatus.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientTag.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientTag.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientClass.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientClass.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    Telescope.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Telescope.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientPhotometry.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientPhotometry.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientSpectrum.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientSpectrum.objects.filter(~Q(created_by=1)).update(created_by=1)

    # do spec data in stages or computer freaks out
    TransientSpecData.objects.filter(modified_by=7).update(modified_by=1)
    TransientSpecData.objects.filter(created_by=7).update(created_by=1)
    TransientSpecData.objects.filter(modified_by=8).update(modified_by=1)
    TransientSpecData.objects.filter(created_by=8).update(created_by=1)
    TransientSpecData.objects.filter(modified_by=12).update(modified_by=1)
    TransientSpecData.objects.filter(created_by=12).update(created_by=1)
    TransientSpecData.objects.filter(modified_by=84).update(modified_by=1)
    TransientSpecData.objects.filter(created_by=84).update(created_by=1)
    TransientSpecData.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientSpecData.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TransientPhotData.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TransientPhotData.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    HostPhotometry.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    HostPhotometry.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    HostPhotData.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    HostPhotData.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    TaskStatus.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    TaskStatus.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    FollowupStatus.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    FollowupStatus.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    InternalSurvey.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    InternalSurvey.objects.filter(~Q(created_by=1)).update(created_by=1)

    Instrument.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Instrument.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    InstrumentConfig.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    InstrumentConfig.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    ConfigElement.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    ConfigElement.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    PhotometricBand.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    PhotometricBand.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    Host.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Host.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    ClassicalNightType.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    ClassicalNightType.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    ObservationGroup.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    ObservationGroup.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    Observatory.objects.filter(~Q(modified_by=1)).update(modified_by=1)
    Observatory.objects.filter(~Q(created_by=1)).update(created_by=1)
    
    # non-public transients
    # should work until 2030 and if I'm still using this code in 2030 something has gone very wrong
    for t in Transient.objects.filter(~Q(name__startswith='201') & ~Q(name__startswith='202')):
        try:
            h = t.host
            if h: h.delete()
        except: pass
        t.delete()

    # remove queries
    Query.objects.all().delete()

    # images
    TransientImage.objects.all().delete()
    TransientDiffImage.objects.all().delete()
    HostImage.objects.all().delete()

    # comments
    Log.objects.all().delete()

    User.objects.filter(~Q(username='admin')).delete()
        
    u = User.objects.get(username='admin')
    u.set_password('changeme')
    u.firstname = 'admin'
    u.email = ''
    u.save()

    for g in Group.objects.all():
        if g.name != 'Public':
            u.groups.remove(g)
            g.delete()
