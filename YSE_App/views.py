from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.views import generic
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u

from .models import *

from astroplan import Observer
from astropy.time import Time
import numpy as np

# Create your views here.
def index(request):
	all_transients = Transient.objects.order_by('id')
	context = {
		'all_transients': all_transients,
	}
	return render(request, 'YSE_App/index.html', context)

def index2(request):
	return render(request, 'YSE_App/index2.html')

def transient_detail(request, transient_id):
        transient = get_object_or_404(Transient, pk=transient_id)
        ra,dec = get_coords_sexagesimal(transient.ra,transient.dec)
        obsnights,obslist = (),()
        for o in ObservingNightDates.objects.order_by('-observing_night')[::-1]:
                can_obs = telescope_can_observe(transient.ra,transient.dec,
                                                str(o.observing_night).split()[0],str(o.observatory))
                obsnights += ([o,can_obs],)
                if can_obs and o.happening_soon() and o.observatory not in obslist: obslist += (o.observatory,)
                
        return render(request, 'YSE_App/transient_detail.html', 
                      {'transient': transient,
                       'observatory_list': obslist, #Observatory.objects.all(),
                       'observing_nights': obsnights,
                       'jpegurl':get_psstamp_url(request, transient_id),
                       'ra':ra,'dec':dec})

def get_psstamp_url(request, transient_id):
        ps1url = "http://plpsipp1v.stsci.edu/cgi-bin/ps1cutouts?pos=%.7f%%2B%.7f&filter=color"%(
                Transient.objects.get(pk=transient_id).ra,Transient.objects.get(pk=transient_id).dec)
        
        response = requests.get(url=ps1url)
        if "<td><img src=" in response.content.decode('utf-8'):
                jpegurl = response.content.decode('utf-8').split('<td><img src="')[1].split('" width="240" height="240" /></td>')[0]
                jpegurl = "http:%s"%jpegurl
        else:
                jpegurl=""

        return(jpegurl)

def get_coords_sexagesimal(radeg,decdeg):
        sc = SkyCoord(radeg,decdeg,unit=u.deg)
        return('%02i:%02i:%02.2f'%(sc.ra.hms[0],sc.ra.hms[1],sc.ra.hms[2]),
               '%02i:%02i:%02.2f'%(sc.dec.dms[0],sc.dec.dms[1],sc.dec.dms[2]))

def telescope_can_observe(ra,dec,date,tel):
        time = Time(date)
        sc = SkyCoord(ra,dec,unit=u.deg)
        tel = Observer.at_site(tel)

        night_start = tel.twilight_evening_astronomical(time,which="previous")
        night_end = tel.twilight_morning_astronomical(time,which="previous")
        can_obs = False
        for jd in np.arange(night_start.mjd,night_end.mjd,0.02):
                time = Time(jd,format="mjd")
                target_up = tel.target_is_up(time,sc)
                if target_up:
                        can_obs = True
                        break

        return(can_obs)
        
def airmassplot(request, transient_id, obs, observatory ):
    import random
    import django
    import datetime
    from astroplan.plots import plot_airmass
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    #from matplotlib import rcParams
    #rcParams['figure.figsize'] = (7,5)
    
    transient = Transient.objects.get(pk=transient_id)
    
    target = SkyCoord(transient.ra,transient.dec,unit=u.deg)
    time = Time(obs, format='iso')
    tel = Observer.at_site(observatory)
    
    fig=Figure()
    ax=fig.add_subplot(111)
    canvas=FigureCanvas(fig)

    ax.set_title("%s, %s, %s"%(observatory,transient.name, obs))

    night_start = tel.twilight_evening_astronomical(time,which="previous")
    night_end = tel.twilight_morning_astronomical(time,which="previous")
    delta_t = night_end - night_start
    observe_time = night_start + delta_t*np.linspace(0, 1, 75)
    plot_airmass(target, tel, observe_time, ax=ax)    
    #ax.axvline(night_start)
    #ax.axvline(night_end)
    
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
