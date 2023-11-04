import requests,re

def tess_obs(ra, dec, discovery_jd):

	before_leeway = 10	 # Days of leeway before date
	after_leeway = 10	 # Days of leeway after date
	tess_date = [
		2458324.5,2458352.5,2458381.5,2458409.5,2458437.5,2458463.5,
		2458490.5,2458516.5,2458542.5,2458568.5,2458595.5,2458624.5,
		2458653.5,2458682.5,2458710.5,2458737.5,2458763.5,2458789.5,
		2458814.5,2458841.5,2458869.5,2458897.5,2458926.5,2458955.5,
		2458982.5,2459008.5,2459034.5,2459060.5,2459087.5,2459114.5,
		2459143.5,2459172.5,2459200.5,2459227.5,2459254.5,2459280.5,
		2459306.5,2459332.5,2459360.5,2459389.5,2459418.5,2459446.5,
		2459473.5,2459499.5,2459524.5,2459550.5,2459578.5,2459607.5,
		2459636.5,2459664.5,2459691.5,2459717.5,
		2459743.5,2459769.5,2459796.5,2459823.5,2459852.5,2459881.5,
		2459909.5,2459936.5,2459962.5,2459987.5,2460013.5,2460040.5,
		2460068.5,2460097.5,2460126.5,2460154.5,2460181.5,2460207.5,
        2460233.5, 2460259.5, 2460285.5, 2460312.5, 2460339.5, 2460366.5, 2460395.5, 
        2460423.5, 2460451.5, 2460479.5, 2460506.5, 2460532.5, 2460558.5, 2460584.5]
	url = 'https://heasarc.gsfc.nasa.gov/wsgi-scripts/TESS/TESS-point_Web_Tool/TESS-point_Web_Tool/wtv_v2.0.py/RADec_result'
	myobj = {'ra': ra, 'dec':dec}
	x = requests.post(url, data = myobj)

	if x.status_code!=200:
    		print('status message:',x.text)
    		error = 'ERROR: could not get {url}, status code {code}'
    		raise RuntimeError(error.format(url=url, code=x.status_code))
    		return(None)

	reg = r" <th> \w+ </th>\n"
	info = re.findall(reg, x.text)
	sectors=[]
	for i,k in enumerate(info):
	    if i%3 == 0:
	        sectors.append(int(k.split('<th>')[1].split('</th>')[0]))

	if len(sectors)>0:
		for sector in sectors:
			if int(sector)<len(tess_date):
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
