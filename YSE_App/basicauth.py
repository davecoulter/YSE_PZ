import datetime
import json
 
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import auth
from django.contrib.auth import authenticate, login
  
# The basic auth decorator
import base64
def login_or_basic_auth_required(view):
	def _decorator(request, *args, **kwargs):
		if 'HTTP_AUTHORIZATION' in request.META.keys():
			auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
			if auth_method.lower() == 'basic':
				credentials = base64.b64decode(credentials.strip()).decode('utf-8')
				username, password = credentials.split(':', 1)
				user = auth.authenticate(username=username, password=password)
				if user is not None and user.is_active:
					# Correct password, and the user is marked "active"
					return view(request, *args, **kwargs)
				else:
					return HttpResponseForbidden('Incorrect user credentials.')
			response = HttpResponse()
			response.status_code = 401
			response['WWW-Authenticate'] = 'Basic'
			return response
		else:
			if request.user.is_authenticated:
				return view(request, *args, **kwargs)
			else:
				return HttpResponseForbidden('Incorrect user credentials')
	return _decorator


