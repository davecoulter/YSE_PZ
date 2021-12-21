#!/usr/bin/env python
# D. Jones - 11/14/17

from YSE_App.models import *

def writeSitesToDB(skycalcfile="/Users/david/Dropbox/research/JSkyCalc/skycalcsites.dat"):

    skycalc = open(skycalcfile,'r')
    for line in skycalc:
        line = line.replace('\n','')
        if line.startswith('"'):
            site = line.split('"')[1]
            line = line.replace('"','')
            others = line.split('%s,'%site)[1]
            lat,lon,tmgmt,dstcode,timezone,tzcode,elevation,horel = others.split(',')
            lat = float(lat); lon = float(lon)
            
            o = Observatory(name=site,latitude=lat,longitude=lon,altitude=elevation,
                            utoffset=tmgmt,daylightsavingscode=dstcode,
                            timezonename=timezone)
            o.save()

