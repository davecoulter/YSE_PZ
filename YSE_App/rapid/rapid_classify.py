# YSE Photometric classifier

# Written by Patrick Aleo (github: patrickaleo), David Jones (github: djones1040)
# Last updated: 2021-06-02

# NOTE: had to change astrorapid to allow for X,Y filters (not in "LSST" filter group)
# had to pick central wavelength of r,g in /Users/patrickaleo/miniconda3/envs/yse_pz/lib/python3.7/site-packages/astrorapid/ANTARES_object


from astrorapid.classify import Classify
from django_cron import CronJobBase, Schedule

import sys
import os
from YSE_App.models import *
from django.db.models import Q
from YSE_App.view_utils import get_all_phot_for_transient
from YSE_App.common.utilities import date_to_mjd
import numpy as np
import sys
import operator

classdict = {
    "SNIa": "SN Ia",
    "SN Ia": "SN Ia",
    "SNIa-norm": "SN Ia",
    "SNIbc": "SN Ib/c",
    "SNII": "SN II",
    "SNIa-91bg": "SN Ia-91bg-like",
    "SNIa-x": "SN Iax",
    "point-Ia": "point-Ia",
    "Kilonova": "Kilonova",
    "SLSN-I": "SLSN-I",
    "PISN": "PISN",
    "ILOT": "ILOT",
    "CART": "CART",
    "TDE": "TDE",
    "AGN": "AGN",
}


def do(debug=False):
    # run this under Admin
    user = User.objects.get(username="Admin")

    # get New, Watch, FollowupRequested, Following
    transients_to_classify = Transient.objects.filter(
        Q(status__name="New")
        | Q(status__name="Watch")
        | Q(status__name="Interesting")
        | Q(status__name="FollowupRequested")
        | Q(status__name="Following")
        | Q(tags__name="YSE")
        | Q(tags__name="YSE Forced Phot")
    ).distinct()

    light_curve_list_z, light_curve_list_noz, transient_list_z, transient_list_noz = (
        [],
        [],
        [],
        [],
    )

    for (
        t
    ) in transients_to_classify:  # .filter(Q(name = '2019np') | Q(name = '2019gf')):
        ra, dec, objid, redshift = t.ra, t.dec, t.name, t.z_or_hostz()
        if not t.mw_ebv is None:
            mwebv = t.mw_ebv
        else:
            mwebv = 0.0

        photdata = get_all_phot_for_transient(user, t.id)
        if t.name == "2021aoh":
            continue  # TODO: WHY DOES THIS FAIL??? IT has data...
        if not photdata:
            continue

        gobs = photdata.filter(band__name="g")
        robs = photdata.filter(band__name="r")
        iobs = photdata.filter(band__name="i")
        zobs = photdata.filter(band__name="z")
        ztf_gobs = photdata.filter(band__name="g-ZTF")
        ztf_robs = photdata.filter(band__name="r-ZTF")
        if (
            not len(gobs)
            and not len(robs)
            and not len(iobs)
            and not len(zobs)
            and not len(ztf_gobs)
            and not len(ztf_robs)
        ):
            continue
        mjd, passband, flux, fluxerr, mag, magerr, zeropoint, photflag = (
            np.array([]),
            np.array([]),
            [],
            [],
            [],
            [],
            [],
            [],
        )

        first_detection_set = False
        for obs, filt in zip(
            [
                gobs.order_by("obs_date"),
                robs.order_by("obs_date"),
                iobs.order_by("obs_date"),
                zobs.order_by("obs_date"),
                ztf_gobs.order_by("obs_date"),
                ztf_robs.order_by("obs_date"),
            ],
            ["g", "r", "i", "z", "X", "Y"],
        ):
            for p in obs:
                if p.data_quality:
                    continue
                if not p.mag:
                    continue  # for some reason if no mag, skip!
                if len(
                    np.where(
                        (filt == passband)
                        & (np.abs(mjd - date_to_mjd(p.obs_date)) < 0.001)
                    )[0]
                ):
                    continue
                mag += [p.mag]
                if p.mag_err:
                    magerr += [p.mag_err]
                    fluxerr_obs = 0.4 * np.log(10) * p.mag_err
                else:
                    magerr += [0.001]
                    fluxerr_obs = 0.4 * np.log(10) * 0.001

                flux_obs = 10 ** (-0.4 * (p.mag - 27.5))
                mjd = np.append(mjd, [date_to_mjd(p.obs_date)])
                flux += [flux_obs]
                fluxerr += [fluxerr_obs]
                zeropoint += [27.5]
                passband = np.append(passband, [filt])

                if flux_obs / fluxerr_obs > 5 and not first_detection_set:
                    photflag += [6144]
                    first_detection_set = True
                elif flux_obs / fluxerr_obs > 5:
                    photflag += [4096]
                else:
                    photflag += [0]

        if redshift:
            light_curve_info = (
                mjd,
                flux,
                fluxerr,
                passband,
                photflag,
                ra,
                dec,
                objid,
                redshift,
                mwebv,
            )
            if len(np.unique(passband)) > 1:
                light_curve_list_z += [light_curve_info]
                transient_list_z += [t]
        else:
            light_curve_info = (
                mjd,
                flux,
                fluxerr,
                passband,
                photflag,
                ra,
                dec,
                objid,
                None,
                mwebv,
            )
            if len(np.unique(passband)) > 1:
                light_curve_list_noz += [light_curve_info]
                transient_list_noz += [t]

                # TODO: ADD no redshift model!!!
                # if len(light_curve_list_noz):
                # 	classification_noz = Classify(model_name = 'ZTF_unknown_redshift', known_redshift=False, bcut=False, zcut=None)
                # 	predictions_noz = classification_noz.get_predictions(light_curve_list_noz)
                # else: predictions_noz = [[]]

    dirname = os.path.dirname(__file__)
    model_filepath_z = os.path.join(
        dirname,
        "V20210807_3Model_YSE_ZTF_50k_no_cuts_2000epochs_dropout0pt2_keras_model.hdf5",
    )

    try:
        if len(light_curve_list_z):
            classification_z = Classify(
                model_filepath=model_filepath_z,
                known_redshift=True,
                passbands=("g", "r", "i", "z", "X", "Y"),
                class_names=tuple(("Pre-explosion", "SNII", "SNIa-norm", "SNIbc")),
                nobs=50,
                mintime=-70,
                maxtime=80,
                timestep=3.0,
                bcut=False,
                zcut=None,
                graph=None,
                model=None,
            )

            predictions_z = classification_z.get_predictions(light_curve_list_z)
            # print(classification_z.class_names)   #CHECK this matches class_names

        else:
            predictions_z = [[]]

    except Exception as e1:
        print(e1)
        pass

    if debug:
        import matplotlib.pyplot as plt

        plt.ion()
        classification_z.plot_light_curves_and_classifications(indexes_to_plot=(0,))

    transient_class_list = []

    # for predictions,tl in zip([predictions_z[0]+predictions_noz[0]], [transient_list_z+transient_list_noz]):
    for predictions, tl in zip([predictions_z[0]], [transient_list_z]):
        for i, (pred, t) in enumerate(zip(predictions, tl)):
            try:
                best_predictions = predictions[i][-1, :]

                adjusted_best_predictions = np.zeros(20)
                idx, outclassnames, PIa = 0, [], 0
                for j in range(len(classification_z.class_names)):
                    if classification_z.class_names[j] == "Pre-explosion":
                        continue
                    elif classification_z.class_names[j].startswith("SNIa"):
                        PIa += best_predictions[j]
                    else:
                        outclassnames += [classification_z.class_names[j]]
                        adjusted_best_predictions[idx] = best_predictions[j]
                        idx += 1

                outclassnames += ["SN Ia"]
                outclassnames = np.array(outclassnames)
                adjusted_best_predictions = adjusted_best_predictions[
                    : len(outclassnames)
                ]
                adjusted_best_predictions[-1] = PIa

                print(
                    t.name,
                    outclassnames[
                        adjusted_best_predictions == np.max(adjusted_best_predictions)
                    ][0],
                )
                transient_class = outclassnames[
                    adjusted_best_predictions == np.max(adjusted_best_predictions)
                ][0]
                transient_class_list.append(transient_class)
                photo_class = TransientClass.objects.filter(
                    name=classdict[transient_class]
                )

            except Exception as e:
                import pdb

                pdb.set_trace()
                print(f"Runtime Error: {e}")
                raise RuntimeError(e)

            if len(photo_class):
                t.photo_class = photo_class[0]
                t.save()
            else:
                print("class %s not in DB" % classdict[transient_class])
                raise RuntimeError("class %s not in DB" % classdict[transient_class])

    print("successfully finished classifying with RAPID")


class rapid_classify_cron(CronJobBase):
    RUN_EVERY_MINS = 120

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.rapid.rapid_classify.rapid_classify_cron"  # a unique code

    def do(self, debug=False):
        try:
            do(debug=debug)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(
                """RAPID cron failed with error %s at line number %s"""
                % (repr(e), exc_tb.tb_lineno)
            )


if __name__ == "__main__":
    do()
