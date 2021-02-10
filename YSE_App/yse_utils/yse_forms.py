import os,pdb,json,datetime,time,string, random
import numpy as np
from django import forms
from YSE_App.models import *
from django.forms import ModelForm
from django.views.generic import FormView, DeleteView
from astropy.time import Time
from django.http import JsonResponse

# form for adjusting the FOV/pointing
class CoordForm(forms.ModelForm):

    class Meta:
        model = CanvasFOV
        fields = ('raCenter','decCenter','fovWidth',)

class YSEMoveFieldsForm(ModelForm):

    targeted_transients = forms.CharField(required=False,max_length=500)
    ra_str = forms.CharField(max_length=100)
    dec_str = forms.CharField(max_length=100)
    
    class Meta:
        model = SurveyField
        fields = ['field_id',
            'targeted_galaxies']

class MoveYSEFormView(FormView):
    form_class = YSEMoveFieldsForm
    template_name = 'YSE_App/form_snippets/YSE_move_field_form.html'
    success_url = '/form-success/'
    
    def form_invalid(self, form):
        response = super(MoveYSEFormView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(MoveYSEFormView, self).form_valid(form)
        if self.request.is_ajax():

            orig_id = form.cleaned_data['field_id']
            new_field_id = orig_id + '.' + str(int(Time.now().mjd))

            # look for existing instance, and overwrite as needed
            # though tbh duplicate field should take care of some of this too
            instance = SurveyField.objects.filter(field_id=new_field_id)
            if len(instance):
                instance = instance[0]
            else:
                instance = SurveyField()
            instance.field_id = new_field_id

            instance.created_by = self.request.user
            instance.modified_by = self.request.user
            try:
                float(form.cleaned_data['ra_str'])
                float(form.cleaned_data['dec_str'])
                instance.ra_cen = float(form.cleaned_data['ra_str'])
                instance.dec_cen = float(form.cleaned_data['dec_str'])
            except:
                sc = SkyCoord(form.cleaned_data['ra_str'],form.cleaned_data['dec_str'],unit=(u.hour,u.deg))
                instance.ra_cen = sc.ra.deg
                instance.dec_cen = sc.dec.deg
            instance.targeted_galaxies = form.cleaned_data['targeted_galaxies']
            instance.obs_group = ObservationGroup.objects.get(name='YSE')
            instance.width_deg = 3.1
            instance.height_deg = 3.1
            instance.instrument = Instrument.objects.get(name='GPC1')

            # does field already exist?
            sfmatch = SurveyField.objects.filter(Q(ra_cen__gt=instance.ra_cen-0.003) & Q(ra_cen__lt=instance.ra_cen+0.003) &
                                            Q(dec_cen__gt=instance.dec_cen-0.003) & Q(dec_cen__lt=instance.dec_cen+0.003))
            msb = SurveyFieldMSB.objects.filter(name=form.cleaned_data['field_id'].split('.')[0])

            if not len(msb):
                data = {
                    'data':{'warning':"Error : can't find MSB for field %s"%instance.field_id,
                            'email_text':''},
                    'message': "",
                }
                return JsonResponse(data)

            if len(sfmatch):
                if sfmatch in msb[0].survey_fields.all():
                    message = "Survey Field already exists with RA,Dec near (%.7f,%.7f) and is in the MSB for field %s. "%(
                        instance.ra_cen,instance.dec_cen,msb[0].name)
                else:
                    message = "Survey Field already exists with RA,Dec near (%.7f,%.7f) and is not yet in the MSB for field %s. "%(
                        instance.ra_cen,instance.dec_cen,msb[0].name)

                data = {
                    'data':{'warning':message,
                            'email_text':"""Dear Angie,

    We would like to please move field %s to the coordinates RA,Dec = %.7f,%.7f.  

    Thanks very much."""%(
        instance.field_id,instance.ra_cen,instance.dec_cen)},
                        'message': "",
                    }
                return JsonResponse(data)

            # check for overlapping fields
            sfcollide = SurveyField.objects.filter(Q(ra_cen__gt=instance.ra_cen/np.abs(np.cos(instance.dec_cen*np.pi/180))-1.55) &
                                                   Q(ra_cen__lt=instance.ra_cen/np.abs(np.cos(instance.dec_cen*np.pi/180))+1.55) &
                                                   Q(dec_cen__gt=instance.dec_cen-1.55) & Q(dec_cen__lt=instance.dec_cen+1.55))
            warning = ""
            if len(sfcollide):
                for sfc in sfcollide:
                    msbmatch = SurveyFieldMSB.objects.get(name=sfc.field_id.split('.')[0])
                    msbsf = msbmatch.survey_fields.filter(field_id=sfc.field_id)
                    if len(msbsf):
                        warning += "Possible colliding field with ID %s, currently in MSB %s\n"%(msbsf[0].field_id,msbmatch.name)

            instance.save()

            # add many-to-many data for targeted transients
            if form.cleaned_data['targeted_transients']:
                for transient_id in form.cleaned_data['targeted_transients'].split(','):
                    instance.targeted_transients.add(Transient.objects.get(pk=transient_id))




            #check if field is in a potentially bad location
            osf = SurveyField.objects.get(field_id=orig_id)
            sc = SkyCoord(instance.ra_cen,instance.dec_cen,unit=u.deg)
            osc = SkyCoord(osf.ra_cen,osf.dec_cen,unit=u.deg)
            if sc.separation(osc).deg > 15:
                warning = "warning : new field is more than 15 deg from old field!\n"
            else:
                warning + ""

            # remove old field from MSB, associate new one with MSB                
            msb = msb[0]                
            msbsf = msb.survey_fields.filter(field_id__startswith=orig_id)
            if len(msbsf):
                for msf in msbsf: msb.survey_fields.remove(msf)
            msb.survey_fields.add(instance)
            if len(msb.survey_fields.all()) > 6: warning = warning + "warning : more than 6 survey fields are part of this MSB!"

            #print(form.cleaned_data)

            # for key,value in form.cleaned_data.items():
            data_dict = {}
            data_dict['warning'] = warning
            data_dict['field_id'] = instance.field_id
            data_dict['ra'] = instance.ra_cen
            data_dict['dec'] = instance.dec_cen
            data_dict['email_text'] = """Dear Angie,

    We would like to please move field %s to the coordinates RA,Dec = %.7f,%.7f.  

    Thanks very much."""%(
        orig_id,instance.ra_cen,instance.dec_cen)

            data = {
                'data':data_dict,
                'message': "Successfully submitted form data.",
            }
            return JsonResponse(data)
