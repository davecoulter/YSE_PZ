"""Regression tests for post-merge dashboard / host photometry fixes."""

from django.test import TestCase
from django.utils import timezone

from YSE_App.data import SpectraService
from YSE_App.models import Host, HostPhotData, HostPhotometry, Transient
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
