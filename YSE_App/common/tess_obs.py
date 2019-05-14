import requests,re

def tess_obs(ra, dec, discovery_jd):

	before_leeway = 20	 # Days of leeway before date
	after_leeway = 100	 # Days of leeway after date
	tess_date = [2458324.5,2458352.5,2458381.5,2458409.5,2458437.5,2458463.5,
				 2458490.5,2458516.5,2458542.5,2458568.5,2458595.5,2458624.5,
				 2458653.5,2458682.5]

	url = 'https://mast.stsci.edu/tesscut'
	url += '/api/v0.1/sector?ra={ra}&dec={dec}'
	r = requests.get(url.format(ra=str(ra), dec=str(dec)))
	if r.status_code!=200:
		print('status message:',r.text)
		error = 'ERROR: could not get {url}, status code {code}'
		raise RuntimeError(error.format(url=url, code=r.status_code))
		return(None)

	reg = '\"sector\"\: \"([0-9]+)\"'
	sectors = re.findall(reg, r.text)

	if len(sectors) == 0:
		return(False)
	else:
		for sector in sectors:
			if (discovery_jd > tess_date[int(sector)-1]-before_leeway and
				discovery_jd < tess_date[int(sector)]+after_leeway):
				return(True)
	return(False)

# These should be false
#print("Should be false:")
#print tess_obs(94.1105250, -21.3756833, 2458481.52282)
#print tess_obs(202.884383, -12.4804833, 2458526.52282)
#print tess_obs(308.684333, +60.1933063, 2458526.52282)

# These should be true
#print "Should be true:"
#print tess_obs(64.46742, -63.67525, 2458345.52282) # 2018fhw
#print tess_obs(65.13394, -38.96065, 2458440.52282) # 2018ioa
#print tess_obs(98.38955, -61.00797, 2458509.52282) # 2019aeg
