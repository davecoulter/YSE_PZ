from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.utilities import GetSexigesimalString
from YSE_App.common.alert import IsK2Pixel, SendTransientAlert
from YSE_App.common.thacher_transient_search import thacher_transient_search
from YSE_App.common.tess_obs import tess_obs
from YSE_App.common.utilities import date_to_mjd
import datetime

class Tags(CronJobBase):

	RUN_EVERY_MINS = 0.1

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.data_ingest.Apply_Tags.Tags'

	def do(self,tag_K2=False):

		try:
			nowdate = datetime.datetime.utcnow() - datetime.timedelta(21)
			transients = Transient.objects.filter(created_date__gt=nowdate)
			for t in transients:
				print('checking transient %s'%t)
				if tag_K2:
					is_k2_C16_validated, C16_msg = IsK2Pixel(t.ra, t.dec, "16")
					is_k2_C17_validated, C17_msg = IsK2Pixel(t.ra, t.dec, "17")
					is_k2_C19_validated, C19_msg = IsK2Pixel(t.ra, t.dec, "19")

					print("K2 C16 Val: %s; K2 Val Msg: %s" % (is_k2_C16_validated, C16_msg))
					print("K2 C17 Val: %s; K2 Val Msg: %s" % (is_k2_C17_validated, C17_msg))
					print("K2 C19 Val: %s; K2 Val Msg: %s" % (is_k2_C19_validated, C19_msg))

					if is_k2_C16_validated:
						k2c16tag = TransientTag.objects.get(name='K2 C16')
						t.k2_validated = True
						t.k2_msg = C16_msg
						t.tags.add(k2c16tag)

					elif is_k2_C17_validated:
						k2c17tag = TransientTag.objects.get(name='K2 C17')
						t.k2_validated = True
						t.k2_msg = C17_msg
						t.tags.add(k2c17tag)

					elif is_k2_C19_validated:
						k2c19tag = TransientTag.objects.get(name='K2 C19')
						t.k2_validated = True
						t.k2_msg = C19_msg
						t.tags.add(k2c19tag)

				tag_TESS,tag_Thacher = True,True #False,False
				print('Checking TESS')
				if tag_TESS and t.disc_date:
					TESSFlag = tess_obs(t.ra,t.dec,date_to_mjd(t.disc_date)+2400000.5)
					if TESSFlag:
						print('tagging %s'%t)
						try:
							tesstag = TransientTag.objects.get(name='TESS')
							t.tags.add(tesstag)
						except: pass
				else:
					TESSFlag = tess_obs(t.ra,t.dec,date_to_mjd(t.modified_date)+2400000.5)
					if TESSFlag:
						print('tagging %s'%t)
						try:
							tesstag = TransientTag.objects.get(name='TESS')
							t.tags.add(tesstag)
						except: pass

				print('Checking Thacher')
				if tag_Thacher and thacher_transient_search(t.ra,t.dec):
					try:
						thachertag = TransientTag.objects.get(name='Thacher')
						t.tags.add(thachertag)
					except: pass

				t.save()

		except Exception as e:
			print(e)
