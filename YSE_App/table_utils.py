from django.shortcuts import render
from .models import *
from . import view_utils
import django_tables2 as tables
from django_tables2 import RequestConfig
from django.db.models import F, Q
from django.db.models.functions import Length, Substr
from django.db.models import Count, Value, Max, Min
from django_tables2 import A
from django.db import models
from .data import PhotometryService
import time
	
class TransientTable(tables.Table):
	
	ra_string = tables.Column(accessor='CoordString.0',
							  verbose_name='RA',orderable=True,order_by='ra')
	dec_string = tables.Column(accessor='CoordString.1',
							   verbose_name='DEC',orderable=True,order_by='dec')
	disc_date_string = tables.Column(accessor='disc_date_string',
									 verbose_name='Disc. Date',orderable=True,order_by='disc_date')
	disc_mag = tables.Column(accessor='disc_mag',
							 verbose_name='Disc. Mag',orderable=True)
	
	def __init__(self,*args, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_columns['host.redshift'].verbose_name = 'Host Redshift'
		self.base_columns['best_spec_class'].verbose_name = 'Spec. Class'

	def order_disc_mag(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transientphotometry__id__in=phot_ids)
		disc_query = Q(transientphotometry__transientphotdata__discovery_point = 1)
		queryset = queryset.annotate(
			disc_mag=Min('transientphotometry__transientphotdata__mag',filter=phot_data_query & disc_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'disc_mag')
		return (queryset, True)
			
	class Meta:
		model = Transient
		fields = ('name','ra_string','dec_string','disc_date_string','disc_mag','obs_group','best_spec_class','redshift','host.redshift','status')
		template_name='YSE_App/django-tables2/bootstrap.html'
		attrs = {
			'th' : {
				'_ordering': {
					'orderable': 'sortable', # Instead of `orderable`
					'ascending': 'ascend',	 # Instead of `asc`
					'descending': 'descend'	 # Instead of `desc`
				}
			},
			'class': 'table table-bordered table-hover',
			'id': 'k2_transient_tbl',
			"columnDefs": [
				{"type":"title-numeric","targets":1},
				{"type":"title-numeric","targets":2},
			],
			"order": [[ 3, "desc" ]],
		}
		
def dashboard_tables(request):
	
	k2_transients = Transient.objects.all()
	
	table = TransientTable(k2_transients)
	RequestConfig(request, paginate={'per_page': 10}).configure(table)
			
	context = {'k2_transients': table}
	
	return render(request, 'YSE_App/dashboard_table.html', context)
