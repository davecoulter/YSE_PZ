import django
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import models
from astropy.coordinates import get_moon, SkyCoord
from django.core.exceptions import ObjectDoesNotExist

from astropy.time import Time
import astropy.units as u
import datetime
import dateutil
import json
import pandas
import time
import numpy as np
from django.conf import settings as djangoSettings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from .data import PhotometryService, SpectraService, ObservingResourceService
from .serializers import *
from rest_framework.request import Request
from django.contrib.auth.decorators import login_required, permission_required
import json
from .basicauth import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.db.models import ForeignKey
from .common.alert import sendemail
from .common.utilities import getRADecBox
from django.db.models import Q
from .queries.yse_python_queries import *
from .queries import yse_python_queries
import sys
from urllib.parse import unquote

from YSE_App.galaxies import path
from YSE_App import frb_observing
from YSE_App import frb_init
from YSE_App import frb_utils
from YSE_App import frb_status
from YSE_App import frb_tables

from .models import *

@csrf_exempt
@login_or_basic_auth_required
def add_yse_survey_fields(request):
    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)

    survey_data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # ready to send error emails
    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
    subject = "Survey Upload Failure"
    txt_msg = "Alert : YSE_PZ Failed to upload today's survey fields "

    survey_entries = []
    yse_group = ObservationGroup.objects.filter(name='YSE')[0]
    for surveylistkey in survey_data.keys():
        surveydict = {'created_by_id':user.id,'modified_by_id':user.id,'obs_group':yse_group}
        survey = survey_data[surveylistkey]

        surveykeys = survey.keys()
        for surveykey in surveykeys:
            if not isinstance(SurveyField._meta.get_field(surveykey), ForeignKey):
                surveydict[surveykey] = survey[surveykey]
            else:
                fkmodel = SurveyField._meta.get_field(surveykey).remote_field.model
                if surveykey == 'photometric_band':
                    fk = fkmodel.objects.filter(name=survey[surveykey].split('-')[1]).filter(instrument__name=survey[surveykey].split('-')[0])
                elif surveykey == 'survey_field':
                    fk = fkmodel.objects.filter(field_id=survey[surveykey])
                else: fk = fkmodel.objects.filter(name=survey[surveykey])
                if not len(fk):
                    print("Sending email to: %s" % user.username)
                    html_msg = "Alert : YSE_PZ Failed to upload survey obs "
                    html_msg += "\nError : %s value doesn\'t exist in SurveyField.%s FK relationship"
                    sendemail(from_addr, user.email, subject,
                              html_msg%(survey[surveykey],surveykey),
                              djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
                    continue

                surveydict[surveykey] = fk[0]

        dbsurveyfield = SurveyField.objects.filter(
            field_id=surveydict['field_id'])

        # no clobbering for now
        if len(dbsurveyfield):
            dbsurveyfield = dbsurveyfield[0]
        else:
            dbsurveyfield = SurveyField.objects.create(**surveydict)

        surveymsb = SurveyFieldMSB.objects.filter(name=surveydict['field_id'].split('.')[0])
        if not len(surveymsb):
            surveymsbdict = {'created_by_id':user.id,'modified_by_id':user.id,
                             'obs_group':yse_group,'name':surveydict['field_id'].split('.')[0]}
            surveymsb = SurveyFieldMSB.objects.create(**surveymsbdict)
            surveymsb.survey_fields.add(dbsurveyfield)
            surveymsb.save()
        elif len(surveymsb):
            surveymsb = surveymsb[0]
            if surveymsb.survey_fields.count() < 6 and \
               not len(surveymsb.survey_fields.filter(field_id=dbsurveyfield.field_id)):
                surveymsb.survey_fields.add(dbsurveyfield)
                surveymsb.save()

    return_dict = {"message":"success"}
    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_yse_survey_obs(request):
    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)

    survey_data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # ready to send error emails
    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
    subject = "Survey Upload Failure"
    txt_msg = "Alert : YSE_PZ Failed to upload today's survey fields "

    survey_entries = []
    for surveylistkey in survey_data.keys():
        surveydict = {'created_by_id':user.id,'modified_by_id':user.id}
        survey = survey_data[surveylistkey]

        surveykeys = survey.keys()
        for surveykey in surveykeys:
            if surveykey in ['ra_cen','dec_cen']: continue
            if not isinstance(SurveyObservation._meta.get_field(surveykey), ForeignKey):
                surveydict[surveykey] = survey[surveykey]
            else:
                fkmodel = SurveyObservation._meta.get_field(surveykey).remote_field.model
                if surveykey == 'photometric_band':
                    fk = fkmodel.objects.filter(name=survey[surveykey].split('-')[1]).filter(instrument__name=survey[surveykey].split('-')[0])
                elif surveykey == 'survey_field':
                    # find survey field, approx 30-arcsec matching
                    fk = fkmodel.objects.filter(Q(ra_cen__gt=float(survey['ra_cen'])-0.01) & Q(ra_cen__lt=float(survey['ra_cen'])+0.01) &
                                                Q(dec_cen__gt=float(survey['dec_cen'])-0.01) & Q(dec_cen__lt=float(survey['dec_cen'])+0.01))

                    # if there's no RA/Dec match, find field based on name
                    if not len(fk):
                        fk = fkmodel.objects.filter(field_id=survey[surveykey])
                        print(survey[surveykey])
                        fk_new = fk[0]
                        fk_new.ra_cen = survey['ra_cen']
                        fk_new.dec_cen = survey['dec_cen']
                        # replace the field id, add a date to the field name
                        orig_id = fk_new.field_id[:]
                        if '_' in orig_id: field_ext = orig_id.split('_')[-1]
                        else: field_ext = '1'
                        new_field_id = orig_id.split('.')[0] + '.' + orig_id.split('.')[1] + '_' + field_ext
                        fk_new.field_id = new_field_id
                        fk_new.pk = None
                        fk_new.save()

                        # then make sure the MSB is up to date
                        msblist = SurveyFieldMSB.objects.filter(survey_fields__in=[fk[0]])
                        for msb in msblist:
                            # hopefully there's only one....
                            msb.survey_fields.remove(fk[0])
                            msb.survey_fields.add(fk_new)
                            # might end up with 7 fields in the MSB in rare cases

                    if not len(fk):
                        try: ztf_id = survey[surveykey].split('.')[0]
                        except: ztf_id = None
                        fk = fkmodel.objects.create(
                            field_id=survey[surveykey],ra_cen=survey['ra_cen'],dec_cen=survey['dec_cen'],
                            instrument=Instrument.objects.get(name='GPC1'),created_by_id=user.id,
                            modified_by_id=user.id,active=1,width_deg=3.1,
                            height_deg=3.1,ztf_field_id=ztf_id,cadence=3)
                else: fk = fkmodel.objects.filter(name=survey[surveykey])
                if not len(fk):
                    print("Sending email to: %s" % user.username)
                    html_msg = "Alert : YSE_PZ Failed to upload survey obs "
                    html_msg += "\nError : %s value doesn\'t exist in SurveyObservation.%s FK relationship"
                    sendemail(from_addr, user.email, subject,
                              html_msg%(survey[surveykey],surveykey),
                              djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
                    continue

                surveydict[surveykey] = fk[0]

        # find pre-existing observation record
        dbsurveyfield = SurveyObservation.objects.filter(
            survey_field=surveydict['survey_field']).filter(
                obs_mjd__gt=float(surveydict['obs_mjd'])-0.01).filter(
                    obs_mjd__lt=float(surveydict['obs_mjd'])+0.01).filter(
                        photometric_band=surveydict['photometric_band'])

        if not len(dbsurveyfield):
            # obs MJD on same night - probably need to get rise/set times
            # to do this right
            time = Time(mjd_to_date(surveydict['obs_mjd']), format='isot')
            tel = Observer(location=location, timezone="UTC")

            sunset = date_to_mjd(tel.sun_set_time(time,which="previous").isot)
            sunrise = date_to_mjd(tel.sun_rise_time(time,which="next").isot)

            dbsurveyfield = SurveyObservation.objects.filter(
                survey_field=surveydict['survey_field']).filter(
                    mjd_requested__gt=sunset).filter(
                        mjd_requested__lt=sunrise).filter(
                            photometric_band=surveydict['photometric_band'])

        if len(dbsurveyfield):
            dbsurveyfield.update(**surveydict)
        else:
            dbsurveyfield = SurveyObservation(**surveydict)
            survey_entries += [dbsurveyfield]

    SurveyObservation.objects.bulk_create(survey_entries)
    return_dict = {"message":"success"}
    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_transient(request):
    transient_data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # ready to send error emails
    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
    subject = "TNS Transient Upload Failure"
    txt_msg = "Alert : YSE_PZ Failed to upload transient %s "

    transient_entries = []
    # first bulk create new transients
    for transientlistkey in transient_data.keys():
        if transientlistkey == 'noupdatestatus': continue
        if transientlistkey == 'TNS': continue

        transient = transient_data[transientlistkey]
        tmp_name = transient['name']

        transientkeys = transient.keys()
        if 'name' not in transientkeys:
            return_dict = {"message":"Error : Transient name not provided for transient %s!"%transientlistkey}
            return JsonResponse(return_dict)
        print('updating transient %s'%transient['name'])
        try:
            transientdict = {'created_by_id':user.id,'modified_by_id':user.id}
            for transientkey in transientkeys:
                if transientkey == 'transientphotometry' or \
                   transientkey == 'transientspectra' or \
                   transientkey == 'host' or \
                   transientkey == 'tags' or \
                   transientkey == 'gw' or \
                   transientkey == 'non_detect_instrument' or \
                   transientkey == 'internal_names': continue

                if not isinstance(Transient._meta.get_field(transientkey), ForeignKey):
                    if transient[transientkey] is not None: transientdict[transientkey] = transient[transientkey]
                else:
                    fkmodel = Transient._meta.get_field(transientkey).remote_field.model
                    if transientkey == 'non_detect_band' and 'non_detect_instrument' in transient.keys():
                        fk = fkmodel.objects.filter(name=transient[transientkey]).filter(instrument__name=transient['non_detect_instrument'])
                        if not len(fk):
                            fk = fkmodel.objects.filter(name=transient[transientkey])
                    else:
                        fk = fkmodel.objects.filter(name=transient[transientkey])
                    if not len(fk):
                        fk = fkmodel.objects.filter(name='Unknown')
                        print("Sending email to: %s" % user.username)
                        html_msg = "Alert : YSE_PZ Failed to upload transient %s "
                        html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
                        sendemail(from_addr, user.email, subject,
                                  html_msg%(transient['name'],transient[transientkey],transientkey),
                                  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

                    transientdict[transientkey] = fk[0]

            dbtransient = Transient.objects.filter(name=transient['name'])
            if len(dbtransient) > 1:
                dbtransient.filter(~Q(pk=dbtransient[0].id)).delete()
                dbtransient = Transient.objects.filter(name=transient['name'])

            if not len(dbtransient):
                # check RA/dec
                ramin,ramax,decmin,decmax = getRADecBox(transient['ra'],transient['dec'],size=0.00042)
                if 'disc_date' in transient.keys():
                    dbtransient = Transient.objects.filter(
                        Q(ra__gt=ramin) & Q(ra__lt=ramax) & Q(dec__gt=decmin) & Q(dec__lt=decmax) &
                        Q(disc_date__gte=dateutil.parser.parse(transient['disc_date'])-datetime.timedelta(365)) &
                        Q(disc_date__lte=dateutil.parser.parse(transient['disc_date'])+datetime.timedelta(365)))
                else:
                    dbtransient = Transient.objects.filter(
                        Q(ra__gt=ramin) & Q(ra__lt=ramax) & Q(dec__gt=decmin) & Q(dec__lt=decmax))

                if len(dbtransient):
                    #dbtransient = dbtransient[0]
                    obs_group = ObservationGroup.objects.get(name=transient['obs_group'])
                    if 'TNS' in transient_data.keys() and transient_data['TNS']:
                        alt_transients = AlternateTransientNames.objects.filter(name=transient['name'])
                        if not len(alt_transients):
                            AlternateTransientNames.objects.create(
                                transient=dbtransient[0],obs_group=obs_group,name=dbtransient[0].name,
                                created_by_id=user.id,modified_by_id=user.id)
                        dbtransient[0].name = transient['name']
                        dbtransient[0].slug = transient['name']
                        dbtransient[0].save()
                    else:
                        alt_transients = AlternateTransientNames.objects.filter(name=transient['name'])
                        if not len(alt_transients):
                            AlternateTransientNames.objects.create(
                                transient=dbtransient[0],obs_group=obs_group,name=transient['name'],
                                created_by_id=user.id,modified_by_id=user.id)
                        transientdict['name'] = dbtransient[0].name

                    if 'noupdatestatus' in transient_data.keys() and not transient_data['noupdatestatus']:
                        if dbtransient[0].status.name == 'Ignore':
                            dbtransient[0].status = TransientStatus.objects.filter(name='New')[0]
                        else: transientdict['status'] = dbtransient[0].status
                    else: transientdict['status'] = dbtransient[0].status
                    if dbtransient[0].postage_stamp_file:
                        transientdict['postage_stamp_file'] = dbtransient[0].postage_stamp_file
                        transientdict['postage_stamp_ref'] = dbtransient[0].postage_stamp_ref
                        transientdict['postage_stamp_diff'] = dbtransient[0].postage_stamp_diff
                        transientdict['postage_stamp_file_fits'] = dbtransient[0].postage_stamp_file_fits
                        transientdict['postage_stamp_ref_fits'] = dbtransient[0].postage_stamp_ref_fits
                        transientdict['postage_stamp_diff_fits'] = dbtransient[0].postage_stamp_diff_fits

                    #taglist = []
                    #if 'tags' in transientkeys:
                    #   for tag in transient['tags']:
                    #       tagobj = TransientTag.objects.get(name=tag)
                    #       taglist += [tagobj]
                    dbtransient.update(**transientdict)
                    if 'tags' in transientkeys:
                        for tag in transient['tags']:
                            tagobj = TransientTag.objects.get(name=tag)
                            dbtransient[0].tags.add(tagobj)
                            dbtransient[0].save()

                else:
                    dbtransient = Transient(**transientdict)

                    transient_entries += [dbtransient]
                    #dbtransient = Transient.objects.create(**transientdict)
            else: #if clobber:
                if 'noupdatestatus' in transient_data.keys() and not transient_data['noupdatestatus']:
                    if dbtransient[0].status.name == 'Ignore': dbtransient[0].status = TransientStatus.objects.filter(name='New')[0]
                    else: transientdict['status'] = dbtransient[0].status
                else: transientdict['status'] = dbtransient[0].status
                if dbtransient[0].postage_stamp_file:
                    transientdict['postage_stamp_file'] = dbtransient[0].postage_stamp_file
                    transientdict['postage_stamp_ref'] = dbtransient[0].postage_stamp_ref
                    transientdict['postage_stamp_diff'] = dbtransient[0].postage_stamp_diff
                    transientdict['postage_stamp_file_fits'] = dbtransient[0].postage_stamp_file_fits
                    transientdict['postage_stamp_ref_fits'] = dbtransient[0].postage_stamp_ref_fits
                    transientdict['postage_stamp_diff_fits'] = dbtransient[0].postage_stamp_diff_fits

                dbtransient.update(**transientdict)
                if 'tags' in transientkeys:
                    for tag in transient['tags']:
                        if not len(dbtransient[0].tags.filter(name=tag)):
                            tagobj = TransientTag.objects.get(name=tag)
                            dbtransient[0].tags.add(tagobj)
                            dbtransient[0].save()
                if 'internal_names' in transient.keys():
                    for internal_name in transient['internal_names'].split(','):
                        # see if exists
                        alt = AlternateTransientNames.objects.filter(name=internal_name)
                        if len(alt): continue

                        # try to figure out the observation group (this isn't perfect)
                        altgroup = ObservationGroup.objects.filter(name__startswith=internal_name.replace(' ','')[:3])
                        if len(altgroup) != 1:
                            altgroup = ObservationGroup.objects.filter(name='Unknown')

                        # make the alternate transient name object
                        AlternateTransientNames.objects.create(
                            name=internal_name,obs_group=altgroup[0],
                            created_by_id=user.id,modified_by_id=user.id,
                            transient=dbtransient[0])

                dbtransient = dbtransient[0]

            #print('saved transient in %.1f sec'%(t4-t3))
            #       dbtransient.tags.add(tagobj)
            #   dbtransient.save()

            #print('applied tags in %.1f sec'%(t5-t4))

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print('Transient %s failed!'%transient['name'])
            print("Sending email to: %s" % user.username)
            html_msg = """Alert : YSE_PZ Failed to upload transient %s with error %s at line number %s"""

            sendemail(from_addr, user.email, subject, html_msg%(transient['name'],e,exc_tb.tb_lineno),
                      djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
            # sending SMS is too scary for now
            #sendsms(from_addr, phone_email, subject, txt_msg%transient['name'],
            #        djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

    Transient.objects.bulk_create(transient_entries)
    for t in transient_entries:
        dbt = Transient.objects.get(name=t.name)
        transient = transient_data[t.name]
        if 'tags' in transient.keys():
            for tag in transient['tags']:
                tagobj = TransientTag.objects.get(name=tag)
                dbt.tags.add(tagobj)
                dbt.save()
        if 'internal_names' in transient.keys():
            for internal_name in transient['internal_names'].split(','):
                # see if exists
                alt = AlternateTransientNames.objects.filter(name=internal_name)
                if len(alt): continue

                # try to figure out the observation group (this isn't perfect)
                altgroup = ObservationGroup.objects.filter(name__startswith=internal_name.replace(' ','')[:3])
                if len(altgroup) != 1:
                    altgroup = ObservationGroup.objects.filter(name='Unknown')

                # make the alternate transient name object
                AlternateTransientNames.objects.create(
                    name=internal_name,obs_group=altgroup[0],
                    created_by_id=user.id,modified_by_id=user.id,
                    transient=dbt)

    # add photometry, spectra, hosts
    phot_entries = []
    for transientlistkey in transient_data.keys():
        if transientlistkey == 'noupdatestatus': continue
        if transientlistkey == 'TNS': continue
        transient = transient_data[transientlistkey]
        transientkeys = transient.keys()

        dbtransient = Transient.objects.filter(name=transient['name'])
        if not len(dbtransient):
            dbtransient = AlternateTransientNames.objects.filter(name=transient['name'])[0].transient
        else: dbtransient = dbtransient[0]

        if 'transientphotometry' in transientkeys:
            # do photometry
            response,transientphot = add_transient_phot_util(
                transient['transientphotometry'],dbtransient,user,do_photdata=False)
            for t in transientphot:
                phot_entries.append(t)

        if 'transientspectra' in transientkeys:
            # spectrum
            add_transient_spec_util(transient['transientspectra'],dbtransient,user)

        if 'host' in transientkeys:
            # host galaxy
            add_transient_host_util(transient['host'],dbtransient,user)

    TransientPhotometry.objects.bulk_create(phot_entries)

    # add photdata
    photdata_entries = []
    for transientlistkey in transient_data.keys():
        if transientlistkey == 'noupdatestatus': continue
        if transientlistkey == 'TNS': continue
        transient = transient_data[transientlistkey]
        transientkeys = transient.keys()

        dbtransient = Transient.objects.filter(name=transient['name'])
        if not len(dbtransient):
            dbtransient = AlternateTransientNames.objects.filter(name=transient['name'])[0].transient
        else: dbtransient = dbtransient[0]

        if 'transientphotometry' in transientkeys:
            # do photometry
            response,transientphot = add_transient_phot_util(
                transient['transientphotometry'],dbtransient,user,do_photdata=True)
            for t in transientphot:
                phot_entries.append(t)
    
    TransientPhotometry.objects.bulk_create(photdata_entries)
    
    return_dict = {"message":"success"}
    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_gw_candidate(request):
    transient_data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # ready to send error emails
    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
    subject = "TNS Transient Upload Failure"
    txt_msg = "Alert : YSE_PZ Failed to upload transient %s "

    for transientlistkey in transient_data.keys():
        if transientlistkey == 'noupdatestatus': continue

        transient = transient_data[transientlistkey]

        transientkeys = transient.keys()
        if 'name' not in transientkeys:
            return_dict = {"message":"Error : Transient name not provided for transient %s!"%transientlistkey}
            return JsonResponse(return_dict)
        print('updating transient %s'%transient['name'])
        try:
            transientdict = {'created_by_id':user.id,'modified_by_id':user.id}
            for transientkey in transientkeys:
                if transientkey == 'transientphotometry' or \
                   transientkey == 'transientspectra' or \
                   transientkey == 'host' or \
                   transientkey == 'tags' or \
                   transientkey == 'gwcandidate' or \
                   transientkey == 'gwcandidateimage' or \
                   transientkey == 'non_detect_instrument': continue

                if not isinstance(Transient._meta.get_field(transientkey), ForeignKey):
                    transientdict[transientkey] = transient[transientkey]
                else:
                    fkmodel = Transient._meta.get_field(transientkey).remote_field.model
                    if transientkey == 'non_detect_band' and 'non_detect_instrument' in transient.keys():
                        fk = fkmodel.objects.filter(
                            name=transient[transientkey]).filter(instrument__name=transient['non_detect_instrument'])
                        if not len(fk):
                            fk = fkmodel.objects.filter(name=transient[transientkey])
                    else:
                        fk = fkmodel.objects.filter(name=transient[transientkey])
                    if not len(fk):
                        fk = fkmodel.objects.filter(name='Unknown')
                        print("Sending email to: %s" % user.username)
                        html_msg = "Alert : YSE_PZ Failed to upload transient %s "
                        html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
                        sendemail(from_addr, user.email, subject,
                                  html_msg%(transient['name'],transient[transientkey],transientkey),
                                  djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

                    transientdict[transientkey] = fk[0]

            dbtransient = Transient.objects.filter(name=transient['name'])
            if not len(dbtransient):
                # ra/dec box query
                sc = SkyCoord(transient['ra'],transient['dec'],frame="fk5",unit=u.deg)
                ramin,ramax,decmin,decmax = getRADecBox(sc.ra.deg,sc.dec.deg,size=5/3600.)
                dbtransient = Transient.objects.filter(Q(ra__gte = ramin) & Q(ra__lte = ramax) & Q(dec__gte = decmin) & Q(dec__lte = decmax))
                if len(dbtransient) > 1: dbtransient = dbtransient[0]
                elif len(dbtransient): dbtransient = dbtransient[0]
                else:
                    dbtransient = Transient.objects.create(**transientdict)
            else:
                if 'noupdatestatus' in transient_data.keys() and not transient_data['noupdatestatus']:
                    if dbtransient[0].status.name == 'Ignore': dbtransient[0].status = TransientStatus.objects.filter(name='New')[0]
                    else: transientdict['status'] = dbtransient[0].status
                else: transientdict['status'] = dbtransient[0].status

                dbtransient.update(**transientdict)
                dbtransient = dbtransient[0]
            if 'tags' in transientkeys:
                for tag in transient['tags']:
                    dbtransient.tags.add(tags=transient['tags'])
                dbtransient.save()

            if 'transientphotometry' in transientkeys:
                # do photometry
                add_transient_phot_util(transient['transientphotometry'],dbtransient,user)

            if 'transientspectra' in transientkeys:
                # spectrum
                add_transient_spec_util(transient['transientspectra'],dbtransient,user)

            if 'host' in transientkeys:
                # host galaxy
                add_transient_host_util(transient['host'],dbtransient,user)

            if 'gwcandidate' in transientkeys:
                # GW candidate info
                add_gw_candidate_util(transient['gwcandidate'],dbtransient,user)
                gwtag = TransientTag.objects.get(name='GW Candidate')
                dbtransient.tags.add(gwtag)
                dbtransient.save()

        except Exception as e:
            print('Transient %s failed!'%transient['name'])
            print("Sending email to: %s" % user.username)
            html_msg = "Alert : YSE_PZ Failed to upload transient %s with error %s"
            sendemail(from_addr, user.email, subject, html_msg%(transient['name'],e),
                      djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
            # sending SMS is too scary for now
            #sendsms(from_addr, phone_email, subject, txt_msg%transient['name'],
            #        djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

    return_dict = {"message":"success"}

    return JsonResponse(return_dict)

def add_gw_candidate_util(gwdict,transient,user):

    if 'name' not in gwdict.keys():
        return_dict = {"message":"no GW name"}
        return JsonResponse(return_dict)

    dbgwdict = {'created_by_id':user.id,'modified_by_id':user.id}
    for gwkey in gwdict.keys():
        if gwkey == 'gwcandidateimage': continue
        if not isinstance(GWCandidate._meta.get_field(gwkey), ForeignKey):
                dbgwdict[gwkey] = gwdict[gwkey]
        else:
            fkmodel = GWCandidate._meta.get_field(gwkey).remote_field.model
            fk = fkmodel.objects.filter(name=gwdict[gwkey])
            if not len(fk):
                # ready to send error emails
                smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
                from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
                subject = "TNS Transient Upload Failure"
                html_msg = "Alert : YSE_PZ Failed to upload transient %s "
                txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
                html_msg += "\nError : %s value doesn\'t exist in GWCandidate.%s FK relationship"
                print("Sending email to: %s" % user.username)
                sendemail(from_addr, user.email, subject,
                          html_msg%(gwdict['name'],gwdict[gwkey],gwkey),
                          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

            gwdict[gwkey] = fk[0]

    dbgwdict['transient'] = transient
    dbgw = GWCandidate.objects.filter(name=dbgwdict['name'])
    if not len(dbgw):
        dbgw = GWCandidate.objects.create(**dbgwdict)
    else: #if clobber:
        dbgw.update(**dbgwdict)
        dbgw = dbgw[0]

    for gwtopkey in gwdict['gwcandidateimage'].keys():
        dbgwimagedict = {'created_by_id':user.id,'modified_by_id':user.id}
        for gwkey in gwdict['gwcandidateimage'][gwtopkey].keys():
            if not isinstance(GWCandidateImage._meta.get_field(gwkey), ForeignKey):
                dbgwimagedict[gwkey] = gwdict['gwcandidateimage'][gwtopkey][gwkey]
            else:
                fkmodel = GWCandidateImage._meta.get_field(gwkey).remote_field.model
                if gwkey == 'image_filter':
                    fk = fkmodel.objects.filter(name=gwdict['gwcandidateimage'][gwtopkey][gwkey].split(' - ')[1]).filter(instrument__name=gwdict['gwcandidateimage'][gwtopkey][gwkey].split(' - ')[0])
                    if not len(fk):
                        fk = fkmodel.objects.filter(name=gwdict['gwcandidateimage'][gwtopkey][gwkey])
                else:
                    fk = fkmodel.objects.filter(name=gwdict['gwcandidateimage'][gwtopkey][gwkey])

                if not len(fk):
                    # ready to send error emails
                    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
                    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
                    subject = "TNS Transient Upload Failure"
                    html_msg = "Alert : YSE_PZ Failed to upload transient %s "
                    txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
                    html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
                    print("Sending email to: %s" % user.username)
                    sendemail(from_addr, user.email, subject,
                              html_msg%(gwdict['name'],gwdict['gwcandidateimage'][gwtopkey],gwdict['gwcandidateimage'][gwtopkey][gwkey]),
                              djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

                dbgwimagedict[gwkey] = fk[0]

        dbgwimagedict['gw_candidate'] = dbgw
        dbgwimage = GWCandidateImage.objects.filter(gw_candidate=dbgw).filter(image_filename=dbgwimagedict['image_filename'])
        if not len(dbgwimage):
            dbgwimage = GWCandidateImage.objects.create(**dbgwimagedict)
        else: #if clobber:
            dbgwimage.update(**dbgwimagedict)
            dbgwimage = dbgwimage[0]

    return_dict = {"message":"GW success"}
    return JsonResponse(return_dict)

def add_transient_host_util(hostdict,transient,user):

    if 'name' not in hostdict.keys():
        return_dict = {"message":"no host"}
        return JsonResponse(return_dict)

    dbhostdict = {'created_by_id':user.id,'modified_by_id':user.id}
    for hostkey in hostdict.keys():
        if not isinstance(Host._meta.get_field(hostkey), ForeignKey):
                dbhostdict[hostkey] = hostdict[hostkey]
        else:
            fkmodel = Host._meta.get_field(hostkey).remote_field.model
            fk = fkmodel.objects.filter(name=hostdict[hostkey])
            if not len(fk):
                # ready to send error emails
                smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
                from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
                subject = "TNS Transient Upload Failure"
                html_msg = "Alert : YSE_PZ Failed to upload transient %s "
                txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
                html_msg += "\nError : %s value doesn\'t exist in transient.%s FK relationship"
                print("Sending email to: %s" % user.username)
                sendemail(from_addr, user.email, subject,
                          html_msg%(transient['name'],transient[transientkey],transientkey),
                          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

            hostdict[hostkey] = fk[0]

    dbhost = Host.objects.filter(name=dbhostdict['name'])
    if not len(dbhost):
        dbhost = Host.objects.create(**dbhostdict)
    else: #if clobber:
        dbhost.update(**dbhostdict)
        dbhost = dbhost[0]

    transient.host = dbhost
    transient.save()

    return_dict = {"message":"host success"}
    return JsonResponse(return_dict)

def add_transient_phot_util(photdict,transient,user,do_photdata=True):

    transientphot_entries = []
    for k in photdict.keys():
        if k == 'clobber' or k == 'mjdmatchmin': continue
        photometry = photdict[k]

        instrument = Instrument.objects.filter(name=photometry['instrument'])
        if not len(instrument):
            instrument = Instrument.objects.filter(name='Unknown')
        instrument = instrument[0]

        obs_group = ObservationGroup.objects.filter(name=photometry['obs_group'])
        if not len(obs_group):
            obs_group = ObservationGroup.objects.filter(name='Unknown')
        obs_group = obs_group[0]

        transientphot = TransientPhotometry.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group)
        if not len(transientphot):
            transientphot = TransientPhotometry( #.objects.create
                instrument=instrument, obs_group=obs_group, transient=transient,
                created_by_id=user.id, modified_by_id=user.id)
            transientphot_entries += [transientphot]
        else: transientphot = transientphot[0]
        existingphot = TransientPhotData.objects.filter(photometry=transientphot)
        if do_photdata:
            for k in photometry['photdata']:
                p = photometry['photdata'][k]
                pmjd = Time(p['obs_date'],format='isot').mjd

                band = PhotometricBand.objects.filter(name=p['band']).filter(instrument__name=photometry['instrument'])
                if len(band): band = band[0]
                else: band = PhotometricBand.objects.filter(name='Unknown')[0]
                obsExists = False

                for idx,e in enumerate(existingphot):
                    if e.photometry.id == transientphot.id:
                        if e.band == band:
                            try:
                                mjd = Time(e.obs_date.isoformat().split('+')[0],format='isot').mjd
                            except:
                                mjd = Time(e.obs_date,format='isot').mjd

                            if np.abs(mjd - pmjd) < photdict['mjdmatchmin']:
                                obsExists = True
                                if photdict['clobber']:

                                    dq = None
                                    if p['data_quality']:
                                        dq = DataQuality.objects.filter(name=p['data_quality'])
                                        if not dq:
                                            dq = DataQuality.objects.filter(name='Bad')
                                        dq = dq[0]

                                    e.obs_date = p['obs_date']
                                    e.flux = p['flux']
                                    e.flux_err = p['flux_err']
                                    e.flux_zero_point = p['flux_zero_point']
                                    e.mag = p['mag']
                                    e.mag_err = p['mag_err']
                                    e.forced = p['forced']
                                    e.diffim = p['diffim']

                                    # Because we're in CLOBBER mode, remove existing dq flags and add the one passed here.
                                    data_quality_flags = e.data_quality.all()
                                    for _dq in data_quality_flags:
                                        e.data_quality.remove(_dq)
                                    e.data_quality.add(dq)

                                    e.photometry = transientphot
                                    e.discovery_point = p['discovery_point']
                                    e.band = band
                                    e.modified_by_id = user.id
                                    e.save()

                                if 'diffimg' in p.keys():
                                    existing_diff = TransientDiffImage.objects.filter(phot_data=e)
                                    p['diffimg']['created_by_id'] = user.id
                                    p['diffimg']['modified_by_id'] = user.id
                                    p['diffimg']['phot_data_id'] = e.id
                                    if not len(existing_diff):
                                        TransientDiffImage.objects.create(**p['diffimg'])
                                    else:
                                        existing_diff.update(**p['diffimg'])


                if not obsExists:
                    dq = None
                    if p['data_quality']:
                        dq = DataQuality.objects.filter(name=p['data_quality'])
                        if not dq:
                            dq = DataQuality.objects.filter(name='Bad')
                        dq = dq[0]

                    e = TransientPhotData.objects.create(
                        obs_date=p['obs_date'],flux=p['flux'],flux_err=p['flux_err'],
                        mag=p['mag'],mag_err=p['mag_err'],forced=p['forced'],
                        diffim=p['diffim'],
                        photometry=transientphot,
                        flux_zero_point=p['flux_zero_point'],
                        discovery_point=p['discovery_point'],band=band,
                        created_by_id=user.id,modified_by_id=user.id)

                    if dq is not None:
                        # Set operator needs a list...
                        e.data_quality.set([dq])
                        e.save()
                    if 'diffimg' in p.keys():
                        p['diffimg']['created_by_id'] = user.id
                        p['diffimg']['modified_by_id'] = user.id
                        p['diffimg']['phot_data_id'] = e.id
                        TransientDiffImage.objects.create(**p['diffimg'])

    return_dict = {"message":"successfully added phot data"}
    return JsonResponse(return_dict),transientphot_entries

def add_transient_spec_util(specdict,transient,user):

    for k in specdict.keys():
        if k == 'clobber': continue
        spectrum = specdict[k]
        # get all the foreign keys we need
        instrument = Instrument.objects.filter(name=spectrum['instrument'])
        if not len(instrument):
            instrument = Instrument.objects.filter(name='Unknown')
        instrument = instrument[0]

        obs_group = ObservationGroup.objects.filter(name=spectrum['obs_group'])
        if not len(obs_group):
            obs_group = ObservationGroup.objects.filter(name='Unknown')
        obs_group = obs_group[0]

        allgroups = []
        if 'groups' in spectrum.keys() and spectrum['groups']:
            for specgroup in spectrum['groups'].split(','):
                group = Group.objects.filter(name=specgroup)
                if not len(group):
                    return_dict = {"message":"group %s is not in DB"%hd['groups']}
                    return JsonResponse(return_dict)
                group = group[0]
                allgroups += [group]

        dq = None
        if 'data_quality' in spectrum.keys() and spectrum['data_quality']:
            dq = DataQuality.objects.filter(name=spectrum['data_quality'])

            if not dq:
                dq = DataQuality.objects.filter(name='Bad')
            dq = dq[0]

        spectrum['instrument'] = instrument
        spectrum['obs_group'] = obs_group

        # get the spectrum
        transientspec = TransientSpectrum.objects.filter(transient=transient).\
            filter(instrument=instrument).filter(obs_group=obs_group).filter(obs_date=spectrum['obs_date'])
        spectrum['created_by_id'] = user.id
        spectrum['modified_by_id'] = user.id
        spectrum['transient'] = transient
        spectrum_copy = spectrum.copy()
        del spectrum_copy['specdata']

        if not len(transientspec):
            transientspec = TransientSpectrum.objects.create(**spectrum_copy)
            # Need to use a set operation to associate many-to-many, also set takes an enumerable...
            transientspec.data_quality.set([dq])
            transientspec.save()
        else:
            if specdict['clobber']:

                # Prior to updating the existing spectrum, we need to clear out dq flags to add the new dq flags
                data_quality_flags = transientspec.data_quality.all()
                for _dq in data_quality_flags:
                    transientspec.data_quality.remove(_dq)
                transientspec.data_quality.add(dq)

                transientspec.update(**spectrum_copy)
                #transientspec.save()
            transientspec = transientspec[0]

        if len(allgroups):
            for group in allgroups:
                if group not in transientspec.groups.all():
                    transientspec.groups.add(group)
                    transientspec.save()

        # add the spec data
        existingspec = TransientSpecData.objects.filter(spectrum=transientspec)
        # loop through new, comp against existing
        if len(existingspec) and specdict['clobber']:
            for e in existingspec: e.delete()
        elif len(existingspec):
            return_dict = {"message":"spectrum exists.  Not clobbering"}
            return JsonResponse(return_dict)

        specdata = spectrum['specdata']
        specdata_entries = []
        for k in specdata.keys():
            s = specdata[k]

            specdata_single = TransientSpecData(spectrum=transientspec,wavelength=s['wavelength'],
                                                flux=s['flux'],flux_err=s['flux_err'],
                                                created_by_id=user.id,modified_by_id=user.id)
            specdata_entries += [specdata_single]
        TransientSpecData.objects.bulk_create(specdata_entries)

    return_dict = {"message":"successfully added spec data"}
    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_transient_phot(request):
    phot_data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    if 'header' in phot_data.keys() and 'transient' in phot_data.keys() and 'photheader' in phot_data.keys():
        hd = phot_data['header']
        tr = phot_data['transient']
        ph = phot_data['photheader']
    else:
        return_dict = {"message":"header, transient, and photheader keys are required"}
        return JsonResponse(return_dict)

    # get all the foreign keys we need
    instrument = Instrument.objects.filter(name=ph['instrument'])
    if not len(instrument):
        instrument = Instrument.objects.filter(name='Unknown')
    instrument = instrument[0]

    obs_group = ObservationGroup.objects.filter(name=ph['obs_group'])
    if not len(obs_group):
        obs_group = ObservationGroup.objects.filter(name='Unknown')
    obs_group = obs_group[0]

    status = TransientStatus.objects.filter(name=tr['status'])
    if not len(status):
        return_dict = {"message":"status %s is not in DB"%tr['status']}
        return JsonResponse(return_dict)
    status = status[0]

    allgroups = []
    if ph['groups']:
        for photgroup in ph['groups'].split(','):
            group = Group.objects.filter(name=photgroup)
            if not len(group):
                return_dict = {"message":"group %s is not in DB"%ph['groups']}
                return JsonResponse(return_dict)
            group = group[0]
            allgroups += [group]

    # get or create transient
    transient = Transient.objects.filter(name=tr['name'])
    if not len(transient):
        transient = Transient.objects.create(name=tr['name'],ra=tr['ra'],dec=tr['dec'],
                                             status=status,created_by_id=user.id,
                                             obs_group=obs_group,
                                             modified_by_id=user.id)
    else: transient = transient[0]
    # get all existing photometry
    transientphot = TransientPhotometry.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group)
    if not len(transientphot):
        transientphot = TransientPhotometry.objects.create(
            instrument=instrument,obs_group=obs_group,transient=transient,
            created_by_id=user.id,modified_by_id=user.id)
    else:
        transientphot = transientphot[0]
        if hd['clobber']:
            transientphot.instrument = instrument
            transientphot.obs_group = obs_group
            transientphot.modified_by_id = user.id
            transientphot.save()

    if len(allgroups):
        for group in allgroups:
            if group not in transientphot.groups.all():
                transientphot.groups.add(group)
                transientphot.save()

    existingphot = TransientPhotData.objects.filter(photometry=transientphot)

    # loop through new, comp against existing
    for k in phot_data.keys():
        if k == 'header' or k == 'transient' or k == 'photheader': continue
        p = phot_data[k]
        pmjd = Time(p['obs_date'],format='isot').mjd
        band = PhotometricBand.objects.filter(name=p['band']).filter(instrument__name=ph['instrument'])
        if len(band): band = band[0]
        else: band = PhotometricBand.objects.filter(name='Unknown')[0]

        obsExists = False
        for e in existingphot:
            if e.photometry.id == transientphot.id:
                if e.band == band:
                    try:
                        mjd = Time(e.obs_date.isoformat().split('+')[0],format='isot').mjd
                    except:
                        mjd = Time(e.obs_date,format='isot').mjd
                    if np.abs(mjd - pmjd) < hd['mjdmatchmin']:
                        obsExists = True
                        if hd['clobber']:

                            dq = None
                            if p['data_quality']:
                                dq = DataQuality.objects.filter(name=p['data_quality'])
                                if not dq:
                                    dq = DataQuality.objects.filter(name='Bad')
                                dq = dq[0]

                            e.obs_date = p['obs_date']
                            e.flux = p['flux']
                            e.flux_err = p['flux_err']
                            e.flux_zero_point = p['flux_zero_point']
                            e.mag = p['mag']
                            e.mag_err = p['mag_err']
                            e.forced = p['forced']
                            e.diffim = p['diffim']

                            # Because we're in CLOBBER mode, remove existing dq flags and add the one passed here.
                            data_quality_flags = e.data_quality.all()
                            for _dq in data_quality_flags:
                                e.data_quality.remove(_dq)
                            e.data_quality.add(dq)

                            e.photometry = transientphot
                            e.discovery_point = p['discovery_point']
                            e.band = band
                            e.modified_by_id = user.id
                            e.save()

        if not obsExists:
            dq = None
            if p['data_quality']:
                dq = DataQuality.objects.filter(name=p['data_quality'])
                if not dq:
                    dq = DataQuality.objects.filter(name='Bad')
                dq = dq[0]
            tpd = TransientPhotData.objects.create(obs_date=p['obs_date'],flux=p['flux'],flux_err=p['flux_err'],
                                                   mag=p['mag'],mag_err=p['mag_err'],forced=p['forced'],
                                                   diffim=p['diffim'],
                                                   photometry=transientphot,
                                                   flux_zero_point=p['flux_zero_point'],
                                                   discovery_point=p['discovery_point'],band=band,
                                                   created_by_id=user.id,modified_by_id=user.id)
            if dq is not None:
                # Set operator needs a list...
                tpd.data_quality.set([dq])
                tpd.save()

    return_dict = {"message": "success"}

    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def add_transient_spec(request):
    try:
        spec_data = JSONParser().parse(request)

        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)

        if 'header' in spec_data.keys() and 'transient' in spec_data.keys():
            hd = spec_data['header']
            tr = spec_data['transient']
        else:
            return_dict = {"message":"header and transient keys are required"}
            return JsonResponse(return_dict)

        # get all the foreign keys we need
        instrument = Instrument.objects.filter(name=hd['instrument'])
        if not len(instrument):
            instrument = Instrument.objects.filter(name='Unknown')
        instrument = instrument[0]

        obs_group = ObservationGroup.objects.filter(name=hd['obs_group'])
        if not len(obs_group):
            obs_group = ObservationGroup.objects.filter(name='Unknown')
        obs_group = obs_group[0]

        allgroups = []
        if hd['groups']:
            for specgroup in hd['groups'].split(','):
                group = Group.objects.filter(name=specgroup)
                if not len(group):
                    return_dict = {"message":"group %s is not in DB"%hd['groups']}
                    return JsonResponse(return_dict)
                group = group[0]
                allgroups += [group]

        # get or create transient
        transient = Transient.objects.filter(name=tr['name'])
        if not len(transient):
            return_dict = {"message":"transient %s is not in DB"%tr['name']}
            return JsonResponse(return_dict)
        else: transient = transient[0]

        dq = None
        if hd['data_quality']:
            dq = DataQuality.objects.filter(name=hd['data_quality'])
            if not dq:
                dq = DataQuality.objects.filter(name='Bad')
            dq = dq[0]

        # get the spectrum
        transientspec = TransientSpectrum.objects.filter(transient=transient).filter(instrument=instrument).filter(obs_group=obs_group).filter(obs_date=hd['obs_date'])
        if not len(transientspec):
            transientspec = TransientSpectrum.objects.create(
                ra=hd['ra'],dec=hd['dec'],instrument=instrument,obs_group=obs_group,transient=transient,
                rlap=hd['rlap'],redshift=hd['redshift'],redshift_err=hd['redshift_err'],
                redshift_quality=hd['redshift_quality'],spectrum_notes=hd['spectrum_notes'],
                spec_phase=hd['spec_phase'],obs_date=hd['obs_date'],
                created_by_id=user.id,modified_by_id=user.id)
            if dq is not None:
                # set takes an enumerable
                transientspec.data_quality.set([dq])
                transientspec.save()
        else:
            transientspec = transientspec[0]
            if hd['clobber']:
                if dq is not None:
                    # If dq flag exists and this is an existing spectrum, we need to remove the old DQ and add the new DQ
                    data_quality_flags = transientspec.data_quality.all()
                    for _dq in data_quality_flags:
                        transientspec.data_quality.remove(_dq)
                    transientspec.data_quality.add(dq)

                transientspec.ra = hd['ra']
                transientspec.dec = hd['dec']
                transientspec.rlap = hd['rlap']
                transientspec.redshift = hd['redshift']
                transientspec.redshift_err = hd['redshift_err']
                transientspec.redshift_quality = hd['redshift_quality']
                transientspec.spectrum_notes = hd['spectrum_notes']
                transientspec.spec_phase = hd['spec_phase']
                transientspec.modified_by_id = user.id
                transientspec.save()
        if len(allgroups):
            for group in allgroups:
                if group not in transientspec.groups.all():
                    transientspec.groups.add(group)
                    transientspec.save()

        # add the spec data
        existingspec = TransientSpecData.objects.filter(spectrum=transientspec)
        # loop through new, comp against existing
        if len(existingspec) and hd['clobber']:
            for e in existingspec: e.delete()
        elif len(existingspec):
            return_dict = {"message":"spectrum exists.  Not clobbering"}
            return JsonResponse(return_dict)

        for k in spec_data.keys():
            if k == 'header' or k == 'transient': continue
            s = spec_data[k]

            TransientSpecData.objects.create(spectrum=transientspec,wavelength=s['wavelength'],
                                             flux=s['flux'],flux_err=s['flux_err'],
                                             created_by_id=user.id,modified_by_id=user.id)

        return_dict = {"message":"success"}
        return JsonResponse(return_dict)
    except Exception as e:
        return_dict = {"message":e.__str__()}
        return JsonResponse(return_dict)

@login_or_basic_auth_required
def get_transient(request, slug):
    t = Transient.objects.filter(slug=slug)

    return_dict = {"transient":""}
    if t.exists():
        transient = t[0]
        serializer = TransientSerializer(instance=transient, context={"request":Request(request)})
        return_dict["transient"] = serializer.data

    return JsonResponse(return_dict)

@login_or_basic_auth_required
def get_rising_transients(request,ndays):
    qs = recent_rising_transient_queryset(ndays=ndays)

    return_dict = {"transient":""}
    for transient in qs:
        serializer = TransientSerializer(instance=transient, context={"request":Request(request)})
        return_dict[transient.name] = serializer.data

    return JsonResponse(return_dict)

def find_separation(host_queryset, query_coord, sep_threshold):

    ra,dec = [],[]
    for host in host_queryset:
        ra += [host.ra]; dec += [host.dec]
    host_coords = SkyCoord(ra, dec, unit=(u.deg, u.deg))
    sep = host_coords.separation(query_coord)
    for idx in np.where(sep.arcminute <= sep_threshold)[0]:
        yield host_queryset[int(idx)],sep.arcminute[idx]

@login_or_basic_auth_required       
def get_host(request, ra, dec, sep):

    query_coord = SkyCoord(ra,dec,unit=(u.deg, u.deg))
    host_candidates = find_separation(Host.objects.all(), query_coord, float(sep))

    serialized_hosts = []
    for host,sep in host_candidates:
        serialized_hosts.append(
            {"host_ra":host.ra,"host_dec":host.dec,
             "host_name":host.name,"host_id":host.id,
             "host_sep":sep}
        )

    return_dict = {"requested ra":float(ra),
                   "requested dec":float(dec),
                   "requested sep":float(sep),
                   "host candidates":serialized_hosts }

    return JsonResponse(return_dict)

@login_or_basic_auth_required       
def get_rising_transients_box(request, ra, dec, ra_width, dec_width):

    qs = recent_rising_transient_queryset(ndays=5)
    ramin,ramax,decmin,decmax = getRADecBox(float(ra),float(dec),float(ra_width),float(dec_width))
    qs = qs.filter(ra__gt=ramin).filter(ra__lt=ramax).filter(dec__gt=decmin).filter(dec__lt=decmax).filter(~Q(status__name='Ignore')).filter(
        Q(status__name='New') | Q(status__name='Watch') | Q(status__name='FollowupRequested') |
        Q(status__name='Following') | Q(status__name='Interesting') |
        ~Q(tags__name='YSE')).filter(disc_date__gt=datetime.datetime.utcnow()-datetime.timedelta(10))

    serialized_transients = []
    for t in qs:
        serialized_transients.append(
            {"transient_ra":t.ra,"transient_dec":t.dec,
             "transient_name":t.name,"transient_id":t.id}
        )

    return_dict = {"requested ra":float(ra),
                   "requested dec":float(dec),
                   "transients":serialized_transients }

    return JsonResponse(return_dict)

@login_or_basic_auth_required       
def get_new_transients_box(request, ra, dec, ra_width, dec_width):

    qs = Transient.objects.all() #filter(disc_date__gte=datetime.datetime.utcnow()-datetime.timedelta(5)) #.filter(~Q(TNS_spec_class__isnull=True))
    ramin,ramax,decmin,decmax = getRADecBox(float(ra),float(dec),float(ra_width),float(dec_width))
    qs = qs.filter(ra__gt=ramin).filter(ra__lt=ramax).filter(dec__gt=decmin).filter(dec__lt=decmax).filter(
        Q(status__name='Watch') | Q(status__name='FollowupRequested') | Q(status__name='Following') | Q(status__name='Interesting') |
        ~Q(tags__name='YSE')).filter(disc_date__gt=datetime.datetime.utcnow()-datetime.timedelta(10))

    serialized_transients = []
    for t in qs:
        serialized_transients.append(
            {"transient_ra":t.ra,"transient_dec":t.dec,
             "transient_name":t.name,"transient_id":t.id}
        )

    return_dict = {"requested ra":float(ra),
                   "requested dec":float(dec),
                   "transients":serialized_transients }

    return JsonResponse(return_dict)

@login_or_basic_auth_required       
def get_all_transients_box(request, ra, dec, ra_width, dec_width):

    qs = Transient.objects.all() #filter(disc_date__gte=datetime.datetime.utcnow()-datetime.timedelta(5)) #.filter(~Q(TNS_spec_class__isnull=True))
    ramin,ramax,decmin,decmax = getRADecBox(float(ra),float(dec),float(ra_width),float(dec_width))
    qs = qs.filter(ra__gt=ramin).filter(ra__lt=ramax).filter(dec__gt=decmin).filter(dec__lt=decmax)

    serialized_transients = []
    for t in qs:
        serialized_transients.append(
            {"transient_ra":t.ra,"transient_dec":t.dec,
             "transient_name":t.name,"transient_id":t.id}
        )

    return_dict = {"requested ra":float(ra),
                   "requested dec":float(dec),
                   "transients":serialized_transients }

    return JsonResponse(return_dict)


@csrf_exempt
@login_or_basic_auth_required
def query_api(request,query_name):

    query = Query.objects.filter(title=unquote(query_name))
    if len(query):
        query = query[0]
        if 'yse_app_transient' not in query.sql.lower(): return Http404('Invalid Query')
        if 'name' not in query.sql.lower(): return Http404('Invalid Query')
        if not query.sql.lower().startswith('select'): return Http404('Invalid Query')
        cursor = connections['explorer'].cursor()
        cursor.execute(query.sql.replace('%','%%'), ())
        #transients = Transient.objects.filter(name__in=(x[0] for x in cursor)).order_by('-disc_date')
        field_names = [c[0] for c in cursor.description]
        field_vals = [x for x in cursor]
        cursor.close()
    else:
        #query = UserQuery.objects.filter(python_query = unquote(query_name))
        #if not len(query): return Http404('Invalid Query')
        #query = query[0]
        try: transients = getattr(yse_python_queries,unquote(query_name))() #.python_query)()
        except: return Http404('Invalid Query')

    serialized_transients = []
    for vals in field_vals:
        #tdict = {"transient_ra":t.ra,"transient_dec":t.dec,
        #        "transient_name":t.name,"transient_id":t.id}
        tdict = {}
        for f,v in zip(field_names,vals):
            tdict[f] = v
        serialized_transients.append(
            tdict
        )

    return_dict = {"transients":serialized_transients }

    return JsonResponse(return_dict)

@csrf_exempt
@login_or_basic_auth_required
def box_search(request,ra,dec,radius):

    qs = None

    ra,dec,radius = float(ra),float(dec),float(radius)

    d = float(dec)*np.pi/180
    width_corr = float(radius)/np.abs(np.cos(d))

    ra_offset = cd.Angle(width_corr, unit=u.deg)
    dec_offset = cd.Angle(radius, unit=u.deg)

    query= """SELECT t.name, ACOS(SIN(t.dec*3.14159/180)*SIN(%s*3.14159/180)+COS(t.dec*3.14159/180)*COS(%s*3.14159/180)*COS((t.ra-%s)*3.14159/180))*180/3.14159 as sep
FROM YSE_App_transient t
WHERE t.ra > %s AND t.ra < %s AND t.dec > %s AND t.dec < %s
HAVING sep < 3.3
""" % (
    dec, dec, ra, ra-radius,ra+radius,
    dec-radius,dec+radius)
    cursor = connections['explorer'].cursor()
    cursor.execute(query, ())

    qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(name__in=(x[0] for x in cursor))

    serialized_transients = []
    for t in qs.filter(Q(tags__name='YSE')):
        serialized_transients.append(
            {"transient_ra":t.ra,"transient_dec":t.dec,
             "transient_name":t.name,"transient_id":t.id}
        )

    return_dict = {"transients":serialized_transients }

    return JsonResponse(return_dict)

def getRADecBox(ra,dec,size=None,dec_size=None):
    if not dec_size:
        RAboxsize = DECboxsize = size
    else:
        RAboxsize = size
        DECboxsize = size

    # get the maximum 1.0/cos(DEC) term: used for RA cut
    minDec = dec-0.5*DECboxsize
    if minDec<=-90.0:minDec=-89.9
    maxDec = dec+0.5*DECboxsize
    if maxDec>=90.0:maxDec=89.9

    invcosdec = max(1.0/np.cos(dec*np.pi/180.0),
                    1.0/np.cos(minDec  *np.pi/180.0),
                    1.0/np.cos(maxDec  *np.pi/180.0))

    ramin = ra-0.5*RAboxsize*invcosdec
    ramax = ra+0.5*RAboxsize*invcosdec
    decmin = dec-0.5*DECboxsize
    decmax = dec+0.5*DECboxsize

    if ra<0.0: ra+=360.0
    if ra>=360.0: ra-=360.0

    if ramin!=None:
        if (ra-ramin)<-180:
            ramin-=360.0
            ramax-=360.0
        elif (ra-ramin)>180:
            ramin+=360.0
            ramax+=360.0
    return(ramin,ramax,decmin,decmax)



# FRB items

@csrf_exempt
@login_or_basic_auth_required
def add_frb_galaxy(request):
    """ Add an FRBGalaxy to the DB from an 
    outside request

    This is mainly intended for testing

    Args:
        request (_type_): _description_

    Returns:
        JsonResponse: _description_
    """
    
    data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Serialize the user and we are all set
    #data['created_by'] = user
    #data['modified_by'] = user

    # Use Serializer
    serializer = FRBGalaxySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        print(f"Generated FRB Galaxy: {data['name']}")
    else:
        print(f"Not valid!")

    return JsonResponse(serializer.data, status=201)

@csrf_exempt
@login_or_basic_auth_required
def rm_frb_galaxy(request):
    """ Remove an FRBGalaxy from the DB
    via an outside request

    This is mainly intended for testing

    Args:
        request (_type_): _description_

    Returns:
        JsonResponse: _description_
    """
    
    data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Serialize the user and we are all set
    #data['created_by'] = user
    #data['modified_by'] = user

    try:
        obj = FRBGalaxy.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        pass
    else:
        obj.delete()
        print(f"Deleted {data['name']}")

    return JsonResponse(data, status=201)

@csrf_exempt
@login_or_basic_auth_required
def ingest_path(request):
    """
    Ingest a PATH analysis into the DB

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

      - transient_name (str): Name of the FRBTransient object
        Must be in the DB already
      - table (str): a table of the PATH candidates and their 
        PATH results, stored as JSON
      - F (str): name of filter; must be present in the
        PhotometricBand table
      - instrument (str): name of the instrument; must be present in the
        Instrument table
      - obs_group (str): name of the instrument; must be present in the
        ObservationGroup table
      - P_Ux (float): Unseen posterior;  added to the transient
      - bright_star (int): 1 if the transient is near a bright star

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    try:
        itransient = FRBTransient.objects.get(name=data['transient_name'])
    except:
        return JsonResponse({"message":f"Could not find transient {data['transient_name']} in DB"}, status=400)
    # Prep 
    tbl = pandas.read_json(data['table'])

    try:
        path.ingest_path_results(
            itransient, tbl, 
            data['F'], 
            data['instrument'], data['obs_group'],
            data['P_Ux'], user,
            remove_previous=True,
            bright_star=data['bright_star']) # May wish to make this optional
    except:
        print("Ingestion failed")
        return JsonResponse({"message":f"Ingestion failed 2x!"}, status=405)
    else:
        print("Successfully ingested")

    return JsonResponse({"message":f"Ingestion successful"}, status=500)

@csrf_exempt
@login_or_basic_auth_required
def targets_from_frb_followup_resource(request):
    """
    Grab a table of targets for a provided FRBFollowupResource

    The request must include the following items
     in its data (all in JSON, of course; 
     data types refer to those after parsing the JSON):

      - resource_name (str): Name of the FRBFollowupResource object

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse:  Table of information
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    try:
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    except:
        return JsonResponse({"message":f"Bad user authentication in DB"}, status=401)

    # Grab the FollowUpResource
    try:
        frb_fu = FRBFollowUpResource.objects.get(name=data['resource_name'])
    except:
        return JsonResponse({"message":f"Could not find resource {data['resource_name']} in DB"}, status=402)

    # Grab the targets
    target_table = frb_fu.generate_target_table()

    # Return
    return JsonResponse(target_table.to_dict(), status=201)


@csrf_exempt
@login_or_basic_auth_required
def ingest_obsplan(request):
    """
    Ingest an observing plan 

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

      - table (str): a table of the request with columns (all strings):
        -- TNS: TNS name
        -- Resource: Resource name
        -- mode: observing mode ['image', 'longslit', 'mask']
      - override (bool): if True, will override several of the
        checks

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Prep 
    obs_tbl = pandas.read_json(data['table'])

    # Run
    code, msg = frb_observing.ingest_obsplan(obs_tbl, user,
                                            data['resource'],
                                            override=data['override'])

    # Return
    return JsonResponse({"message":f"{msg}"}, status=code)

@csrf_exempt
@login_or_basic_auth_required
def ingest_obslog(request):
    """
    Ingest an observing log

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

      - table (str): a table of the request with columns 
            -- TNS (str)
            -- Resource (str)
            -- mode (str)
            -- Conditions (str)
            -- texp (float)
            -- date (timestamp)
            -- success (bool)
       - override (bool): if True, will override existing entries

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Prep 
    obs_tbl = pandas.read_json(data['table'])

    # Run
    code, msg = frb_observing.ingest_obslog(obs_tbl, user,
                                            override=data['override'])

    # Return
    return JsonResponse({"message":f"{msg}"}, status=code)


@csrf_exempt
@login_or_basic_auth_required
def add_frb_followup_resource(request):
    """ Add an FRBFollowUpResource to the DB from an 
    outside request

    This is mainly intended for recovering from a "problem"

    Args:
        request (_type_): _description_

    Returns:
        JsonResponse: _description_
    """
    
    data = JSONParser().parse(request)

    # Authenticate
    # TODO -- SHOULD RESTRICT TO ADMIN
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Use Serializer
    serializer = FRBFollowUpResourceSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        print(f"Generated FRBFollowUpResource: {data['name']}")
    else:
        return JsonResponse('Not valid!', status=401)

    return JsonResponse('Success!', status=201)


@csrf_exempt
@login_or_basic_auth_required
def ingest_z(request):
    """
    Ingest a table of Redshifts

    For now, these are spectroscopic only

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

      - table (str): a table of the request with columns 
            TNS (str) -- TNS of the FRB that has this galaxy as its preferred host
            Galaxy (str) -- JNAME *matching* that in FFFF-PZ
            Resource (str) -- Name of the FRB Followup Resource
            Redshift (float) -- Redshift of the galaxy 
            Quality (int) -- Quality of the redshift 

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Prep
    z_tbl = pandas.read_json(data['table'])

    # Run
    code, msg = frb_observing.ingest_z(z_tbl)

    # Return
    return JsonResponse({"message":f"{msg}"}, status=code)

@csrf_exempt
@login_or_basic_auth_required
def ingest_frbs(request):
    """
    Ingest a table of FRBs

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

      - table (str): a table of the request with columns 
            TNS (str) -- TNS of the FRB 
            frb_survey (str) -- TNS of the FRB 
            ra (float) -- RA of the FRB (centroid) [deg]
            dec (float) -- Dec of the FRB (centroid) [deg]
            a_err (float) -- Semi-major localization error of the FRB [deg]
            b_err (float) -- Semi-minor localization error of the FRB [deg]
            theta (float) -- Position angle of the FRB; E from N [deg]
            DM (float) -- Dispersion Measure of the FRB
            tags (str, optional) -- Tag(s) for the FRB.  comma separated
      - delete (bool): Delete FRBs first?

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Prep
    frb_tbl = pandas.read_json(data['table'])

    # Run
    code, msg = frb_init.add_df_to_db(frb_tbl, user,
                                      delete_existing=data['delete'])

    # Return
    return JsonResponse({"message":f"{msg}"}, status=code)

@csrf_exempt
@login_or_basic_auth_required
def addmodify_criteria(request):
    """
    Add or modify a set of criteria for
    one of the FRB samples

    The request must include the following items
     in its data (all in JSON, of course; 
     data types are for after parsing the JSON):

    - All of the required properties for the FRBSelectionCriteria
        model

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Run
    code, msg = frb_utils.addmodify_obj(FRBSampleCriteria, data, user)

    # Return
    return JsonResponse({"message":f"{msg}"}, status=code)

@csrf_exempt
@login_or_basic_auth_required
def rm_frb(request):
    """ Remove an FRBTransient from the DB
    via an outside request

    Input data includes:
        - name (str): TNS Name of the FRBTransient

    Args:
        request (_type_): _description_

    Returns:
        JsonResponse: _description_
    """
    
    data = JSONParser().parse(request)

    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)

    # Check on root
    if username != 'root':
        msg = 'Not authorized!'
        return JsonResponse({"message":f"m{msg}"}, status=401)
    user = auth.authenticate(username=username, password=password)

    # Grab it
    try:
        obj = FRBTransient.objects.get(name=data['name'])
    except ObjectDoesNotExist:
        msg = "FRB does not exist!"
        return JsonResponse({"message":f"m{msg}"}, status=202)
    else:
        obj.delete()
        print(f"Deleted {data['name']}")

    msg = 'FRB removed!'
    return JsonResponse({"message":f"m{msg}"}, status=200)

@csrf_exempt
@login_or_basic_auth_required
def frb_update_status(request):
    """
    Update the status for one or more FRBs

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse: 
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    username, password = credentials.split(':', 1)
    user = auth.authenticate(username=username, password=password)

    # Run
    for name in data['names']:
        print(f"Working on status of: {name}")
        # Grab the FRB
        try:
            frb=FRBTransient.objects.get(name=name)
        except ObjectDoesNotExist:
            return JsonResponse({"message": f'FRB {name} not in DB'}, status=401)
        frb_status.set_status(frb)

    # Return
    return JsonResponse({"message": "All good!"}, status=200)


@csrf_exempt
@login_or_basic_auth_required
def get_frb_table(request):
    """
    Grab and return a table of all FRBs in FFFF-PZ

    The request must include the following items
     in its data (all in JSON, of course; 
     data types refer to those after parsing the JSON):

    Args:
        request (requests.request): 
            Request from outside FFFF-PZ

    Returns:
        JsonResponse:  Table of information
    """
    
    # Parse the data into a dict
    data = JSONParser().parse(request)

    # Deal with credentials
    try:
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    except:
        return JsonResponse({"message":f"Bad user authentication in DB"}, status=401)

    # Grab
    frbs = frb_tables.summary_table()
    
    # Return
    return JsonResponse(frbs.to_dict(), status=201)