import requests,re

def tess_obs(ra, dec, discovery_jd):

	before_leeway = 10	 # Days of leeway before date
	after_leeway = 30	 # Days of leeway after date
	tess_date = [
		2458324.5,2458352.5,2458381.5,2458409.5,2458437.5,2458463.5,
		2458490.5,2458516.5,2458542.5,2458568.5,2458595.5,2458624.5,
		2458653.5,2458682.5,2458710.5,2458737.5,2458763.5,2458789.5,
		2458814.5,2458841.5,2458869.5,2458897.5,2458926.5,2458955.5,
		2458982.5,2459008.5,2459034.5,2459060.5,2459087.5,2459114.5,
		2459143.5,2459172.5,2459200.5,2459227.5,2459254.5,2459280.5,
		2459306.5,2459332.5,2459360.5]

	url = 'https://heasarc.gsfc.nasa.gov/cgi-bin/tess/webtess/'
	url += 'wtv.py?Entry={ra}%2C{dec}'
	r = requests.get(url.format(ra=str(ra), dec=str(dec)))
	if r.status_code!=200:
		print('status message:',r.text)
		error = 'ERROR: could not get {url}, status code {code}'
		raise RuntimeError(error.format(url=url, code=r.status_code))
		return(None)

	reg = r"observed in camera \w+.\nSector \w+"
	info = re.findall(reg, r.content.decode())
	sectors=[]
	for k in info:
	    sectors.append(int(re.split(r'\s', k)[5])-1)

	if len(sectors)>0:
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
