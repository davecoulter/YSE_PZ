from django.conf import settings
import requests
from YSE_App.models.on_call_date_models import OnCallDate
from datetime import datetime
import smtplib
from django.contrib.auth.models import User
from YSE_App.models.profile_models import Profile

def IsK2Pixel(ra, dec):

	print("Checking K2")
	print("Input: (%0.5f, %0.5f)" % (ra, dec))

	YES = 'yes'
	HTTP_SUCCESS = 200

	url_formatter = "%s?ra=%0.5f&dec=%0.5f"
	endpoint_uri = settings.KEPLER_API_ENDPOINT
	formatted_url = url_formatter % (settings.KEPLER_API_ENDPOINT, ra, dec)

	r = requests.get(formatted_url)
	if r.status_code == HTTP_SUCCESS:
		print("K2 API call success")

		is_K2 = (r.text == YES)
		if is_K2:
			print("Is K2")
		else:
			print("Not K2")
		return is_K2

	else:
		return False
		# What to do? By default email on call to check the 
		# transient
		pass


def SendTransientAlert():

	print("Sending Alert")

	smtpserver = "%s:%s" % (settings.SMTP_HOST, settings.SMTP_PORT)
	from_addr = "%s@gmail.com" % settings.SMTP_LOGIN
	subject = "K2 Transient - Action Required"
	message = "Please check https://ziggy.ucolick.org/yse/dashboard/."

	today_year = datetime.today().date().year
	today_month = datetime.today().date().month
	today_day = datetime.today().date().day

	print(OnCallDate.objects.all())
	print("Today: %s" % datetime.today().date())

	# ocd_result = OnCallDate.objects.filter(on_call_date = datetime.today().date())

	# if ocd_result.exists():
	# 	ocd = ocd_result.first()

	# 	print("On Call Date: %s" % ocd.on_call_date.strftime('%m/%d/%Y'))

	# 	# Get users, iterate & send email
	# 	on_call_users = ocd.user.all()
	# 	for user in on_call_users:
	# 		print("Alerting user: %s" % user.username)
	# 		profile = Profile.objects.get(user__id =user.id)

	# 		sendemail(from_addr, user.email, subject, message, 
	# 			settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

	# 		phone_email = "%s%s%s@%s" % (profile.phone_area, 
	# 								profile.phone_first_three, 
	# 								profile.phone_last_four,
	# 								profile.phone_provider_str)

	# 		sendtext(from_addr, phone_email, subject, message, 
	# 			settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

	test_user = User.objects.get(username='dcoulter')
	print("Alerting user: %s" % test_user.username)
	profile = Profile.objects.get(user__id=test_user.id)

	sendemail(from_addr, test_user.email, subject, message, 
		settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

	phone_email = "%s%s%s@%s" % (profile.phone_area, 
							profile.phone_first_three, 
							profile.phone_last_four,
							profile.phone_provider_str)

	print("Target SMS: %s" % phone_email)

	sendemail(from_addr, phone_email, subject, message, 
		settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

def sendemail(from_addr, to_addr,
			subject, message,
			login, password, smtpserver, cc_addr=None):

	print("Preparing email")

	header  = 'From: %s\n' % from_addr
	header += 'To: %s\n' % to_addr

	if cc_addr is not None:
		header += 'Cc: %s\n' % cc_addr

	header += 'Subject: %s\n' % subject
	message = header + message
 
	with smtplib.SMTP(smtpserver) as server:
		try:
			server.starttls()
			server.login(login, password)
			problems = server.sendmail(from_addr, to_addr, message)
			print("Send success")
		except e:
			print("Send fail")
	# server.quit()


# def sendtext(from_addr, to_phone_number, carrier, cc_addr_list, subject, message, login, password, smtpserver='smtp.gmail.com:587'):
# 	# should add their carrier     
# 	sendemail(from_addr, to_phone_number + "@" + carrier, cc_addr_list, subject, message, login, password, smtpserver='smtp.gmail.com:587')


# # for i in range(len(observers)): 
# sendemail("xhakaj.enia@gmail.com", email_ID[-1]+"@ucsc.edu", "", "Hellooo", "Hellooo from Enia", "xhakaj.enia@gmail.com", "CataclysmicVariablesSURF2016")
# sendtext("xhakaj.enia@gmail.com", phone_numbers[-1], carrier[-1], "", "Hellooo", "Hellooo from Enia", "xhakaj.enia@gmail.com", "CataclysmicVariablesSURF2016")

