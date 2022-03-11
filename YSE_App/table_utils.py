from django.shortcuts import render
from .models import *
from . import view_utils
import django_tables2 as tables
from django_tables2 import RequestConfig
from django.db.models import F, Q
from django.db.models.functions import Length, Substr
from django.db.models import Count, Value, Max, Min
from django.db.models.functions import Greatest, Coalesce
from django_tables2 import A
from django.db import models
from .data import PhotometryService
import time
import django_filters
import itertools
from astropy.coordinates import get_moon, SkyCoord
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
from django.db.models.expressions import RawSQL

rcParams["figure.figsize"] = (7, 7)


class TransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class FieldTransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    ztf_field = tables.Column(
        accessor="nearest_ztf_field", verbose_name="ZTF Field", orderable=False
    )
    ztf_sep = tables.Column(
        accessor="nearest_ztf_field_sep", verbose_name="ZTF Sep.", orderable=False
    )
    get_yse_pointings = tables.TemplateColumn(
        "<a href=\"{% url 'yse_pointings' record.nearest_ztf_field record.name %}\" target='_blank'>Get Pointings</a>",
        orderable=False,
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class AdjustFieldTransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    yse_field = tables.Column(
        accessor="nearest_yse_field", verbose_name="YSE Field", orderable=False
    )
    yse_sep = tables.Column(
        accessor="nearest_yse_field_sep", verbose_name="YSE Sep.", orderable=False
    )
    get_yse_pointings = tables.TemplateColumn(
        "<a href=\"{% url 'adjust_yse_pointings' record.nearest_yse_field record.name %}\" target='_blank'>Get Pointings</a>",
        orderable=False,
        verbose_name="Get YSE Pointings",
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class YSETransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    requested_followup_resources = tables.Column(
        accessor="pk", verbose_name="Req. Followup"
    )
    successful_followup_resources = tables.Column(
        accessor="pk", verbose_name="Followed By"
    )
    followup_comments = tables.Column(accessor="pk", verbose_name="Followup Comments")
    context_class = tables.Column(
        accessor="context_class", verbose_name="QUB Class.", orderable=True
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name_yse" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def render_requested_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def render_successful_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def render_followup_comments(self, value):
        qs = Log.objects.filter(transient_followup__transient__id=value).values_list(
            "comment"
        )

        comment_list = []
        for q in qs:
            if q is not None:
                comment_list += [q]

        return "; ".join(np.unique(comment_list))

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class YSEFullTransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    context_class = tables.Column(
        accessor="context_class", verbose_name="QUB Class.", orderable=True
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name_yse" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def render_requested_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def render_successful_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "context_class",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class YSERisingTransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    context_class = tables.Column(
        accessor="context_class", verbose_name="QUB Class.", orderable=True
    )
    dm_g = tables.TemplateColumn(
        "{{ record.dm_g|floatformat:3 }}",
        verbose_name="Delta g",
        orderable=True,
        order_by="dm_g",
    )
    dm_r = tables.TemplateColumn(
        "{{ record.dm_r|floatformat:3 }}",
        verbose_name="Delta r",
        orderable=True,
        order_by="dm_r",
    )
    dm_i = tables.TemplateColumn(
        "{{ record.dm_i|floatformat:3 }}",
        verbose_name="Delta i",
        orderable=True,
        order_by="dm_i",
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name_yse" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def render_requested_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(Q(status__name="Requested") | Q(status__name="InProcess"))
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def render_successful_followup_resources(self, value):

        qs_too = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("too_resource__telescope__name", flat=True)
        )
        qs_class = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("classical_resource__telescope__name", flat=True)
        )
        qs_queued = (
            TransientFollowup.objects.filter(transient__id=value)
            .filter(status__name="Successful")
            .values_list("queued_resource__telescope__name", flat=True)
        )

        resource_list = []
        for qs in [qs_too, qs_class, qs_queued]:
            for q in qs:
                if q is not None:
                    resource_list += [q]

        return ", ".join(np.unique(resource_list))

    def render_dt(self, value):

        return "%.2f" % value / 24 / 60 / 60

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "context_class",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class NewTransientTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="CoordString.0", verbose_name="RA", orderable=True, order_by="ra"
    )
    dec_string = tables.Column(
        accessor="CoordString.1", verbose_name="DEC", orderable=True, order_by="dec"
    )
    disc_date_string = tables.Column(
        accessor="disc_date_string",
        verbose_name="Disc. Date",
        orderable=True,
        order_by="disc_date",
    )
    recent_mag = tables.Column(
        accessor="recent_mag", verbose_name="Last Mag", orderable=True
    )
    recent_magdate = tables.Column(
        accessor="recent_magdate", verbose_name="Last Obs. Date", orderable=True
    )
    best_redshift = tables.Column(
        accessor="z_or_hostz",
        verbose_name="Redshift",
        orderable=True,
        order_by="host__redshift",
    )
    ps_score = tables.Column(
        accessor="point_source_probability", verbose_name="PS Score", orderable=True
    )

    # mw_ebv = tables.Column(accessor='mw_ebv',
    # 						   verbose_name='MW E(B-V)',orderable=True)
    mw_ebv = tables.TemplateColumn(
        """{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
        verbose_name="MW E(B-V)",
        orderable=True,
        order_by="mw_ebv",
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["best_spec_class"].verbose_name = "Spec. Class"

    def order_best_redshift(self, queryset, is_descending):

        queryset = queryset.annotate(
            best_redshift=Coalesce("redshift", "host__redshift")
        ).order_by(("-" if is_descending else "") + "best_redshift")
        return (queryset, True)

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    def order_recent_magdate(self, queryset, is_descending):

        all_phot = TransientPhotometry.objects.values("transient").filter(
            transient__in=queryset
        )
        phot_ids = all_phot.values("id")

        phot_data_query = Q(transientphotometry__id__in=phot_ids)
        queryset = queryset.annotate(
            recent_magdate=Max(
                "transientphotometry__transientphotdata__obs_date",
                filter=phot_data_query,
            )  # ,filter=phot_data_query
        ).order_by(("-" if is_descending else "") + "recent_magdate")
        return (queryset, True)

    class Meta:
        model = Transient
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "disc_date_string",
            "recent_mag",
            "recent_magdate",
            "mw_ebv",
            "obs_group",
            "best_spec_class",
            "best_redshift",
            "ps_score",
            "status_string",
        )

        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "class": "table table-bordered table-hover",
            "id": "k2_transient_tbl",
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "order": [[3, "desc"]],
        }


class FollowupTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.transient.slug %}\">{{ record.transient.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="transient.CoordString.0",
        verbose_name="RA",
        orderable=True,
        order_by="transient.ra",
    )
    dec_string = tables.Column(
        accessor="transient.CoordString.1",
        verbose_name="DEC",
        orderable=True,
        order_by="transient.dec",
    )
    recent_mag = tables.Column(
        accessor="transient.recent_mag", verbose_name="Recent Mag", orderable=True
    )

    observation_window = tables.Column(
        accessor="observation_window",
        verbose_name="Observation Window",
        orderable=True,
        order_by="valid_start",
    )

    action = tables.TemplateColumn(
        '<a target="_blank" href="{% url \'admin:YSE_App_transientfollowup_change\' record.id %}">Edit</a>',
        verbose_name="Action",
        orderable=False,
    )

    status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:5px;" type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_followup_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Followup Status",
        orderable=True,
        order_by="status",
    )

    # disc_mag = tables.Column(accessor='disc_mag',
    # 						 verbose_name='Disc. Mag',orderable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_columns["transient.status"].verbose_name = "Transient Status"
        # self.base_columns['status'].verbose_name = 'Followup Status'

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    class Meta:
        model = TransientFollowup
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "recent_mag",
            "transient.status",
            "observation_window",
            "action",
        )
        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "class": "table table-bordered table-hover",
            "order": [[2, "desc"]],
        }


class ObsNightFollowupTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.transient.slug %}\">{{ record.transient.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="transient.CoordString.0",
        verbose_name="RA",
        orderable=True,
        order_by="transient.ra",
    )
    dec_string = tables.Column(
        accessor="transient.CoordString.1",
        verbose_name="DEC",
        orderable=True,
        order_by="transient.dec",
    )
    recent_mag = tables.Column(
        accessor="transient.recent_mag", verbose_name="Recent Mag", orderable=True
    )

    # observation_window = tables.Column(accessor='observation_window',
    # 						  verbose_name='Observation Window',orderable=True,order_by='valid_start')

    rise_time = tables.Column(
        verbose_name="Rise Time (UT)", orderable=False, accessor="transient.CoordString"
    )
    set_time = tables.Column(
        verbose_name="Set Time (UT)", orderable=False, accessor="transient.CoordString"
    )
    moon_angle = tables.Column(
        verbose_name="Moon Angle", orderable=False, accessor="transient.CoordString"
    )
    created_by = tables.Column(
        verbose_name="Added By", orderable=True, accessor="created_by"
    )
    comment = tables.Column(verbose_name="Comments", orderable=True, accessor="id")

    transient_status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.transient.id }}_status_name" class="dropbtn">{{ record.transient.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.transient.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Transient Status",
        orderable=True,
        order_by="status",
    )

    followup_status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_followup_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="followupStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Followup Status",
        orderable=True,
        order_by="status",
    )

    # disc_mag = tables.Column(accessor='disc_mag',
    # 						 verbose_name='Disc. Mag',orderable=True)

    def __init__(self, *args, classical_obs_date=None, **kwargs):
        super().__init__(*args, **kwargs)

        # self.base_columns['transient.status'].verbose_name = 'Transient Status'
        # self.base_columns['status'].verbose_name = 'Followup Status'

        location = EarthLocation.from_geodetic(
            classical_obs_date[0].resource.telescope.longitude * u.deg,
            classical_obs_date[0].resource.telescope.latitude * u.deg,
            classical_obs_date[0].resource.telescope.elevation * u.m,
        )
        self.tel = Observer(location=location, timezone="UTC")
        self.tme = Time(str(classical_obs_date[0].obs_date).split()[0])

    def render_rise_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_rise_time = self.tel.target_rise_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_rise_time and target_rise_time.value == target_rise_time.value:
            risetime = target_rise_time.isot.split("T")[-1].split(".")[0]
        else:
            risetime = None

        return risetime

    def render_set_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_set_time = self.tel.target_set_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_set_time and target_set_time.value == target_set_time.value:
            settime = target_set_time.isot.split("T")[-1].split(".")[0]
        else:
            settime = None

        return settime

    def render_moon_angle(self, value):
        mooncoord = get_moon(self.tme)
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        return "%.1f" % sc.separation(mooncoord).deg

    def render_airmass(self, value):
        from astroplan.plots import plot_airmass

    def render_comment(self, value):

        comments = Log.objects.filter(transient_followup__id=value)
        comment_list = []
        for c in comments:
            comment_list += [c.comment]
        if len(comment_list):
            return "; ".join(comment_list)
        else:
            return ""

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    class Meta:
        model = TransientFollowup
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "recent_mag",
            "rise_time",
            "set_time",
            "moon_angle",
            "transient_status_string",
            "created_by",
        )
        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "class": "table table-bordered table-hover",
            "order": [[2, "desc"]],
        }


class ToOFollowupTable(tables.Table):

    name_string = tables.TemplateColumn(
        "<a href=\"{% url 'transient_detail' record.transient.slug %}\">{{ record.transient.name }}</a>",
        verbose_name="Name",
        orderable=True,
        order_by="name",
    )
    ra_string = tables.Column(
        accessor="transient.CoordString.0",
        verbose_name="RA",
        orderable=True,
        order_by="transient.ra",
    )
    dec_string = tables.Column(
        accessor="transient.CoordString.1",
        verbose_name="DEC",
        orderable=True,
        order_by="transient.dec",
    )
    recent_mag = tables.Column(
        accessor="transient.recent_mag", verbose_name="Recent Mag", orderable=True
    )

    # observation_window = tables.Column(accessor='observation_window',
    # 						  verbose_name='Observation Window',orderable=True,order_by='valid_start')

    rise_time = tables.Column(
        verbose_name="Rise Time (UT)", orderable=False, accessor="transient.CoordString"
    )
    set_time = tables.Column(
        verbose_name="Set Time (UT)", orderable=False, accessor="transient.CoordString"
    )
    moon_angle = tables.Column(
        verbose_name="Moon Angle", orderable=False, accessor="transient.CoordString"
    )
    created_by = tables.Column(
        verbose_name="Added By", orderable=True, accessor="created_by"
    )
    comment = tables.Column(verbose_name="Comments", orderable=True, accessor="id")

    transient_status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.transient.id }}_status_name" class="dropbtn">{{ record.transient.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.transient.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Transient Status",
        orderable=True,
        order_by="status",
    )

    followup_status_string = tables.TemplateColumn(
        """<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_followup_statuses %}
													<li><a data-status_id="{{ status.id }}" data-status_name="{{ status.name }}" transient_id="{{ record.id }}" class="followupStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
        verbose_name="Followup Status",
        orderable=True,
        order_by="status",
    )

    def __init__(self, *args, too_resource=None, **kwargs):
        super().__init__(*args, **kwargs)

        location = EarthLocation.from_geodetic(
            too_resource[0].telescope.longitude * u.deg,
            too_resource[0].telescope.latitude * u.deg,
            too_resource[0].telescope.elevation * u.m,
        )
        self.tel = Observer(location=location, timezone="UTC")
        self.tme = Time(str(datetime.datetime.now()).split()[0])

    def render_rise_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_rise_time = self.tel.target_rise_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_rise_time and target_rise_time.value == target_rise_time.value:
            risetime = target_rise_time.isot.split("T")[-1].split(".")[0]
        else:
            risetime = None

        return risetime

    def render_set_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_set_time = self.tel.target_set_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_set_time and target_set_time.value == target_set_time.value:
            settime = target_set_time.isot.split("T")[-1].split(".")[0]
        else:
            settime = None

        return settime

    def render_moon_angle(self, value):
        mooncoord = get_moon(self.tme)
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        return "%.1f" % sc.separation(mooncoord).deg

    def render_airmass(self, value):
        from astroplan.plots import plot_airmass

    def render_comment(self, value):

        comments = Log.objects.filter(transient_followup__id=value)
        comment_list = []
        for c in comments:
            comment_list += [c.comment]
        if len(comment_list):
            return "; ".join(comment_list)
        else:
            return ""

    def order_recent_mag(self, queryset, is_descending):

        raw_query = """
SELECT pd.mag
   FROM YSE_App_transient t, YSE_App_transientphotdata pd, YSE_App_transientphotometry p
   WHERE pd.photometry_id = p.id AND
   YSE_App_transient.id = t.id AND
   pd.id = (
		 SELECT pd2.id FROM YSE_App_transientphotdata pd2, YSE_App_transientphotometry p2
		 WHERE pd2.photometry_id = p2.id AND p2.transient_id = t.id AND ISNULL(pd2.data_quality_id) = True
		 ORDER BY pd2.obs_date DESC
		 LIMIT 1
	 )
"""

        queryset = queryset.annotate(recent_mag=RawSQL(raw_query, ())).order_by(
            ("-" if is_descending else "") + "recent_mag"
        )

        return (queryset, True)

    class Meta:
        model = TransientFollowup
        fields = (
            "name_string",
            "ra_string",
            "dec_string",
            "recent_mag",
            "rise_time",
            "set_time",
            "moon_angle",
            "transient_status_string",
            "created_by",
        )
        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "class": "table table-bordered table-hover",
            "order": [[2, "desc"]],
        }


class YSEObsNightTable(tables.Table):

    field_id = tables.Column(
        accessor="survey_field.field_id",
        verbose_name="Field ID",
        order_by="survey_field.field_id",
    )
    ra_string = tables.Column(
        accessor="survey_field.CoordString.0",
        verbose_name="RA",
        orderable=True,
        order_by="survey_field.ra_dec",
    )
    dec_string = tables.Column(
        accessor="survey_field.CoordString.1",
        verbose_name="DEC",
        orderable=True,
        order_by="survey_field.dec_cen",
    )
    band = tables.Column(
        accessor="photometric_band.name", verbose_name="band", orderable=True
    )

    rise_time = tables.Column(
        verbose_name="Rise Time (UT)",
        orderable=False,
        accessor="survey_field.CoordString",
    )
    set_time = tables.Column(
        verbose_name="Set Time (UT)",
        orderable=False,
        accessor="survey_field.CoordString",
    )
    moon_angle = tables.Column(
        verbose_name="Moon Angle", orderable=False, accessor="survey_field.CoordString"
    )
    selection = tables.CheckBoxColumn(
        accessor="pk", attrs={"th__input": {"onclick": "toggle(this)"}}
    )
    status_str = tables.TemplateColumn(
        "<span id='{{record.id}}_status'>{{record.status.name}}</span>",
        verbose_name="status",
    )
    # status_string = tables.TemplateColumn("""<div class="btn-group">
    # <button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
    # 										<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
    # 									</button>
    # 									<ul class="dropdown-menu">
    # 										{% for status in all_followup_statuses %}
    # 												<li><a data-status_id="{{ status.id }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
    # 										{% endfor %}
    # 									</ul>
    # </div>""",
    # 									  verbose_name='Followup Status',orderable=True,order_by='status')

    def __init__(self, *args, obs_date=None, **kwargs):
        super().__init__(*args, **kwargs)
        telescope = Telescope.objects.get(name="Pan-STARRS1")

        # self.base_columns['transient.status'].verbose_name = 'Transient Status'
        # self.base_columns['status'].verbose_name = 'Followup Status'

        location = EarthLocation.from_geodetic(
            telescope.longitude * u.deg,
            telescope.latitude * u.deg,
            telescope.elevation * u.m,
        )
        self.tel = Observer(location=location, timezone="UTC")
        self.tme = Time(str(obs_date).split()[0])

    def render_rise_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_rise_time = self.tel.target_rise_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_rise_time:
            risetime = target_rise_time.isot.split("T")[-1].split(".")[0]
        else:
            risetime = None

        return risetime

    def render_set_time(self, value):
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        target_set_time = self.tel.target_set_time(
            self.tme, sc, horizon=18 * u.deg, which="previous"
        )

        if target_set_time:
            settime = target_set_time.isot.split("T")[-1].split(".")[0]
        else:
            settime = None

        return settime

    def render_moon_angle(self, value):
        mooncoord = get_moon(self.tme)
        sc = SkyCoord("%s %s" % (value[0], value[1]), unit=(u.hourangle, u.deg))
        return "%.1f" % sc.separation(mooncoord).deg

    def render_airmass(self, value):
        from astroplan.plots import plot_airmass

    class Meta:
        model = SurveyObservation
        fields = (
            "field_id",
            "ra_string",
            "dec_string",
            "rise_time",
            "set_time",
            "moon_angle",
        )  # ,'transient.status')
        template_name = "YSE_App/django-tables2/bootstrap.html"
        attrs = {
            "th": {
                "_ordering": {
                    "orderable": "sortable",  # Instead of `orderable`
                    "ascending": "ascend",  # Instead of `asc`
                    "descending": "descend",  # Instead of `desc`
                }
            },
            "columnDefs": [
                {"type": "title-numeric", "targets": 1},
                {"type": "title-numeric", "targets": 2},
            ],
            "class": "table table-bordered table-hover",
            "order": [[2, "desc"]],
        }


def annotate_with_disc_mag(qs):

    all_phot = TransientPhotometry.objects.values(
        "transient"
    )  # .filter(transient__in = queryset)
    phot_ids = all_phot.values("id")

    phot_data_query = Q(transientphotometry__id__in=phot_ids)
    disc_query = Q(transientphotometry__transientphotdata__discovery_point=1)

    qs = qs.annotate(
        disc_mag=Min(
            "transientphotometry__transientphotdata__mag",
            filter=phot_data_query & disc_query,
        )
    )

    qs = qs.annotate(
        obs_group_name=Min("obs_group__name"),
        host_redshift=Min("host__redshift"),
        spec_class=Min("best_spec_class__name"),
        status_name=Min("status__name"),
    )
    return qs


class TransientFilter(django_filters.FilterSet):

    # name_string = django_filters.CharFilter(name='name',lookup_expr='icontains',
    # 										label='Name')

    ex = django_filters.CharFilter(method="filter_ex", label="Search")
    search_fields = [
        "name",
        "ra",
        "dec",
        "disc_date",
        "disc_mag",
        "obs_group_name",
        "spec_class",
        "redshift",
        "host_redshift",
        "status_name",
    ]

    class Meta:
        model = Transient
        fields = ["ex"]

    def filter_ex(self, qs, name, value):
        if value:

            qs = annotate_with_disc_mag(qs)

            q_parts = value.split()

            list1 = self.search_fields
            list2 = q_parts
            perms = [zip(x, list2) for x in itertools.permutations(list1, len(list2))]

            q_totals = Q()
            for perm in perms:
                q_part = Q()
                for p in perm:
                    q_part = q_part & Q(**{p[0] + "__icontains": p[1]})
                q_totals = q_totals | q_part

            qs = qs.filter(q_totals)
        return qs


class RisingTransientFilter(django_filters.FilterSet):

    # name_string = django_filters.CharFilter(name='name',lookup_expr='icontains',
    # 										label='Name')

    # name = django_filters.CharFilter(name='name',lookup_expr='icontains',method='filter_name')
    recent_mag_lt = django_filters.NumberFilter(
        field_name="recent_mag", label="Max Recent Mag", lookup_expr="lt"
    )
    days_since_disc = django_filters.NumberFilter(
        field_name="days_since_disc", label="Max Days Since Disc", lookup_expr="lt"
    )
    ra_min = django_filters.NumberFilter(
        field_name="ra", label="Min. RA (deg)", lookup_expr="gt"
    )
    ra_max = django_filters.NumberFilter(
        field_name="ra", label="Max. RA (deg)", lookup_expr="lt"
    )
    dec_min = django_filters.NumberFilter(
        field_name="dec", label="Min. Dec (deg)", lookup_expr="gt"
    )
    dec_max = django_filters.NumberFilter(
        field_name="dec", label="Max. Dec (deg)", lookup_expr="lt"
    )
    ebv_max = django_filters.NumberFilter(
        field_name="mw_ebv", label="Max. MW E(B-V)", lookup_expr="lt"
    )

    # recent_mag__gt = django_filters.NumberFilter(name='recent_mag', lookup_expr='recent_mag__gt')
    # recent_mag__lt = django_filters.NumberFilter(name='recent_mag', lookup_expr='recent_mag__lt')
    ex = django_filters.CharFilter(method="filter_ex", label="Search")
    search_fields = [
        "name",
        "ra",
        "dec",
        "disc_date",
        "disc_mag",
        "obs_group_name",
        "spec_class",
        "redshift",
        "host_redshift",
        "status_name",
        "recent_mag",
    ]

    class Meta:
        model = Transient
        fields = [
            "ex",
            "recent_mag_lt",
            "days_since_disc",
            "ra_min",
            "ra_max",
            "dec_min",
            "dec_max",
            "ebv_max",
        ]

    def filter_ex(self, qs, name, value):
        if value:

            qs = annotate_with_disc_mag(qs)

            q_parts = value.split()

            list1 = self.search_fields
            list2 = q_parts
            perms = [zip(x, list2) for x in itertools.permutations(list1, len(list2))]

            q_totals = Q()
            for perm in perms:
                q_part = Q()
                for p in perm:
                    q_part = q_part & Q(**{p[0] + "__icontains": p[1]})
                q_totals = q_totals | q_part

            qs = qs.filter(q_totals)
        return qs


class FollowupFilter(django_filters.FilterSet):

    ex = django_filters.CharFilter(method="filter_ex", label="Search")
    search_fields = [
        "transient__name",
        "transient__status__name",
        "status__name",
        "valid_start",
        "valid_stop",
    ]

    class Meta:
        model = TransientFollowup
        fields = ["ex"]

    def filter_ex(self, qs, name, value):
        if value:
            q_parts = value.split()

            list1 = self.search_fields
            list2 = q_parts
            perms = [zip(x, list2) for x in itertools.permutations(list1, len(list2))]

            q_totals = Q()
            for perm in perms:
                q_part = Q()
                for p in perm:
                    q_part = q_part & Q(**{p[0] + "__icontains": p[1]})
                q_totals = q_totals | q_part

            qs = qs.filter(q_totals)
        return qs


class ObsNightFollowupFilter(django_filters.FilterSet):

    ex = django_filters.CharFilter(method="filter_ex", label="Search")
    search_fields = [
        "transient__name",
        "transient__status__name",
        "status__name",
        "valid_start",
        "valid_stop",
    ]

    class Meta:
        model = TransientFollowup
        fields = ["ex"]

    def filter_ex(self, qs, name, value):
        if value:
            q_parts = value.split()

            list1 = self.search_fields
            list2 = q_parts
            perms = [zip(x, list2) for x in itertools.permutations(list1, len(list2))]

            q_totals = Q()
            for perm in perms:
                q_part = Q()
                for p in perm:
                    q_part = q_part & Q(**{p[0] + "__icontains": p[1]})
                q_totals = q_totals | q_part

            qs = qs.filter(q_totals)
        return qs


def dashboard_tables(request):

    k2_transients = Transient.objects.all()

    table = TransientTable(k2_transients)
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    context = {"k2_transients": table}

    return render(request, "YSE_App/dashboard_table.html", context)
