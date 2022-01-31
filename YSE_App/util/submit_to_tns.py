from YSE_App.models import *
import json
from YSE_App.common.utilities import GetSexigesimalString
from django.db.models import FloatField,ExpressionWrapper, F, Q
from YSE_App.util import tnsAPI
from django.conf import settings as djangoSettings
from django.http import JsonResponse

_author_list = "DECAT/YSE Team: A. Rest (JHU, STScI), A. Agnello, C. R. Angus, Z. Ansari, N. Arendse, C. Gall, C. Grillo, S. H. Bruun, C. Hede, J. Hjorth, L. Izzo, H. Korhonen, S. Raimundo, D. Kodi Ramanah, A. Sarangi, R. Wojtak, H. Pfister (DARK, U Copenhagen), K. Auchettl (DARK, UC Santa Cruz, U Melbourne), K. C. Chambers, M. E. Huber, E. A. Magnier, T. J. L. de Boer, J. R. Fairlamb, C. C. Lin, R. J. Wainscoat, T. Lowe, M. Willman, J. Bulger, A. S. B. Schultz (IfA, Hawaii), N. Earl, A. Engel, K. D. French, A. Gagliano, G. Narayan, M. Soraisam (Illinois), R. Angulo, Q. Wang (JHU), F. Valdes, A. Zenteno (NOIRLab), S. J. Smartt, K. W. Smith (Queen's University Belfast), K. Alexander, P. Blanchard, L. DeMarchi, A. Hajela, C. D. Kilpatrick, C. Stauffer, M. Stroh (Northwestern U.), W. Jacobson-Galán, R. Margutti, D. Matthews (UC Berkeley), S. Gomez, J. Pierel, R. Ridden-Harper, L. Strolger (STScI), M. Drout (U Toronto), D. A. Coulter, G. Dimitriadis, R. J. Foley, D. Jones, T. Hung, C. Rojas-Bravo, M. R. Siebert (UC Santa Cruz), E. Ramirez-Ruiz (UC Santa Cruz, DARK)"

_groupid = '83'

_json_template = {
  "at_report": {
    "0": {
      "ra": {
        "value": "10:20:30.0",
        "error": "0.5",
        "units": "arcsec"
      },
      "dec": {
        "value": "+20:30:40.05",
        "error": "0.5",
        "units": "arcsec"
      },
      "groupid": "1",
      "reporter": "J. Smith, on behalf of SurveyName...",
      "discovery_datetime": "2016-03-01.234",
      "at_type": "1",
      "host_name": "NGC 1234",
      "host_redshift": "",
      "transient_redshift": "",
      "internal_name": "",
      "remarks": "",
      "proprietary_period_groups": [],
      "proprietary_period": {
        "proprietary_period_value": "0",
        "proprietary_period_units": "days"
      },
      "non_detection": {
        "obsdate": "2016-02-28.123",
        "limiting_flux": "21.5",
        "flux_units": "1",
        "filter_value": "50",
        "instrument_value": "103",
        "exptime": "60",
        "observer": "Robot",
        "comments": "",
        "archiveid": "",
        "archival_remarks": ""
      },
      "photometry": {
        "photometry_group": {
          "0": {
            "obsdate": "2016-03-01.234",
            "flux": "19.5",
            "flux_error": "0.2",
            "limiting_flux": "",
            "flux_units": "1",
            "filter_value": "50",
            "instrument_value": "103",
            "exptime": "60",
            "observer": "Robot",
            "comments": ""
          }
        }
      },
      "related_files": {
        "0": {
          "related_file_name": "",
          "related_file_comments": ""
        }
      }
    }
  }
}

tns_filt_ids = {'g':21,'r':22,'i':23,'z':24}

def submit_to_tns(request,transient_name):

    t = Transient.objects.get(name=transient_name)

    # to submit, we need to get:
    # discovery date
    # can this just be the first 5-sigma detection?
    tp = TransientPhotData.objects.filter(photometry__transient=t).filter(photometry__instrument__name='DECam')
    tp = tp.annotate(snr=ExpressionWrapper(F('flux')/F('flux_err'),output_field=FloatField()))
    tp_det = tp.filter(snr__gt=5).order_by('obs_date')
    
    disc_data = tp_det[0]
    disc_date = tp_det[0].obs_date
    
    # two photometric points nearest to the discovery date
    # (and some assurance that they aren't crazy?  or at least not negative)
    tp_seconddisc = tp_det.filter(Q(obs_date__gt=disc_date-datetime.timedelta(0.2)) &
                                  Q(obs_date__lt=disc_date+datetime.timedelta(0.2)) &
                                  ~Q(id=disc_data.id))
                
    # non-detection if possible
    tp_nondet = tp.filter(snr__lt=3).filter(obs_date__lt=disc_date).order_by('-obs_date')


    # host info
    if t.host is not None:
        host_name = t.host.name
        host_z = t.host.redshift
    else:
        host_name = None; host_z = None
    
    # sensible internal name??

    # now let's throw all this in to the template
    json_tmpl = _json_template.copy()

    ra_str,dec_str = GetSexigesimalString(t.ra,t.dec)
    json_tmpl['at_report']["0"]["ra"]["value"] = ra_str
    json_tmpl['at_report']["0"]["dec"]["value"] = dec_str
    json_tmpl['at_report']["0"]["groupid"] = _groupid
    json_tmpl['at_report']["0"]["reporter"] = _author_list

    decimal_date = disc_date.hour/24.+disc_date.minute/60./24.+disc_date.second/60./60./24.
    json_tmpl['at_report']["0"]["discovery_datetime"] = f"{disc_date.strftime('%Y-%m-%d')}.{decimal_date*1000:.0f}"

    if host_name is not None:
        json_tmpl['at_report']["0"]["host_name"] = host_name
    else:
        json_tmpl['at_report']["0"]["host_name"] = ""
    if host_z is not None:
        json_tmpl['at_report']["0"]["host_redshift"] = host_z
    else:
        json_tmpl['at_report']["0"]["host_redshift"] = ""

    if len(tp_nondet):
        mag_lim = -2.5*np.log10(tp_nondet[0].flux + 3*tp_nondet[0].flux_err) + 27.5
        if mag_lim == mag_lim and tp_nondet[0].flux + 3*tp_nondet[0].flux_err > 0:

            decimal_date = tp_nondet[0].obs_date.hour/24.+tp_nondet[0].obs_date.minute/60./24.+tp_nondet[0].obs_date.second/60./60./24.
            date_str = f"{tp_nondet[0].obs_date.strftime('%Y-%m-%d')}.{decimal_date*1000:.0f}"

            json_tmpl['at_report']['0']["non_detection"] = {
                "obsdate": date_str,
                "limiting_flux": f"{mag_lim:.1f}",
                "flux_units": "1",
                "filter_value": tns_filt_ids[tp_nondet[0].band.name],
                "instrument_value": "87",
                "exptime": "50", # hard-coded
                "observer": "DECAT/YSE Team",
                "comments": "",
                "archiveid": "",
                "archival_remarks": ""
            }
        else:
            json_tmpl['at_report']['0']["non_detection"] = \
                {"archiveid": "0",
                 "archival_remarks": "DECam"}
    else:
        json_tmpl['at_report']['0']["non_detection"] = \
            {"archiveid": "0",
             "archival_remarks": "DECam"}


    # disc data
    decimal_date = tp_det[0].obs_date.hour/24.+tp_det[0].obs_date.minute/60./24.+tp_det[0].obs_date.second/60./60./24.
    date_str = f"{tp_det[0].obs_date.strftime('%Y-%m-%d')}.{decimal_date*1000:.0f}"
    
    json_tmpl['at_report']['0']['photometry']['photometry_group']['0'] = \
         {"obsdate": date_str,
         "flux": f"{tp_det[0].mag:.3f}",
         "flux_error": f"{tp_det[0].mag_err:.3f}",
         "limiting_flux": "",
         "flux_units": "1",
         "filter_value": tns_filt_ids[tp_det[0].band.name],
         "instrument_value": "87",
         "exptime": "50",
         "observer": "DECAT/YSE Team",
         "comments": ""
          }
        
    if len(tp_seconddisc) == 1:
        # add this to the dictionary
        decimal_date = tp_seconddisc[0].obs_date.hour/24.+tp_seconddisc[0].obs_date.minute/60./24.+tp_seconddisc[0].obs_date.second/60./60./24.
        date_str = f"{tp_seconddisc[0].obs_date.strftime('%Y-%m-%d')}.{decimal_date*1000:.0f}"

        json_tmpl['at_report']['0']['photometry']['photometry_group']['1'] = \
            {"obsdate": date_str,
             "flux": f"{tp_seconddisc[0].mag:.3f}",
             "flux_error": f"{tp_seconddisc[0].mag_err:.3f}",
             "limiting_flux": "",
             "flux_units": "1",
             "filter_value": tns_filt_ids[tp_seconddisc[0].band.name],
             "instrument_value": "87",
             "exptime": "50",
             "observer": "DECAT/YSE Team",
             "comments": ""
             }

    # send to TNS
    response = tnsAPI.main(djangoSettings.TNSAPIKEY,djangoSettings.TNSID,djangoSettings.TNSUSER,json_tmpl)

    if 'id_code' in response.keys() and response['id_code'] == 200:
        success = True
        at_key = list(response['data']['feedback']['at_report'][0].keys())[0]
        obj_name = response['data']['feedback']['at_report'][0][at_key]['objname']
    else:
        success = False
        message = response.copy()
        

    if success:
        old_name = t.name

        t_qs = Transient.objects.filter(name=obj_name)
        if len(t_qs):
            # if we uploaded a DECam candidate that already has a TNS ID, we need to proceed with caution
            t_existing = t_qs[0]

            # let's add the DECam photometry to the old object, and then delete the new one
            # we'll still create the AlternateTransientName below
            tp_header = TransientPhotometry.objects.filter(transient=t).filter(instrument__name='DECam')
            for tps in tp_header:
                tps.transient = t_existing
                tps.save()
            t.delete()
            t = t_existing
        else:
            t.name = obj_name
            t.slug = obj_name
            t.save()
            
        # just to make sure
        alt_qs = AlternateTransientNames.objects.filter(name=old_name)
        if not len(alt_qs):
            user = request.user
            obsgroup = ObservationGroup.objects.get(name='DECAT')
            alt = AlternateTransientNames.objects.create(name=old_name,transient=t,obs_group=obsgroup,
                                                         created_by_id=user.id,modified_by_id=user.id)

            t.save()

        context = {'msg':f'success!  This SN is now called: {obj_name}'}
    else:
        context = {'msg':str(message),
                   'new_id':None}

    return JsonResponse(context)
