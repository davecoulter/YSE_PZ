from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
import sys
from datetime import datetime

from .models import *
# from .forms import *
from .common import utilities
import json

from django.views.generic import FormView
from .forms import *
from django.http import JsonResponse
from django.forms.models import model_to_dict
from .common import alert
import numpy as np


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



			instance.save() #update_fields=['created_by','modified_by']

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

			data_dict['valid_start'] = form.cleaned_data['valid_start']
			data_dict['valid_stop'] = form.cleaned_data['valid_stop']
			data_dict['spec_priority'] = form.cleaned_data['spec_priority']
			data_dict['phot_priority'] = form.cleaned_data['phot_priority']
			data_dict['offset_star_ra'] = form.cleaned_data['offset_star_ra']
			data_dict['offset_star_dec'] = form.cleaned_data['offset_star_dec']
			data_dict['offset_north'] = form.cleaned_data['offset_north']
			data_dict['offset_east'] = form.cleaned_data['offset_east']

			data_dict['modified_by'] = instance.modified_by.username

			data = {
				'message': "Successfully submitted form data.",
				'data': data_dict
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
			for log in logs:
				emaillist += [log.created_by.email]
			emaillist = np.unique(emaillist)

			transient_name = instance.transient.name
			base_url = "https://ziggy.ucolick.org/yse/" 
			if settings.DEBUG:
				base_url =  "https://ziggy.ucolick.org/yse_test/"
			subject = "YSE_PZ: new comment added to event %s"%transient_name
			body = """\
			<html>
			<head></head>
			<body>
			<h1>Comment added!</h1>
			<p>
			<a href='%stransient_detail/%s/'>%s</a>
			</p>
			<br />
			<p>Go to <a href='%s/dashboard/'>YSE Dashboard</a></p> 
			</body>
			</html>
			""" % (base_url, transient_name, transient_name, base_url)
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
