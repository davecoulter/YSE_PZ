#!/usr/bin/env python
# to be run in python manage.py shell
# adds the ZTF fields with high metrics to the survey list, so they can
# be used in queries

import astropy.table as at
from YSE_App.models import *
from django.conf import settings as djangoSettings


def main():

    ztf = at.Table.read(
        "%s/good_ZTF_field_metric.txt" % djangoSettings.STATIC_ROOT, format="ascii"
    )
    user = User.objects.filter(username="admin")[0]

    survey_entries = []
    for z in ztf:
        surveydict = {"created_by_id": user.id, "modified_by_id": user.id}
        surveydict["obs_group"] = ObservationGroup.objects.filter(name="ZTF")[0]
        surveydict["field_id"] = "ZTF.%i" % z["field"]
        surveydict["ra_cen"] = z["RA"]
        surveydict["dec_cen"] = z["Dec"]
        surveydict["instrument"] = Instrument.objects.filter(name="ZTF-Cam")[0]
        surveydict["width_deg"] = 6.9
        surveydict["height_deg"] = 6.9
        surveydict["ztf_field_id"] = z["field"]

        dbsurveyfield = SurveyField.objects.filter(field_id=surveydict["field_id"])

        if len(dbsurveyfield):
            dbsurveyfield.update(**surveydict)
        else:
            dbsurveyfield = SurveyField(**surveydict)
            survey_entries += [dbsurveyfield]

    SurveyField.objects.bulk_create(survey_entries)

    return


if __name__ == "__main__":
    main()
