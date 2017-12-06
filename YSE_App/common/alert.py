from django.conf import settings
import requests
from YSE_App.models.on_call_date_models import OnCallDate
from datetime import datetime, date, timedelta
import smtplib
from django.contrib.auth.models import User
from YSE_App.models.profile_models import Profile
from email.mime.text import MIMEText

def IsK2Pixel(ra, dec):

	print("Checking K2")
	print("Input: (%0.5f, %0.5f)" % (ra, dec))

	YES = 'yes'
	HTTP_SUCCESS = 200

	url_formatter = "%s?ra=%0.5f&dec=%0.5f"
	endpoint_uri = settings.KEPLER_API_ENDPOINT
	formatted_url = url_formatter % (settings.KEPLER_API_ENDPOINT, ra, dec)

	try:
		r = requests.get(formatted_url)

		if r.status_code == HTTP_SUCCESS:
			print("K2 API call success")

		is_K2 = (r.text == YES)
		if is_K2:
			print("Is K2")
		else:
			print("Not K2")

		return (is_K2, "200 Success")

	except requests.exceptions.RequestException as e:  # This is the correct syntax
		# By default, return True... so we don't miss any
		
		print("K2 API call failed")
		return (True, ("K2 API error: %s" % e))

def SendTransientAlert():

	print("Sending Alert")

	smtpserver = "%s:%s" % (settings.SMTP_HOST, settings.SMTP_PORT)
	from_addr = "%s@gmail.com" % settings.SMTP_LOGIN
	
	subject = "K2 Transient - Action Required"
	message = "Please check https://ziggy.ucolick.org/yse/dashboard/. New!!"

	# today() is UTC, so convert it to Pacific Standard Time
	print("UTC time: %s" % datetime.today())
	
	PST_date = datetime.today() + timedelta(hours=settings.LOCAL_UTC_OFFSET)

	print(OnCallDate.objects.all())
	print("Today: %s" % PST_date)
	
	ocd_result = OnCallDate.objects.filter(on_call_date=PST_date.date())
	print(ocd_result)

	if ocd_result.exists():
		ocd = ocd_result.first()

		print("On Call Date: %s" % ocd.on_call_date.strftime('%m/%d/%Y'))

		# Get users, iterate & send email
		on_call_users = ocd.user.all()
		for user in on_call_users:
			print("Alerting user: %s" % user.username)
			profile = Profile.objects.get(user__id =user.id)

			print("Target SMS: %s" % user.email)
			sendemail(from_addr, user.email, subject, message, 
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

	msg = MIMEText(message)
	msg['Subject'] = subject
	msg['From'] = from_addr
	msg['To'] = to_addr

	with smtplib.SMTP(smtpserver) as server:
		try:
			server.starttls()
			server.login(login, password)
			resp = server.sendmail(from_addr, [to_addr], msg.as_string())
			print("Send success")
		except e:
			print("Send fail")
