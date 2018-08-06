#!/usr/bin/env python
# D. Jones - quick way to make a fake TNS email line

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from astropy.coordinates import SkyCoord
import astropy.units as u

class TNSFakeEmails:
	def __init__(self):
		pass
	
	def add_options(self, parser=None, usage=None, config=None):
		import optparse
		if parser == None:
			parser = optparse.OptionParser(usage=usage, conflict_handler="resolve")

		parser.add_option(
			'-r','--ra', default=None, type="string",
			help='right ascension, can be comma-separated (default=%default)')
		parser.add_option(
			'-d','--dec', default=None, type="string",
			help='dec, can be comma-separated (default=%default)')
		parser.add_option(
			'-s','--snid', default=None, type="string",
			help='SN ID, can be comma-separated (default=%default)')
		parser.add_option(
			'--SMTP_HOST', default="smtp.gmail.com", type="string",
			help="SMTP_HOST (default=%default)")
		parser.add_option(
			'--SMTP_PORT', default="587", type="string",
			help="SMTP_PORT")
		parser.add_option(
			'--SMTP_LOGIN', default="ktwo.test.ucsctransients", type="string",
			help="SMTP_LOGIN")
		parser.add_option(
			'--SMTP_PASSWORD', default="LetsTestYoungSupernovae!", type="string",
			help="SMTP_PASSWORD")

		return parser
		
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
		except:
			 print("Send fail")

if __name__ == "__main__":
	
	import os
	import optparse

	tfe = TNSFakeEmails()

	usagestring = 'mkFakeEmails.py <options>'
	parser = tfe.add_options(usage=usagestring)
	options,  args = parser.parse_args()

	emailtext = "Dear <em class=\"placeholder\">Dr. David Jones</em><br/><br/><br/>The following new transient/s were reported on:<br/><br/>"

	for s,r,d in zip(options.snid.split(','),options.ra.split(','),options.dec.split(',')):
		if ':' not in r:
			sc = SkyCoord(r,d,unit=u.deg)
			scstring = sc.to_string('hmsdms')
			r = scstring.split()[0].replace('h',':').replace('m',':').replace('s','')
			d = scstring.split()[1].replace('d',':').replace('m',':').replace('s','')
		if '+' not in d and '-' not in d: d = '+%s'%d
		linetmpl = "<a href=\"https://wis-tns.weizmann.ac.il/object/%s\"><em class=\"placeholder\">%s</em></a> RA=<em class=\"placeholder\">%s</em>, DEC=<em class=\"placeholder\">%s</em>, Discovery date=<em class=\"placeholder\">None</em>, Discovery mag=<em class=\"placeholder\">None</em> <em class=\"placeholder\">None</em>, Filter: <em class=\"placeholder\">None</em>, Reporter: <em class=\"placeholder\">None</em>, Source group: <em class=\"placeholder\">None</em><br/>"%(s,s,r,d)
		emailtext += linetmpl
	emailtext += """<br/><br/>Best Regards,<br/>The TNS team"""
		
	smtpserver = "%s:%s" % (options.SMTP_HOST, options.SMTP_PORT)
	from_addr = "%s@gmail.com" % options.SMTP_LOGIN
	subject = "TNS - New reports and classifications"

	sendemail(from_addr, from_addr, subject, emailtext,
			  options.SMTP_LOGIN, options.SMTP_PASSWORD, smtpserver)
