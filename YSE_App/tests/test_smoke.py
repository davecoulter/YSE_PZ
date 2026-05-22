from django.contrib.auth.models import User
from django.test import Client, TestCase

from YSE_App.models import Host, ObservationGroup, Transient, TransientStatus


class LoginSmokeTests(TestCase):
    def test_login_page_returns_200(self):
        response = Client().get("/login/")
        self.assertEqual(response.status_code, 200)


class TransientModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, _ = User.objects.get_or_create(
            username="yse_test_user",
            defaults={"email": "yse_test@example.com"},
        )
        audit_defaults = {"created_by": cls.user, "modified_by": cls.user}
        cls.status, _ = TransientStatus.objects.get_or_create(
            name="New",
            defaults=audit_defaults,
        )
        cls.obs_group, _ = ObservationGroup.objects.get_or_create(
            name="test-group",
            defaults=audit_defaults,
        )

    def test_separation_without_host_returns_none(self):
        transient = Transient(ra=10.0, dec=20.0, host_id=None)
        self.assertIsNone(transient.Separation())

    def test_separation_with_host_returns_formatted_arcsec(self):
        host = Host.objects.create(
            ra=10.0,
            dec=20.0,
            name="test-host",
            created_by=self.user,
            modified_by=self.user,
        )
        transient = Transient.objects.create(
            name="test-transient",
            ra=10.0,
            dec=20.0,
            host=host,
            status=self.status,
            obs_group=self.obs_group,
            created_by=self.user,
            modified_by=self.user,
        )
        self.assertEqual(transient.Separation(), "0.00")
