import os,pdb,json,datetime,time,string, random
import numpy as np
from django import forms
from YSE_App.models import *

# form for adjusting the FOV/pointing
class CoordForm(forms.ModelForm):

	class Meta:
		model = CanvasFOV
		fields = ('raCenter','decCenter','fovWidth',)

