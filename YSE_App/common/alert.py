from django.conf import settings
import requests
from YSE_App.models.on_call_date_models import OnCallDate
from datetime import datetime, date, timedelta
import smtplib
from django.contrib.auth.models import User
from YSE_App.models.profile_models import Profile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def SendTransientAlert(transient_id, transient_name, ra, dec):

	print("Sending Alert")

	smtpserver = "%s:%s" % (settings.SMTP_HOST, settings.SMTP_PORT)
	from_addr = "%s@gmail.com" % settings.SMTP_LOGIN
	
	# 2017itz RA=10:18:00.38, DEC=-28:07:50.05, Discovery date=2017-12-04 22:04:48, Discovery mag=18.94 ABMag, Filter: G - Gaia, Reporter: A. Delgado, D. Harrison, S. Hodgkin, M. van Leeuwen, G. Rixon, A. Yoldas (University of Cambridge),..., Source group: GaiaAlerts

	subject = "TNS K2 Transient - Action Required" 
	if settings.DEBUG:
		subject = "[TESTING] TNS K2 Transient - Action Required"

	base_url = "https://ziggy.ucolick.org/yse/" 
	if settings.DEBUG:
		base_url =  "https://ziggy.ucolick.org/yse_test/"

	html_msg = """\
		<html>
			<head></head>
			<body>
				<h1>New K2 Tranisent!</h1>
				<p>
					<a href='%stransient_detail/%s/'>%s</a> (%s, %s)
				</p>
				<br />
				<p>Go to <a href='%s/dashboard/'>YSE Dashboard</a></p> 
			</body>
		</html>
	""" % (base_url, transient_id, transient_name, ra, dec, base_url)

	txt_msg = "New K2 Transient: %s (%s, %s)\n\nDetail: %s/transient_detail/%s/\n\nDashboard: %s/dashboard/" % \
			(base_url, transient_name, ra, dec, transient_id, base_url)

	# today() is UTC, so convert it to Pacific Standard Time
	print("UTC Now: %s" % datetime.today())
	
	PST_date = datetime.today() + timedelta(hours=settings.LOCAL_UTC_OFFSET)
	TargetOnCallDate = PST_date

	# Once we've correct for local time, we need to know which OnCall date to
	# actually access. If it is before 9:00 AM, it's yesterday's OnCallDate. If
	# it is >= 9:00 AM, it is today's OnCallDate
	begin_business_hours = 9 # PST
	end_business_hours = 17 # PST
	current_hour = PST_date.time().hour

	if current_hour < begin_business_hours:
		TargetOnCallDate = TargetOnCallDate - timedelta(days=1)

	print("PST Now: %s" % PST_date)
	print("Target On Call Date: %s" % TargetOnCallDate)

	business_hours = True
	if (current_hour < begin_business_hours) or (current_hour >= end_business_hours):
		business_hours = False

	print("Business Hours? %s" % business_hours)

	# Send email to everyone regardless of business hours
	all_users = User.objects.filter().exclude(username='admin')
	for user in all_users:
		sendemail(from_addr, user.email, subject, html_msg, 
					settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

	if business_hours:
		print("Sending SMS to everyone")
		for user in all_users:
			print("Sending text to: %s" % user.username)

			profile = Profile.objects.get(user__id =user.id)
			phone_email = "%s%s%s@%s" % (profile.phone_area, 
								profile.phone_first_three, 
								profile.phone_last_four,
								profile.phone_provider_str)

			sendsms(from_addr, phone_email, subject, txt_msg, 
					settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)
	else:		
		print("Non-business hours... only send SMS to On Call list")

		# Only send SMS to on call user
		ocd_result = OnCallDate.objects.filter(on_call_date=TargetOnCallDate.date())
		print(ocd_result)

		if ocd_result.exists():
			ocd = ocd_result.first()

			print("On Call Date: %s" % ocd.on_call_date.strftime('%m/%d/%Y'))

			# Get users, iterate & send email
			on_call_users = ocd.user.all()
			for user in on_call_users:
				print("Alerting on call user: %s" % user.username)
				profile = Profile.objects.get(user__id =user.id)

				phone_email = "%s%s%s@%s" % (profile.phone_area, 
								profile.phone_first_three, 
								profile.phone_last_four,
								profile.phone_provider_str)

				print("Target SMS: %s" % phone_email)

				sendsms(from_addr, phone_email, subject, txt_msg, 
					settings.SMTP_LOGIN, settings.SMTP_PASSWORD, smtpserver)

def sendemail(from_addr, to_addr,
			subject, message,
			login, password, smtpserver, cc_addr=None):

	print("Preparing email")

	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = from_addr
	msg['To'] = to_addr
	payload = MIMEText(message, 'html')
	msg.attach(payload)

	with smtplib.SMTP(smtpserver) as server:
		try:
			server.starttls()
			server.login(login, password)
			resp = server.sendmail(from_addr, [to_addr], msg.as_string())
			print("Send success")
		except e:
			print("Send fail")

def sendsms(from_addr, to_addr,
			subject, message,
			login, password, smtpserver, cc_addr=None):

	print("Preparing SMS")

	msg = MIMEMultipart('alternative')
	msg['Subject'] = subject
	msg['From'] = from_addr
	msg['To'] = to_addr
	payload = MIMEText(message, 'plain')
	msg.attach(payload)

	with smtplib.SMTP(smtpserver) as server:
		try:
			server.starttls()
			server.login(login, password)
			resp = server.sendmail(from_addr, [to_addr], msg.as_string())
			print("Send success")
		except e:
			print("Send fail")
