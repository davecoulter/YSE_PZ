from YSE_App.models import *
from YSE_App.common.utilities import *
from astroplan import moon_illumination
from astropy.time import Time

def main():
	start_mjd = 58814 #58868
	
	survey_obs = SurveyObservation.objects.filter(status__name="Successful").filter(obs_mjd__gt=start_mjd).filter(obs_mjd__lt=start_mjd+29)

	g_stack_main,r_stack_main,i_stack_main,z_stack_main = [],[],[],[]
	r_stack_sup,i_stack_sup = [],[]
	for so in survey_obs:
		if so.survey_field.field_id != '365.A': continue
		t = Time(so.obs_mjd,format='mjd',scale='utc')
		illum = moon_illumination(t)
		if so.photometric_band.name == 'g':
			g_stack_main += [so.image_id]
		if so.photometric_band.name == 'z':
			z_stack_main += [so.image_id]
		elif illum > 0.33 and so.photometric_band.name == 'r':
			r_stack_main += [so.image_id]
		elif illum > 0.33 and so.photometric_band.name == 'i':
			i_stack_main += [so.image_id]
		elif illum <= 0.33 and so.photometric_band.name == 'i':
			i_stack_sup += [so.image_id]
		elif illum <= 0.33 and so.photometric_band.name == 'r':
			r_stack_sup += [so.image_id]

	print('g stack:')
	for g in g_stack_main:
		print(g)
	print('r stack:')
	for r in r_stack_main:
		print(r)
	print('i stack:')
	for i in i_stack_main:
		print(i)
	print('z stack:')
	for z in z_stack_main:
		print(z)
	print('supplemental r stack:')
	for r in r_stack_sup:
		print(r)
	print('supplemental i stack:')
	for i in i_stack_sup:
		print(i)
