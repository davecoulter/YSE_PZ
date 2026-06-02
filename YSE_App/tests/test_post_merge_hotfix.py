"""Regression tests for post-merge dashboard / host photometry fixes."""

from django.test import Client, TestCase
from django.utils import timezone

from YSE_App.data import SpectraService
from YSE_App.models import (
    Host,
    HostPhotData,
    HostPhotometry,
    Transient,
    TransientSpecData,
    TransientSpectrum,
)
from YSE_App.table_utils import annotate_dashboard_transient_fields
from YSE_App.tests.fixtures_minimal import (
    attach_synthetic_photometry,
    audit_fields,
    create_instrument_stack,
    create_test_user,
    create_minimal_transient,
    create_transient_with_synthetic_data,
)
from YSE_App import view_utils


class AnnotateDashboardFieldsTests(TestCase):
    def test_recent_mag_and_date_populated_when_photometry_exists(self):
        user = create_test_user(username="annotate_dashboard_user")
        transient = create_minimal_transient(user, name="annotate-mag-test")
        attach_synthetic_photometry(user, transient, n_points=3)

        row = annotate_dashboard_transient_fields(
            Transient.objects.filter(pk=transient.pk)
        ).first()

        self.assertIsNotNone(row.recent_mag)
        self.assertIsNotNone(row.recent_magdate)


class HostPhotDataHelperTests(TestCase):
    def test_get_recent_phot_for_host_returns_model_or_none(self):
        user = create_test_user(username="host_phot_user")
        audit = audit_fields(user)
        obs_group, instrument, band = create_instrument_stack(
            user, obs_group_name="host-phot-stack"
        )
        host = Host.objects.create(
            name="host-phot-test",
            ra=10.0,
            dec=20.0,
            **audit,
        )
        photometry = HostPhotometry.objects.create(
            host=host,
            instrument=instrument,
            obs_group=obs_group,
            **audit,
        )
        HostPhotData.objects.create(
            photometry=photometry,
            band=band,
            mag=18.5,
            obs_date=timezone.now(),
            **audit,
        )

        result = view_utils.get_recent_phot_for_host(user, host_id=host.id)
        self.assertIsInstance(result, HostPhotData)
        self.assertEqual(result.mag, 18.5)

        empty = view_utils.get_recent_phot_for_host(user, host_id=999999)
        self.assertIsNone(empty)


class SpectraAuthorizationTests(TestCase):
    """2026kie-style empty UI is usually missing DB rows or group-restricted spectra."""

    def test_groupless_synthetic_spectrum_is_authorized(self):
        user = create_test_user(username="spectra_auth_user")
        transient = create_transient_with_synthetic_data(
            user, name="spec-auth-test", with_spectrum=True
        )
        spectra = SpectraService.GetAuthorizedTransientSpectrum_ByUser_ByTransient(
            user, transient.id, includeBadData=True
        )
        self.assertEqual(spectra.count(), 1)


class SpectrumPlotRegressionTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="spectrumplot_regression_user")
        self.client = Client()
        self.client.force_login(self.user)

    def _add_spec_points(self, spectrum, n_points=20):
        for i in range(n_points):
            TransientSpecData.objects.create(
                spectrum=spectrum,
                wavelength=4000 + 10 * i,
                flux=1.0 + 0.1 * i,
                created_by=self.user,
                modified_by=self.user,
            )

    def test_spectrumplot_returns_200_with_valid_points(self):
        transient = create_transient_with_synthetic_data(
            self.user, name="specplot-valid", with_spectrum=True
        )
        spectrum = TransientSpectrum.objects.filter(transient=transient).first()
        self._add_spec_points(spectrum)

        response = self.client.get(f"/spectrumplot/{transient.id}/")
        self.assertEqual(response.status_code, 200)

    def test_spectrumplot_serves_cached_html_on_second_request(self):
        transient = create_transient_with_synthetic_data(
            self.user, name="specplot-cache", with_spectrum=True
        )
        spectrum = TransientSpectrum.objects.filter(transient=transient).first()
        self._add_spec_points(spectrum)

        url = f"/spectrumplot/{transient.id}/"
        first = self.client.get(url)
        second = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.content, second.content)

    def test_spectrumplot_skips_empty_spectrum_and_still_returns_200(self):
        transient = create_transient_with_synthetic_data(
            self.user, name="specplot-empty-guard", with_spectrum=True
        )
        empty_spectrum = TransientSpectrum.objects.filter(transient=transient).first()
        self.assertIsNotNone(empty_spectrum)

        nonempty_spectrum = TransientSpectrum.objects.create(
            transient=transient,
            instrument=empty_spectrum.instrument,
            obs_group=empty_spectrum.obs_group,
            ra=transient.ra,
            dec=transient.dec,
            obs_date=timezone.now(),
            redshift=0.05,
            created_by=self.user,
            modified_by=self.user,
        )
        self._add_spec_points(nonempty_spectrum)

        response = self.client.get(f"/spectrumplot/{transient.id}/")
        self.assertEqual(response.status_code, 200)
