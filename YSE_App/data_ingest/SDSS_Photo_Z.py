from django_cron import CronJobBase, Schedule
from YSE_App.models.transient_models import *
from YSE_App.common.alert import sendemail
from django.conf import settings as djangoSettings
import datetime
import numpy as np
import pandas as pd
import os
import pickle
import sys
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

import SciServer
from SciServer import CasJobs
from SciServer import SkyQuery


def jobDescriber(jobDescription):
    # Prints the results of the CasJobs job status functions in a human-readable manner
    # Input: the python dictionary returned by getJobStatus(jobId) or waitForJob(jobId)
    # Output: prints the dictionary to screen with readable formatting
    import pandas

    if jobDescription["Status"] == 0:
        status_word = "Ready"
    elif jobDescription["Status"] == 1:
        status_word = "Started"
    elif jobDescription["Status"] == 2:
        status_word = "Cancelling"
    elif jobDescription["Status"] == 3:
        status_word = "Cancelled"
    elif jobDescription["Status"] == 4:
        status_word = "Failed"
    elif jobDescription["Status"] == 5:
        status_word = "Finished"
    else:
        status_word = "Status not found!!!!!!!!!"

    print("JobID: ", jobDescription["JobID"])
    print("Status: ", status_word, " (", jobDescription["Status"], ")")
    print("Target (context being searched): ", jobDescription["Target"])
    print("Message: ", jobDescription["Message"])
    print("Created_Table: ", jobDescription["Created_Table"])
    print("Rows: ", jobDescription["Rows"])
    wait = pandas.to_datetime(jobDescription["TimeStart"]) - pandas.to_datetime(
        jobDescription["TimeSubmit"]
    )
    duration = pandas.to_datetime(jobDescription["TimeEnd"]) - pandas.to_datetime(
        jobDescription["TimeStart"]
    )
    print("Wait time: ", wait.seconds, " seconds")
    print("Query duration: ", duration.seconds, "seconds")


class YSE(CronJobBase):

    RUN_EVERY_MINS = 240

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "YSE_App.data_ingest.Photo_Z.YSE"

    def do(
        self,
        user="awe2",
        password="StandardPassword",
        search=1,
        path_to_model="YSE_DNN_photoZ_model_315.hdf5",
        debug=True,
    ):
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
            from django.db.models import Q  # HAS To Remain Here, I dunno why

            print("Entered the photo_z cron")
            # save time b/c the other cron jobs print a time for completion

            transients = Transient.objects.filter(
                Q(host__isnull=False) & Q(host__photo_z__isnull=True)
            )

            my_index = np.array(
                range(0, len(transients))
            )  # dummy index used in DF, then used to create a mapping from matched galaxies back to these hosts

            transient_dictionary = dict(zip(my_index, transients))

            RA = []
            DEC = []
            for i, T in enumerate(transients):  # get rid of fake entries
                if T.host.ra and T.host.dec:
                    RA.append(T.host.ra)
                    DEC.append(T.host.dec)
                else:
                    transient_dictionary.pop(i)

            DF_pre = pd.DataFrame()
            DF_pre["myindex"] = list(transient_dictionary.keys())
            DF_pre["RA"] = RA
            DF_pre["DEC"] = DEC

            SciServer.Authentication.login(user, password)

            try:
                SciServer.SkyQuery.dropTable("SDSSTable1", datasetName="MyDB")
                SciServer.SkyQuery.dropTable("SDSSTable2", datasetName="MyDB")
            except Exception as e:
                print("tables are not in CAS MyDB, continuing")
                print("if system says table is already in DB, contact Andrew Engel")

            SciServer.CasJobs.uploadPandasDataFrameToTable(
                DF_pre, "SDSSTable1", context="MyDB"
            )

            myquery = "SELECT s.myindex, p.z, p.zErr, p.nnAvgZ "
            myquery += "INTO MyDB.SDSSTable2 "
            myquery += "FROM MyDB.SDSSTable1 s "
            myquery += "CROSS APPLY dbo.fGetNearestObjEq(s.RA,s.DEC,1.0/60.0) AS nb "
            myquery += "INNER JOIN Photoz p ON p.objID = nb.objID"

            jobID = CasJobs.submitJob(sql=myquery, context="DR16")

            waited = SciServer.CasJobs.waitForJob(jobId=jobID)

            jobDescription = CasJobs.getJobStatus(jobID)

            jobDescriber(jobDescription)

            PhotoDF = SciServer.SkyQuery.getTable(
                "SDSSTable2", datasetName="MyDB", top=10
            )

            # change this
            PhotoDF.drop_duplicates(
                subset="#myindex", inplace=True
            )  # neccessary to patch some bugs
            PhotoDF.dropna(inplace=True)

            whats_left = PhotoDF["#myindex"].values
            point_estimates = PhotoDF["z"].values
            error = PhotoDF["zErr"].values
            other_z = PhotoDF["nnAvgZ"]

            point_estimates[error < -9998] = other_z[
                error < -9998
            ]  # if there is a bad error, then authors write this is more effective

            for i, value in enumerate(whats_left):
                T = transient_dictionary[value]
                T.host.photo_z = point_estimates[i]
                T.host.photo_z_err = error[i]
                # T.host.photo_z_posterior = posterior[i] #Gautham suggested we add it to the host model
                T.host.photo_z_source = "SDSS"
                T.host.save()  # takes a long time and then my query needs to be reset which is also a long time

            print("time taken with upload:", datetime.datetime.utcnow() - nowdate)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(
                """Photo-z cron failed with error %s at line number %s"""
                % (e, exc_tb.tb_lineno)
            )
            # html_msg = """Photo-z cron failed with error %s at line number %s"""%(e,exc_tb.tb_lineno)
            # sendemail(from_addr, user.email, subject, html_msg,
            #          djangoSettings.SMTP_LOGIN, djangoSettings.SMTP_PASSWORD, smtpserver)


# IDK = YSE() #why is this suddenly neccessary???
# IDK.do()
