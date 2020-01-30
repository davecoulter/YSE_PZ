from YSE_App.models import *
from django.db.models import DateTimeField, ExpressionWrapper, F, Q
from django.db.models.functions import Greatest
from django.db.models.expressions import RawSQL
from datetime import timedelta
import astropy.coordinates as cd
import astropy.units as u
import numpy as np
from YSE_App.common.utilities import *
from itertools import chain
from django.db import connection,connections

def makeRegistrar():
	registry = {}
	def registrar(func):
		registry[func.__name__] = func
		return func	 # normally a decorator returns a wrapped function,
					 # but here we return func unmodified, after registering it
	registrar.all = registry
	return registrar
python_query_reg = makeRegistrar()

def annotate_rising_transient_qs(qs):

	g_filters = "('g-ZTF', 'g', 'V', 'gp', 'g-Sloan')"
	r_filters = "('r-ZTF', 'r', 'rp', 'r-Sloan')"
	i_filters = "('i-ZTF', 'i')"

	last_mag_query = """
SELECT %s
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p, YSE_App_photometricband pb, YSE_App_instrument i
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pb.instrument_id	= i.id AND
   pd.band_id = pb.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2 , YSE_App_photometricband pb2, YSE_App_instrument i2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND pd2.band_id = pb2.id AND pb2.instrument_id = i2.id AND i2.name != 'Gaia-Photometric' AND
		 ISNULL(pd2.data_quality_id) = True AND pb2.name IN %s
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1 OFFSET %i
	 )
"""	

	# g/V rise
	qs = qs.annotate(recent_g_mag=RawSQL(last_mag_query%('pd.mag',g_filters,0),())).\
			annotate(recent_g_mag_err=RawSQL(last_mag_query%('pd.mag_err',g_filters,0),())).\
			annotate(recent_g_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',g_filters,0),())).\
			annotate(second_most_recent_g_mag=RawSQL(last_mag_query%('pd.mag',g_filters,1),())).\
			annotate(second_most_recent_g_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',g_filters,1),())).\
			annotate(second_most_recent_g_ulim=RawSQL(last_mag_query%('-2.5*LOG10(pd.flux+3*pd.flux_err)+27.5 as lim',g_filters,1),())).\
			annotate(second_most_recent_g_flux=RawSQL(last_mag_query%('pd.flux',g_filters,1),())).\
			annotate(second_most_recent_g_flux_err=RawSQL(last_mag_query%('pd.flux_err',g_filters,1),()))

	qs = qs.annotate(dm_g=-1*(F('recent_g_mag') - F('second_most_recent_g_mag')))
	qs = qs.annotate(dt_g=F('recent_g_obs') - F('second_most_recent_g_obs'))
	qs = qs.annotate(rise_rate_g=F('dm_g')/(Greatest(F('dt_g'),4*60*60)/24/60/60))
	qs = qs.annotate(dm_lim_g=-1*(F('recent_g_mag') - F('second_most_recent_g_ulim')))
	qs = qs.annotate(rise_rate_g_lim=F('dm_lim_g')/(F('dt_g')/24/60/60))
	qs = qs.annotate(rise_rate_g_sig=F('dm_g')/F('recent_g_mag_err'))
	qs = qs.annotate(rise_rate_g_lim_sig=F('dm_lim_g')/F('recent_g_mag_err'))

	# r rise
	qs = qs.\
			annotate(recent_r_mag=RawSQL(last_mag_query%('pd.mag',r_filters,0),())).\
			annotate(recent_r_mag_err=RawSQL(last_mag_query%('pd.mag_err',r_filters,0),())).\
			annotate(recent_r_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',r_filters,0),())).\
			annotate(second_most_recent_r_mag=RawSQL(last_mag_query%('pd.mag',r_filters,1),())).\
			annotate(second_most_recent_r_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',r_filters,1),())).\
			annotate(second_most_recent_r_ulim=RawSQL(last_mag_query%('-2.5*LOG10(pd.flux+3*pd.flux_err)+27.5 as lim',r_filters,1),())).\
			annotate(second_most_recent_r_flux=RawSQL(last_mag_query%('pd.flux',r_filters,1),())).\
			annotate(second_most_recent_r_flux_err=RawSQL(last_mag_query%('pd.flux_err',r_filters,1),()))

	qs = qs.annotate(dm_r=-1*(F('recent_r_mag') - F('second_most_recent_r_mag')))
	qs = qs.annotate(dt_r=F('recent_r_obs') - F('second_most_recent_r_obs'))
	qs = qs.annotate(rise_rate_r=F('dm_r')/(F('dt_r')/24/60/60))
	qs = qs.annotate(dm_lim_r=-1*(F('recent_r_mag') - F('second_most_recent_r_ulim')))
	qs = qs.annotate(rise_rate_r_lim=F('dm_lim_r')/(F('dt_r')/24/60/60))
	qs = qs.annotate(rise_rate_r_sig=F('dm_r')/F('recent_r_mag_err'))
	qs = qs.annotate(rise_rate_r_lim_sig=F('dm_lim_r')/F('recent_r_mag_err'))

	# i rise
	qs = qs.\
		annotate(recent_i_mag=RawSQL(last_mag_query%('pd.mag',i_filters,0),())).\
		annotate(recent_i_mag_err=RawSQL(last_mag_query%('pd.mag_err',i_filters,0),())).\
		annotate(recent_i_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',i_filters,0),())).\
		annotate(second_most_recent_i_mag=RawSQL(last_mag_query%('pd.mag',i_filters,1),())).\
		annotate(second_most_recent_i_obs=RawSQL(last_mag_query%('UNIX_TIMESTAMP(pd.obs_date)',i_filters,1),())).\
		annotate(second_most_recent_i_ulim=RawSQL(last_mag_query%('-2.5*LOG10(pd.flux+3*pd.flux_err)+27.5 as lim',i_filters,1),())).\
		annotate(second_most_recent_i_flux=RawSQL(last_mag_query%('pd.flux',i_filters,1),())).\
		annotate(second_most_recent_i_flux_err=RawSQL(last_mag_query%('pd.flux_err',i_filters,1),()))

	qs = qs.annotate(dm_i=-1*(F('recent_i_mag') - F('second_most_recent_i_mag')))
	qs = qs.annotate(dt_i=F('recent_i_obs') - F('second_most_recent_i_obs'))
	qs = qs.annotate(rise_rate_i=F('dm_i')/(F('dt_i')/24/60/60))
	qs = qs.annotate(dm_lim_i=-1*(F('recent_i_mag') - F('second_most_recent_i_ulim')))
	qs = qs.annotate(rise_rate_i_lim=F('dm_lim_i')/(F('dt_i')/24/60/60))
	qs = qs.annotate(rise_rate_i_sig=F('dm_i')/F('recent_i_mag_err'))
	qs = qs.annotate(rise_rate_i_lim_sig=F('dm_lim_i')/F('recent_i_mag_err'))

	return qs

@python_query_reg
def fastrising_transient_queryset(ndays=7):

	# g/V rise
	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(ndays))
	qs = annotate_rising_transient_qs(qs)
	
	qs_final = qs.filter((Q(rise_rate_g__gte=0.5) & (Q(rise_rate_g_sig__gte=1)))|
						 (Q(rise_rate_g_lim__gte=0.5) & (Q(rise_rate_g_lim_sig__gte=1)))|
						 (Q(rise_rate_r__gte=0.5) & (Q(rise_rate_r_sig__gte=1)))|
						 (Q(rise_rate_r_lim__gte=0.5) & (Q(rise_rate_r_lim_sig__gte=1)))|
						 (Q(rise_rate_i__gte=0.5) & (Q(rise_rate_i_sig__gte=1)))|
						 (Q(rise_rate_i_lim__gte=0.5) & (Q(rise_rate_i_lim_sig__gte=1))))

	return qs_final

@python_query_reg
def rising_transient_queryset(ndays=14):

	# g/V rise
	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(ndays))	
	qs = annotate_rising_transient_qs(qs)
	qs_final = qs.filter((Q(rise_rate_g__gte=0) & (Q(rise_rate_g_sig__gte=1)))|
						 (Q(rise_rate_g_lim__gte=0) & (Q(rise_rate_g_lim_sig__gte=1)))|
						 (Q(rise_rate_r__gte=0) & (Q(rise_rate_r_sig__gte=1)))|
						 (Q(rise_rate_r_lim__gte=0) & (Q(rise_rate_r_lim_sig__gte=1)))|
						 (Q(rise_rate_i__gte=0) & (Q(rise_rate_i_sig__gte=1)))|
						 (Q(rise_rate_i_lim__gte=0) & (Q(rise_rate_i_lim_sig__gte=1))))
	
	return qs_final

@python_query_reg
def recent_rising_transient_queryset(ndays=5):

	# g/V rise
	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(ndays))	
	qs = annotate_rising_transient_qs(qs)
	qs_final = qs.filter((Q(rise_rate_g__gte=0) & (Q(rise_rate_g_sig__gte=1)))|
						 (Q(rise_rate_g_lim__gte=0) & (Q(rise_rate_g_lim_sig__gte=1)))|
						 (Q(rise_rate_r__gte=0) & (Q(rise_rate_r_sig__gte=1)))|
						 (Q(rise_rate_r_lim__gte=0) & (Q(rise_rate_r_lim_sig__gte=1)))|
						 (Q(rise_rate_i__gte=0) & (Q(rise_rate_i_sig__gte=1)))|
						 (Q(rise_rate_i_lim__gte=0) & (Q(rise_rate_i_lim_sig__gte=1))))
	
	return qs_final

@python_query_reg
def sne_in_last_nights_fields():

	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(tags__name='YSE')
	survey_obs = SurveyObservation.objects.filter(obs_mjd__gte=date_to_mjd(datetime.datetime.utcnow()-datetime.timedelta(1)))
	qs_list = []
	done_list = []
	for s in survey_obs:
		if s.survey_field.field_id in done_list: continue
		done_list += [s.survey_field.field_id]
		d = s.survey_field.dec_cen*np.pi/180
		width_corr = 3.3/np.abs(np.cos(d))
		# Define the tile offsets:
		ra_offset = cd.Angle(width_corr/2., unit=u.deg)
		dec_offset = cd.Angle(3.3/2., unit=u.deg)
		qs_list += [(Q(ra__gt = s.survey_field.ra_cen-ra_offset.degree) &
					 Q(ra__lt = s.survey_field.ra_cen+ra_offset.degree) &
					 Q(dec__gt = s.survey_field.dec_cen-dec_offset.degree) &
					 Q(dec__lt = s.survey_field.dec_cen+dec_offset.degree))]

	query_full = qs_list[0]
	for q in qs_list[1:]:
		query_full = np.bitwise_or(query_full,q)
	qs_final = qs.filter(query_full)

	return qs_final

@python_query_reg
def sne_15deg_from_yse():

	qs = None
	survey_obs = SurveyObservation.objects.filter(obs_mjd__gte=date_to_mjd(datetime.datetime.utcnow()-datetime.timedelta(14)))
	done_list = []
	for s in survey_obs:
		if s.survey_field.field_id in done_list: continue
		done_list += [s.survey_field.field_id]
		d = s.survey_field.dec_cen*np.pi/180
		width_corr = 15/np.abs(np.cos(d))
		#radius = ((ra-s.survey_field.ra_cen)**2. + (dec-s.survey_field.dec_cen)**2.)**(1/2.)

		ra_offset = cd.Angle(width_corr, unit=u.deg)
		dec_offset = cd.Angle(15, unit=u.deg)

		query= """SELECT t.name, ACOS(SIN(t.dec*3.14159/180)*SIN(%s*3.14159/180)+COS(t.dec*3.14159/180)*COS(%s*3.14159/180)*COS((t.ra-%s)*3.14159/180))*180/3.14159 as sep
FROM YSE_App_transient t
WHERE t.ra > %s AND t.ra < %s AND t.dec > %s AND t.dec < %s
HAVING sep < 15
""" % (
	s.survey_field.dec_cen, s.survey_field.dec_cen, s.survey_field.ra_cen,
	s.survey_field.ra_cen-ra_offset.degree,s.survey_field.ra_cen+ra_offset.degree,
	s.survey_field.dec_cen-dec_offset.degree,s.survey_field.dec_cen+dec_offset.degree)
		cursor = connections['explorer'].cursor()
		cursor.execute(query, ())

		if qs is None:
			qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(~Q(tags__name='YSE')).filter(~Q(status__name='Ignore')).filter(name__in=(x[0] for x in cursor))
		else:
			qs_single = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(~Q(tags__name='YSE')).filter(~Q(status__name='Ignore')).filter(name__in=(x[0] for x in cursor))
			qs = qs | qs_single
		cursor.close()

	return qs

def sne_in_yse_field(field_id):

	qs = None
	survey_field = SurveyField.objects.filter(field_id=field_id)[0]

	d = survey_field.dec_cen*np.pi/180
	width_corr = 1.65/np.abs(np.cos(d))
	#radius = ((ra-s.survey_field.ra_cen)**2. + (dec-s.survey_field.dec_cen)**2.)**(1/2.)

	ra_offset = cd.Angle(width_corr, unit=u.deg)
	dec_offset = cd.Angle(15, unit=u.deg)

	query= """SELECT t.name, ACOS(SIN(t.dec*3.14159/180)*SIN(%s*3.14159/180)+COS(t.dec*3.14159/180)*COS(%s*3.14159/180)*COS((t.ra-%s)*3.14159/180))*180/3.14159 as sep
FROM YSE_App_transient t
WHERE t.ra > %s AND t.ra < %s AND t.dec > %s AND t.dec < %s
HAVING sep < 3.3
""" % (
	survey_field.dec_cen, survey_field.dec_cen, survey_field.ra_cen,
	survey_field.ra_cen-ra_offset.degree,survey_field.ra_cen+ra_offset.degree,
	survey_field.dec_cen-dec_offset.degree,survey_field.dec_cen+dec_offset.degree)
	cursor = connections['explorer'].cursor()
	cursor.execute(query, ())

	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(~Q(status__name='Ignore')).filter(name__in=(x[0] for x in cursor))

	return qs

def sne_in_yse_field_with_ignore(field_id):

	qs = None
	survey_field = SurveyField.objects.filter(field_id=field_id)[0]

	d = survey_field.dec_cen*np.pi/180
	width_corr = 1.65/np.abs(np.cos(d))
	#radius = ((ra-s.survey_field.ra_cen)**2. + (dec-s.survey_field.dec_cen)**2.)**(1/2.)

	ra_offset = cd.Angle(width_corr, unit=u.deg)
	dec_offset = cd.Angle(15, unit=u.deg)

	query= """SELECT t.name, ACOS(SIN(t.dec*3.14159/180)*SIN(%s*3.14159/180)+COS(t.dec*3.14159/180)*COS(%s*3.14159/180)*COS((t.ra-%s)*3.14159/180))*180/3.14159 as sep
FROM YSE_App_transient t
WHERE t.ra > %s AND t.ra < %s AND t.dec > %s AND t.dec < %s
HAVING sep < 3.3
""" % (
	survey_field.dec_cen, survey_field.dec_cen, survey_field.ra_cen,
	survey_field.ra_cen-ra_offset.degree,survey_field.ra_cen+ra_offset.degree,
	survey_field.dec_cen-dec_offset.degree,survey_field.dec_cen+dec_offset.degree)
	cursor = connections['explorer'].cursor()
	cursor.execute(query, ())

	qs = Transient.objects.filter(created_date__gte=datetime.datetime.utcnow()-datetime.timedelta(90)).filter(name__in=(x[0] for x in cursor))

	return qs

