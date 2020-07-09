

#####################################################################################
from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings
import datetime
import numpy as np
import pandas as pd
import os
#import pickle #did you know pickle leads to system being hackable or something? don't load if you dont need it...
import sys
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
import sfdmap #https://github.com/kbarbary/sfdmap
#####################################################################################
def Myinception_batchnorm_decay_big(input_layer, nbS1, nbS2, name, output_name, without_kernel_5=False, without_kernel_7=False, l=1e-5, C=0.1):
        
    s1_0 = tf.keras.layers.Conv2D(filters=nbS1,
                      kernel_size=1,
                      padding='same',
                      activation=tf.keras.layers.PReLU(shared_axes=[1,2]),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      name=name + "S1_0")(input_layer)
    
    s2_0 = tf.keras.layers.Conv2D(filters=nbS2,
                      kernel_size=3,
                      padding='same',
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      name=name + "S2_0")(s1_0)
    batch_s2_0 = tf.keras.layers.BatchNormalization()(s2_0)
    prelu_s2_0 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s2_0)
                      
    s1_2 = tf.keras.layers.Conv2D(filters=nbS1,
                      kernel_size=1,
                      padding='same',
                      activation=tf.keras.layers.PReLU(shared_axes=[1, 2]),
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      name=name + "S1_2")(input_layer)
         
    pool0 = tf.keras.layers.AveragePooling2D(pool_size=2,
                       strides=1,
                       padding="same",
                       name=name + "pool0")(s1_2)

    if not(without_kernel_5):
        s1_1 = tf.keras.layers.Conv2D(filters=nbS1,
                          kernel_size=1,
                          padding='same',
                          activation=tf.keras.layers.PReLU(shared_axes=[1, 2]),
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S1_1")(input_layer)

        s2_1 = tf.keras.layers.Conv2D(filters=nbS1,
                          kernel_size=3,
                          padding='same',
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S2_1")(s1_1)
        batch_s2_1 = tf.keras.layers.BatchNormalization()(s2_1)
        prelu_s2_1 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s2_1)

        s3_1 = tf.keras.layers.Conv2D(filters=nbS2,
                          kernel_size=3,
                          padding='same',
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S3_1")(prelu_s2_1)
        batch_s3_1 = tf.keras.layers.BatchNormalization()(s3_1)
        prelu_s3_1 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s3_1)

    if not(without_kernel_7):
        s1_3 = tf.keras.layers.Conv2D(filters=nbS1,
                          kernel_size=1,
                          padding='same',
                          activation=tf.keras.layers.PReLU(shared_axes=[1, 2]),
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S1_3")(input_layer)

        s2_3 = tf.keras.layers.Conv2D(filters=nbS1,
                          kernel_size=3,
                          padding='same',
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S2_3")(s1_3)
        batch_s2_3 = tf.keras.layers.BatchNormalization()(s2_3)
        prelu_s2_3 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s2_3)

        s3_3 = tf.keras.layers.Conv2D(filters=nbS1,
                          kernel_size=3,
                          padding='same',
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S3_3")(prelu_s2_3)
        batch_s3_3 = tf.keras.layers.BatchNormalization()(s3_3)
        prelu_s3_3 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s3_3)

        s4_3 = tf.keras.layers.Conv2D(filters=nbS2,
                          kernel_size=3,
                          padding='same',
                          kernel_initializer=tf.keras.initializers.he_normal(),
                          bias_initializer=tf.keras.initializers.Constant(C),
                          kernel_regularizer=tf.keras.regularizers.l2(l),
                          name=name + "S4_3")(prelu_s3_3)
        batch_s4_3 = tf.keras.layers.BatchNormalization()(s4_3)
        prelu_s4_3 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s4_3)
    
    s2_2 = tf.keras.layers.Conv2D(filters=nbS2,
                      kernel_size=1,
                      padding='same',
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      name=name + "S2_2")(input_layer)
    batch_s2_2 = tf.keras.layers.BatchNormalization()(s2_2)
    prelu_s2_2 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s2_2)
    
    if without_kernel_5 and without_kernel_7: #pool, 1 ,3
        output = tf.keras.layers.concatenate([prelu_s2_2, prelu_s2_0, pool0],axis=3,name=output_name)
    
    if without_kernel_7 and not(without_kernel_5): #pool, 1, 3, 5
        output = tf.keras.layers.concatenate([prelu_s2_2, prelu_s3_1, prelu_s2_0, pool0],
                               axis=3,name=output_name)
    if not(without_kernel_5) and not(without_kernel_7):
        output = tf.keras.layers.concatenate([prelu_s2_2, prelu_s2_0, prelu_s4_3, prelu_s3_1, pool0],
                               axis=3,name=output_name)
        
    return output
    


def Myinception_batchnorm_reduce_decay_max(input_layer, nbS1, nbS2, name, output_name, without_kernel_5=False, l=1e-5, C=0.1):
        
    s1_0 = tf.keras.layers.Conv2D(filters=nbS1,
                      kernel_size=1,
                      padding='same',
                      activation=tf.keras.layers.PReLU(shared_axes=[1,2]),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      name=name + "S1_0")(input_layer)
    
    s2_0 = tf.keras.layers.Conv2D(filters=nbS2,
                      kernel_size=2,
                      strides=2,
                      padding='valid',
                      kernel_initializer=tf.keras.initializers.he_normal(),
                      bias_initializer=tf.keras.initializers.Constant(C),
                      kernel_regularizer=tf.keras.regularizers.l2(l),
                      name=name + "S2_0")(s1_0)
    batch_s2_0 = tf.keras.layers.BatchNormalization()(s2_0)
    prelu_s2_0 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_s2_0)
                        
         
    pool0 = tf.keras.layers.MaxPooling2D(pool_size=2,
                       strides=2,
                       padding="valid",
                      name=name + "pool0")(input_layer)

    output = tf.keras.layers.concatenate([prelu_s2_0, pool0],axis=3,name=output_name)

    return output

def create_model_groundup_decay_ultimate(NB_BINS, C=0.1, l=1e-5): #Implementing more suggestions form Inception V3...
    
    input_images = tf.keras.layers.Input(shape=(104,104,5))
    input_derived_data = tf.keras.layers.Input(shape=(1))
    
    conv0 = tf.keras.layers.Conv2D(filters=16,
                                kernel_size=3,
                                strides=1,
                                padding='valid',
                                activation=None,
                                kernel_initializer=tf.keras.initializers.he_normal(),
                                bias_initializer=tf.keras.initializers.Constant(C),
                                kernel_regularizer=tf.keras.regularizers.l2(l), name='conv0')(input_images)
    
    batch_conv0 = tf.keras.layers.BatchNormalization()(conv0)
    prelu_conv0 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv0)
    
    conv1 = tf.keras.layers.Conv2D(filters=16,
                            kernel_size=3,
                            strides=1,
                            padding='valid',
                            activation=None,
                            kernel_initializer=tf.keras.initializers.he_normal(),
                            bias_initializer=tf.keras.initializers.Constant(C),
                            kernel_regularizer=tf.keras.regularizers.l2(l), name='conv1')(prelu_conv0)
    
    batch_conv1 = tf.keras.layers.BatchNormalization()(conv1)
    prelu_conv1 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv1)

    conv2 = tf.keras.layers.Conv2D(filters=16,
                            kernel_size=3,
                            strides=1,
                            padding='valid',
                            activation=None,
                            kernel_initializer=tf.keras.initializers.he_normal(),
                            bias_initializer=tf.keras.initializers.Constant(C),
                            kernel_regularizer=tf.keras.regularizers.l2(l), name='conv2')(prelu_conv1)
    
    batch_conv2 = tf.keras.layers.BatchNormalization()(conv2)
    prelu_conv2 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv2)
                                
    conv3 = tf.keras.layers.Conv2D(filters=32,
                                kernel_size=3,
                                strides=3,
                                padding='valid',
                                activation=tf.keras.layers.PReLU(shared_axes=[1, 2]),
                                kernel_initializer=tf.keras.initializers.he_normal(),
                                bias_initializer=tf.keras.initializers.Constant(C),
                                kernel_regularizer=tf.keras.regularizers.l2(l), name='conv3')(prelu_conv2)
    
    pool1 = tf.keras.layers.AveragePooling2D(pool_size=5,strides=3,padding='valid',name='pool1')(prelu_conv2)

    cat1 = tf.keras.layers.concatenate([conv3,pool1],axis=3,name='cat1')
    
    i0 = Myinception_batchnorm_decay_big(cat1, 48, 64, name="I0_", output_name="INCEPTION0", l=l)
    
    i1 = Myinception_batchnorm_decay_big(i0, 64, 92, name="I1_", output_name="INCEPTION1", l=l)
    
    i2 = Myinception_batchnorm_reduce_decay_max(i1, 92, 128, name="I2_", output_name="INCEPTION2", l=l) #this should reduce the grid

    i3 = Myinception_batchnorm_decay_big(i2, 128, 218, name="I3_", output_name="INCEPTION3", without_kernel_7=True, l=l)
    
    i4 = Myinception_batchnorm_decay_big(i3, 218, 360, name="I4_", output_name="INCEPTION4", without_kernel_7=True, l=l)
    
    i5 = Myinception_batchnorm_reduce_decay_max(i4, 360, 402, name="I5_", output_name="INCEPTION5", l=l) #this should reduce the grid

    i6 = Myinception_batchnorm_decay_big(i5, 402, 512, name="I6_", output_name="INCEPTION6", without_kernel_5=True, without_kernel_7=True, l=l)

    i7 = Myinception_batchnorm_decay_big(i6, 512, 720, name="I7_", output_name="INCEPTION7", without_kernel_5=True, without_kernel_7=True, l=l)
    
    poolend = keras.layers.AveragePooling2D(pool_size=8,strides=1,padding='valid',name='poolend')(i7)
    
    flat = keras.layers.Flatten()(poolend)
    
    cat2 = tf.keras.layers.concatenate([flat,input_derived_data], axis=1, name='cat2')
    
    fc0 = tf.keras.layers.Dense(units=1952, activation=tf.keras.layers.ReLU(), name='fc0')(cat2)#f2 * 2 + f1
    d0 = tf.keras.layers.Dropout(0.25)(fc0)
    fc1 = tf.keras.layers.Dense(units=1952, activation=tf.keras.layers.ReLU(), name='fc0b')(d0)
    d1 = tf.keras.layers.Dropout(0.25)(fc1)
    fc2 = tf.keras.layers.Dense(units=NB_BINS, activation=tf.keras.activations.softmax, name='fc2')(d1)
        
    model = tf.keras.Model(inputs=[input_images, input_derived_data], outputs=[fc2])
    
    return(model)
    
def create_model_groundup_decay_ultimate(NB_BINS, C=0.1, l=1e-5): #Implementing more suggestions form Inception V3...
    
    input_images = tf.keras.layers.Input(shape=(104,104,5))
    input_derived_data = tf.keras.layers.Input(shape=(1))
    
    conv0 = tf.keras.layers.Conv2D(filters=16,
                                kernel_size=3,
                                strides=1,
                                padding='valid',
                                activation=None,
                                kernel_initializer=tf.keras.initializers.he_normal(),
                                bias_initializer=tf.keras.initializers.Constant(C),
                                kernel_regularizer=tf.keras.regularizers.l2(l), name='conv0')(input_images)
    
    batch_conv0 = tf.keras.layers.BatchNormalization()(conv0)
    prelu_conv0 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv0)
    
    conv1 = tf.keras.layers.Conv2D(filters=16,
                            kernel_size=3,
                            strides=1,
                            padding='valid',
                            activation=None,
                            kernel_initializer=tf.keras.initializers.he_normal(),
                            bias_initializer=tf.keras.initializers.Constant(C),
                            kernel_regularizer=tf.keras.regularizers.l2(l), name='conv1')(prelu_conv0)
    
    batch_conv1 = tf.keras.layers.BatchNormalization()(conv1)
    prelu_conv1 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv1)

    conv2 = tf.keras.layers.Conv2D(filters=16,
                            kernel_size=3,
                            strides=1,
                            padding='valid',
                            activation=None,
                            kernel_initializer=tf.keras.initializers.he_normal(),
                            bias_initializer=tf.keras.initializers.Constant(C),
                            kernel_regularizer=tf.keras.regularizers.l2(l), name='conv2')(prelu_conv1)
    
    batch_conv2 = tf.keras.layers.BatchNormalization()(conv2)
    prelu_conv2 = tf.keras.layers.PReLU(shared_axes=[1,2])(batch_conv2)
                                
    conv3 = tf.keras.layers.Conv2D(filters=32,
                                kernel_size=3,
                                strides=3,
                                padding='valid',
                                activation=tf.keras.layers.PReLU(shared_axes=[1, 2]),
                                kernel_initializer=tf.keras.initializers.he_normal(),
                                bias_initializer=tf.keras.initializers.Constant(C),
                                kernel_regularizer=tf.keras.regularizers.l2(l), name='conv3')(prelu_conv2)
    
    pool1 = tf.keras.layers.AveragePooling2D(pool_size=5,strides=3,padding='valid',name='pool1')(prelu_conv2)

    cat1 = tf.keras.layers.concatenate([conv3,pool1],axis=3,name='cat1')
    
    i0 = Myinception_batchnorm_decay_big(cat1, 48, 64, name="I0_", output_name="INCEPTION0", l=l)
    
    i1 = Myinception_batchnorm_decay_big(i0, 64, 92, name="I1_", output_name="INCEPTION1", l=l)
    
    i2 = Myinception_batchnorm_reduce_decay_max(i1, 92, 128, name="I2_", output_name="INCEPTION2", l=l) #this should reduce the grid

    i3 = Myinception_batchnorm_decay_big(i2, 128, 218, name="I3_", output_name="INCEPTION3", without_kernel_7=True, l=l)
    
    i4 = Myinception_batchnorm_decay_big(i3, 218, 360, name="I4_", output_name="INCEPTION4", without_kernel_7=True, l=l)
    
    i5 = Myinception_batchnorm_reduce_decay_max(i4, 360, 402, name="I5_", output_name="INCEPTION5", l=l) #this should reduce the grid

    i6 = Myinception_batchnorm_decay_big(i5, 402, 512, name="I6_", output_name="INCEPTION6", without_kernel_5=True, without_kernel_7=True, l=l)

    i7 = Myinception_batchnorm_decay_big(i6, 512, 720, name="I7_", output_name="INCEPTION7", without_kernel_5=True, without_kernel_7=True, l=l)
    
    poolend = keras.layers.AveragePooling2D(pool_size=8,strides=1,padding='valid',name='poolend')(i7)
    flat = keras.layers.Flatten()(poolend)
    
    cat2 = tf.keras.layers.concatenate([flat,input_derived_data], axis=1, name='cat2')
    
    fc0 = tf.keras.layers.Dense(units=1952, activation=tf.keras.layers.ReLU(), name='fc0')(cat2)#f2 * 2 + f1 + 1
    d0 = tf.keras.layers.Dropout(0.2)(fc0)
    fc1 = tf.keras.layers.Dense(units=1952, activation=tf.keras.layers.ReLU(), name='fc0b')(d0)
    d1 = tf.keras.layers.Dropout(0.2)(fc1)
    fc2 = tf.keras.layers.Dense(units=NB_BINS, activation=tf.keras.activations.softmax, name='fc2')(d1)
        
    model = tf.keras.Model(inputs=[input_images, input_derived_data], outputs=[fc2])
    
    return(model)
    
#####################################################################################

class YSE(CronJobBase):
    RUN_EVERY_MINS = 30
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'YSE_App.data_ingest.PS1_PhotoZ.YSE'
    
    def do(self):
        """
        Predicts photometric redshifts from RA and DEC points in SDSS

        An outline of the algorithem is:

        first pull from SDSS u,g,r,i,z magnitudes from SDSS; 
            should be able to handle a list/array of RA and DEC

        place u,g,r,i,z into a vector, append the derived information into the data array

        predict the information from the model

        return the predictions in the same order to the user

        inputs:
            Ra: list or array of len N, right ascensions of target galaxies in decimal degrees
            Dec: list or array of len N, declination of target galaxies in decimal degrees
            search: float, arcmin tolerance to search for the object in SDSS Catalogue
            path_to_model: str, filepath to saved model for prediction
        
        Returns:
            predictions: array of len N, photometric redshift of input galaxy

        """
        
        try:
            nowdate = datetime.datetime.utcnow() - datetime.timedelta(1)
            from django.db.models import Q #HAS To Remain Here, I dunno why
            print('Entered the photo_z Pan-Starrs CNN cron')        
            #save time b/c the other cron jobs print a time for completion
            
            m = sfdmap.SFDMap(mapdir=djangoSettings.STATIC_ROOT+'/sfddata-master/sfddata-master')
            model_filepath = djangoSettings.STATIC_ROOT+'PS_7_01_ultimate.hdf5' #fill this in with one
                
            NB_BINS = 270
            BATCH_SIZE = 64
            ZMIN = 0.0
            ZMAX = 0.6
            BIN_SIZE = (ZMAX - ZMIN) / NB_BINS
            range_z = np.linspace(ZMIN, ZMAX, NB_BINS + 1)[:NB_BINS]
            
            transients = Transient.objects.filter(Q(host__isnull=False))
            
            my_index = np.array(range(0,len(transients))) #dummy index used in DF, then used to create a mapping from matched galaxies back to these hosts
               
            transient_dictionary = dict(zip(my_index,transients))
                        
            #another script will place the images into the data model, just pull them out here...
            #print('Original length of Transients: ',len(transients))
            for i,T in enumerate(transients): #get rid of fake entries, or entries not yet classified or given a PS cutout
                ID = T.name
                if not(os.path.isfile(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,'g'))) or not(os.path.isfile(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,'r'))) or not(os.path.isfile(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,'i'))) or not(os.path.isfile(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,'z'))) or not(os.path.isfile(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,'y'))): #check if cutout exists from that transient name in dir...
                #It would be simpler maybe to just go around the data model, make a dictionary for the images in the cutout folder and grab them from there...
                    transient_dictionary.pop(i) #if I don't have the image in the data model, drop that transient, wait until the other cron does its job.
 
            #print('attempting to create model')
            mymodel = create_model_groundup_decay_ultimate(NB_BINS)
            #print('attempting to load model')
            mymodel.load_weights(model_filepath)
			
            #first do a modulo to find how many 1000's exist in the transient dictionary
            outer_loop_how_many = len(transient_dictionary)//1000
            remainder_how_many = len(transient_dictionary)%1000

            #next take these numbers to make a list of the keys to transient_dictionary, then query parts of that list in turn...
            whats_left = list(transient_dictionary.keys()) #list holding the keys to transient after removing bad entries...

            #create a holding array for predictions
            posterior = np.zeros((len(whats_left),NB_BINS)) #(how many unique hosts,how many bins of discrete redshift)

            for outer_index in range(outer_loop_how_many):
                use_these_indices = whats_left[outer_index*1000:(outer_index+1)*1000]
                #now reset the data array
                DATA = np.zeros((1000,104,104,5)) #safe because if not 1000 would have //1000 = 0 and range(0) is empty []
                #Now reset the ra and dec lists so I can grab more extinctions
                RA = []
                DEC = []
                for inner_index,value in enumerate(use_these_indices):
                    T = transient_dictionary[use_these_indices[value]]
                    ID = T.name
                    for j,F in enumerate(['g','r','i','z','y']):
                        DATA[inner_index,:,:,j] = np.load(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,F))
                    RA.append(T.host.ra)
                    DEC.append(T.host.dec)

                #Next run model and place into posterior
                Extinctions = m.ebv(np.array(RA),np.array(DEC))
                posterior[outer_index*1000:(outer_index+1)*1000] = mymodel.predict([DATA,Extinctions])

            #next use the remainder

            use_these_indices = whats_left[((outer_index+1)*1000):((outer_index+1)*1000)+remainder_how_many]
            #Reset Data, only create array large enough to hold whats left
            DATA = np.zeros((len(use_these_indices),104,104,5))
            #reset ra,dec
            RA = []
            DEC = []
            for inner_index,value in enumerate(use_these_indices):
                T = transient_dictionary(use_these_indices[value])
                ID = T.name
                for j,F in enumerate(['g','r','i','z','y']):
                    DATA[inner_index,:,:,j] = np.load(djangoSettings.STATIC_ROOT+'/cutouts/cutout_{}_{}.npy'.format(ID,F))
                RA.append(T.host.ra)
                DEC.append(T.host.dec)

            Extinctions = m.ebv(np.array(RA),np.array(DEC))
            posterior[outer_index*1000:(outer_index+1)*1000] = mymodel.predict([DATA,Extinctions])
            #Now posterior should be full!
			
            #print('done')
            point_estimates = np.sum(range_z*posterior,1)
                
            error = np.ones(len(point_estimates))
            for i in range(len(point_estimates)):
                error[i] = np.std(np.random.choice(a=range_z,size=1000,p=posterior[i,:],replace=True)) #this could be parallized i'm sure
                
            for i,value in enumerate(list(transient_dictionary.keys())):
                T = transient_dictionary[value]
                if not(T.host.photo_z_PSCNN): 
                    T.host.photo_z_PSCNN = point_estimates[i]
                    T.host.photo_z_err_PSCNN = error[i]
                    #T.host.photo_z_posterior_PSCNN = posterior[i] #Gautham suggested we add it to the host model
                    #T.host.photo_z_source = 'YSE internal PS CNN' #this is not neccessary its in the name
                    T.host.save() #takes a long time and then my query needs to be reset which is also a long time
    
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("""PS Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno))
            #html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            #sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)