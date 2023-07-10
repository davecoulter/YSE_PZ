""" Testing a simple read of CSV """
import sys
import dateutil
import datetime

import pandas

from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.db.models import ForeignKey
from django.db.models import Q

from .basicauth import login_or_basic_auth_required
from .models import Transient
from .common.utilities import getRADecBox

from IPython import embed

@csrf_exempt
@login_or_basic_auth_required
def add_transient(csv_file:str):
    # Load up the table
    df_frbs = pandas.read_csv(csv_file)

    #auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    #credentials = base64.b64decode(credentials.strip()).decode('utf-8')
    #username, password = credentials.split(':', 1)
    #user = auth.authenticate(username=username, password=password)
    user = auth.authenticate(username='root', password='F4isthebest')

    '''
    # ready to send error emails
    smtpserver = "%s:%s" % (djangoSettings.SMTP_HOST, djangoSettings.SMTP_PORT)
    from_addr = "%s@gmail.com" % djangoSettings.SMTP_LOGIN
    subject = "TNS Transient Upload Failure"
    txt_msg = "Alert : YSE_PZ Failed to upload transient %s "
    '''

    transient_entries = []
    # first bulk create new transients
    for ss in range(len(df_frbs)):

        transient = df_frbs.iloc[ss]

        transientkeys = transient.keys()
        if 'Name' not in transientkeys:
            return_dict = {"message":"Error : Transient name not provided for transient %s!"%transientlistkey}
            #return JsonResponse(return_dict)
            raise ValueError(return_dict)
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
                        raise ValueError(html_msg)
                        #sendemail(from_addr, user.email, subject,
                        #          html_msg%(transient['name'],transient[transientkey],transientkey),
                        #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

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
                    raise ValueError("Should not have been in DB!!")
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
                    embed(header='add transient')
                    dbtransient = Transient(**transientdict)

                    transient_entries += [dbtransient]
                    #dbtransient = Transient.objects.create(**transientdict)
            else: #if clobber:
                raise ValueError("Should not have been in DB!!")
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

            #sendemail(from_addr, user.email, subject, html_msg%(transient['name'],e,exc_tb.tb_lineno),
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)
            # sending SMS is too scary for now
            #sendsms(from_addr, phone_email, subject, txt_msg%transient['name'],
            #        djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)

if __name__ == '__main__':
    add_transient('chime_test.csv')