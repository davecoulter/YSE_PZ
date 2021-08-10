#!/usr/bin/env python

import pylab as plt
plt.ion()
import numpy as np
from YSE_App.models import *

def main():
    plt.close('all')
    ax = plt.axes()
    class_names = {'SN Ia':['SN Ia','SN Ia-91T-like','SN Ia-91bg-like','SN Ia-pec'],
                   'SN Ib/c':['SN Ic','	SN Ib/c','SN Ib-Ca-rich','SN Ibn','SN Ib-pec','SN Ic-pec','SN Ic-BL','SN Icn'],
                   'SN II':['SN II','SN IIP','SN IIL','SN IIn','SN IIb']}
    all_labels = np.concatenate((class_names['SN Ia'],class_names['SN Ib/c'],class_names['SN II']))

    transients_to_classify = \
        Transient.objects.filter(Q(status__name = 'New') |
                                 Q(status__name = 'Watch') |
                                 Q(status__name = 'Interesting') |
                                 Q(status__name = 'FollowupRequested') |
                                 Q(status__name = 'Following') |
                                 Q(tags__name = 'YSE') | Q(tags__name = 'YSE Forced Phot')).distinct()
    
    matrix = np.zeros([3,3])
    for i,class1 in enumerate(['SN Ia','SN Ib/c','SN II']):
        for j,class2 in enumerate(['SN Ia','SN Ib/c','SN II']):
            class1list = class_names[class1]
            class2list = class_names[class2]
            
            list_correct = len(transients_to_classify.filter(photo_class__name=class1).filter(best_spec_class__name__in=class2list))
            list_full = len(transients_to_classify.filter(best_spec_class__name__in=class2list).filter(photo_class__name__in=['SN Ia','SN Ib/c','SN II']))

            matrix[j,i] = float(list_correct)/list_full

    cb = ax.imshow(matrix.transpose(),cmap=plt.cm.Blues,vmin=0.0,vmax=1.0)#,origin="lower")
    for i in range(3):
        for j in range(3):
            ax.text(i, j, '%.3f'%matrix[i,j], va='center', ha='center',color='k')
    #import pdb; pdb.set_trace()
    ax.xaxis.set_ticks([0,1,2])
    ax.xaxis.set_ticklabels(['SN Ia','SN Ibc','SN II'])
    ax.yaxis.set_ticks([0,1,2])
    ax.yaxis.set_ticklabels(['SN Ia','SN Ibc','SN II'])
    
    ax.set_ylabel('Predicted Class')
    ax.set_xlabel('True Class')
