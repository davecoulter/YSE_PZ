from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np

def GetSexigesimalString(ra_decimal, dec_decimal):
	c = SkyCoord(self.ra,self.dec,unit=(unit.deg, unit.deg))
	ra = c.ra.hms
	dec = c.dec.dms

	ra_string = "%02d:%02d:%0.1f" % (ra[0],ra[1],ra[2])
	dec_string = "%02d:%02d:%0.1f" % (dec[0],np.abs(dec[1]),np.abs(dec[2]))

	# Python has a -0.0 object. If the deg is this (because object lies < 60 min south), the string formatter will drop the negative sign
	if c.dec < 0.0 and dec[0] == 0.0:
		dec_string = "-0:%02d:%0.1f" % (np.abs(dec[1]),np.abs(dec[2]))

	return (ra_string, dec_string)