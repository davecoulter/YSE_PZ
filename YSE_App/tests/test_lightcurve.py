import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from YSE_App.models import (
    Instrument,
    ObservationGroup,
    Observatory,
    PhotometricBand,
    Telescope,
    Transient,
    TransientPhotData,
    TransientPhotometry,
    TransientStatus,
)


class LightcurvePlotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, _ = User.objects.get_or_create(
            username="lc_test_user",
            defaults={"email": "lc_test@example.com", "is_staff": True},
        )
        audit = {"created_by": cls.user, "modified_by": cls.user}
        cls.status, _ = TransientStatus.objects.get_or_create(name="New", defaults=audit)
        cls.obs_group, _ = ObservationGroup.objects.get_or_create(
            name="lc-test-group", defaults=audit
        )
        cls.observatory = Observatory.objects.create(
            name="TestObs",
            utc_offset=0,
            tz_name="UTC",
            **audit,
        )
        cls.telescope = Telescope.objects.create(
            name="TestTel",
            observatory=cls.observatory,
            latitude=0.0,
            longitude=0.0,
            elevation=0.0,
            **audit,
        )
        cls.instrument = Instrument.objects.create(
            name="GPC1", telescope=cls.telescope, **audit
        )
        cls.band = PhotometricBand.objects.create(
            name="r",
            instrument=cls.instrument,
            disp_color="#ff0000",
            disp_symbol="circle",
            **audit,
        )
        cls.transient = Transient.objects.create(
            name="lc-test-sn",
            ra=10.0,
            dec=20.0,
            status=cls.status,
            obs_group=cls.obs_group,
            **audit,
        )
        cls.transient_empty = Transient.objects.create(
            name="lc-test-empty",
            ra=11.0,
            dec=21.0,
            status=cls.status,
            obs_group=cls.obs_group,
            **audit,
        )
        photometry = TransientPhotometry.objects.create(
            transient=cls.transient,
            instrument=cls.instrument,
            obs_group=cls.obs_group,
            **audit,
        )
        TransientPhotData.objects.create(
            photometry=photometry,
            band=cls.band,
            obs_date=timezone.now(),
            mag=18.5,
            mag_err=0.1,
            **audit,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_lightcurveplot_detail_empty_returns_empty_body(self):
        response = self.client.get(
            f"/lightcurveplot_detail/{self.transient_empty.id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_lightcurveplot_detail_with_photometry_returns_html(self):
        response = self.client.get(f"/lightcurveplot_detail/{self.transient.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 100)
        self.assertIn(b"plot", response.content.lower())

    def _assert_query_count_bounded(self, url, max_queries, label):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=label)
        self.assertLess(
            len(context.captured_queries),
            max_queries,
            msg=f"{label}: {len(context.captured_queries)} queries (max {max_queries})",
        )

    def test_lightcurveplot_detail_query_count_bounded(self):
        """Regression: avoid per-point PhotometricBand.objects.get N+1 queries."""
        self._assert_query_count_bounded(
            f"/lightcurveplot_detail/{self.transient.id}/",
            max_queries=25,
            label="lightcurveplot_detail",
        )

    def test_lightcurveplot_flux_query_count_bounded(self):
        self._assert_query_count_bounded(
            f"/lightcurveplot_flux/{self.transient.id}/",
            max_queries=25,
            label="lightcurveplot_flux",
        )

    def test_lightcurveplot_summary_query_count_bounded(self):
        self._assert_query_count_bounded(
            f"/lightcurveplot_summary/{self.transient.id}/",
            max_queries=25,
            label="lightcurveplot_summary",
        )

    def test_lightcurveplot_flux_empty_returns_empty_body(self):
        response = self.client.get(
            f"/lightcurveplot_flux/{self.transient_empty.id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
