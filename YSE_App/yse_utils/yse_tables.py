import django_tables2 as tables
import numpy as np
from astropy import units as u
from astropy import wcs
from astropy.coordinates import SkyCoord
from django.db.models import Avg
from django.db.models import F
from django.db.models import Q

from YSE_App.models import *

# Table models
class TargetFieldTable(tables.Table):

    # def __init__(self,*args,**kwargs):
    # 	#self.sessionAuthor = kwargs.pop('sessionAuthor')
    # 	super().__init__(*args,**kwargs)

    paginator_class = tables.LazyPaginator

    button_template_name_file = "YSE_App/yse_sky/button_toggler.html"
    obsButton = tables.columns.TemplateColumn(
        template_name=button_template_name_file,
        orderable=True,
        verbose_name="Currently Observing",
    )

    fieldLink = tables.columns.TemplateColumn(
        "<a href=\" {% url 'msb_detail' record.id %} \"> {{ record.name }} </a>",
        orderable=True,
        verbose_name="Field",
    )
    fieldSet = tables.Column(
        accessor="fieldSet",
        # linkify=('fieldset_detail', {'pk': tables.A('fieldSet.id')}),
        verbose_name="Field Set",
    )
    name_str = tables.Column(accessor="name", verbose_name="Field")
    distance = tables.Column()

    class Meta:
        model = SurveyFieldMSB
        template_name = "django_tables2/bootstrap4.html"

        fields = ["name_str"]

        # def get_top_pinned_data(self):

        # 	visFields = []
        # 	distList = []
        # 	prioList = []

        # retrieve the recent FOV for this user
        # 	fov = CanvasFOV.objects.filter(author=self.sessionAuthor).latest('created')
        # 	decLoLimit = fov.decCenter - fov.fovWidth/2.
        # 	decUpLimit = fov.decCenter + fov.fovWidth/2.
        # 	raLoLimit = fov.raCenter - fov.fovWidth/2.
        # 	raUpLimit = fov.raCenter + fov.fovWidth/2.
        # 	if raLoLimit < 0.:
        # 		raLoLimit = 0.
        # 		raLoLimit_wrap = fov.raCenter - fov.fovWidth/2. + 360.
        # 	else:
        # 		raLoLimit_wrap = raLoLimit

        # 	if raUpLimit > 360.:
        # 		raUpLimit = 360.
        # 		raUpLimit_wrap = fov.raCenter + fov.fovWidth/2. - 360.
        # 	else:
        # 		raUpLimit_wrap = raUpLimit

        # get relevant fields
        # 	fields_queryset = TargetField.objects.filter(targetFieldActive__exact=True)

        # set limits on the retrieved fields
        # 	fields_queryset = fields_queryset.filter(fieldDec_deg__gte=decLoLimit)
        # 	fields_queryset = fields_queryset.filter(fieldDec_deg__lte=decUpLimit)

        # 	fields_queryset = fields_queryset.filter(Q(fieldRA_deg__gte=raLoLimit) |
        # 											 Q(fieldRA_deg__gte=raLoLimit_wrap))
        # 	fields_queryset = fields_queryset.filter(Q(fieldRA_deg__lte=raUpLimit) |
        # 											 Q(fieldRA_deg__lte=raUpLimit_wrap))

        # 	fields = list(fields_queryset)
        # 	fovCenter = SkyCoord(fov.raCenter,fov.decCenter,unit='deg')
        # 	fovMaxDist = np.sqrt((fov.fovWidth/2.)**2 + (fov.fovWidth/2.)**2)

        # loop over the fields store ones within the canvas FOV
        # 	for i in range(len(fields)):
        # 		fieldCenter = SkyCoord(fields[i].fieldRA_deg,fields[i].fieldDec_deg,unit='deg')
        # 		fieldOffset = fieldCenter.separation(fovCenter).value
        # 		if fieldOffset <= fovMaxDist:
        # 			visFields.append(fields[i])
        # 			distList.append(fieldOffset)
        # 			prioList.append(fields[i].fieldPriority)

        # 	visFieldsSort = np.array(visFields)[np.argsort(distList)]

        # 	pinned_row_list = []
        # 	for i in range(len(visFieldsSort)):
        # 		rowDict = {}
        # 		rowDict['id'] = visFieldsSort[i].id
        # 		rowDict['fieldName'] = visFieldsSort[i].fieldName
        # 		rowDict['telinstName'] = visFieldsSort[i].telinstName
        # 		rowDict['fieldRA'] = visFieldsSort[i].fieldRA
        # 		rowDict['fieldDec'] = visFieldsSort[i].fieldDec
        # 		rowDict['fieldPriority'] = visFieldsSort[i].fieldPriority
        # 		rowDict['obsStatus'] = visFieldsSort[i].obsStatus
        # 		pinned_row_list.append(rowDict)

        # this is duplicated table data; disabling it for now
        # 	return None

    def order_distance(self, QuerySet, is_descending):

        # retrieve the recent FOV for this user
        fov = CanvasFOV.objects.all()
        if len(fov):
            fov = fov.latest("created")
            d2R = np.pi / 180.0
            raC = fov.raCenter
            decC = fov.decCenter
            cosDec = np.cos(decC * d2R)
            QuerySet = QuerySet.annotate(
                offset=((Avg("survey_fields__ra_cen") - raC) * cosDec) ** 2
                + (Avg("survey_fields__dec_cen") - decC) ** 2
            ).order_by(("-" if is_descending else "") + "offset")

            return (QuerySet, True)
        else:
            return (fov, True)

    def order_obsButton(self, QuerySet, is_descending):
        QuerySet = QuerySet.annotate(amount=F("obsStatus")).order_by(
            ("-" if is_descending else "") + "amount"
        )
        return (QuerySet, True)

    def order_fieldLink(self, QuerySet, is_descending):
        QuerySet = QuerySet.order_by(("-" if is_descending else "") + "fieldName")
        return (QuerySet, True)
