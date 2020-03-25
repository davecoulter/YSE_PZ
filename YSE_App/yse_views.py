from django.shortcuts import render, get_object_or_404, render_to_response
from .table_utils import FieldTransientTable,AdjustFieldTransientTable,RisingTransientFilter
from .queries.yse_python_queries import *
from .queries import yse_python_queries
import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django.db.models import Count, Value, Max, Min
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

@login_required
def yse_planning(request):

	# rising transients
	rising_transients = rising_transient_queryset(ndays=7).filter(~Q(status__name='Ignore')).filter(~Q(tags__name='YSE'))

	recent_mag_raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
         SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
         WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
         ORDER BY pd2.obs_date DESC
         LIMIT 1
     )
"""
	rising_transients = rising_transients.annotate(recent_mag=RawSQL(recent_mag_raw_query,()))

	days_from_disc_query = """SELECT DATEDIFF(curdate(), t.disc_date) as days_since_disc
FROM YSE_App_transient t WHERE YSE_App_transient.id = t.id"""
	rising_transients = rising_transients.annotate(days_since_disc=RawSQL(days_from_disc_query,()))
	
	risingtransientfilter = RisingTransientFilter(request.GET, queryset=rising_transients,prefix='yserise')
	table_rising = FieldTransientTable(risingtransientfilter.qs,prefix='yserise')
	RequestConfig(request, paginate={'per_page': 10}).configure(table_rising)

	# possibly interesting transients
	good_transients = Transient.objects.filter(~Q(status__name='Ignore'))

	recent_mag_raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
         SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
         WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
         ORDER BY pd2.obs_date DESC
         LIMIT 1
     )
"""
	good_transients = good_transients.annotate(recent_mag=RawSQL(recent_mag_raw_query,())).filter(~Q(tags__name='YSE'))

	days_from_disc_query = """SELECT DATEDIFF(curdate(), t.disc_date) as days_since_disc
FROM YSE_App_transient t WHERE YSE_App_transient.id = t.id"""
	good_transients = good_transients.annotate(days_since_disc=RawSQL(days_from_disc_query,()))
	
	goodtransientfilter = RisingTransientFilter(request.GET, queryset=good_transients,prefix='ysegood')
	table_good = FieldTransientTable(goodtransientfilter.qs,prefix='ysegood')
	RequestConfig(request, paginate={'per_page': 10}).configure(table_good)

	# transients w/i 15 deg of existing fields
	nearby_transients = sne_15deg_from_yse() #qs_start=rising_transients)

	recent_mag_raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
         SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
         WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
         ORDER BY pd2.obs_date DESC
         LIMIT 1
     )
"""

	nearby_transients = nearby_transients.annotate(recent_mag=RawSQL(recent_mag_raw_query,())).filter(~Q(tags__name='YSE'))

	days_from_disc_query = """SELECT DATEDIFF(curdate(), t.disc_date) as days_since_disc
FROM YSE_App_transient t WHERE YSE_App_transient.id = t.id"""
	nearby_transients = nearby_transients.annotate(days_since_disc=RawSQL(days_from_disc_query,()))

	nearbytransientfilter = RisingTransientFilter(request.GET, queryset=nearby_transients,prefix='ysenearby')
	table_nearby = AdjustFieldTransientTable(nearbytransientfilter.qs,prefix='ysenearby')
	RequestConfig(request, paginate={'per_page': 10}).configure(table_nearby)

	
	if request.META['QUERY_STRING']:
		anchor = request.META['QUERY_STRING'].split('-')[0]
	else: anchor = ''	
	context = {'transient_rising_table':(table_rising,'yserise',risingtransientfilter),
			   'transient_good_table':(table_good,'ysegood',goodtransientfilter),
			   'transient_nearby_table':(table_nearby,'ysenearby',nearbytransientfilter),
			   'anchor':anchor
	}
	return render(request, 'YSE_App/yse_planning.html', context)

@login_required
@csrf_exempt
def yse_msb_change(request,field_to_drop,field_to_add,snid,ra_to_add,dec_to_add):
	# get the field to drop
	drop_field = SurveyField.objects.filter(field_id=field_to_drop)[0]
	instrument = drop_field.instrument
	
	# field to add
	#field_to_add = '%s.%s'%(field_to_drop.split('.')[0],snid)
	yse_group = ObservationGroup.objects.filter(name='YSE')[0]
	add_dict = {'created_by_id':request.user.id,'modified_by_id':request.user.id,'obs_group':yse_group,
				'ra_cen':ra_to_add,'dec_cen':dec_to_add,'ztf_field_id':field_to_add.split('.')[0],
				'cadence':3,'instrument':instrument,'width_deg':3.3,'height_deg':3.3,
				'field_id':field_to_add}

	add_field = SurveyField.objects.filter(field_id=field_to_add)
	if not len(add_field):
		add_field = SurveyField.objects.create(**add_dict)
	else: add_field = add_field[0]
	
	msb = SurveyFieldMSB.objects.filter(name=field_to_add.split('.')[0])[0]
	msb.survey_fields.remove(drop_field)
	msb.survey_fields.add(add_field)
	msb.save()

	return redirect('adjust_yse_pointings', field_name=field_to_add,snid=snid)
