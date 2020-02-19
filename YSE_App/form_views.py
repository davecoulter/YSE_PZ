from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse_lazy
import requests
import sys
from datetime import datetime
import re
from astroplan import moon_illumination
from astropy.time import Time

from .models import *
# from .forms import *
from .common import utilities
import json

from django.views.generic import FormView, DeleteView
from .forms import *
from django.http import JsonResponse
from django.forms.models import model_to_dict
from .common import alert
from .common.utilities import date_to_mjd, coordstr_to_decimal
import numpy as np
from django.views.decorators.csrf import csrf_exempt
from .basicauth import *

class AddTransientFollowupFormView(FormView):
	form_class = TransientFollowupForm
	template_name = 'YSE_App/form_snippets/transient_followup_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddTransientFollowupFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddTransientFollowupFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			if instance.classical_resource:
				instance.valid_start = instance.classical_resource.begin_date_valid
				instance.valid_stop = instance.classical_resource.end_date_valid
				
			instance.save() #update_fields=['created_by','modified_by']

			if instance.transient.status.name in ['New','Watch','Ignore']:
				instance.transient.status = TransientStatus.objects.filter(name='FollowupRequested')[0]
				instance.transient.save()
			
			if form.cleaned_data['comment']:
				log = Log(transient_followup=TransientFollowup.objects.get(id=instance.id),
						  comment=form.cleaned_data['comment'])
				log.created_by = self.request.user
				log.modified_by = self.request.user
				log.save()
			
			print(form.cleaned_data)

			# for key,value in form.cleaned_data.items():
			data_dict = {}
			data_dict['id'] = instance.id
			data_dict['status_id'] = instance.status.id
			data_dict['status_name'] = instance.status.name
			if instance.too_resource:
				data_dict['too_resource'] = str(instance.too_resource)
			if instance.classical_resource:
				data_dict['classical_resource'] = str(instance.classical_resource)
			if instance.queued_resource:
				data_dict['queued_resource'] = str(instance.queued_resource)

			if instance.classical_resource:
				data_dict['valid_start'] = instance.classical_resource.begin_date_valid
				data_dict['valid_stop'] = instance.classical_resource.end_date_valid
			else:
				data_dict['valid_start'] = form.cleaned_data['valid_start']
				data_dict['valid_stop'] = form.cleaned_data['valid_stop']

			data_dict['spec_priority'] = form.cleaned_data['spec_priority']
			data_dict['phot_priority'] = form.cleaned_data['phot_priority']
			data_dict['offset_star_ra'] = form.cleaned_data['offset_star_ra']
			data_dict['offset_star_dec'] = form.cleaned_data['offset_star_dec']
			data_dict['offset_north'] = form.cleaned_data['offset_north']
			data_dict['offset_east'] = form.cleaned_data['offset_east']
			data_dict['comment'] = form.cleaned_data['comment']
			
			data_dict['modified_by'] = instance.modified_by.username

			data = {
				'data':data_dict,
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

class AddClassicalResourceFormView(FormView):
	form_class = ClassicalResourceForm
	template_name = 'YSE_App/form_snippets/classical_resource_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddClassicalResourceFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddClassicalResourceFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			instance.begin_date_valid = form.cleaned_data['observing_date']
			instance.end_date_valid = form.cleaned_data['observing_date'] + datetime.timedelta(1)
			
			instance.save() #update_fields=['created_by','modified_by']
			instance.groups.set(Group.objects.filter(name='YSE'))
			instance.save()


			obsdatedict = {'created_by':self.request.user,'modified_by':self.request.user,
						   'resource':instance,'night_type':ClassicalNightType.objects.filter(name='Full')[0],
						   'obs_date':form.cleaned_data['observing_date']}
			ClassicalObservingDate.objects.create(**obsdatedict)
			
			print(form.cleaned_data)

			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

class AddToOResourceFormView(FormView):
	form_class = ToOResourceForm
	template_name = 'YSE_App/form_snippets/classical_resource_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddToOResourceFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddToOResourceFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			
			instance.save() #update_fields=['created_by','modified_by']

			print(form.cleaned_data)

			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response
		
		
class AddTransientObservationTaskFormView(FormView):
	form_class = TransientObservationTaskForm
	template_name = 'YSE_App/form_snippets/transient_observation_task_form.html'
	success_url = '/form-success/'

	def form_invalid(self, form):
		response = super(AddTransientObservationTaskFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddTransientObservationTaskFormView, self).form_valid(form)
		if self.request.is_ajax():
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by =self.request.user
			instance.save()

			print(form.cleaned_data)

			data_dict = {}
			data_dict['id'] = instance.id
			data_dict['status_id'] = instance.status.id
			data_dict['status_name'] = instance.status.name
			data_dict['instrument_config'] = str(instance.instrument_config)

			config_eles = instance.instrument_config.configelement_set.all()
			config_string = "<ul>"
			for ce in config_eles:
				config_string += ("<li>" + ce.name + "</li>")
			config_string += "</ul>"
			data_dict['config_eles'] = config_string

			data_dict['instrument_config'] = str(instance.instrument_config)

			data_dict['exposure_time'] = form.cleaned_data['exposure_time']
			data_dict['number_of_exposures'] = form.cleaned_data['number_of_exposures']
			data_dict['desired_obs_date'] = form.cleaned_data['desired_obs_date']
			data_dict['actual_obs_date'] = form.cleaned_data['actual_obs_date']
			data_dict['description'] = form.cleaned_data['description']
			
			# Related fields...
			data_dict['observatory'] = instance.instrument_config.instrument.telescope.observatory.name
			data_dict['telescope'] = instance.instrument_config.instrument.telescope.name
			data_dict['instrument'] = instance.instrument_config.instrument.name
			data_dict['modified_by'] = instance.modified_by.username

			data = {
				'message': "Successfully submitted form data.",
				'data': data_dict
			}
			return JsonResponse(data)
		else:
			return response

class AddSurveyFieldFormView(FormView):
	form_class = SurveyFieldForm
	template_name = 'YSE_App/form_snippets/survey_field_form.html'
	success_url = '/form-success/'

	def form_invalid(self, form):
		response = super(AddSurveyFieldFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddSurveyFieldFormView, self).form_valid(form)
		if self.request.is_ajax():
			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			instance.obs_group = ObservationGroup.objects.get(name='YSE')
			instance.width_deg = 3.3
			instance.height_deg = 3.3
			instance.first_mjd = date_to_mjd(form.cleaned_data['valid_start'])
			instance.last_mjd = date_to_mjd(form.cleaned_data['valid_stop'])
			instance.ra_cen,instance.dec_cen = coordstr_to_decimal(
				form.cleaned_data['coord'])
			
			instance.save() #update_fields=['created_by','modified_by']

			print(form.cleaned_data)

			# clear out the conflicting SurveyObservationTasks
			# danger!
			obs_requests = SurveyObservation.objects.\
						   filter(survey_field__field_id=instance.field_id).\
						   filter(mjd_requested__range=(instance.first_mjd,
														instance.last_mjd))
			obs_requests.delete()
			
			# use the SurveyField to populate the SurveyObservationTask list
			# rules: follow cad
			#import pdb; pdb.set_trace()
			mjd = np.arange(instance.first_mjd,instance.last_mjd,instance.cadence)
			#if len(mjd) > 1: import pdb; pdb.set_trace()
			for i,m in enumerate(mjd):
				t = Time(m,format='mjd')
				illum = moon_illumination(t)
				if illum < 0.33:
					if i % 2: band1name,band2name = 'g','r'
					else: band1name,band2name = 'g','i'
				elif illum < 0.66:
					if i % 2: band1name,band2name = 'g','i'
					else: band1name,band2name = 'g','z'
				else:
					if i % 2: band1name,band2name = 'r','i'
					else: band1name,band2name = 'r','z'
					
				band1 = PhotometricBand.objects.filter(
					name=band1name,instrument__name=instance.instrument.name)[0]
				band2 = PhotometricBand.objects.filter(
					name=band2name,instrument__name=instance.instrument.name)[0]
				SurveyObservation.objects.create(
					mjd_requested=m,
					survey_field=instance,
					status=TaskStatus.objects.get(name='Requested'),
					exposure_time=27,
					photometric_band=band1,
					created_by=self.request.user,
					modified_by=self.request.user)
				SurveyObservation.objects.create(
					mjd_requested=m,
					survey_field=instance,
					status=TaskStatus.objects.get(name='Requested'),
					exposure_time=27,
					photometric_band=band2,
					created_by=self.request.user,
					modified_by=self.request.user)

			# for key,value in form.cleaned_data.items():
			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

class AddSurveyObsFormView(FormView):
	form_class = SurveyObsForm
	template_name = 'YSE_App/form_snippets/survey_obs_form.html'
	success_url = '/form-success/'

	@csrf_exempt
	@login_or_basic_auth_required
	def dispatch(self, request, *args, **kwargs):

		if not self.request.is_ajax():
			auth_method, credentials = self.request.META['HTTP_AUTHORIZATION'].split(' ', 1)
			credentials = base64.b64decode(credentials.strip()).decode('utf-8')
			username, password = credentials.split(':', 1)
			self.request.user = auth.authenticate(username=username, password=password)
		
		return super(AddSurveyObsFormView, self).dispatch(request, *args, **kwargs)
	
	def form_invalid(self, form):
		response = super(AddSurveyObsFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddSurveyObsFormView, self).form_valid(form)
		if 'hi': #self.request.is_ajax():
			instance = form.save(commit=False)

			telescope = Telescope.objects.get(name='Pan-STARRS1')
			location = EarthLocation.from_geodetic(
				telescope.longitude*u.deg,telescope.latitude*u.deg,
				telescope.elevation*u.m)
			tel = Observer(location=location, timezone="US/Hawaii")
			
			m = date_to_mjd(form.cleaned_data['survey_obs_date'])
			time = Time(m,format='mjd')
			sunset_forobs = mjd_to_date(tel.sun_set_time(time,which="next"))
			survey_field_blocks = SurveyFieldMSB.objects.filter(name__in=form.cleaned_data['ztf_field_id'])
			#survey_field = SurveyField.objects.filter(ztf_field_id__in=form.cleaned_data['ztf_field_id'])
			for sb in survey_field_blocks:
				for s in sb.survey_fields.all():
					t = Time(m,format='mjd')
					illum = moon_illumination(t)

					# need to see what was observed in the previous obs w/ the same moon illumination
					previous_obs = SurveyObservation.objects.filter(survey_field=s).\
						filter(Q(obs_mjd__lt=m) | Q(mjd_requested__lt=m)).order_by('-obs_mjd').\
						order_by('-mjd_requested').select_related()

					def previous_obs_func(illum_min,illum_max):
						filt = []
						for p in previous_obs:
							if p.obs_mjd: mjd_prev = p.obs_mjd
							elif p.mjd_requested: mjd_prev = p.mjd_requested
							t_prev = Time(mjd_prev,format='mjd')
							illum_prev = moon_illumination(t_prev)
							if illum_prev >= illum_min and illum_prev <= illum_max:
								filt += [p.photometric_band.name]
							if len(filt) == 2: return filt
						return None

					if s.field_id.lower().startswith('virgo'):
						if illum < 0.66:
							filt = previous_obs_func(0,0.66)
							if filt is None: band1name,band2name = 'g','r'
							elif 'r' in filt: band1name,band2name = 'g','i'
							elif 'i' in filt: band1name,band2name = 'g','z'
							else: band1name,band2name = 'g','r'
						else:
							filt = previous_obs_func(0.66,1)
							if filt is None or 'z' in filt: band1name,band2name = 'r','i'
							else: band1name,band2name = 'r','z'
					else:
						if illum < 0.33:
							filt = previous_obs_func(0,0.33)
							if filt is None or 'i' in filt: band1name,band2name = 'g','r'
							else: band1name,band2name = 'g','i'
						elif illum < 0.66:
							filt = previous_obs_func(0.33,0.66)
							if filt is None or 'z' in filt: band1name,band2name = 'g','i'
							else: band1name,band2name = 'g','z'
						else:
							filt = previous_obs_func(0.66,1)
							if filt is None or 'z' in filt: band1name,band2name = 'r','i'
							else: band1name,band2name = 'r','z'

					band1 = PhotometricBand.objects.filter(
						name=band1name,instrument__name=s.instrument.name)[0]
					band2 = PhotometricBand.objects.filter(
						name=band2name,instrument__name=s.instrument.name)[0]

					SurveyObservation.objects.create(
						mjd_requested=date_to_mjd(sunset_forobs),
						survey_field=s,
						status=TaskStatus.objects.get(name='Requested'),
						exposure_time=27,
						photometric_band=band1,
						created_by=self.request.user,
						modified_by=self.request.user)
					SurveyObservation.objects.create(
						mjd_requested=date_to_mjd(sunset_forobs),
						survey_field=s,
						status=TaskStatus.objects.get(name='Requested'),
						exposure_time=27,
						photometric_band=band2,
						created_by=self.request.user,
						modified_by=self.request.user)

			# for key,value in form.cleaned_data.items():
			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

		
class AddOncallUserFormView(FormView):
	form_class = OncallForm
	template_name = 'YSE_App/form_snippets/oncall_form.html'
	success_url = '/form-success/'

	def form_invalid(self, form):
		response = super(AddOncallUserFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddOncallUserFormView, self).form_valid(form)
		if self.request.is_ajax():
			instance = form.save(commit=False)
			#instance.created_by = self.request.user
			#instance.modified_by = self.request.user
			#instance.obs_group = ObservationGroup.objects.get(name='YSE')
			#instance.width_deg = 3.3
			#instance.height_deg = 3.3
			first_mjd = date_to_mjd(form.cleaned_data['valid_start'])
			last_mjd = date_to_mjd(form.cleaned_data['valid_stop'])
			#instance.ra_cen,instance.dec_cen = coordstr_to_decimal(
			#	form.cleaned_data['coord'])
			
			#instance.save() #update_fields=['created_by','modified_by']

			#print(form.cleaned_data)

			# clear out the conflicting SurveyObservationTasks
			# danger!
			#obs_requests = SurveyObservation.objects.\
			#			   filter(survey_field__id=instance.field_id).\
			#			   filter(mjd_requested__range=(instance.first_mjd,
			#											instance.last_mjd))
			#obs_requests.delete()
			
			# use the SurveyField to populate the SurveyObservationTask list
			# rules: follow cad
			#import pdb; pdb.set_trace()
			mjd = np.arange(first_mjd,last_mjd,1)
			for i,m in enumerate(mjd):
				t = Time(m,format='mjd')
				yse_date = YSEOnCallDate.objects.filter(on_call_date='%s 00:00:00'%t.iso.split()[0])
				if not len(yse_date):
					yse_date = YSEOnCallDate.objects.create(
						created_by=self.request.user,
						modified_by=self.request.user,
						on_call_date='%s 00:00:00'%t.iso.split()[0])
				else:
					yse_date = yse_date[0]
				yse_date.user.add(form.cleaned_data['user'])
				yse_date.save()
				
			# for key,value in form.cleaned_data.items():
			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
	
		else:
			return response

		
class AddTransientCommentFormView(FormView):
	form_class = TransientCommentForm
	template_name = 'simple.html'#YSE_App/form_snippets/transient_followup_form.html'
	success_url = '/form-success/'

	def form_invalid(self, form):
		response = super(AddTransientCommentFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddTransientCommentFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			
			instance.save() #update_fields=['created_by','modified_by']
			print(form.cleaned_data)

			# send emails to everyone else on the comments thread
			logs = Log.objects.filter(transient=instance.transient.id)
				
			emaillist = []
			if '@channel' in instance.comment:
				for user in User.objects.all():
					emaillist += [user.email]
			else:
				for log in logs:
					emaillist += [log.created_by.email]
				for user in re.compile(r"\@(\w+)").findall(instance.comment):
					usermatch = User.objects.filter(username=user)
					if len(usermatch):
						emaillist += [usermatch[0].email]
			emaillist = np.unique(emaillist)

			transient_name = instance.transient.name
			base_url = "https://ziggy.ucolick.org/yse/" 
			if settings.DEBUG:
				base_url =	"https://ziggy.ucolick.org/yse_test/"
			subject = "YSE_PZ: new comment added to event %s"%transient_name
			body = """\
			<html>
			<head></head>
			<body>
			<h1>Comment added!</h1>
			<p>
			<a href='%stransient_detail/%s/'>%s</a><br>
			%s says:<br>
			%s <br>
			</p>
			<br />
			<p>Go to <a href='%s/dashboard/'>YSE Dashboard</a></p> 
			</body>
			</html>
			""" % (base_url, transient_name, transient_name,
				   str(instance.created_by),instance.comment, base_url)
			for email in emaillist:
				alert.send_email_simple(email, subject, body)

				
			# for key,value in form.cleaned_data.items():
			data_dict = {}
			data_dict['id'] = instance.id
			data_dict['created_by'] = str(instance.created_by)
			data_dict['modified_date'] = instance.modified_date.strftime('%b. %-d, %Y, %H:%M ') + \
								   instance.modified_date.strftime('%p').lower()[0]+'.'+\
								   instance.modified_date.strftime('%p').lower()[1]+'.'
			data_dict['comment'] = instance.comment
			
			data = {
				'message': "Successfully submitted form data.",
				'data': data_dict
			}
			return JsonResponse(data)
		else:
			return response
		
class AddDashboardQueryFormView(FormView):
	form_class = AddDashboardQueryForm
	template_name = 'YSE_App/form_snippets/dashboard_query_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddDashboardQueryFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddDashboardQueryFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			instance.user = self.request.user

			instance.save() #update_fields=['created_by','modified_by']

			print(form.cleaned_data)

			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

class RemoveDashboardQueryFormView(DeleteView):
	model = UserQuery
	form_class = RemoveDashboardQueryForm
	template_name = 'YSE_App/personaldashboard.html'
	success_url = reverse_lazy('personaldashboard')
	
	def form_invalid(self, form):
		response = super(RemoveDashboardQueryFormView, self).form_invalid(form)

		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

class AddFollowupNoticeFormView(FormView):
	form_class = AddFollowupNoticeForm
	template_name = 'YSE_App/form_snippets/dashboard_followup_notice_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddFollowupNoticeFormView, self).form_invalid(form)
		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddFollowupNoticeFormView, self).form_valid(form)
		if self.request.is_ajax():

			instance = form.save(commit=False)
			instance.created_by = self.request.user
			instance.modified_by = self.request.user
			try: instance.profile = Profile.objects.filter(user=self.request.user)[0]
			except:
				data = {
					'message': """User %s has no profile object in the YSE_PZ database.  
Contact D. Jones or D. Coulter."""%self.request.user,
				}
				return JsonResponse(data)

				
			instance.save() #update_fields=['created_by','modified_by']

			print(form.cleaned_data)

			data = {
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response

class RemoveFollowupNoticeFormView(DeleteView):
	model = UserTelescopeToFollow
	form_class = RemoveFollowupNoticeForm
	template_name = 'YSE_App/personaldashboard.html'
	success_url = reverse_lazy('personaldashboard')
	
	def form_invalid(self, form):
		response = super(RemoveFollowupNoticeFormView, self).form_invalid(form)

		if self.request.is_ajax():
			return JsonResponse(form.errors, status=400)
		else:
			return response
		
