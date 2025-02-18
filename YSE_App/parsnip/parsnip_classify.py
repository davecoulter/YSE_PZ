#!/usr/bin/env python3
# YSE DR1 ParSNIP Photometric classifier
# 3 Classes (Ia/II/Ibc). Option for 2 classes (Ia/CC) but not used here.

# Written by Patrick Aleo (github: patrickaleo)
# Model by Patrick Aleo, Kostya Malanchev
# See YSE DR1 paper for details (https://arxiv.org/pdf/2211.07128.pdf)
# Last updated: 2023-03-21

from django_cron import CronJobBase, Schedule
from django.conf import settings as djangoSettings
import configparser

# read in the options from the param file and the command line
# some convoluted syntax here, making it so param file is not required

# parser = self.add_options(usage=usagestring)
# options,  args = parser.parse_known_args()

config = configparser.ConfigParser()
#print("CONFIG", config)
config.read("%s/settings.ini"%djangoSettings.PROJECT_DIR)
#config.get('parsnip','parsnip_classifier_onnx_model_path')
import argparse
# Added model paths to settings.ini fileself.
# Will run automatically without --arguments
usagestring = "parsnip_classify.py <options>"
parser = argparse.ArgumentParser(usage=usagestring, conflict_handler="resolve")
parser.add_argument('--parsnip_classifier_onnx_model_path', default=config.get('parsnip','parsnip_classifier_onnx_model_path'), type=str, help='parsnip_classifier_onnx_model_path')
parser.add_argument('--parsnip_sims_model_path', default=config.get('parsnip','parsnip_sims_model_path'), type=str, help='parsnip_sims_model_path')
print(parser)
options,  args = parser.parse_known_args()
#print("OP", options.parsnip_classifier_onnx_model_path)
#print("OP2", options.parsnip_sims_model_path)

# config = configparser.ConfigParser()
# parsnip_classifier_onnx_model_path = config.read("%s/settings.ini"%djangoSettings.parsnip_classifier_onnx_model_path)
# print("parsnip_classifier_onnx_model_path", parsnip_classifier_onnx_model_path)

import pickle
import pandas as pd
import sys
import os
from YSE_App.models import *
from django.db.models import Q
from YSE_App.view_utils import get_all_phot_for_transient
from YSE_App.common.utilities import date_to_mjd
import numpy as np
import sys
import operator

import parsnip
import lcdata
from astropy.io import ascii
from astropy.table import Table

import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import classification_report

import onnxruntime as rt

BAND_MAP = {
    'g': 'ps1::g',
    'r': 'ps1::r',
    'i': 'ps1::i',
    'z': 'ps1::z',
    'X': 'ztfg',
    'Y': 'ztfr',
}

def load_parsnip_RFC_file(n_classes):
    print(f"Loading ParSNIP RCF model files for {n_classes} Classes...")
    #sess = rt.InferenceSession(f"./YSE_APP/parsnip/parsnip_random_forest_classifier_model_220112_{n_classes}classes.onnx")
    sess = rt.InferenceSession(options.parsnip_classifier_onnx_model_path)
    #sess = "test"

    input_name = sess.get_inputs()[0].name
    #input_name = "test2"
    label_name = sess.get_outputs()[0].name
    #label_name = "test3"
    print("Loaded!")
    return sess, input_name, label_name

# def do(model, sess_3cls, input_name_3cls, label_name_3cls, sess_2cls, input_name_2cls, label_name_2cls, plot_cm=True, debug=False):
def do(model, sess_3cls, input_name_3cls, label_name_3cls, plot_cm=True, debug=False):
	def _generate_features(model):
		# From the ParSNIP paper
		# order of features determined by classification_paper.py in YSEphotclass github repo
		FEATURES = ['color',
					'color_error',
					'luminosity',
					'luminosity_error',
					'reference_time_error',
					's1',
					's1_error',
					's2',
					's2_error',
					's3',
					's3_error']

		dataset = lc
		#with open('dataset.pickle', 'wb') as f:
		#    print("saving pickle")
		#    pickle.dump(dataset, f)

		predictions = model.predict_dataset(dataset)
		avail_features = [f for f in FEATURES if f in predictions.columns]
		features = predictions[avail_features]
		features_x = np.stack([features[c] for c in features.columns]).T
		return features_x



	# run this under Admin
	user = User.objects.get(username='Admin')

	# get New, Watch, FollowupRequested, Following
	transients_to_classify = \
		Transient.objects.filter(Q(status__name = 'New') |
								 Q(status__name = 'Watch') |
								 Q(status__name = 'Interesting') |
								 Q(status__name = 'FollowupRequested') |
								 Q(status__name = 'Following') |
								 Q(tags__name = 'YSE') | Q(tags__name = 'YSE Forced Phot')).distinct()

	light_curve_list_z,transient_list_t,tns_spec_allclass_l = [],[],[]
	#print("len transients_to_classify", len(transients_to_classify))
	for t in transients_to_classify: # test with transients_to_classify[20000:20100]
		ra, dec, objid, spec_class = t.ra, t.dec, t.name, t.TNS_spec_class
		#if objid != '2021mwb': continue # for testing

		redshift = t.redshift #t.z_or_hostz() throws error...
		if redshift is None:
			#print(f"No z for {objid}! Using median value of YSE DR1 (z=0.14)...")
			#redshift = 0.14  # dummy (YSE DR1 median)
			#continue

			#if no spec redshift, use a photoz estimate
            # In case of No host
			if t.host is None:
				print("No host. Can't get photo-z! Use median value (z=0.14)")
				redshift = 0.14
			else:
                # if has a host, use photoz of host
			    if t.host.photo_z:
				    print("Using photo-z")
				    redshift = t.host.photo_z
			    elif t.host.photo_z_internal:
				    print("Using photo-z_internal")
				    redshift = t.host.photo_z_internal
			    elif t.host.photo_z_PSCNN:
				    print("Using photo-z_PSCNN")
				    redshift = t.host.photo_z_PSCNN
			    # elif t.host.photo_z_source:
				#     print("Using photo-z_source")
				#     redshift = t.host.photo_z_source
			    # if no spec redshift nor photoz estimate, use median of YSE DR1 value
			    else:
				    print(f"No z for {objid}! Using median value of YSE DR1 (z=0.14)...")
				    redshift = 0.14  # dummy (YSE DR1 median)

		if not t.mw_ebv is None:
			mwebv = t.mw_ebv
		else:
			mwebv = 0.0

		meta = {}
		meta.setdefault('object_id', [objid])
		meta.setdefault('ra', [ra])
		meta.setdefault('dec', [dec])
		meta.setdefault('mwebv', [mwebv])
		meta.setdefault('redshift', [redshift])
		meta.setdefault('spec_class', [spec_class])

		print(meta)

		photdata = get_all_phot_for_transient(user, t.id)
		if not photdata:
			print("No photdata. Continue...")
			continue

		gobs = photdata.filter(band__name = 'g')
		robs = photdata.filter(band__name = 'r')
		iobs = photdata.filter(band__name = 'i')
		zobs = photdata.filter(band__name = 'z')
		ztf_gobs = photdata.filter(band__name = 'g-ZTF')
		ztf_robs = photdata.filter(band__name = 'r-ZTF')

		if not len(gobs) and not len(robs) and not len(iobs) and not len(zobs) and not len(ztf_gobs) and not len(ztf_robs):
		   print("no good obs! continue...")
		   continue
		mjd, passband, fluxcals, fluxerrs, mag, magerr, zeropoint, photflag = np.array([]),np.array([]),[],[],[],[],[],[]

		for obs,filt in zip([gobs.order_by('obs_date'),robs.order_by('obs_date'), iobs.order_by('obs_date'), zobs.order_by('obs_date'), ztf_gobs.order_by('obs_date'), ztf_robs.order_by('obs_date')], ['g', 'r', 'i', 'z', 'X', 'Y']):
			for p in obs:

				if p.data_quality == 'YSE_App.DataQuality.None':
				    print("p.data_quality has issue? skip!", p.data_quality)
				    continue
				if not p.mag: 		 # for some reason if no mag, skip!
				    #print("no p.mag")
				    continue
				#if len(np.where((filt == passband) & (np.abs(mjd - date_to_mjd(p.obs_date)) < 0.001))[0]): continue
				mag += [p.mag]
				if p.mag_err:
					magerr += [p.mag_err]
					fluxerr_obs = 0.4*np.log(10)*p.mag_err
				else:
					magerr += [0.001]
					fluxerr_obs = 0.4*np.log(10)*0.001

				flux_obs = 10**(-0.4*(p.mag-27.5))
				mjd = np.append(mjd,[date_to_mjd(p.obs_date)])
				fluxcals += [flux_obs]
				fluxerrs += [fluxerr_obs]
				zeropoint += [27.5]
				passband = np.append(passband,[filt])
		pbs = [BAND_MAP[flt] for flt in passband]

		if len(mjd) <= 1:
			print(f"Only 1 epoch! Skip...")
			continue

		table = Table({'mjd': list(map(float, mjd)),
					   'flux': list(map(float, fluxcals)),
					   'fluxerr': list(map(float, fluxerrs)),
					   'bandpass': list(map(str, pbs))})
		light_curve_info = lcdata.Dataset(Table(meta), [table])

		light_curve_list_z += [light_curve_info,]
		transient_list_t += [t]

	parsnip_d_3cls, parsnip_d_2cls = {}, {}
	best_preds_3cls, probs_3cls, best_preds_2cls, probs_2cls, TNS_spec_3class_l, TNS_spec_2class_l = [], [], [], [], [], []
	for lc, t in zip(light_curve_list_z, transient_list_t):

		print("Defining Features model")
		try:
		    features_x = _generate_features(model=model)
		except Exception as e:
		    print(e)
		    print("Some error with making features from this object. Skip!")
		    continue


		for n_classes in [3]: #[3, 2]
			print("Running classifiers!")
			if n_classes == 3:
				TNS_spec_3class_l.append(t.TNS_spec_class)
				print("Tertiary (SN Ia / SN II / SN Ibc) classifier")
				pred_onx_3cls = sess_3cls.run([label_name_3cls],
											  {input_name_3cls: features_x.astype(np.float32)})[0]
				res_3cls = sess_3cls.run(None, {'float_input': features_x.astype(np.float32)})

				photclass_3cls = str(pred_onx_3cls[0]).replace('SN', 'SN ').replace('SN Ibc', 'SN Ib/c')
				prob_3cls_d = res_3cls[1][:2][0]

				prob_3cls_d = {k.replace('SN', 'SN '): v for k, v in prob_3cls_d.items()}
				prob_3cls_d = {k.replace('SN Ibc', 'SN Ib/c'): v for k, v in prob_3cls_d.items()}
				photo_class_conf = float(round(prob_3cls_d.get(photclass_3cls), 3) * 100)  # probability converted to %
				print(prob_3cls_d)
				print(photclass_3cls)
				print(photo_class_conf)

				best_preds_3cls.append(photclass_3cls)
				probs_3cls.append(prob_3cls_d)

				parsnip_d_3cls[t.name] = [photclass_3cls, prob_3cls_d]

				# Save 3 class photometric classification
				t.photo_class = TransientClass.objects.get(name=photclass_3cls)
				t.save()

				t.photo_class_conf = photo_class_conf
				t.save()
				print("Saving photo class", t.photo_class)
				print("Saving photo class conf", t.photo_class_conf)

			# elif n_classes == 2:
			# 	TNS_spec_2class_l.append(t_info.TNS_spec_class)
			# 	print("Binary (SN Ia / CC SN) classifier")
			# 	pred_onx_2cls = sess_2cls.run([label_name_2cls],
			# 								  {input_name_2cls: features_x.astype(np.float32)})[0]
			# 	res_2cls = sess_2cls.run(None, {'float_input': features_x.astype(np.float32)})
            #
			# 	photclass_2cls = pred_onx_2cls[0]
			# 	prob_2cls_d = res_2cls[1][:2][0]
			# 	print(prob_2cls_d)
			# 	print(photclass_2cls)
            #
			# 	best_preds_2cls.append(photclass_2cls)
			# 	probs_2cls.append(prob_2cls_d)
            #
			# 	parsnip_d_2cls[t_info.name] = [photclass_2cls, prob_2cls_d]
            #
			# 	# Save 2 class photometric classification
			# 	t.photo_class_2cls = photclass_2cls
			# 	t.photo_class_prob_2cls_d = prob_2cls_d
			# 	t.photo_class_2cls_conf = round(prob_2cls_d.get(photclass_2cls), 3) * 100 # probability converted to %
			# 	t.save()

			else:
				raise("Not Implemented!")

	# print("Successfully finished classifying with ParSNIP!")
	# print("Final results...")
	# print("Last object:")
	# print("t.photo_class", t.photo_class)
	# print("t.photo_class_conf", t.photo_class_conf)

	# print("t.photo_class_2cls", t.photo_class_2cls)
	# print("t.photo_class_prob_2cls_d", t.photo_class_prob_2cls_d)
	# print("t.photo_class_2cls_conf", t.photo_class_2cls_conf)


	if plot_cm == True:
		print("plot_cm is true! Saving confusion matrices to ./YSE_App/parsnip/ directory")
		#print(np.unique(tns_spec_allclass_l))
		replace_d_3cls = {'SN II': 'SNII',
						  'SN IIP': 'SNII',
						  'SN IIb': 'SNII',
						  'SN IIn': 'SNII',
						  'SN Ia': 'SNIa',
						  'SN Ia-91T-like': 'SNIa',
						  'SN Iax[02cx-like]': 'SNIa',
						  'SN Ia-pec': 'SNIa',
						  'SN Ia-CSM': 'SNIa',
						  'SN Ia-SC': 'SNIa',
						  'SN Ia-91bg-like': 'SNIa',
						  'SN Ib': 'SNIbc',
						  'SN Ib-pec': 'SNIbc',
						  'SN Ibn': 'SNIbc',
						  'SN Ib/c': 'SNIbc',
						  'SN Ic': 'SNIbc',
						  'SN Ic-BL': 'SNIbc',
						  '---': 'Other',
						  'CV': 'Star',
						  'LBV': 'Other',
						  'LRN': 'Other',
						  'TDE': 'Other',
						  'SN I': 'Other',
						  'SLSN-I': 'Other',
						  'SLSN-II': 'Other',
						  'SN Iax': 'Other',
						  'SN': 'Other',
						  'AGN': 'Other',
						  'Galaxy': 'Other',
						  'Other': 'Other',
						  None: 'Other',
						  'nan': 'NA'}

		TNS_spec_class_l_3cls = [x if x not in replace_d_3cls else replace_d_3cls[x] for x in TNS_spec_3class_l]

		print(classification_report(TNS_spec_class_l_3cls, best_preds_3cls, target_names=['Other', 'SNII', 'SNIa', 'SNIbc']))

		# Percentages only
		cm_3cls = confusion_matrix(TNS_spec_class_l_3cls, best_preds_3cls, labels=['SNII', 'SNIa', 'SNIbc'], normalize='true')
		disp_3cls = ConfusionMatrixDisplay(confusion_matrix=cm_3cls, display_labels=['SNII', 'SNIa', 'SNIbc'])
		disp_3cls.plot()
		plt.title(f"{len(TNS_spec_class_l_3cls)} Spec. Objects")
		plt.savefig(f'./YSE_App/parsnip/new_completeness_cm_3classes_norm.png', dpi=300, bbox_inches='tight')
		plt.show()

		# With counts
		cm_3cls = confusion_matrix(TNS_spec_class_l_3cls, best_preds_3cls, labels=['SNII', 'SNIa', 'SNIbc'])
		disp_3cls = ConfusionMatrixDisplay(confusion_matrix=cm_3cls, display_labels=['SNII', 'SNIa', 'SNIbc'])
		disp_3cls.plot()
		plt.title(f"{len(TNS_spec_class_l_3cls)} Spec. Objects")
		plt.savefig(f'./YSE_App/parsnip/new_completeness_cm_3classes_counts.png', dpi=300, bbox_inches='tight')
		plt.show()


		# replace_d_2cls = {'SN II': 'SNCC',
		# 				  'SN IIP': 'SNCC',
		# 				  'SN IIb': 'SNCC',
		# 				  'SN IIn': 'SNCC',
		# 				  'SN Ia': 'SNIa',
		# 				  'SN Ia-91T-like': 'SNIa',
		# 				  'SN Iax[02cx-like]': 'SNIa',
		# 				  'SN Ia-pec': 'SNIa',
		# 				  'SN Ia-CSM': 'SNIa',
		# 				  'SN Ia-SC': 'SNIa',
		# 				  'SN Ia-91bg-like': 'SNIa',
		# 				  'SN Ib': 'SNCC',
		# 				  'SN Ib-pec': 'SNCC',
		# 				  'SN Ibn': 'SNCC',
		# 				  'SN Ib/c': 'SNCC',
		# 				  'SN Ic': 'SNCC',
		# 				  'SN Ic-BL': 'SNCC',
		# 				  '---': 'Other',
		# 				  'CV': 'Star',
		# 				  'LBV': 'Other',
		# 				  'LRN': 'Other',
		# 				  'TDE': 'Other',
		# 				  'SN I': 'Other',
		# 				  'SLSN-I': 'Other',
		# 				  'SLSN-II': 'Other',
		# 				  'SN Iax': 'Other',
		# 				  'SN': 'Other',
		# 				  'AGN': 'Other',
		# 				  'Galaxy': 'Other',
		# 				  'Other': 'Other',
		# 				  None: 'Other',
		# 				  'nan': 'NA'}
        #
		# TNS_spec_class_l_2cls = [x if x not in replace_d_2cls else replace_d_2cls[x] for x in TNS_spec_2class_l]
        #
		# print(classification_report(TNS_spec_class_l_2cls, best_preds_2cls, target_names=['Other', 'SNCC', 'SNIa']))
        #
		# # Percentages only
		# cm_2cls = confusion_matrix(TNS_spec_class_l_2cls, best_preds_2cls, labels=['SNCC', 'SNIa'], normalize='true')
		# disp_2cls = ConfusionMatrixDisplay(confusion_matrix=cm_2cls, display_labels=['SNCC', 'SNIa'])
		# disp_2cls.plot()
		# plt.title(f"{len(TNS_spec_class_l_2cls)} Spec. Objects")
		# plt.savefig(f'./YSE_App/parsnip/new_completeness_cm_2classes_norm.png', dpi=300, bbox_inches='tight')
		# #plt.show()
        #
		# # With counts
		# cm_2cls = confusion_matrix(TNS_spec_class_l_2cls, best_preds_2cls, labels=['SNCC', 'SNIa'])
		# disp_2cls = ConfusionMatrixDisplay(confusion_matrix=cm_2cls, display_labels=['SNCC', 'SNIa'])
		# disp_2cls.plot()
		# plt.title(f"{len(TNS_spec_class_l_2cls)} Spec. Objects")
		# plt.savefig(f'./YSE_App/parsnip/new_completeness_cm_2classes_counts.png', dpi=300, bbox_inches='tight')
		# #plt.show()

	print("Done with ParSNIP classifications! Cron run Successfully.")


class parsnip_classify_cron(CronJobBase):
	RUN_EVERY_MINS = 120

	schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
	code = 'YSE_App.parsnip.parsnip_classify.parsnip_classify_cron'	 # a unique code
	print("running ParSNIP Cron!")
	model = parsnip.load_model(options.parsnip_sims_model_path) # Loads the model
	#model = 'test' # for testing

	#print("Model", model)
	#print("Model settings", model.settings)

	sess_3cls, input_name_3cls, label_name_3cls = load_parsnip_RFC_file(n_classes=3) # takes ~3min to load model
	#sess_2cls, input_name_2cls, label_name_2cls = load_parsnip_RFC_file(n_classes=2)

	#def do(self, model=model, sess_3cls=sess_3cls, input_name_3cls=input_name_3cls, label_name_3cls=label_name_3cls, sess_2cls=sess_2cls, input_name_2cls=input_name_2cls, label_name_2cls=label_name_2cls, plot_cm=False, debug=False):
	def do(self, model=model, sess_3cls=sess_3cls, input_name_3cls=input_name_3cls, label_name_3cls=label_name_3cls, plot_cm=False, debug=False):
		try:
			#do(model=model, sess_3cls=sess_3cls, input_name_3cls=input_name_3cls, label_name_3cls=label_name_3cls, sess_2cls=sess_2cls, input_name_2cls=input_name_2cls, label_name_2cls=label_name_2cls, plot_cm=False, debug=debug)
			do(model=model, sess_3cls=sess_3cls, input_name_3cls=input_name_3cls, label_name_3cls=label_name_3cls, plot_cm=False, debug=debug)
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print("""PARSNIP cron failed with error %s at line number %s"""%(repr(e),exc_tb.tb_lineno))

  # def add_options(self, parser=None, usage=None, config=None):
  # import argparse
  # if parser == None:
  #  parser = argparse.ArgumentParser(usage=usage, conflict_handler="resolve")
  #
  # # The basics
  # parser.add_argument('-v', '--verbose', action="count", dest="verbose",default=1)
  # parser.add_argument('--clobber', default=False, action="store_true", help='clobber output file')
  # parser.add_argument('-s','--settingsfile', default=None, type=str, help='settings file (login/password info)')
  # parser.add_argument('--status', default='New', type=str, help='transient status to enter in YS_PZ')
  # parser.add_argument('--parsnip_classifier_onnx_model_path', default=config.get('main','parsnip_classifier_onnx_model_path'), type=str, help='parsnip_classifier_onnx_model_path')
  # parser.add_argument('--parsnip_sims_model_path', default=config.get('main','parsnip_sims_model_path'), type=str, help='parsnip_classifier_onnx_model_path')
  #
  # if config:
  #  parser.add_argument('--parsnip_classifier_onnx_model_path', default=config.get('main','parsnip_classifier_onnx_model_path'), type=str, help='parsnip_classifier_onnx_model_path')
  #  parser.add_argument('--parsnip_sims_model_path', default=config.get('main','parsnip_sims_model_path'), type=str, help='parsnip_classifier_onnx_model_path')
  #
  # else:
  #  pass
  #
  #
  # return(parser)

if __name__ == "__main__":
	do()
