import datetime
import json
import logging
import os
import pdb
import random
import string
import time

from astropy import units as u
from astropy import wcs
from astropy.coordinates import SkyCoord
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.db.models import F
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin
from django_tables2 import RequestConfig

import YSE_App.yse_utils.utility_functions as utility
from YSE_App.models import *

# view for updating the obs status of a row in the DB
@csrf_protect
@login_required
def toggle_field(request):

    if request.method == "POST":
        try:
            # unpack the data
            targetField_id = request.POST.get("rowID")
            viewer_state = utility.str2bool(request.POST.get("rowState"))  # oof

            # get the row from the DB
            tfs = SurveyFieldMSB.objects.get(
                id__exact=targetField_id
            ).survey_fields.select_related()
            if tfs[0].active == viewer_state:
                for tf in tfs[0:1]:
                    tf.active = not tfs[0].active
                    # save
                    tf.save()

                for tf in tfs[1:]:
                    tf.active = tfs[0].active
                    # save
                    tf.save()

                return JsonResponse({"newState": tf.active})

                # general unknown error
        except Exception as e:
            print(e)
            return HttpResponseServerError()


# view for toggling active status of a fieldset
@csrf_protect
@login_required
def toggle_fieldset(request):

    if request.method == "POST":
        try:
            # unpack the data
            fieldSet_id = request.POST.get("rowID")
            viewer_state = utility.str2bool(request.POST.get("rowState"))  # oof

            # get the row from the DB
            fs = FieldSet.objects.get(id__exact=fieldSet_id)

            # if the DB obsStatus agress with what the user sees,
            # do the toggle and parse the data, otherwise do nothing
            if fs.fieldSetActive == viewer_state:

                # toggle
                fs.fieldSetActive = not fs.fieldSetActive
                fs.save()

                # now apply to all TargetFields in this set
                targetFields = list(fs.targetfield_set.all())
                for field in targetFields:
                    field.targetFieldActive = fs.fieldSetActive
                    field.save()

            return JsonResponse(
                {"newState": fs.fieldSetActive}
            )  # this must be returned for toggling

            # general unknown error
        except Exception as e:
            print(e)
            return HttpResponseServerError()


@csrf_protect
@login_required
def get_field_verts(request):

    if request.method == "POST":

        # logger.info('drawing field verts')
        DtoR = np.pi / 180.0
        RtoD = DtoR ** -1

        # get the field info
        targetField_id = request.POST.get("rowID")
        # site = request.POST.get('telescope')

        # retrieve the recent FOV for this user
        fov = CanvasFOV.objects.latest("created")

        try:
            # get the row from the DB
            tf = SurveyField.objects.get(id__exact=targetField_id)
            # ts = models.Telescope.objects.get(siteName__exact=site)

            # HTML canvas origin is upper left, astropy assumes the same
            # set up a projection
            w = wcs.WCS(naxis=2)
            # field center pixel numbers
            w.wcs.crpix = [fov.canvas_x_grid_size / 2.0, fov.canvas_y_grid_size / 2.0]
            # pixel deltas (north up, east left, pixel origin at upper left)
            w.wcs.cdelt = np.array(
                [
                    -1.0 * fov.fovWidth / fov.canvas_x_grid_size,
                    -1.0 * fov.fovWidth / fov.canvas_y_grid_size,
                ]
            )
            # field center RA/Dec
            w.wcs.crval = [fov.raCenter, fov.decCenter]
            w.wcs.cunit = ["deg", "deg"]
            w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

            # construct the SkyCoords for the scope fields
            boxCenter = SkyCoord(tf.ra_cen, tf.dec_cen, unit="deg")
            boxXSize = tf.width_deg * u.deg
            boxYSize = tf.height_deg * u.deg

            offsetMagnitude = (
                np.sqrt((boxXSize.value / 2.0) ** 2 + (boxYSize.value / 2.0) ** 2)
                * u.deg
            )
            tanAngle = (
                np.arctan2(boxXSize.value / 2.0, boxYSize.value / 2.0) * 180.0 / np.pi
            )

            box_ul = boxCenter.directional_offset_by(
                (90.0 - tanAngle) * u.deg, offsetMagnitude
            )
            box_lr = boxCenter.directional_offset_by(
                (-90.0 - tanAngle) * u.deg, offsetMagnitude
            )
            box_ll = boxCenter.directional_offset_by(
                (90.0 + tanAngle) * u.deg, offsetMagnitude
            )
            box_ur = boxCenter.directional_offset_by(
                (-90.0 + tanAngle) * u.deg, offsetMagnitude
            )
            worlds_box = np.array(
                [
                    [boxCenter.ra.value, boxCenter.dec.value],
                    [box_ul.ra.value, box_ul.dec.value],
                    [box_ur.ra.value, box_ur.dec.value],
                    [box_lr.ra.value, box_lr.dec.value],
                    [box_ll.ra.value, box_ll.dec.value],
                ]
            )
            pix_box = w.wcs_world2pix(worlds_box, 0)

            # Convert the RA/Dec to pixel coordinates.
            tmp = [
                [pix_box[1][0], pix_box[1][1]],
                [pix_box[2][0], pix_box[2][1]],
                [pix_box[3][0], pix_box[3][1]],
                [pix_box[4][0], pix_box[4][1]],
            ]

            ret_verts = json.dumps(tmp)
            return HttpResponse(ret_verts, content_type="application/json")

            # general unknown error
        except Exception as e:
            print("ERROR: {}".format(e))
            return HttpResponse()
            # return HttpResponseServerError()


@csrf_protect
@login_required
def get_sn_verts(request):

    if request.method == "POST":

        # logger.info('drawing field verts')
        DtoR = np.pi / 180.0
        RtoD = DtoR ** -1

        # get the field info
        transient_id = request.POST.get("rowID")
        # site = request.POST.get('telescope')

        # retrieve the recent FOV for this user
        fov = CanvasFOV.objects.latest("created")

        try:
            # get the row from the DB
            tf = Transient.objects.get(id__exact=transient_id)
            # ts = models.Telescope.objects.get(siteName__exact=site)

            # HTML canvas origin is upper left, astropy assumes the same
            # set up a projection
            w = wcs.WCS(naxis=2)
            # field center pixel numbers
            w.wcs.crpix = [fov.canvas_x_grid_size / 2.0, fov.canvas_y_grid_size / 2.0]
            # pixel deltas (north up, east left, pixel origin at upper left)
            w.wcs.cdelt = np.array(
                [
                    -1.0 * fov.fovWidth / fov.canvas_x_grid_size,
                    -1.0 * fov.fovWidth / fov.canvas_y_grid_size,
                ]
            )
            # field center RA/Dec
            w.wcs.crval = [fov.raCenter, fov.decCenter]
            w.wcs.cunit = ["deg", "deg"]
            w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

            # construct the SkyCoords for the scope fields
            boxCenter = SkyCoord(tf.ra, tf.dec, unit="deg")
            boxXSize = 1.0 * u.deg
            boxYSize = 1.0 * u.deg

            offsetMagnitude = (
                np.sqrt((boxXSize.value / 2.0) ** 2 + (boxYSize.value / 2.0) ** 2)
                * u.deg
            )
            tanAngle = (
                np.arctan2(boxXSize.value / 2.0, boxYSize.value / 2.0) * 180.0 / np.pi
            )

            box_ul = boxCenter.directional_offset_by(
                (90.0 - tanAngle) * u.deg, offsetMagnitude
            )
            box_lr = boxCenter.directional_offset_by(
                (-90.0 - tanAngle) * u.deg, offsetMagnitude
            )
            box_ll = boxCenter.directional_offset_by(
                (90.0 + tanAngle) * u.deg, offsetMagnitude
            )
            box_ur = boxCenter.directional_offset_by(
                (-90.0 + tanAngle) * u.deg, offsetMagnitude
            )
            worlds_box = np.array(
                [
                    [boxCenter.ra.value, boxCenter.dec.value],
                    [box_ul.ra.value, box_ul.dec.value],
                    [box_ur.ra.value, box_ur.dec.value],
                    [box_lr.ra.value, box_lr.dec.value],
                    [box_ll.ra.value, box_ll.dec.value],
                ]
            )
            pix_box = w.wcs_world2pix(worlds_box, 0)

            # Convert the RA/Dec to pixel coordinates.
            tmp = [
                [pix_box[1][0], pix_box[1][1]],
                [pix_box[2][0], pix_box[2][1]],
                [pix_box[3][0], pix_box[3][1]],
                [pix_box[4][0], pix_box[4][1]],
            ]

            ret_verts = json.dumps(tmp)
            # import pdb; pdb.set_trace()
            return HttpResponse(ret_verts, content_type="application/json")

            # general unknown error
        except Exception as e:
            print("ERROR: {}".format(e))
            return HttpResponse()
            # return HttpResponseServerError()


@csrf_protect
@login_required
def get_fieldmsb_verts(request):

    if request.method == "POST":

        # logger.info('drawing field verts')
        DtoR = np.pi / 180.0
        RtoD = DtoR ** -1

        # get the field info
        targetField_id = request.POST.get("rowID")
        # site = request.POST.get('telescope')

        # retrieve the recent FOV for this user
        fov = CanvasFOV.objects.latest("created")

        try:
            # get the row from the DB
            tfs = SurveyFieldMSB.objects.get(
                id__exact=targetField_id
            ).survey_fields.select_related()
            rowID_list, activeStatus_list = [], []
            for tf in tfs:
                # HTML canvas origin is upper left, astropy assumes the same
                # set up a projection
                w = wcs.WCS(naxis=2)
                # field center pixel numbers
                w.wcs.crpix = [
                    fov.canvas_x_grid_size / 2.0,
                    fov.canvas_y_grid_size / 2.0,
                ]
                # pixel deltas (north up, east left, pixel origin at upper left)
                w.wcs.cdelt = np.array(
                    [
                        -1.0 * fov.fovWidth / fov.canvas_x_grid_size,
                        -1.0 * fov.fovWidth / fov.canvas_y_grid_size,
                    ]
                )
                # field center RA/Dec
                w.wcs.crval = [fov.raCenter, fov.decCenter]
                w.wcs.cunit = ["deg", "deg"]
                w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

                # construct the SkyCoords for the scope fields
                boxCenter = SkyCoord(tf.ra_cen, tf.dec_cen, unit="deg")
                boxXSize = tf.width_deg * u.deg
                boxYSize = tf.height_deg * u.deg

                offsetMagnitude = (
                    np.sqrt((boxXSize.value / 2.0) ** 2 + (boxYSize.value / 2.0) ** 2)
                    * u.deg
                )
                tanAngle = (
                    np.arctan2(boxXSize.value / 2.0, boxYSize.value / 2.0)
                    * 180.0
                    / np.pi
                )

                box_ul = boxCenter.directional_offset_by(
                    (90.0 - tanAngle) * u.deg, offsetMagnitude
                )
                box_lr = boxCenter.directional_offset_by(
                    (-90.0 - tanAngle) * u.deg, offsetMagnitude
                )
                box_ll = boxCenter.directional_offset_by(
                    (90.0 + tanAngle) * u.deg, offsetMagnitude
                )
                box_ur = boxCenter.directional_offset_by(
                    (-90.0 + tanAngle) * u.deg, offsetMagnitude
                )
                worlds_box = np.array(
                    [
                        [boxCenter.ra.value, boxCenter.dec.value],
                        [box_ul.ra.value, box_ul.dec.value],
                        [box_ur.ra.value, box_ur.dec.value],
                        [box_lr.ra.value, box_lr.dec.value],
                        [box_ll.ra.value, box_ll.dec.value],
                    ]
                )
                pix_box = w.wcs_world2pix(worlds_box, 0)

                # Convert the RA/Dec to pixel coordinates.
                # tmp = [ [pix_box[1][0],pix_box[1][1]],
                # 		[pix_box[2][0],pix_box[2][1]],
                # 		[pix_box[3][0],pix_box[3][1]],
                # 		[pix_box[4][0],pix_box[4][1]] ]

                # ret_verts = json.dumps(tmp)
                rowID_list.append(tf.id)
                activeStatus_list.append(tf.active)

            ret_list = json.dumps([rowID_list, activeStatus_list])
            return HttpResponse(ret_list)

            # import pdb; pdb.set_trace()
            # return HttpResponse(ret_verts, content_type="application/json")

            # general unknown error
        except Exception as e:
            print("ERROR: {}".format(e))
            return HttpResponse()
            # return HttpResponseServerError()


@csrf_protect
@login_required
def update_target_field_locations(request):

    DtoR = np.pi / 180.0
    RtoD = DtoR ** -1

    if request.method == "POST":

        # unpack the data
        fieldIDs = request.POST.getlist("fieldNames[]")
        fieldXCoords = request.POST.getlist("fieldXCoords[]")
        fieldYCoords = request.POST.getlist("fieldYCoords[]")
        fieldSetID = request.POST["fieldSetID"]

        # create a new FieldSet in which to store these fields
        fs_new = FieldSet.objects.get(id__exact=fieldSetID)
        fs_new.id = None
        fs_new.save()  # necessary to FK into this entry
        fs_new.fieldSetName += "_custom_{}".format(
            timezone.now().strftime("%Y%m%d_%H:%M")
        )
        fs_new.fieldText = "# FieldName, FieldRA, FieldDec, Telscope, Filter, ExpTime, Priority, Status"

        # retrieve the recent FOV for this user
        fov = CanvasFOV.objects.filter(
            author=request.session.get("rand_session_id", "ANON")
        ).latest("created")

        # set up the WCS
        w = wcs.WCS(naxis=2)
        # field center pixel numbers
        w.wcs.crpix = [fov.canvas_x_grid_size / 2.0, fov.canvas_y_grid_size / 2.0]

        # pixel deltas (north up, east left, pixel origin at upper left)
        w.wcs.cdelt = np.array(
            [
                -1.0 * fov.fovWidth / fov.canvas_x_grid_size,
                -1.0 * fov.fovWidth / fov.canvas_y_grid_size,
            ]
        )
        # field center RA/Dec
        w.wcs.crval = [fov.raCenter, fov.decCenter]
        w.wcs.cunit = ["deg", "deg"]
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        for i in range(len(fieldIDs)):
            fieldID = fieldIDs[i]
            fieldXCoord = float(fieldXCoords[i])
            fieldYCoord = float(fieldYCoords[i])

            fieldCenterCoords = w.wcs_pix2world([[fieldXCoord, fieldYCoord]], 0)

            # look up this field
            tf_new = SurveyFieldMSB.objects.get(id__exact=fieldID.split("_")[1])

            # set PK to None so the ORM will execute an insert
            tf_new.id = None

            # update the coordinates
            tf_new.fieldRA_deg = fieldCenterCoords[0][0]
            tf_new.fieldDec_deg = fieldCenterCoords[0][1]

            tf_new.fieldRA = utility.deg2sex(tf_new.fieldRA_deg / 15.0)
            tf_new.fieldDec = utility.deg2sex(tf_new.fieldDec_deg)

            # update the FK into the FieldSet table
            tf_new.fieldSet = fs_new

            # update the FieldSet text to reflect the new entry
            newTextRow = "\n{}, ".format(tf_new.fieldName)
            newTextRow += "{}, {}, ".format(tf_new.fieldRA, tf_new.fieldDec)
            newTextRow += "{}, {}, {}, ".format(
                tf_new.telinstName, tf_new.filterName, tf_new.exposureTime
            )
            newTextRow += "{}, {}".format(tf_new.fieldPriority, tf_new.obsStatus)
            fs_new.fieldText += newTextRow

            # leave the rest unchanged and save
            tf_new.save()

            # save the new FieldSet
        fs_new.save()

        return JsonResponse({"redirect": fs_new.get_absolute_url()})


@csrf_protect
@login_required
def init_draw_fields(request):
    if request.method == "POST":
        try:
            rowID_list = []
            activeStatus_list = []
            # retrieve the recent FOV for this user
            fov = CanvasFOV.objects.latest("created")

            decLoLimit = fov.decCenter - fov.fovWidth / 2.0
            decUpLimit = fov.decCenter + fov.fovWidth / 2.0

            if decUpLimit > 90:
                raLoLimit = 0.0
                raUpLimit = 360.0
                decFactor = 1.0
            else:
                decFactor = np.cos(decUpLimit * np.pi / 180.0)
                raLoLimit = fov.raCenter - fov.fovWidth / 2.0 / decFactor
                raUpLimit = fov.raCenter + fov.fovWidth / 2.0 / decFactor

            if raLoLimit < 0.0:
                raLoLimit = 0.0
                raLoLimit_wrap = raLoLimit + 360.0
            else:
                raLoLimit_wrap = raLoLimit

            if raUpLimit > 360.0:
                raUpLimit = 360.0
                raUpLimit_wrap = raUpLimit - 360.0
            else:
                raUpLimit_wrap = raUpLimit

                # get all fields
            field_names = SurveyFieldMSB.objects.values_list("survey_fields__field_id")
            fields_queryset = SurveyField.objects.filter(
                field_id__in=field_names
            )  # .filter(active=True)

            # set limits on the retrieved fields
            fields_queryset = fields_queryset.filter(dec_cen__gte=decLoLimit)
            fields_queryset = fields_queryset.filter(dec_cen__lte=decUpLimit)

            fields_queryset = fields_queryset.filter(
                Q(ra_cen__gte=raLoLimit) | Q(ra_cen__gte=raLoLimit_wrap)
            )
            fields_queryset = fields_queryset.filter(
                Q(ra_cen__lte=raUpLimit) | Q(ra_cen__lte=raUpLimit_wrap)
            )

            fields = list(fields_queryset)
            fovCenter = SkyCoord(fov.raCenter, fov.decCenter, unit="deg")
            fovMaxDist = np.sqrt((fov.fovWidth / 2.0) ** 2 + (fov.fovWidth / 2.0) ** 2)

            # loop over the fields and construct the object to pass back to the JS
            # but only if it is within the canvas FOV
            for i in range(len(fields)):
                fieldCenter = SkyCoord(fields[i].ra_cen, fields[i].dec_cen, unit="deg")
                fieldOffset = fieldCenter.separation(fovCenter).value
                if fieldOffset <= fovMaxDist:
                    rowID_list.append(fields[i].id)
                    activeStatus_list.append(fields[i].active)

            ret_list = json.dumps([rowID_list, activeStatus_list])
            return HttpResponse(ret_list)

            # general unknown error
        except Exception as e:
            print(e)
            return HttpResponseServerError()


@csrf_protect
@login_required
def init_draw_transients(request):
    if request.method == "POST":
        try:
            rowID_list = []
            activeStatus_list = []
            # retrieve the recent FOV for this user
            fov = CanvasFOV.objects.latest("created")

            decLoLimit = fov.decCenter - fov.fovWidth / 2.0
            decUpLimit = fov.decCenter + fov.fovWidth / 2.0

            if decUpLimit > 90:
                raLoLimit = 0.0
                raUpLimit = 360.0
                decFactor = 1.0
            else:
                decFactor = np.cos(decUpLimit * np.pi / 180.0)
                raLoLimit = fov.raCenter - fov.fovWidth / 2.0 / decFactor
                raUpLimit = fov.raCenter + fov.fovWidth / 2.0 / decFactor

            if raLoLimit < 0.0:
                raLoLimit = 0.0
                raLoLimit_wrap = raLoLimit + 360.0
            else:
                raLoLimit_wrap = raLoLimit

            if raUpLimit > 360.0:
                raUpLimit = 360.0
                raUpLimit_wrap = raUpLimit - 360.0
            else:
                raUpLimit_wrap = raUpLimit

                # get all fields
            if (
                "query_name" in request.POST.keys()
                and request.POST["query_name"] != "default"
            ):
                query_name = request.POST["query_name"]
                query = Query.objects.filter(title=unquote(query_name))
                if len(query):
                    query = query[0]
                    if "yse_app_transient" not in query.sql.lower():
                        return Http404("Invalid Query")
                    if "name" not in query.sql.lower():
                        return Http404("Invalid Query")
                    if not query.sql.lower().startswith("select"):
                        return Http404("Invalid Query")
                    cursor = connections["explorer"].cursor()
                    cursor.execute(query.sql.replace("%", "%%"), ())
                    transients = Transient.objects.filter(
                        name__in=(x[0] for x in cursor)
                    ).order_by("-disc_date")
                    cursor.close()
                else:
                    query = UserQuery.objects.filter(python_query=unquote(query_name))
                    if not len(query):
                        return Http404("Invalid Query")
                    query = query[0]
                    transients = getattr(yse_python_queries, query.python_query)()
            else:
                transients = Transient.objects.filter(~Q(status__name="Ignore"))

                # set limits on the retrieved fields
            transients = transients.filter(dec__gte=decLoLimit)
            transients = transients.filter(dec__lte=decUpLimit)

            transients = transients.filter(
                Q(ra__gte=raLoLimit) | Q(ra__gte=raLoLimit_wrap)
            )
            transients = transients.filter(
                Q(ra__lte=raUpLimit) | Q(ra__lte=raUpLimit_wrap)
            )

            fields = list(transients)
            fovCenter = SkyCoord(fov.raCenter, fov.decCenter, unit="deg")
            fovMaxDist = np.sqrt((fov.fovWidth / 2.0) ** 2 + (fov.fovWidth / 2.0) ** 2)

            # loop over the fields and construct the object to pass back to the JS
            # but only if it is within the canvas FOV
            for i in range(len(fields[0:50])):
                fieldCenter = SkyCoord(fields[i].ra, fields[i].dec, unit="deg")
                fieldOffset = fieldCenter.separation(fovCenter).value
                if fieldOffset <= fovMaxDist:
                    rowID_list.append(fields[i].id)
                    activeStatus_list.append(True)

            ret_list = json.dumps([rowID_list, activeStatus_list])
            return HttpResponse(ret_list)

            # general unknown error
        except Exception as e:
            print(e)
            return HttpResponseServerError()


@csrf_protect
@login_required
def init_draw_fields_detail(request):
    if request.method == "POST":
        try:
            rowID_list = []
            activeStatus_list = []

            fieldSetID = request.POST["fieldSetID"]

            # retrieve the recent FOV for this user
            fov = CanvasFOV.objects.filter.latest("created")

            decLoLimit = fov.decCenter - fov.fovWidth / 2.0
            decUpLimit = fov.decCenter + fov.fovWidth / 2.0

            if decUpLimit > 90:
                raLoLimit = 0.0
                raUpLimit = 360.0
                decFactor = 1.0
            else:
                decFactor = np.cos(decUpLimit * np.pi / 180.0)
                raLoLimit = fov.raCenter - fov.fovWidth / 2.0 / decFactor
                raUpLimit = fov.raCenter + fov.fovWidth / 2.0 / decFactor

            if raLoLimit < 0.0:
                raLoLimit = 0.0
                raLoLimit_wrap = raLoLimit + 360.0
            else:
                raLoLimit_wrap = raLoLimit

            if raUpLimit > 360.0:
                raUpLimit = 360.0
                raUpLimit_wrap = raUpLimit - 360.0
            else:
                raUpLimit_wrap = raUpLimit

                # get all fields for this fieldset
            fs = models.FieldSet.objects.get(id__exact=fieldSetID)
            fields_queryset = fs.targetfield_set.all()

            # set limits on the retrieved fields
            fields_queryset = fields_queryset.filter(fieldDec_deg__gte=decLoLimit)
            fields_queryset = fields_queryset.filter(fieldDec_deg__lte=decUpLimit)

            fields_queryset = fields_queryset.filter(
                Q(fieldRA_deg__gte=raLoLimit) | Q(fieldRA_deg__gte=raLoLimit_wrap)
            )
            fields_queryset = fields_queryset.filter(
                Q(fieldRA_deg__lte=raUpLimit) | Q(fieldRA_deg__lte=raUpLimit_wrap)
            )

            # realize it
            fields = list(fields_queryset)

            fovCenter = SkyCoord(fov.raCenter, fov.decCenter, unit="deg")
            fovMaxDist = np.sqrt((fov.fovWidth / 2.0) ** 2 + (fov.fovWidth / 2.0) ** 2)

            # loop over the fields and construct the object to pass back to the JS
            # but only if it is within the canvas FOV
            for i in range(len(fields)):
                fieldCenter = SkyCoord(
                    fields[i].fieldRA_deg, fields[i].fieldDec_deg, unit="deg"
                )
                fieldOffset = fieldCenter.separation(fovCenter).value
                if fieldOffset <= fovMaxDist:
                    rowID_list.append(fields[i].id)
                    activeStatus_list.append(fields[i].obsStatus)

            ret_list = json.dumps([rowID_list, activeStatus_list])
            return HttpResponse(ret_list)

            # general unknown error
        except Exception as e:
            print(e)
            return HttpResponseServerError()
