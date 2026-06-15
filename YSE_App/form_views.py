from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse, HttpResponseNotFound
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse, reverse_lazy
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

from YSE_App.util import lcogt
# for getting YSE filter selection
from django.conf import settings as djangoSettings

# reddest filter for YSE is from settings.py
_reddest_yse_filter = djangoSettings.REDYSEFILTER

def is_ajax(request):
	return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

class AddTransientFollowupFormView(FormView):
	form_class = TransientFollowupForm
	template_name = 'YSE_App/form_snippets/transient_followup_form.html'

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["user"] = self.request.user
		transient_id = self.request.POST.get("transient") or self.request.GET.get("transient")
		if transient_id:
			kwargs["transient_id"] = int(transient_id)
		return kwargs

	def _transient_detail_success_url(self, transient):
		return reverse("transient_detail", kwargs={"slug": transient.slug}) + "#followup_tab"

	def _followup_response_data(self, instance, form):
		data_dict = {
			"id": instance.id,
			"status_id": instance.status.id,
			"status_name": instance.status.name,
			"valid_start": instance.valid_start,
			"valid_stop": instance.valid_stop,
			"spec_priority": form.cleaned_data["spec_priority"],
			"phot_priority": form.cleaned_data["phot_priority"],
			"offset_star_ra": form.cleaned_data["offset_star_ra"],
			"offset_star_dec": form.cleaned_data["offset_star_dec"],
			"offset_north": form.cleaned_data["offset_north"],
			"offset_east": form.cleaned_data["offset_east"],
			"comment": form.cleaned_data["comment"],
			"modified_by": instance.modified_by.username,
		}
		if instance.too_resource:
			data_dict["too_resource"] = str(instance.too_resource)
		if instance.classical_resource:
			data_dict["classical_resource"] = str(instance.classical_resource)
		if instance.queued_resource:
			data_dict["queued_resource"] = str(instance.queued_resource)
		return data_dict

	def _create_followup_from_form(self, form):
		from YSE_App.services.audience import resolve_followup_audience

		instance = form.save(commit=False)
		instance.created_by = self.request.user
		instance.modified_by = self.request.user
		instance.requested_by = self.request.user
		instance.valid_start = form.cleaned_data["valid_start"]
		instance.valid_stop = form.cleaned_data["valid_stop"]

		is_public, audience_groups = resolve_followup_audience(
			self.request.user,
			instance.transient_id,
			audience_groups=list(form.cleaned_data.get("audience_groups") or []),
			linked_resource=(
				form.cleaned_data.get("classical_resource")
				or form.cleaned_data.get("too_resource")
				or form.cleaned_data.get("queued_resource")
			),
			explicit_audience=True,
		)
		instance.is_public = is_public
		instance.save()

		if audience_groups:
			instance.groups.set(audience_groups)

		if instance.transient.status.name in ["New", "Watch", "Ignore", "Interesting"]:
			instance.transient.status = TransientStatus.objects.filter(
				name="FollowupRequested"
			)[0]
			instance.transient.save()

		if form.cleaned_data["comment"]:
			log = Log(
				transient_followup=instance,
				comment=form.cleaned_data["comment"],
				created_by=self.request.user,
				modified_by=self.request.user,
			)
			log.save()

		return instance

	def form_invalid(self, form):
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		transient_id = self.request.POST.get("transient")
		if transient_id:
			transient = Transient.objects.filter(pk=transient_id).only("slug").first()
			if transient:
				from django.contrib import messages

				messages.error(
					self.request,
					"Could not save follow-up: "
					+ "; ".join(
						f"{field}: {', '.join(errors)}"
						for field, errors in form.errors.items()
					),
				)
				return HttpResponseRedirect(self._transient_detail_success_url(transient))
		referer = self.request.META.get("HTTP_REFERER")
		if referer:
			return HttpResponseRedirect(referer)
		return HttpResponseRedirect(reverse_lazy("dashboard"))

	def form_valid(self, form):
		instance = self._create_followup_from_form(form)
		if is_ajax(self.request):
			data = {
				"data": self._followup_response_data(instance, form),
				"message": "Successfully submitted form data.",
			}
			return JsonResponse(data)
		return HttpResponseRedirect(
			self._transient_detail_success_url(instance.transient)
		)

class AddClassicalResourceFormView(FormView):
	form_class = ClassicalResourceForm
	template_name = 'YSE_App/form_snippets/classical_resource_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddClassicalResourceFormView, self).form_invalid(form)
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddClassicalResourceFormView, self).form_valid(form)
		if is_ajax(self.request):

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

			obs_date = form.cleaned_data['observing_date']
			data = {
				'message': "Successfully submitted form data.",
				'observing_calendar_url': '/observing_calendar/',
				'obs_date': obs_date.strftime('%Y-%m-%d'),
				'telescope': str(instance.telescope.name),
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
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddToOResourceFormView, self).form_valid(form)
		if is_ajax(self.request):

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
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddTransientObservationTaskFormView, self).form_valid(form)
		if is_ajax(self.request):
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
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddSurveyFieldFormView, self).form_valid(form)
		if is_ajax(self.request):
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

		if not is_ajax(self.request):
			auth_method, credentials = self.request.META['HTTP_AUTHORIZATION'].split(' ', 1)
			credentials = base64.b64decode(credentials.strip()).decode('utf-8')
			username, password = credentials.split(':', 1)
			self.request.user = auth.authenticate(username=username, password=password)
		
		return super(AddSurveyObsFormView, self).dispatch(request, *args, **kwargs)
	
	def form_invalid(self, form):
		response = super(AddSurveyObsFormView, self).form_invalid(form)
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddSurveyObsFormView, self).form_valid(form)
		if 'hi': #is_ajax(self.request):
			instance = form.save(commit=False)

			telescope = Telescope.objects.get(name='Pan-STARRS1')
			location = EarthLocation.from_geodetic(
				telescope.longitude*u.deg,telescope.latitude*u.deg,
				telescope.elevation*u.m)
			tel = Observer(location=location, timezone="US/Hawaii")
			
			m = date_to_mjd(form.cleaned_data['survey_obs_date'])
			time = Time(m,format='mjd')
			sunset_forobs = mjd_to_date(tel.sun_set_time(time,which="next"))

			if form.cleaned_data['instrument'][0] == 'GPC1':
				survey_field = SurveyFieldMSB.objects.filter(name=form.cleaned_data['ztf_field_id'][0])
			elif form.cleaned_data['instrument'][0] == 'GPC2':
				survey_field = SurveyFieldMSB.objects.filter(name=form.cleaned_data['ztf_field_id'][0]+'P2')
			else:
				return HttpResponseNotFound

			for sb in survey_field:
				for s in sb.survey_fields.all():
					t = Time(m,format='mjd')
					illum = moon_illumination(t)

					# need to see what was observed in the previous obs w/ the same moon illumination
					# first have to grab the MSB associated with this observation, if it exists
					# otherwise it's gonna schedule different filters for different pointings

					previous_msb = SurveyFieldMSB.objects.filter(survey_fields__in=[s])
					if len(previous_msb):
						previous_field = previous_msb[0].survey_fields.all()[0]
						previous_obs = SurveyObservation.objects.filter(survey_field=previous_field).\
							filter(Q(obs_mjd__lt=m) & Q(obs_mjd__isnull=False)).order_by('-obs_mjd').\
							order_by('-mjd_requested').select_related()
					else:
						previous_obs = SurveyObservation.objects.filter(survey_field=s).\
							filter(Q(obs_mjd__lt=m) | Q(obs_mjd__isnull=False)).order_by('-obs_mjd').\
							order_by('-mjd_requested').select_related()

					# reddest_yse_filter gives hard-coded YSE "mini-survey" filter choice
					if s.instrument.name == 'GPC2':
						reddest_yse_filter = _reddest_yse_filter[:]
					else:
						reddest_yse_filter = 'z'
					
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
							elif 'i' in filt: band1name,band2name = 'g',reddest_yse_filter
							else: band1name,band2name = 'g','r'
						else:
							filt = previous_obs_func(0.66,1)
							if filt is None or 'z' in filt or 'y' in filt: band1name,band2name = 'r','i'
							else: band1name,band2name = 'r',reddest_yse_filter
					else:
						if illum < 0.33:
							filt = previous_obs_func(0,0.33)
							if filt is None or 'i' in filt: band1name,band2name = 'g','r'
							else: band1name,band2name = 'g','i'
						elif illum < 0.66:
							filt = previous_obs_func(0.33,0.66)
							if filt is None or 'z' in filt or 'y' in filt: band1name,band2name = 'g','i'
							else: band1name,band2name = 'g',reddest_yse_filter
						else:
							filt = previous_obs_func(0.66,1)
							if filt is None or 'z' in filt or 'y' in filt: band1name,band2name = 'r','i'
							else: band1name,band2name = 'r',reddest_yse_filter

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
						modified_by=self.request.user,
						priority=form.cleaned_data['priority'])
					SurveyObservation.objects.create(
						mjd_requested=date_to_mjd(sunset_forobs),
						survey_field=s,
						status=TaskStatus.objects.get(name='Requested'),
						exposure_time=27,
						photometric_band=band2,
						created_by=self.request.user,
						modified_by=self.request.user,
						priority=form.cleaned_data['priority'])

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
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddOncallUserFormView, self).form_valid(form)
		if is_ajax(self.request):
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

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["user"] = self.request.user
		transient_id = self.request.POST.get("transient") or self.request.GET.get("transient")
		if transient_id:
			kwargs["transient_id"] = int(transient_id)
		return kwargs

	def _transient_detail_success_url(self, transient):
		return reverse("transient_detail", kwargs={"slug": transient.slug})

	def _create_comment_from_form(self, form):
		from YSE_App.services.audience import resolve_comment_audience
		from YSE_App.services.comments import create_transient_comment, log_to_comment_dict

		transient = form.cleaned_data["transient"]
		is_public, audience_groups = resolve_comment_audience(
			self.request.user,
			transient.id,
			is_public=form.cleaned_data.get("is_public", False),
			audience_groups=form.cleaned_data.get("audience_groups"),
		)
		log = create_transient_comment(
			transient=transient,
			comment=form.cleaned_data["comment"],
			user=self.request.user,
			is_public=is_public,
			audience_groups=audience_groups,
		)
		return log, log_to_comment_dict(log)

	def form_invalid(self, form):
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		return super(AddTransientCommentFormView, self).form_invalid(form)

	def form_valid(self, form):
		log, comment_dict = self._create_comment_from_form(form)
		if is_ajax(self.request):
			data = {
				"message": "Successfully submitted form data.",
				"data": comment_dict,
			}
			return JsonResponse(data)
		return HttpResponseRedirect(self._transient_detail_success_url(log.transient))
		
class AddDashboardQueryFormView(FormView):
	form_class = AddDashboardQueryForm
	template_name = 'YSE_App/form_snippets/dashboard_query_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddDashboardQueryFormView, self).form_invalid(form)
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddDashboardQueryFormView, self).form_valid(form)
		if is_ajax(self.request):

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

		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

class AddFollowupNoticeFormView(FormView):
	form_class = AddFollowupNoticeForm
	template_name = 'YSE_App/form_snippets/dashboard_followup_notice_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddFollowupNoticeFormView, self).form_invalid(form)
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddFollowupNoticeFormView, self).form_valid(form)
		if is_ajax(self.request):

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

		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

class AddAutomatedSpectrumRequestFormView(FormView):
	form_class = AutomatedSpectrumRequest
	template_name = 'YSE_App/form_snippets/spectrum_request_form.html'
	success_url = '/form-success/'
	
	def form_invalid(self, form):
		response = super(AddAutomatedSpectrumRequestFormView, self).form_invalid(form)
		if is_ajax(self.request):
			return JsonResponse(form.errors, status=400)
		else:
			return response

	def form_valid(self, form):
		response = super(AddAutomatedSpectrumRequestFormView, self).form_valid(form)
		if is_ajax(self.request):
			tfdict = {}
			
			# some hard-coded logic
			if 'goodman' in form.cleaned_data['instrument'].name.lower():
				resource = ClassicalResource.objects.filter(telescope__name=form.cleaned_data['instrument'].telescope).\
					filter(principal_investigator__name='Dimitriadis')
				if not len(self.request.user.groups.all().filter(name='SOAR')):
					data_dict = {'errors':'you need to be in the SOAR permissions group to submit this request!',
								 'errorflag':1}
					data = {
						'data':data_dict,
						'message': "Successfully submitted form data.",
					}
					return JsonResponse(data)
			else:
				resource = ToOResource.objects.filter(telescope__name=form.cleaned_data['instrument'].telescope) #.\
					#filter(principal_investigator__name='Kilpatrick')
				if not len(self.request.user.groups.all().filter(name='LCOGT')):
					data_dict = {'errors':'you need to be in the LCOGT permissions group to submit this request!',
								 'errorflag':1}
					data = {
						'data':data_dict,
						'message': "Successfully submitted form data.",
					}
					return JsonResponse(data)
				
			# make sure the dates line up, with a +/-1 day window to make life easier
			resource = resource.filter(Q(begin_date_valid__lt=form.cleaned_data['spectrum_valid_start']+datetime.timedelta(1)) &
									   Q(end_date_valid__gt=form.cleaned_data['spectrum_valid_stop']-datetime.timedelta(1)))

			if not len(resource):
				data_dict = {'errors':'could not find a matching resource, make sure the dates are valid and the program is still active!',
							 'errorflag':1}
				data = {
					'data':data_dict,
					'message': "Successfully submitted form data.",
				}
				return JsonResponse(data)
			else:
				resource = resource[0]
			
			status = FollowupStatus.objects.get(name='Requested')

			if 'goodman' in form.cleaned_data['instrument'].name.lower():
				tf = TransientFollowup(status=status,valid_start=form.cleaned_data['spectrum_valid_start'],
									   valid_stop=form.cleaned_data['spectrum_valid_stop'],classical_resource=resource,
									   transient=form.cleaned_data['transient'],created_by=self.request.user,modified_by=self.request.user)
			else:
				tf = TransientFollowup(status=status,valid_start=form.cleaned_data['spectrum_valid_start'],
									   valid_stop=form.cleaned_data['spectrum_valid_stop'],too_resource=resource,
									   transient=form.cleaned_data['transient'],created_by=self.request.user,modified_by=self.request.user)

			tf.save()

			# now charlie's code
			lcogt.main(
				 tf.transient.name,tf.transient.ra,tf.transient.dec,form.cleaned_data['exp_time'],
				 form.cleaned_data['instrument'].telescope.name.split()[0],
				 form.cleaned_data['spectrum_valid_start'].replace(tzinfo=None).isoformat(),
				 form.cleaned_data['spectrum_valid_stop'].replace(tzinfo=None).isoformat())

			data_dict = {'errors':'',
						 'errorflag':0}
			data = {
				'data':data_dict,
				'message': "Successfully submitted form data.",
			}
			return JsonResponse(data)
		else:
			return response
