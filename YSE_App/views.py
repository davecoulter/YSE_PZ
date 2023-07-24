from django.db.models.query import EmptyQuerySet
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse, HttpResponseNotFound
from django.conf import settings as djangoSettings
from django.template import loader
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q
from rest_framework.renderers import JSONRenderer
import requests
from django.template.defaulttags import register
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Lower
from django.db import connection,connections
from django.shortcuts import redirect
from django.db.models import Count, Value, Max, Min
import zipfile
from io import BytesIO
from YSE_App.yse_utils.yse_pa import yse_pa
from django.utils.decorators import method_decorator

from astropy.utils import iers
iers.conf.auto_download = True
from astropy.utils.iers import conf
conf.auto_max_age = None

from .models import *
from .forms import *
from .common import utilities
from . import view_utils
import datetime
from datetime import timedelta
import pytz
from pytz import timezone
from .serializers import *
from django.core import serializers
import os
from .data import PhotometryService, SpectraService, ObservingResourceService
import json
import time
import dateutil.parser
from astroplan import moon_illumination
from astropy.time import Time
from .common.utilities import getRADecBox

from .table_utils import TransientTable,YSETransientTable,YSEFullTransientTable,YSERisingTransientTable,NewTransientTable,ObsNightFollowupTable,FollowupTable,TransientFilter,FollowupFilter,YSEObsNightTable,ToOFollowupTable
from .table_utils import CandidatesTable
from .queries.yse_python_queries import *
from .queries import yse_python_queries
import django_tables2 as tables
from django_tables2 import RequestConfig
from .basicauth import *
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from urllib.parse import unquote

from .common.utilities import date_to_mjd, mjd_to_date
from django.views.generic.list import ListView

# Create your views here.

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse_lazy('dashboard'))
    return render(request, 'YSE_App/index.html')

#def add_followup(request,obj):
#        return '<a href="%s">Add followup for %s</a>' % (obj.firm_url,obj.firm_url)

# Create your views here.
def auth_login(request):
    logout(request)
    next_page = request.POST.get('next')

    user = None
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        
        # Redirect to requested page
        if next_page:
            return HttpResponseRedirect(next_page)
        else:
            return HttpResponseRedirect('/dashboard/')
        #render(request,'YSE_App/dashboard.html')
    else:
        return render(request, 'YSE_App/login.html')

def auth_logout(request):
    logout(request)
    return render(request, 'YSE_App/index.html')

@login_required
def dashboard(request):

    transient_categories = []
    for title,statusname in zip(['New Transients','Followup Requested','Following','Interesting','Watch','Finished Following','Needs Template'],
                                ['New','FollowupRequested','Following','Interesting','Watch','FollowupFinished','NeedsTemplate']):
        status = TransientStatus.objects.filter(name=statusname).order_by('-modified_date')
        if len(status) == 1:
            transients = Transient.objects.filter(status=status[0]).order_by('-disc_date')
        else:
            transients = Transient.objects.filter(status=None).order_by('-disc_date')
        transientfilter = TransientFilter(request.GET, queryset=transients,prefix=statusname.lower())
        if statusname == 'New': table = NewTransientTable(transientfilter.qs,prefix=statusname.lower())
        else: table = TransientTable(transientfilter.qs,prefix=statusname.lower())
        RequestConfig(request, paginate={'per_page': 10}).configure(table)
        transient_categories += [(table,title,statusname.lower(),transientfilter),]
    
    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-')[0]
    else: anchor = ''
    context = {
        'transient_categories':transient_categories,
        'all_transient_statuses':TransientStatus.objects.order_by('name'),
        'anchor':anchor,
    }

    return render(request, 'YSE_App/dashboard.html', context)

@login_required
def personaldashboard(request):

    queries = UserQuery.objects.filter(user = request.user)
    tables = []

    for q in queries:
        transients = []
        if q.query:
            try:
                if 'yse_app_transient' not in q.query.sql.lower(): continue
                if 'name' not in q.query.sql.lower(): continue
                if not q.query.sql.lower().startswith('select'): continue

                cursor = connections['explorer'].cursor()
                cursor.execute(q.query.sql.replace('%','%%'), ())
                transients = Transient.objects.filter(name__in=(x[0] for x in cursor)).order_by('-disc_date')
                cursor.close()

                transientfilter = TransientFilter(request.GET, queryset=transients, prefix=q.query.title.replace(' ',''))
                table = TransientTable(transientfilter.qs, prefix=q.query.title.replace(' ',''))
                RequestConfig(request, paginate={'per_page': 10}).configure(table)
                tables += [(table, q.query.title, q.query.title.replace(' ', ''), transientfilter, q.id, len(transients))]
            except:
                # Query bombed
                tables += [(Transient.objects.none(), q.query.title + ' [QUERY ID %s IS BROKEN]' % q.query_id, q.query.title.replace(' ', ''), Transient.objects.none(), q.id, len(transients))]
                pass
        elif q.python_query:
            transients = getattr(yse_python_queries, q.python_query)()

            transientfilter = TransientFilter(request.GET, queryset=transients,prefix=q.python_query)
            table = TransientTable(transientfilter.qs,prefix=q.python_query)
            RequestConfig(request, paginate={'per_page': 10}).configure(table)
            tables += [(table,q.python_query, q.python_query, transientfilter, q.id, len(transients))]
            
    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-')[0]
    else:
        anchor = ''

    context = {
        'user':request.user,
        'transient_categories':tables,
        'all_transient_statuses':TransientStatus.objects.all(),
        'anchor':anchor,
        'add_dashboard_query_form': AddDashboardQueryForm(),
        'add_followup_notice_form': AddFollowupNoticeForm(),
        'followup_notices': UserTelescopeToFollow.objects.filter(profile__user=request.user)
    }

    return render(request, 'YSE_App/personaldashboard.html', context)

@login_required
def transient_summary(request,status_or_query_name,
                      template='YSE_App/transient_summary_paginate.html',
                      extra_context=None,
                      page_template='YSE_App/transient_summary_individual.html'):

    # Status update properties
    transients = []

    all_transient_statuses = TransientStatus.objects.all()
    transient_status_follow = TransientStatus.objects.get(name="Following")
    transient_status_followrequest = TransientStatus.objects.get(name="FollowupRequested")
    transient_status_watch = TransientStatus.objects.get(name="Watch")
    transient_status_ignore = TransientStatus.objects.get(name="Ignore")
    transient_status_interesting = TransientStatus.objects.get(name="Interesting")
    
    #all_simple_followups = SimpleTransientSpecRequest.objects.all()

    #transients_with_followup = SimpleTransientFollowupRequest.objects.all().values('transient__name').distinct()

    from django.utils import timezone
    transient_followup_form = TransientFollowupForm()
    transient_followup_form.fields["too_resource"].queryset = view_utils.get_authorized_too_resources(request.user).filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('telescope__name')
    transient_followup_form.fields["queued_resource"].queryset = view_utils.get_authorized_queued_resources(request.user).filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('telescope__name')

    
    status = TransientStatus.objects.filter(name=status_or_query_name.replace('followrequest','FollowupRequested')).order_by('-modified_date')
    if len(status) == 1:
        transients = Transient.objects.filter(status=status[0]).order_by('-disc_date')
    else:
        query = Query.objects.filter(title=unquote(status_or_query_name))
        if len(query):

            try:
                query = query[0]
                if 'yse_app_transient' not in query.sql.lower(): return Http404('Invalid Query')
                if 'name' not in query.sql.lower(): return Http404('Invalid Query')
                if not query.sql.lower().startswith('select'): return Http404('Invalid Query')
                cursor = connections['explorer'].cursor()
                cursor.execute(query.sql.replace('%','%%'), ())
                transients = Transient.objects.filter(name__in=(x[0] for x in cursor)).order_by('-disc_date')
                cursor.close()
            except:
                # Query bombed
                pass
        else:
            query = UserQuery.objects.filter(python_query = unquote(status_or_query_name))
            if not len(query):
                return HttpResponseNotFound("Invalid Query")
            query = query[0]
            transients = getattr(yse_python_queries,query.python_query)()

    if 'sort' in request.GET.keys():
        if request.GET['sort'] == 'last_obs_date' or request.GET['sort'] == '-last_obs_date':
            if request.GET['sort'] == '-last_obs_date':
                is_descending = True
            else:
                is_descending = False
            
            all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = transients)
            phot_ids = all_phot.values('id')
        
            phot_data_query = Q(transientphotometry__id__in=phot_ids)
            transients = transients.annotate(
                recent_magdate=Max('transientphotometry__transientphotdata__obs_date',filter=phot_data_query), #,filter=phot_data_query
            ).order_by(('-' if is_descending else '') + 'recent_magdate')
            
        elif request.GET['sort'] == 'last_mag' or request.GET['sort'] == '-last_mag':
            raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
         SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
         WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id
         ORDER BY pd2.obs_date DESC
         LIMIT 1
     )
"""
            if request.GET['sort'] == '-last_mag': is_descending = True
            else: is_descending = False
            transients = transients.annotate(last_mag=RawSQL(raw_query,())).order_by(('-' if is_descending else '') + 'last_mag')
        else:
            transients = transients.order_by(request.GET['sort'])
            
    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-')[0]
    else: anchor = ''
    context = {
        'transients':transients,
        'all_transient_statuses': all_transient_statuses,
        'transient_status_follow': transient_status_follow,
        'transient_status_followrequest': transient_status_followrequest,
        'transient_status_watch': transient_status_watch,
        'transient_status_interesting': transient_status_interesting,
        'transient_status_ignore': transient_status_ignore,
        'transient_followup_form': transient_followup_form,
        'anchor':anchor,
        #'transients_with_followup': transients_with_followup
    }
    if transient_followup_form.fields["valid_start"].initial:
        context['followup_initial_dates'] = \
            (transient_followup_form.fields["valid_start"].initial.strftime('%m/%d/%Y HH:MM'),
             transient_followup_form.fields["valid_stop"].initial.strftime('%m/%d/%Y HH:MM'))
    
    if extra_context is not None:
        context.update(extra_context)
    else:
        template = 'YSE_App/transient_summary.html'
        context['page_template'] = page_template
    if is_ajax(request):
        template = 'YSE_App/transient_summary_paginate.html'

    return render(request, template, context)


@login_required
def followup(request):

    followup_transients = None

    telescopes = Telescope.objects.all()

    table_list = []
    for t in telescopes:
        followup_transients = TransientFollowup.objects.filter(Q(too_resource__telescope__name=t) |
                                                               Q(classical_resource__telescope__name=t) |
                                                               Q(queued_resource__telescope__name=t))
        followuptransientfilter = FollowupFilter(request.GET, queryset=followup_transients,prefix=t)
        
        followup_table = FollowupTable(followuptransientfilter.qs,prefix=t)
        RequestConfig(request, paginate={'per_page': 10}).configure(followup_table)
        table_list += [(t.name,followup_table,t.name.replace(' ','_'),followup_transients,followuptransientfilter)]

    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-ex')[0]
    else: anchor = ''
    context = {
        'followup_tables':table_list,
        'anchor':anchor,
        'all_followup_statuses':FollowupStatus.objects.all(),
    }
    return render(request, 'YSE_App/transient_followup.html', context)

@login_required
def transient_tags(request):
    all_transient_tags = TransientTag.objects.all()
    context = {
        'all_transient_tags': all_transient_tags
    }
    return render(request, 'YSE_App/transient_tags.html', context)

@login_required
def get_transient_tags(request):
    id_str= request.GET.getlist('tagid')
    ids = []
    for id in id_str:
        ids.append(int(id))

    transient_queryset = Transient.objects.filter(tags__in=ids).distinct()
    transient_objs = [t for t in transient_queryset]

    serializer = TransientSerializer(transient_objs, context={'request': request}, many=True)
    return_data = {}

    for i,data in enumerate(serializer.data):
        return_data[i] = data

    return JsonResponse(return_data)

@login_required
def dashboard_example(request):
    return render(request, 'YSE_App/dashboard_example.html')


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@login_required
def calendar(request):
    all_dates = OnCallDate.objects.all()
    colors = ['#dd4b39', 
                '#f39c12', 
                '#00c0ef', 
                '#0073b7', 
                '#f012be', 
                '#3c8dbc',
                '#00a65a',
                '#d2d6de',
                '#001f3f']

    user_colors = {}
    for i, u in enumerate(User.objects.all().exclude(username='admin')):
        user_colors[u.username] = colors[i % len(colors)]

    context = {
        'all_dates': all_dates,
        'user_colors': user_colors
    }
    return render(request, 'YSE_App/calendar.html', context)

@login_required
def yse_oncall_calendar(request):
    all_dates = YSEOnCallDate.objects.all()
    users = all_dates.order_by('-on_call_date').values_list('user__username',flat=True).distinct()

    colors = ['#dd4b39', 
              '#f39c12', 
              '#00c0ef', 
              '#0073b7', 
              '#f012be', 
              '#3c8dbc',
              '#00a65a',
              '#d2d6de',
              '#001f3f']

    user_colors = {}
    for i, u in enumerate(users): #User.objects.all().exclude(username='admin').order_by()):
        #user_colors[u.username] = colors[i % len(colors)]
        user_colors[u] = colors[i % len(colors)]
    oncall_form = OncallForm()
        
    context = {
        'all_dates': all_dates,
        'user_colors': user_colors,
        'oncall_form': oncall_form,
        'date_start': datetime.datetime.now().__str__().split()[0],
        'date_end': (datetime.datetime.now()+datetime.timedelta(1)).__str__().split()[0]
    }
    return render(request, 'YSE_App/yse_oncall_calendar.html', context)


@login_required
def observing_calendar(request):
    all_dates = ClassicalObservingDate.objects.all().select_related()
    colors = ['#dd4b39', 
                '#f39c12', 
                '#00c0ef', 
                '#0073b7', 
                '#f012be', 
                '#3c8dbc',
                '#00a65a',
                '#d2d6de',
                '#001f3f']

    telescope_colors = {}
    for i, c in enumerate(ClassicalResource.objects.all().select_related()):
        telescope_colors[c.telescope.name] = colors[i % len(colors)]

    context = {
        'all_dates': all_dates,
        'telescope_colors': telescope_colors
    }
    return render(request, 'YSE_App/observing_calendar.html', context)

@login_required
def too_calendar(request):

    colors = ['#dd4b39', 
              '#f39c12', 
              '#00c0ef', 
              '#0073b7', 
              '#f012be', 
              '#3c8dbc',
              '#00a65a',
              '#d2d6de',
              '#001f3f']

    # don't show everything, for speed
    first_calendar_date = (datetime.datetime.utcnow()-datetime.timedelta(60)).replace(tzinfo=pytz.UTC)
    last_calendar_date = (datetime.datetime.utcnow()+datetime.timedelta(60)).replace(tzinfo=pytz.UTC)
    all_too_resources = ToOResource.objects.filter(~Q(end_date_valid__lt=first_calendar_date) &
                                               ~Q(begin_date_valid__gt=last_calendar_date)).select_related()

    telescope_colors = {}
    all_resources = ()
    for i, c in enumerate(all_too_resources.select_related()):
        telescope_colors[c.telescope.name] = colors[i % len(colors)]

        if c.begin_date_valid.replace(tzinfo=pytz.UTC) > first_calendar_date: date_start = c.begin_date_valid
        else: date_start = first_calendar_date

        if c.end_date_valid.replace(tzinfo=pytz.UTC) > last_calendar_date: date_end = last_calendar_date
        else: date_end = c.end_date_valid

        date_list = [date_start + datetime.timedelta(days=x) \
                     for x in range(0, (date_end-date_start).days+2)]
        all_resources += ((c,[(d.year,d.month,d.day) for d in date_list]),)
        
    context = {
        'all_resources': all_resources,
        'telescope_colors': telescope_colors
    }
    return render(request, 'YSE_App/too_calendar.html', context)

@login_required
def too_requests(request, telescope, pi_name):

    nowdate = datetime.datetime.utcnow()
    # get follow requests for telescope/date
    too_resource = ToOResource.objects.\
        filter(telescope__name = telescope.replace('_',' ')).\
        filter(begin_date_valid__lte=nowdate).filter(end_date_valid__gte=nowdate).select_related()
    if pi_name != 'None':
        too_resource = too_resource.filter(principal_investigator__name = pi_name)
    
    follow_requests = TransientFollowup.objects.filter(too_resource = too_resource[0]).\
        filter(valid_start__lte = too_resource[0].end_date_valid).\
        filter(valid_stop__gte = too_resource[0].begin_date_valid).\
        filter(Q(status__name='Requested') | Q(status__name='InProcess') | Q(status__name='Failed')).select_related()

    followuptransientfilter = FollowupFilter(
        request.GET, queryset=follow_requests,prefix=telescope.replace('_',''))
        
    followup_table = ToOFollowupTable(followuptransientfilter.qs,prefix=telescope.replace('_',''),too_resource=too_resource)
    RequestConfig(request, paginate={'per_page': 20}).configure(followup_table)
    table = (telescope.replace('_',' '),followup_table,telescope,follow_requests,followuptransientfilter)

    location = EarthLocation.from_geodetic(
        too_resource[0].telescope.longitude*u.deg,too_resource[0].telescope.latitude*u.deg,
        too_resource[0].telescope.elevation*u.m)
    time = Time(str(nowdate).split('+')[0], format='iso')
    tel = Observer(location=location, timezone="UTC")

    sunset = tel.sun_set_time(time,which="previous").isot.split('T')[-1][:-7]
    night_start_12 = tel.twilight_evening_nautical(time,which="previous").isot.split('T')[-1][:-7]
    night_start_18 = tel.twilight_evening_astronomical(time,which="previous").isot.split('T')[-1][:-7]
    night_end_18 = tel.twilight_morning_astronomical(time,which="previous").isot.split('T')[-1][:-7]
    night_end_12 = tel.twilight_morning_nautical(time,which="previous").isot.split('T')[-1][:-7]
    sunrise = tel.sun_rise_time(time,which="previous").isot.split('T')[-1][:-7]

    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-ex')[0]
    else: anchor = ''
    context = {
        'followup_table':table,
        'anchor':anchor,
        'all_followup_statuses':FollowupStatus.objects.all(),
        'all_transient_statuses':TransientStatus.objects.all(),
        'follow_requests': follow_requests,
        'telescope':telescope.replace('_',' '),
        'obs_date':nowdate.isoformat().split('T')[0],
        'too_resource':too_resource[0],
        'sunriseset':(sunset,night_start_12,night_start_18,night_end_18,night_end_12,sunrise)
    }
    return render(request, 'YSE_App/too_requests.html', context)

@login_required
def yse_home(request):
    oncall_form = OncallForm()
    classical_resource_form = ClassicalResourceForm()
    too_resource_form = ToOResourceForm()

    fastrising_transients = fastrising_transient_queryset(ndays=7).filter(tags__name='YSE')
    fastrisingtransientfilter = TransientFilter(request.GET, queryset=fastrising_transients,prefix='ysefastrise')
    table_fastrising = YSERisingTransientTable(fastrisingtransientfilter.qs,prefix='ysefastrise')
    RequestConfig(request, paginate={'per_page': 10}).configure(table_fastrising)

    rising_transients = rising_transient_queryset(ndays=7).filter(tags__name='YSE')
    risingtransientfilter = TransientFilter(request.GET, queryset=rising_transients,prefix='yserise')
    table_rising = YSERisingTransientTable(risingtransientfilter.qs,prefix='yserise')
    RequestConfig(request, paginate={'per_page': 10}).configure(table_rising)

    
    transients = Transient.objects.filter(tags__name='YSE').filter(~Q(status__name='Ignore')).order_by('-disc_date')
    transientfilter = TransientFilter(request.GET, queryset=transients,prefix='yse')
    table = YSEFullTransientTable(transientfilter.qs,prefix='yse')
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    ztftransients = Transient.objects.filter(tags__name='ZTF in YSE Fields').filter(~Q(status__name='Ignore')).order_by('-disc_date')
    ztftransientfilter = TransientFilter(request.GET, queryset=ztftransients,prefix='yseztf')
    ztftable = YSEFullTransientTable(ztftransientfilter.qs,prefix='yseztf')
    RequestConfig(request, paginate={'per_page': 10}).configure(ztftable)

    
    transients_follow = Transient.objects.filter(tags__name='YSE').order_by('-disc_date').filter(Q(status__name='FollowupRequested') | Q(status__name='Following'))
    transientfilter_follow = TransientFilter(request.GET, queryset=transients_follow,prefix='yse_follow')
    table_follow = YSETransientTable(transientfilter_follow.qs,prefix='yse_follow')
    RequestConfig(request, paginate={'per_page': 10}).configure(table_follow)

    #obsnights = view_utils.get_obs_nights_happening_soon(request.user)
    obsnights = ObservingResourceService.GetAuthorizedClassicalResource_ByUser(request.user).\
        filter(begin_date_valid__lte=datetime.datetime.utcnow()+datetime.timedelta(5)).\
        filter(begin_date_valid__gte=datetime.datetime.utcnow()-datetime.timedelta(1)).\
        select_related().order_by('begin_date_valid')

    too_resources = view_utils.get_too_resources(request.user)
    all_transient_statuses = TransientStatus.objects.all()

    # get current fields
    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)
    ut_obs_date = (datetime.datetime.utcnow()+datetime.timedelta(1)).strftime('%Y-%m-%d 00:00:00')
    time = Time(ut_obs_date, format='iso')
    tel = Observer(location=location, timezone="UTC")
    sunset_forobs = tel.sun_set_time(time,which="next")
    sunrise_forobs = tel.sun_rise_time(time,which="next")

    obs_date_now = datetime.datetime.utcnow().strftime('%Y-%m-%d 00:00:00')
    survey_obs = SurveyObservation.objects.filter(
        Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
        filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
        filter(survey_field__instrument__name__startswith = 'GPC').select_related()
    field_pk = survey_obs.values('survey_field').distinct()
    survey_fields_tonight = SurveyField.objects.filter(pk__in = field_pk).filter(~Q(obs_group__name='ZTF')).select_related()

    ut_obs_date = (datetime.datetime.utcnow()).strftime('%Y-%m-%d 00:00:00')
    time = Time(ut_obs_date, format='iso')
    tel = Observer(location=location, timezone="UTC")
    sunset_forobs = tel.sun_set_time(time,which="next")
    sunrise_forobs = tel.sun_rise_time(time,which="next")

    obs_date_last = datetime.datetime.utcnow().strftime('%Y-%m-%d 00:00:00')
    survey_obs = SurveyObservation.objects.filter(
        Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
        filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
        filter(survey_field__instrument__name__startswith = 'GPC').select_related()
    field_pk = survey_obs.values('survey_field').distinct()
    survey_fields_last_night = SurveyField.objects.filter(pk__in = field_pk).filter(~Q(obs_group__name='ZTF')).select_related()
    
    
    nowdate = datetime.datetime.utcnow()
    on_call = YSEOnCallDate.objects.filter(on_call_date__gte=nowdate-timedelta(0.5)).\
        filter(on_call_date__lte=nowdate+timedelta(0.5))

    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-')[0]
    else: anchor = ''   
    context = {'on_call_observers':on_call,
               'oncall_form':oncall_form,
               'date_start': datetime.datetime.now().__str__().split()[0],
               'date_end': (datetime.datetime.now()+datetime.timedelta(1)).__str__().split()[0],
               'transient_table':(table,'yse',transientfilter),
               'ztf_transient_table':(ztftable,'ztfyse',ztftransientfilter),
               'transient_follow_table':(table_follow,'yse_follow',transientfilter_follow),
               'transient_rising_table':(table_rising,'yserise',risingtransientfilter),
               'transient_fastrising_table':(table_fastrising,'ysefastrise',fastrisingtransientfilter),
               'upcoming_observing_nights':obsnights,
               'too_resources':too_resources,
               'all_transient_statuses':all_transient_statuses,
               'survey_fields_tonight':survey_fields_tonight,
               'survey_fields_last_night':survey_fields_last_night,
               'obs_date_last':obs_date_last.split()[0],
               'obs_date_now':obs_date_now.split()[0],
               'classical_resource_form':classical_resource_form,
               'too_resource_form':too_resource_form,
               'anchor':anchor
    }
    return render(request, 'YSE_App/yse_home.html', context)


@login_required
def yse_observing_calendar(request):

    all_obs = SurveyObservation.objects.all().select_related()
    all_dates,all_ztf_ids,all_filters = np.array([]),np.array([]),np.array([])

    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)
    tel = Observer(location=location, timezone="UTC")

    todaydate = dateutil.parser.parse(datetime.datetime.today().strftime('%Y-%m-%d 00:00:00'))
    base = todaydate-datetime.timedelta(30)
    date_list = [base + datetime.timedelta(days=x) for x in range(40)]
    obstuple = ()
    colors = ['#dd4b39', 
              '#f39c12', 
              '#00c0ef']

    for i,date in enumerate(date_list):

        time = Time(date_to_mjd(date.strftime('%Y-%m-%d 00:00:00')),format='mjd')
        
        sunset_forobs = tel.sun_set_time(time,which="next")
        sunrise_forobs = tel.sun_rise_time(time,which="next")
        survey_obs_ps1 = SurveyObservation.objects.filter(
            Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
            filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
            filter(survey_field__instrument__name='GPC1')
        survey_obs_ps2 = SurveyObservation.objects.filter(
            Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
            filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
            filter(survey_field__instrument__name='GPC2')

        if not len(survey_obs_ps1) and not len(survey_obs_ps2): continue
        ztf_obs_ps1_ids = survey_obs_ps1.filter(obs_mjd__isnull=False).values_list('survey_field__ztf_field_id',flat=True).distinct()
        ztf_sched_ps1_ids = survey_obs_ps1.filter(obs_mjd__isnull=True).values_list('survey_field__ztf_field_id',flat=True).distinct()
        ztf_obs_ps2_ids = survey_obs_ps2.filter(obs_mjd__isnull=False).values_list('survey_field__ztf_field_id',flat=True).distinct()
        ztf_sched_ps2_ids = survey_obs_ps2.filter(obs_mjd__isnull=True).values_list('survey_field__ztf_field_id',flat=True).distinct()
        
        ztf_obs_ps1_str = ''
        for z in ztf_obs_ps1_ids:
            filters = survey_obs_ps1.filter(survey_field__ztf_field_id=z).values_list('photometric_band__name',flat=True).distinct()
            ztf_obs_ps1_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))
        ztf_sched_ps1_str = ''
        for z in ztf_sched_ps1_ids:
            if z in ztf_obs_ps1_ids: continue
            filters = survey_obs_ps1.filter(survey_field__ztf_field_id=z).values_list('photometric_band__name',flat=True).distinct()
            ztf_sched_ps1_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))
        ztf_obs_ps2_str = ''
        for z in ztf_obs_ps2_ids:
            filters = survey_obs_ps2.filter(survey_field__ztf_field_id=z).values_list('photometric_band__name',flat=True).distinct()
            ztf_obs_ps2_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))
        ztf_sched_ps2_str = ''
        for z in ztf_sched_ps2_ids:
            if z in ztf_obs_ps2_ids: continue
            filters = survey_obs_ps2.filter(survey_field__ztf_field_id=z).values_list('photometric_band__name',flat=True).distinct()
            ztf_sched_ps2_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))

            
        if len(survey_obs_ps1) and len(survey_obs_ps2):
            obstuple += ((ztf_obs_ps1_str[:-2],date,
                          '%i%%'%(moon_illumination(time)*100),colors[i%len(colors)],ztf_sched_ps1_str[:-2],ztf_obs_ps2_str[:-2],ztf_sched_ps2_str[:-2]),)
        elif len(survey_obs_ps1) and not len(survey_obs_ps2):
            obstuple += ((ztf_obs_ps1_str[:-2],date,
                          '%i%%'%(moon_illumination(time)*100),colors[i%len(colors)],ztf_sched_ps1_str[:-2],'None','None'),)
        elif len(survey_obs_ps2) and not len(survey_obs_ps1):
            obstuple += (('None',date,
                          '%i%%'%(moon_illumination(time)*100),colors[i%len(colors)],'None',ztf_obs_ps2_str[:-2],ztf_sched_ps2_str[:-2]),)

    context = {
        'all_obs': obstuple,
        'utc_time': datetime.datetime.utcnow().isoformat().replace(' ','T'),
    }

    return render(request, 'YSE_App/yse_observing_calendar.html', context)

@login_required
def decam_observing_calendar(request):

    all_obs = SurveyObservation.objects.all().select_related()
    all_dates,all_decam_ids,all_filters = np.array([]),np.array([]),np.array([])

    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)
    tel = Observer(location=location, timezone="UTC")

    todaydate = dateutil.parser.parse(datetime.datetime.today().strftime('%Y-%m-%d 00:00:00'))
    base = todaydate-datetime.timedelta(30)
    date_list = [base + datetime.timedelta(days=x) for x in range(40)]
    obstuple = ()
    colors = ['#dd4b39', 
              '#f39c12', 
              '#00c0ef']
    for i,date in enumerate(date_list):

        time = Time(date_to_mjd(date.strftime('%Y-%m-%d 00:00:00')),format='mjd')
        
        sunset_forobs = tel.sun_set_time(time,which="next")
        sunrise_forobs = tel.sun_rise_time(time,which="next")
        survey_obs = SurveyObservation.objects.filter(
            Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
            filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
            filter(survey_field__obs_group__name='DECAT')
        if not len(survey_obs): continue
        decam_obs_ids = survey_obs.filter(obs_mjd__isnull=False).values_list('survey_field__field_id',flat=True).distinct()
        decam_sched_ids = survey_obs.filter(obs_mjd__isnull=True).values_list('survey_field__field_id',flat=True).distinct()
        
        decam_obs_str = ''
        for z in decam_obs_ids:
            filters = survey_obs.filter(survey_field__field_id=z).filter(survey_field__obs_group__name='DECAT').\
                values_list('photometric_band__name',flat=True).distinct()
            decam_obs_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))
        decam_sched_str = ''
        for z in decam_sched_ids:
            if z in decam_obs_ids: continue
            filters = survey_obs.filter(survey_field__decam_field_id=z).filter(survey_field__obs_group__name='DECAT').\
                values_list('photometric_band__name',flat=True).distinct()
            decam_sched_str += '%s: %s; '%(z.__str__(),','.join([f.__str__() for f in filters]))

            
        if len(survey_obs):
            obstuple += ((decam_obs_str[:-2],date,
                          '%i%%'%(moon_illumination(time)*100),colors[i%len(colors)],decam_sched_str[:-2]),)

    context = {
        'all_obs': obstuple,
        'utc_time': datetime.datetime.utcnow().isoformat().replace(' ','T'),
    }
    return render(request, 'YSE_App/yse_observing_calendar.html', context)


@login_required
def observing_night(request, telescope, obs_date, pi_name):

    # get follow requests for telescope/date
    classical_obs_date = ClassicalObservingDate.objects.filter(obs_date__startswith = obs_date).filter(resource__telescope__name = telescope.replace('_',' ')).select_related()
    if pi_name != 'None':
        classical_obs_date = classical_obs_date.filter(resource__principal_investigator__name = pi_name)
    
    #follow_requests = TransientFollowup.objects.filter(classical_resource = classical_obs_date[0].resource).\
    #    filter(valid_start__lte = classical_obs_date[0].obs_date).\
    #    filter(valid_stop__gte = classical_obs_date[0].obs_date).select_related()
    follow_requests = TransientFollowup.objects.filter(classical_resource = classical_obs_date[0].resource).\
        filter(valid_start__lte = classical_obs_date[0].resource.begin_date_valid).\
        filter(valid_stop__gte = classical_obs_date[0].resource.end_date_valid).select_related()

    followuptransientfilter = FollowupFilter(request.GET, queryset=follow_requests,prefix=telescope)
        
    followup_table = ObsNightFollowupTable(followuptransientfilter.qs,prefix=telescope,classical_obs_date=classical_obs_date)
    RequestConfig(request, paginate={'per_page': 20}).configure(followup_table)
    table = (telescope.replace('_',' '),followup_table,telescope,follow_requests,followuptransientfilter)

    location = EarthLocation.from_geodetic(
        classical_obs_date[0].resource.telescope.longitude*u.deg,classical_obs_date[0].resource.telescope.latitude*u.deg,
        classical_obs_date[0].resource.telescope.elevation*u.m)
    time = Time(str(classical_obs_date[0].obs_date).split('+')[0], format='iso')
    tel = Observer(location=location, timezone="UTC")

    sunset = tel.sun_set_time(time,which="previous").isot.split('T')[-1][:-7]
    night_start_12 = tel.twilight_evening_nautical(time,which="previous").isot.split('T')[-1][:-7]
    night_start_18 = tel.twilight_evening_astronomical(time,which="previous").isot.split('T')[-1][:-7]
    night_end_18 = tel.twilight_morning_astronomical(time,which="previous").isot.split('T')[-1][:-7]
    night_end_12 = tel.twilight_morning_nautical(time,which="previous").isot.split('T')[-1][:-7]
    sunrise = tel.sun_rise_time(time,which="previous").isot.split('T')[-1][:-7]

    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-ex')[0]
    else: anchor = ''
    context = {
        'followup_table':table,
        'anchor':anchor,
        'all_followup_statuses':FollowupStatus.objects.all(),
        'all_transient_statuses':TransientStatus.objects.all(),
        'follow_requests': follow_requests,
        'telescope':telescope.replace('_',' '),
        'obs_date':obs_date,
        'classical_obs_date':classical_obs_date[0],
        'sunriseset':(sunset,night_start_12,night_start_18,night_end_18,night_end_12,sunrise)
    }
    return render(request, 'YSE_App/observing_night.html', context)

@login_required
def yse_observing_night(request, obs_date):

    #survey_field_form = SurveyFieldForm()
    survey_obs_form = SurveyObsForm()
    
    telescope = Telescope.objects.get(name='Pan-STARRS1')
    location = EarthLocation.from_geodetic(
        telescope.longitude*u.deg,telescope.latitude*u.deg,
        telescope.elevation*u.m)

    ut_obs_date = (dateutil.parser.parse(obs_date)).strftime('%Y-%m-%d 00:00:00')
    time = Time(ut_obs_date, format='iso')
    tel = Observer(location=location, timezone="UTC")

    sunset = tel.sun_set_time(time,which="next").isot.split('T')[-1][:-7]
    night_start_12 = tel.twilight_evening_nautical(time,which="next").isot.split('T')[-1][:-7]
    night_start_18 = tel.twilight_evening_astronomical(time,which="next").isot.split('T')[-1][:-7]
    night_end_18 = tel.twilight_morning_astronomical(time,which="next").isot.split('T')[-1][:-7]
    night_end_12 = tel.twilight_morning_nautical(time,which="next").isot.split('T')[-1][:-7]
    sunrise = tel.sun_rise_time(time,which="next").isot.split('T')[-1][:-7]
    moon_illum = '%.3f'%moon_illumination(time)

    sunset_forobs = tel.sun_set_time(time,which="next")
    sunrise_forobs = tel.sun_rise_time(time,which="next")
    
    # get follow requests for telescope/date
    survey_obs = SurveyObservation.objects.filter(
        Q(mjd_requested__gte = date_to_mjd(sunset_forobs)-0.1) | Q(obs_mjd__gte = date_to_mjd(sunset_forobs)-0.1)).\
        filter(Q(mjd_requested__lte = date_to_mjd(sunrise_forobs)+0.1) | Q(obs_mjd__lte = date_to_mjd(sunrise_forobs)+0.1)).\
        filter(survey_field__instrument__name__startswith = 'GPC').select_related()
    obs_table = YSEObsNightTable(survey_obs,obs_date=obs_date)

    if request.META['QUERY_STRING']:
        anchor = request.META['QUERY_STRING'].split('-ex')[0]
    else: anchor = ''
    context = {
        'survey_obs':survey_obs,
        'all_statuses':TaskStatus.objects.all(),
        'anchor':anchor,
        'obs_date':obs_date,
        'obs_table':obs_table,
        #'survey_field_form':survey_field_form,
        'survey_obs_form':survey_obs_form,
        'sunriseset':(sunset,night_start_12,night_start_18,night_end_18,night_end_12,sunrise,moon_illum)
    }

    context['obs_date_str'] = datetime.datetime(
            int(obs_date.split('-')[0]),int(obs_date.split('-')[1]),int(obs_date.split('-')[2])).strftime('%m/%d/%Y')
    return render(request, 'YSE_App/yse_observing_night.html', context)


def download_target_list(request, telescope, obs_date):

    # get follow requests for telescope/date
    classical_obs_date = ClassicalObservingDate.objects.filter(obs_date__startswith = obs_date).filter(resource__telescope__name = telescope.replace('_',' '))
    follow_requests = TransientFollowup.objects.filter(classical_resource = classical_obs_date[0].resource).filter(valid_start__lte = classical_obs_date[0].obs_date).filter(valid_stop__gte = classical_obs_date[0].obs_date)

    location = EarthLocation.from_geodetic(
        classical_obs_date[0].resource.telescope.longitude*u.deg,classical_obs_date[0].resource.telescope.latitude*u.deg,
        classical_obs_date[0].resource.telescope.elevation*u.m)
    time = Time(str(classical_obs_date[0].obs_date).split('+')[0], format='iso')
    tel = Observer(location=location, timezone="UTC")

    
    content = "!Data {name %20} ra_h ra_m ra_s dec_d dec_m dec_s equinox {comment *}\n"
    for f in follow_requests:
        comments = ';'.join([l.comment for l in Log.objects.filter(transient_followup=f)])
        if f.transient.recent_mag():
            content += "%s  %s %s 2000 mag = %.2f comment = %s\n"%(
                f.transient.name.ljust(20),f.transient.CoordString()[0].replace(':',' '),
                f.transient.CoordString()[1].replace(':',' '),float(f.transient.recent_mag()),comments)

        else:
            content += "%s  %s %s 2000 comment = %s\n"%(
                f.transient.name.ljust(20),f.transient.CoordString()[0].replace(':',' '),
                f.transient.CoordString()[1].replace(':',' '),comments)
            
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % '%s_%s.txt'%(telescope,obs_date)

    return response

def download_targets_and_finders(request, telescope, obs_date):

    # get follow requests for telescope/date
    classical_obs_date = ClassicalObservingDate.objects.filter(obs_date__startswith = obs_date).filter(resource__telescope__name = telescope.replace('_',' '))
    follow_requests = TransientFollowup.objects.filter(classical_resource = classical_obs_date[0].resource).filter(valid_start__lte = classical_obs_date[0].obs_date).filter(valid_stop__gte = classical_obs_date[0].obs_date)

    location = EarthLocation.from_geodetic(
        classical_obs_date[0].resource.telescope.longitude*u.deg,classical_obs_date[0].resource.telescope.latitude*u.deg,
        classical_obs_date[0].resource.telescope.elevation*u.m)
    time = Time(str(classical_obs_date[0].obs_date).split('+')[0], format='iso')
    tel = Observer(location=location, timezone="UTC")

    
    content = "!Data {name %20} ra_h ra_m ra_s dec_d dec_m dec_s equinox {comment *}\n"
    content_offsets = "\n"
    findernamelist = []
    for f in follow_requests:
        content += "%s  %s %s 2000 mag = %.2f\n"%(
            f.transient.name.ljust(20),f.transient.CoordString()[0].replace(':',' '),f.transient.CoordString()[1].replace(':',' '),float(f.transient.recent_mag()))
        offdictlist, findername = view_utils.finder().finderchart_noview()
        findernamelist += [findername]
        for offdict in offdictlist:
            content_offsets += "%s  %s %s 2000 mag = %.2f raoffset=%.2f decoffset=%.2f\n"%(
                offdict['id'].ljust(20),offdict['ra'],offdict['dec'],
                float(offdict['mag']),float(offdict['ra_off']),float(offdict['dec_off']))
        
            
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % '%s_%s.txt'%(telescope,obs_date)

    return response


@login_required
def transient_detail(request, slug):

    classical_resource_form = ClassicalResourceForm()
    too_resource_form = ToOResourceForm()
    automated_spectrum_form = AutomatedSpectrumRequest()
    
    transient = Transient.objects.filter(slug=slug)
    alternate_transient = AlternateTransientNames.objects.filter(slug=slug)
    if len(alternate_transient) and not len(transient):
        transient = Transient.objects.filter(name=alternate_transient[0].transient.name).select_related()
        #return redirect('/transient_detail/%s/'%transient[0].slug)
        return HttpResponseRedirect(reverse_lazy('transient_detail',kwargs={'slug':transient[0].slug}))
    logs = Log.objects.filter(transient=transient[0].id)

    obs = None
    if len(transient) == 1:
        from django.utils import timezone
        
        transient_obj = transient.first() # This should throw an exception if more than one or none are returned
        transient_id = transient[0].id

        alt_names = AlternateTransientNames.objects.filter(transient__pk=transient_id)

        transient_followup_form = TransientFollowupForm()
        #transient_followup_form.fields["classical_resource"].queryset = \
        #       view_utils.get_authorized_classical_resources(request.user).filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('telescope__name')
        transient_followup_form.fields["too_resource"].queryset = view_utils.get_authorized_too_resources(request.user).filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('telescope__name')
        transient_followup_form.fields["queued_resource"].queryset = view_utils.get_authorized_queued_resources(request.user).filter(end_date_valid__gt = timezone.now()-timedelta(days=1)).order_by('telescope__name')

        transient_observation_task_form = TransientObservationTaskForm()

        spectrum_upload_form = SpectrumUploadForm()
        
        # Status update properties
        all_transient_statuses = TransientStatus.objects.all()
        transient_status_follow = TransientStatus.objects.get(name="Following")
        transient_status_watch = TransientStatus.objects.get(name="Watch")
        transient_status_interesting = TransientStatus.objects.get(name="Interesting")
        transient_status_ignore = TransientStatus.objects.get(name="Ignore")
        transient_comment_form = TransientCommentForm()
        # Transient tag
        all_colors = WebAppColor.objects.all().select_related()
        all_transient_tags = TransientTag.objects.all().select_related()
        assigned_transient_tags = transient_obj.tags.all().select_related()

        # GW Candidate?
        gwcand,gwimages = None,None
        for att in assigned_transient_tags:
            if att.name == 'GW Candidate':
                gwcand = GWCandidate.objects.filter(name = transient_obj.name)
                if len(gwcand):
                    gwimages = GWCandidateImage.objects.filter(gw_candidate__name = gwcand[0].name)

        # Get associated Observations
        followups = TransientFollowup.objects.filter(transient__pk=transient_id).select_related()
        if followups:
            for i in range(len(followups)):
                followups[i].observation_set = TransientObservationTask.objects.filter(followup=followups[i].id)

                if followups[i].classical_resource:
                    followups[i].resource = followups[i].classical_resource
                elif followups[i].too_resource:
                    followups[i].resource = followups[i].too_resource
                elif followups[i].queued_resource:
                    followups[i].resource = followups[i].queued_resource

                comments = Log.objects.filter(transient_followup=followups[i].id).select_related()
                comment_list = []
                for c in comments:
                    comment_list += [c.comment]
                if len(comments): followups[i].comment = '; '.join(comment_list)
                #else:
        #   followups = None

        hostdata = Host.objects.filter(pk=transient_obj.host_id).select_related()
        if hostdata:
            hostphotdata = view_utils.get_recent_phot_for_host(request.user, host_id=hostdata[0].id)
            transient_obj.hostdata = hostdata[0]

            ramin,ramax,decmin,decmax = getRADecBox(transient_obj.hostdata.ra,transient_obj.hostdata.dec,size=1/60.)
            
            transients_near_host = Transient.objects.filter(
                Q(ra__gt=ramin) & Q(ra__lt=ramax) &
                Q(dec__gt=decmin) & Q(dec__lt=decmax) & ~Q(name=transient_obj.name)).values_list('name',flat=True)
            transients_near_host = ','.join(transients_near_host)
        else:
            hostphotdata = None
            transients_near_host = None

        if hostphotdata: transient_obj.hostphotdata = hostphotdata

        lastphotdata = view_utils.get_recent_phot_for_transient(request.user, transient_id=transient_id)
        firstphotdata = view_utils.get_disc_mag_for_transient(request.user, transient_id=transient_id)
        allphotdata = view_utils.get_all_phot_for_transient(request.user, transient_id).select_related()
        #import pdb
        #pdb.set_trace()

        has_new_comment = len(Log.objects.filter(transient=transient_obj).\
                              filter(modified_date__gt=datetime.datetime.now()-datetime.timedelta(1))) > 0

        '''
        # https://django-tables2.readthedocs.io/en/latest/pages/tutorial.html
        # Candidates
        candidates = Host.objects.all().select_related()
        # Include P_Ox??
        candidatefilter = CandidateFilter(
            request.GET, queryset=candidates)#,prefix=t)
        candidate_table = CandidateTable(candidatefilter.qs,prefix=t)
        RequestConfig(request, paginate={'per_page': 10}).configure(candidate_table)
        candidate_table_context = (candidate_table,candidates,candidatefilter)
        '''

        
        # obsnights,tellist = view_utils.getObsNights(transient[0])
        # too_resources = ToOResource.objects.all()
        #
        # for i in range(len(too_resources)):
        #   telescope = too_resources[i].telescope
        #   too_resources[i].telescope_id = telescope.id
        #   observatory = Observatory.objects.get(pk=telescope.observatory_id)
        #   too_resources[i].deltahours = too_resources[i].awarded_too_hours - too_resources[i].used_too_hours
        obsnights = view_utils.get_obs_nights_happening_soon(request.user)
        too_resources = view_utils.get_too_resources(request.user)

        date = datetime.datetime.now(tz=pytz.utc)
        date_format='%m/%d/%Y %H:%M:%S'
        
        spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(request.user, transient_id, includeBadData=True)
        context = {
            'transient':transient_obj,
            'followups':followups,
            # 'telescope_list': tellist,
            'observing_nights': obsnights,
            'too_resource_list': too_resources.select_related(),
            'nowtime':date.strftime(date_format),
            'transient_followup_form': transient_followup_form,
            'transient_observation_task_form': transient_observation_task_form,
            'transient_comment_form': transient_comment_form,
            'alt_names': alt_names,
            'all_transient_statuses': all_transient_statuses,
            'transient_status_follow': transient_status_follow,
            'transient_status_watch': transient_status_watch,
            'transient_status_ignore': transient_status_ignore,
            'transient_status_interesting': transient_status_interesting,
            'logs':logs,
            'all_transient_tags': all_transient_tags,
            'assigned_transient_tags': assigned_transient_tags,
            'all_colors': all_colors,
            'all_transient_spectra': spectra,
            'gw_candidate':gwcand,
            'gw_images':gwimages,
            'spectrum_upload_form':spectrum_upload_form,
            'diff_images':TransientDiffImage.objects.filter(phot_data__photometry__transient__name=transient_obj.name),
            'classical_resource_form':classical_resource_form,
            'too_resource_form':too_resource_form,
            'new_comment':has_new_comment,
            'transients_near_host':transients_near_host
        }

        if transient_followup_form.fields["valid_start"].initial:
            context['followup_initial_dates'] = \
                (transient_followup_form.fields["valid_start"].initial.strftime('%m/%d/%Y HH:MM'),
                 transient_followup_form.fields["valid_stop"].initial.strftime('%m/%d/%Y HH:MM'))           
        
        if lastphotdata and firstphotdata:
            context['recent_mag'] = lastphotdata.mag
            context['recent_filter'] = lastphotdata.band
            context['recent_magdate'] = lastphotdata.obs_date
            context['first_mag'] = firstphotdata.mag
            context['first_filter'] = firstphotdata.band
            context['first_magdate'] = firstphotdata.obs_date
            context['allphotdata']=allphotdata
        if transient_obj.postage_stamp_file:
            context['qub_candidate'] = transient_obj.postage_stamp_file.split('/')[-1].split('_')[0]
            
        context['automated_spectrum_form'] = automated_spectrum_form


        # we need to add a submit to TNS button
        # for transients that don't have TNS names
        # - for now, this is only DECam transients
        tns_submit_logs = logs.filter(comment__startswith='Submitted to TNS')
        tns_sandbox_logs = logs.filter(comment__startswith='TNS sandbox')
        if not len(tns_submit_logs) and '_cand' in transient_obj.name and \
           'DECAT' in list(assigned_transient_tags.values_list('name',flat=True)):
            submit_to_tns = True
        else:
            submit_to_tns = False
        context['submit_to_tns'] = submit_to_tns
        if len(tns_sandbox_logs):
            context['tns_sandbox_url'] = tns_sandbox_logs[0].comment.split()[2]
        
        return render(request,
            'YSE_App/transient_detail.html',
            context)

    else:
        return Http404('Transient not found')

@login_required
def transient_edit(request, transient_id=None):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TransientForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TransientForm()

    return render(request, 'YSE_App/transient_edit.html', {'form': form})


from wsgiref.util import FileWrapper
@csrf_exempt
@login_or_basic_auth_required
def download_data(request, slug):

    if 'HTTP_AUTHORIZATION' in request.META.keys():
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    else:
        user = request.user
        
    transient = Transient.objects.filter(slug=slug)
    data = {transient[0].name:{'transient':{},'host':{},'photometry':{},'spectra':{}}}
    data[transient[0].name]['transient'] = json.loads(serializers.serialize("json", transient, use_natural_foreign_keys=True))

    if transient[0].host:
        host = Host.objects.filter(id=transient[0].host.id)
        data[transient[0].name]['host'] = json.loads(serializers.serialize("json", host, use_natural_foreign_keys=True))


    # Get photometry by user & transient
    authorized_phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(user, transient[0].id)
    if len(authorized_phot):
        data[transient[0].name]['photometry'] = json.loads(serializers.serialize("json", authorized_phot,use_natural_foreign_keys=True))

        # Get data points
        for p,pd in zip(authorized_phot,range(len(data[transient[0].name]['photometry']))):
            photdata = PhotometryService.GetAuthorizedTransientPhotData_ByPhotometry(user, p.id, includeBadData=True)
            data[transient[0].name]['photometry'][pd]['data'] = json.loads(serializers.serialize("json", photdata, use_natural_foreign_keys=True))


    # Get spectra by user & transient
    authorized_spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(user, transient[0].id, includeBadData=True)
    if len(authorized_spectra):
        data[transient[0].name]['spectra'] = json.loads(serializers.serialize("json", authorized_spectra, use_natural_foreign_keys=True))

        for s,sd in zip(authorized_spectra,range(len(data[transient[0].name]['spectra']))):
            specdata = SpectraService.GetAuthorizedTransientSpecData_BySpectrum(user, s.id, includeBadData=True)
            if specdata:
                data[transient[0].name]['spectra'][sd]['data'] = \
                    json.loads(serializers.serialize("json", specdata, use_natural_foreign_keys=True))

    response = JsonResponse(data)
    response['Content-Disposition'] = 'attachment; filename=%s' % '%s_data.json'%slug
    return response

@csrf_exempt
@login_or_basic_auth_required
def download_photometry(request, slug):

    if 'HTTP_AUTHORIZATION' in request.META.keys():
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    else:
        user = request.user

        
    content = ""
        
    transient = Transient.objects.filter(slug=slug)
    data = {transient[0].name:{'transient':{},'host':{},'photometry':{},'spectra':{}}}
    data[transient[0].name]['transient'] = json.loads(serializers.serialize("json", transient, use_natural_foreign_keys=True))
    for k in data[transient[0].name]['transient'][0]['fields'].keys():
        if k not in ['created_by','modified_by','candidate_hosts']:
            content += "# %s: %s\n"%(k.upper(),data[transient[0].name]['transient'][0]['fields'][k])
            
    content += "\n"
    content += "VARLIST:  MJD        FLT  FLUXCAL   FLUXCALERR    MAG     MAGERR     MAGSYS   TELESCOPE    INSTRUMENT   DQ\n"
    linefmt =  "OBS:      %.3f  %s  %.3f  %.3f  %.3f  %.3f  %s  %s  %s  %s\n"

    
    # Get photometry by user & transient
    authorized_phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(user, transient[0].id)
    if len(authorized_phot):
        data[transient[0].name]['photometry'] = json.loads(serializers.serialize("json", authorized_phot,use_natural_foreign_keys=True))

        # Get data points
        for p,pd in zip(authorized_phot,range(len(data[transient[0].name]['photometry']))):

            telescope = data[transient[0].name]['photometry'][pd]['fields']['instrument'].split(' - ')[0]
            instrument = data[transient[0].name]['photometry'][pd]['fields']['instrument'].split(' - ')[1]
            telescope = telescope.replace(' ','_')
            instrument = instrument.replace(' ','_')
            
            photdata = PhotometryService.GetAuthorizedTransientPhotData_ByPhotometry(user, p.id, includeBadData=True).order_by('obs_date')
            data[transient[0].name]['photometry'][pd]['data'] = json.loads(serializers.serialize("json", photdata, use_natural_foreign_keys=True))

            for d in data[transient[0].name]['photometry'][pd]['data']:
                mjd = date_to_mjd(d['fields']['obs_date'])
                if not len(d['fields']['data_quality']):
                    data_quality = None
                else:
                    data_quality = ','.join(d['fields']['data_quality'])
                if d['fields']['flux'] and d['fields']['flux_zero_point'] and not d['fields']['mag']:
                    if d['fields']['flux_err']: flux_err = d['fields']['flux_err']
                    else: flux_err = 0
                    
                    flux = d['fields']['flux']*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                    flux_err = flux_err*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                    mag = -2.5*np.log10(flux)+27.5
                    mag_err = 2.5/np.log(10)*flux_err/flux

                    content += linefmt%(
                        mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,mag,mag_err,d['fields']['mag_sys'],telescope,instrument,data_quality)
                    
                elif not d['fields']['flux'] and d['fields']['mag']:
                    if d['fields']['mag_err']: mag_err = d['fields']['mag_err']
                    else: mag_err = 0
                    
                    flux = 10**(-0.4*(d['fields']['mag']-27.5))
                    flux_err = 0.4*np.log(10)*flux*mag_err
                    
                    content += linefmt%(
                        mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,d['fields']['mag'],mag_err,d['fields']['mag_sys'],telescope,instrument,data_quality)
                    
                elif d['fields']['flux'] and d['fields']['flux_zero_point'] and d['fields']['mag']:
                    if d['fields']['flux_err']: flux_err = d['fields']['flux_err']
                    else: flux_err = 0
                    if d['fields']['mag_err']: mag_err = d['fields']['mag_err']
                    else: mag_err = 0
                    
                    flux = d['fields']['flux']*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                    flux_err = flux_err*10**(0.4*(d['fields']['flux_zero_point']-27.5))

                    content += linefmt%(
                        mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,d['fields']['mag'],mag_err,d['fields']['mag_sys'],telescope,instrument,data_quality)

                elif d['fields']['flux'] and d['fields']['mag']:
                    # if somebody didn't provide a ZPT, we can still work with this
                    if d['fields']['mag_err']: mag_err = d['fields']['mag_err']
                    else: mag_err = 0
                    
                    flux = 10**(-0.4*(d['fields']['mag']-27.5))
                    flux_err = 0.4*np.log(10)*flux*mag_err
                    
                    content += linefmt%(
                        mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,d['fields']['mag'],mag_err,d['fields']['mag_sys'],telescope,instrument,data_quality)
                    
                else:
                    continue

    content += "# END: \n"
                
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % '%s_data.snana.txt'%slug

    return response

@csrf_exempt
@login_or_basic_auth_required
def download_bulk_photometry(request, query_title):

    if 'HTTP_AUTHORIZATION' in request.META.keys():
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    else:
        user = request.user


    query = Query.objects.filter(title=unquote(query_title))
    if len(query):
        cursor = connections['explorer'].cursor()
        cursor.execute(query[0].sql.replace('%','%%'), ())
        transients = Transient.objects.filter(name__in=(x[0] for x in cursor)).order_by('-disc_date')
        cursor.close()

    elif getattr(yse_python_queries,query_title):
        transients = getattr(yse_python_queries,query_title)()

    s = BytesIO()
    archive = zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED)
    for transient in transients:
        
        content = ""

        data = {transient.name:{'transient':{},'host':{},'photometry':{},'spectra':{}}}
        data[transient.name]['transient'] = json.loads(serializers.serialize("json", Transient.objects.filter(name=transient.name), use_natural_foreign_keys=True))
        for k in data[transient.name]['transient'][0]['fields'].keys():
            if k not in ['created_by','modified_by','candidate_hosts']:
                content += "# %s: %s\n"%(k.upper(),data[transient.name]['transient'][0]['fields'][k])

        content += "\n"
        content += "MJD,FLT,FLUXCAL,FLUXCALERR,MAG,MAGERR,MAGSYS,TELESCOPE,INSTRUMENT\n"
        linefmt =  "%.3f,%s,%.3f,%.3f,%.3f,%.3f,%s,%s,%s\n"


        # Get photometry by user & transient
        authorized_phot = PhotometryService.GetAuthorizedTransientPhotometry_ByUser_ByTransient(user, transient.id)
        if len(authorized_phot):
            data[transient.name]['photometry'] = json.loads(serializers.serialize("json", authorized_phot,use_natural_foreign_keys=True))

            # Get data points
            for p,pd in zip(authorized_phot,range(len(data[transient.name]['photometry']))):

                telescope = data[transient.name]['photometry'][pd]['fields']['instrument'].split(' - ')[0]
                instrument = data[transient.name]['photometry'][pd]['fields']['instrument'].split(' - ')[1]

                photdata = PhotometryService.GetAuthorizedTransientPhotData_ByPhotometry(user, p.id, includeBadData=True).order_by('obs_date')
                data[transient.name]['photometry'][pd]['data'] = json.loads(serializers.serialize("json", photdata, use_natural_foreign_keys=True))

                for d in data[transient.name]['photometry'][pd]['data']:
                    mjd = date_to_mjd(d['fields']['obs_date'])
                    if d['fields']['flux'] and d['fields']['flux_zero_point'] and not d['fields']['mag']:
                        if d['fields']['flux_err']: flux_err = d['fields']['flux_err']
                        else: flux_err = 0

                        flux = d['fields']['flux']*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                        flux_err = flux_err*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                        mag = -2.5*np.log10(flux)+27.5
                        mag_err = 2.5/np.log(10)*flux_err/flux

                        content += linefmt%(
                            mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,mag,mag_err,d['fields']['mag_sys'],telescope,instrument)

                    elif not d['fields']['flux'] and d['fields']['mag']:
                        if d['fields']['mag_err']: mag_err = d['fields']['mag_err']
                        else: mag_err = 0

                        flux = 10**(-0.4*(d['fields']['mag']-27.5))
                        flux_err = 0.4*np.log(10)*flux*mag_err

                        content += linefmt%(
                            mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,d['fields']['mag'],mag_err,d['fields']['mag_sys'],telescope,instrument)

                    elif d['fields']['flux'] and d['fields']['flux_zero_point'] and d['fields']['mag']:
                        if d['fields']['flux_err']: flux_err = d['fields']['flux_err']
                        else: flux_err = 0
                        if d['fields']['mag_err']: mag_err = d['fields']['mag_err']
                        else: mag_err = 0

                        flux = d['fields']['flux']*10**(0.4*(d['fields']['flux_zero_point']-27.5))
                        flux_err = flux_err*10**(0.4*(d['fields']['flux_zero_point']-27.5))

                        content += linefmt%(
                            mjd,d['fields']['band'].split(' - ')[1],flux,flux_err,d['fields']['mag'],mag_err,d['fields']['mag_sys'],telescope,instrument)

                    else:
                        continue

        archive.writestr('%s.csv'%transient.name,content)

    archive.close()
    response = HttpResponse(s.getvalue(), content_type='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename=YSEPZ_transient_photometry.zip'
    return response

@csrf_exempt
@login_or_basic_auth_required
def download_spectra(request, slug):

    if 'HTTP_AUTHORIZATION' in request.META.keys():
        auth_method, credentials = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
        credentials = base64.b64decode(credentials.strip()).decode('utf-8')
        username, password = credentials.split(':', 1)
        user = auth.authenticate(username=username, password=password)
    else:
        user = request.user


    transient = Transient.objects.get(slug=slug)
    
    st = BytesIO()
    archive = zipfile.ZipFile(st, 'w', zipfile.ZIP_DEFLATED)
    authorized_spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(user, transient.id, includeBadData=True)
    if len(authorized_spectra):

        for s in authorized_spectra:
            content = ""
            data = {}
            #data['spectra'] = json.loads(serializers.serialize("json", s, use_natural_foreign_keys=True))
            #import pdb; pdb.set_trace()
            for k in s.__dict__.keys(): #data['spectra'].keys():
                if k not in ['_state', 'id', 'created_by_id', 'created_date', 'modified_by_id', 'modified_date']:
                    content += "# %s: %s\n"%(k.upper(),s.__dict__[k])
            
            specdata = SpectraService.GetAuthorizedTransientSpecData_BySpectrum(user, s.id, includeBadData=True)
            if specdata:
                content += "\n"
                content += "wavelength,flux,fluxerr\n"
                linefmt =  "%.3f,%8.5e,%8.5e\n"

                for sd in specdata.order_by('wavelength'):
                    if sd.flux_err:
                        content += linefmt%(sd.wavelength,sd.flux,sd.flux_err)
                    else:
                        content += linefmt%(sd.wavelength,sd.flux,-99)

                archive.writestr('%s-%s-%s.csv'%(transient.name,s.instrument.name,s.obs_date.isoformat().split('T')[0]),content)

    archive.close()
    response = HttpResponse(st.getvalue(), content_type='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename=%s_spectra.zip'%transient.name
    return response

@csrf_exempt
@login_or_basic_auth_required
def upload_spectrum(request):

    if request.method == 'POST':
        form = SpectrumUploadForm(request.POST, request.FILES)
        if form.is_valid():
            #form.save()
            transient = Transient.objects.filter(id=form.data['transient'])[0]
            tspec = TransientSpectrum.objects.filter(transient=transient).\
                filter(instrument=form.data['instrument']).\
                filter(obs_group=form.data['obs_group']).\
                filter(obs_date=form.data['obs_date'])

            specdict = {'transient':transient,'ra':form.data['ra'],
                        'dec':form.data['dec'],'obs_date':form.data['obs_date'],
                        'obs_group':ObservationGroup.objects.filter(id=form.data['obs_group'])[0],
                        'instrument':Instrument.objects.filter(id=form.data['instrument'])[0],
                        'created_by':request.user,'modified_by':request.user}
            
            if form.data['spec_phase']:
                specdict['spec_phase'] = form.data['spec_phase']
            #if form.data['data_quality']:
            #    specdict['data_quality'] = DataQuality.objects.get(pk=form.data['data_quality'])
            if not len(tspec):
                tspec = TransientSpectrum.objects.create(**specdict)
                if form.data['data_quality']:
                    tspec.data_quality.add(DataQuality.objects.get(pk=form.data['data_quality']))
            else:
                tspec.update(**specdict)
                tspec = tspec[0]
            tspec.save()

            if 'permissions' in form.data.keys() and form.data['permissions']:
                for p in form.cleaned_data['permissions']:
                    tspec.groups.add(Group.objects.filter(name=p)[0])
                tspec.save()
            
            existingspec = TransientSpecData.objects.filter(spectrum=tspec)
            if len(existingspec):
                existingspec.delete()


            td = []
            for line in request.FILES['filename']:
                line = line.decode('utf-8').replace('\n','')
                if line.startswith('#'): continue
                if len(line.split()) == 3:
                    wavelength,flux,flux_err = line.split()
                    wavelength,flux,flux_err = float(wavelength),float(flux),float(flux_err)
                    td += [TransientSpecData(
                        spectrum=tspec,wavelength=wavelength,flux=flux,flux_err=flux_err,
                        created_by=request.user,modified_by=request.user)]
                elif len(line.split()) == 2:
                    wavelength,flux = line.split()
                    wavelength,flux = float(wavelength),float(flux)
                    td += [TransientSpecData(
                        spectrum=tspec,wavelength=wavelength,flux=flux,
                        created_by=request.user,modified_by=request.user)]
                elif len(line.split(',')) == 3:
                    wavelength,flux,flux_err = line.split(',')
                    wavelength,flux,flux_err = float(wavelength),float(flux),float(flux_err)
                    td += [TransientSpecData(
                        spectrum=tspec,wavelength=wavelength,flux=flux,flux_err=flux_err,
                        created_by=request.user,modified_by=request.user)]
                elif len(line.split(',')) == 2:
                    wavelength,flux = line.split(',')
                    wavelength,flux = float(wavelength),float(flux)
                    td += [TransientSpecData(
                        spectrum=tspec,wavelength=wavelength,flux=flux,
                        created_by=request.user,modified_by=request.user)]
                else:
                    raise RuntimeError('bad input')

            TransientSpecData.objects.bulk_create(td)
                
            return redirect('transient_detail', slug=transient.slug) #HttpResponseRedirect(reverse_lazy('transient_detail',transient.slug))
    else:
        form = SpectrumUploadForm()
    return render(request, 'YSE_App/form_snippets/spectrum_upload_form.html', {
        'form': form
    })

@csrf_exempt
@login_or_basic_auth_required
def change_status_for_query(request, query_id, status_id):

    transients = []
    q = UserQuery.objects.get(pk=query_id)
    if q.query:
        try:
            cursor = connections['explorer'].cursor()
            cursor.execute(q.query.sql.replace('%', '%%'), ())
            transients = Transient.objects.filter(name__in=(x[0] for x in cursor)).order_by('-disc_date')
            cursor.close()
        except:
            # Query bombed
            pass


    elif q.python_query:
        transients = getattr(yse_python_queries,q.python_query)()

    new_status = TransientStatus.objects.get(pk=status_id)
    for t in transients:
        t.status = new_status
        t.save()

    return redirect('personaldashboard')

@login_required
def delete_followup(request,followup_id):
    followup = get_object_or_404(TransientFollowup,pk=followup_id)
    slug = followup.transient.slug
    followup.delete()
    return HttpResponseRedirect(reverse_lazy('transient_detail',kwargs={'slug':slug}))
    
@method_decorator(login_required, name='dispatch')
class SearchResultsView(ListView):
    model = Transient
    template_name = 'YSE_App/search_results.html'

    def get_context_data(self):
        query = self.request.GET.get('q')

        transients = None
        # a few use cases
        # if there's a gap or a comma in the middle, assume RA/Dec
        size = 5/3600. # box size
        if ',' in query or len(query.split()) > 1:
            if ',' in query:
                if len(query.split(',')) == 2:
                    ra,dec = query.split(',')
                elif len(query.split(',')) == 3:
                    ra,dec,size = query.split(',')
            else:
                if len(query.split()) == 2:
                    ra,dec = query.split()
                elif len(query.split()) == 3:
                    ra,dec,size = query.split()
            try:
                ra,dec = float(ra),float(dec)
                decimal = True
            except:
                sc = SkyCoord(ra,dec,unit=(u.hour,u.deg))
                ra,dec = sc.ra.deg,sc.dec.deg
                decimal = False

            ramin,ramax,decmin,decmax = getRADecBox(ra,dec,size=float(size))
            transients = Transient.objects.filter(Q(ra__gt=ramin) & Q(ra__lt=ramax) & Q(dec__gt=decmin) & Q(dec__lt=decmax))
                
        if transients is None:
            # otherwise execute a simple search on name
            transients = Transient.objects.filter(name__icontains=query)
        
        context = super().get_context_data()
        transientfilter = TransientFilter(self.request.GET, queryset=transients,prefix='')
        table = TransientTable(transientfilter.qs,prefix='')
        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        context['transient_search_results'] = (table,'Search Results','Search Results',transientfilter)

        return context

#@login_required
#def atlas_forced_phot(request,slug):
#
#    from YSE_App.data_ingest import kirstys_script
#    
#    transient = Transient.objects.get(slug=slug)
#
#    ### request forced photometry for this transient.name from ATLAS
#    ###  transient.ra, transient.dec
#
#    ### save the photometry to the database
#
#    context = {'msg':'success'}
#    #response = HttpResponse(context, content_type='text/plain') #JsonResponse(context)
#    return JsonResponse(context) #HttpResponse('')

    
@login_required
def ztf_forced_phot(request,slug):


    from YSE_App.data_ingest import ZTF_Forced_Phot

    transient = Transient.objects.get(slug=slug)

    # make sure this request wasn't run w/i the last 12 hours
    old_log = Log.objects.filter(transient=transient).\
        filter(modified_date__gt=datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)-datetime.timedelta(0.5))
    if len(old_log):
        context = {'msg':'error: forced phot was requested %.1f hours ago (must be >12)'%((datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)-old_log[0].modified_date).seconds/3600.)}
        #response = HttpResponse(context, content_type='text/plain') #JsonResponse(context)
        return JsonResponse(context) #HttpResponse('')
    
    # run ZTF forced phot script
    ztf = ZTF_Forced_Phot.ZTF_Forced_Phot(
        ztf_email_address='%s@gmail.com'%djangoSettings.SMTP_LOGIN,ztf_email_password=djangoSettings.SMTP_PASSWORD,
        ztf_email_imapserver='imap.gmail.com',ztf_user_address='%s@gmail.com'%djangoSettings.SMTP_LOGIN,
        ztf_user_password=djangoSettings.ZTFPASS)

    log_file_name = ztf.run_ztf_fp(
        all_jd=False, days=60, decl=transient.dec, directory_path=djangoSettings.ZTFTMPDIR,
        do_plot=False, emailcheck=0, fivemindelay=60, jdend=None,
        jdstart=None, logfile=None, mjdend=None, mjdstart=None,
        plotfile=None, ra=transient.ra, skip_clean=False, source_name=slug,
        verbose=False)

    # then need to do some logging
    commentstr = """ZTF Forced Phot
log_file_name=%s
job_submitted=%s"""%(log_file_name,datetime.datetime.utcnow().isoformat())

    l = Log.objects.create(
        created_by=request.user,modified_by=request.user,
        transient=transient,comment=commentstr)

    context = {'msg':'success'}
    #response = HttpResponse(context, content_type='text/plain') #JsonResponse(context)
    return JsonResponse(context) #HttpResponse('')

from django_tables2 import SingleTableView


class CandidatesListView(SingleTableView):
    model = Host
    table_class = CandidatesTable
    template_name = 'YSE_App/candidates.html'