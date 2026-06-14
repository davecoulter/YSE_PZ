"""Tests that TNS ingest tags photometry and spectra with the Public collaboration group."""

from __future__ import annotations

import json
from unittest import mock

from django.contrib.auth.models import Group
from django.test import Client, TestCase

from YSE_App.common.collaboration_groups import (
    PUBLIC_COLLABORATION_GROUP_NAME,
    TNS_IMPORT_COLLABORATION_GROUPS,
    collaboration_groups_from_photometry_upload,
)
from YSE_App.data_ingest.TNS_uploads import processTNS
from YSE_App.data_utils import add_transient_phot_util, add_transient_spec_util
from YSE_App.models import Transient, TransientPhotometry, TransientSpectrum
from YSE_App.tests.fixtures_minimal import (
    create_instrument_stack,
    create_minimal_transient,
    create_test_user,
    ensure_transient_statuses,
)


def _sample_tns_photometry_json():
    return {
        "photometry": [
            {
                "instrument": {"name": "ZTF-Cam"},
                "filters": {"name": "r"},
                "flux_unit": {"name": "ABMag"},
                "flux": 18.5,
                "fluxerr": 0.1,
                "obsdate": "2026-06-01 12:00:00",
                "observer": "ZTF",
            },
            {
                "instrument": {"name": "ATLAS-05"},
                "filters": {"name": "orange-ATLAS"},
                "flux_unit": {"name": "ABMag"},
                "flux": 19.0,
                "fluxerr": 0.2,
                "obsdate": "2026-06-02 08:00:00",
                "observer": "ATLAS",
            },
        ],
        "spectra": [],
    }


class TnsImportGroupConstantsTests(TestCase):
    def test_tns_import_groups_use_public(self):
        self.assertEqual(
            list(TNS_IMPORT_COLLABORATION_GROUPS),
            [PUBLIC_COLLABORATION_GROUP_NAME],
        )


class TnsPhotometryUploadShapeTests(TestCase):
    def test_get_tns_photometry_marks_public_on_header_and_points(self):
        proc = processTNS()
        proc.clobber = True
        phot, *_ = proc.getTNSPhotometry(_sample_tns_photometry_json())

        for block in phot.values():
            if not isinstance(block, dict) or "photdata" not in block:
                continue
            self.assertEqual(block.get("groups"), list(TNS_IMPORT_COLLABORATION_GROUPS))
            for point in block["photdata"].values():
                self.assertEqual(point.get("groups"), list(TNS_IMPORT_COLLABORATION_GROUPS))


class TnsImportGroupsPersistTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = create_test_user("tns_grp_admin", is_staff=True)
        ensure_transient_statuses(cls.admin)
        Group.objects.get_or_create(name=PUBLIC_COLLABORATION_GROUP_NAME)
        cls.transient = create_minimal_transient(
            cls.admin,
            name="2026tgrp",
            obs_group_name="tns-test-survey",
        )
        cls.obs_group, cls.instrument, cls.band = create_instrument_stack(
            cls.admin,
            obs_group_name="ZTF",
        )

    def test_add_transient_phot_util_applies_public_from_tns_upload(self):
        photdict = {
            "mjdmatchmin": 0.01,
            "clobber": True,
            0: {
                "instrument": self.instrument.name,
                "obs_group": self.obs_group.name,
                "groups": list(TNS_IMPORT_COLLABORATION_GROUPS),
                "photdata": {
                    "pt1": {
                        "obs_date": "2026-06-01T12:00:00",
                        "band": self.band.name,
                        "groups": list(TNS_IMPORT_COLLABORATION_GROUPS),
                        "mag": 18.5,
                        "mag_err": 0.1,
                        "flux": None,
                        "flux_err": None,
                        "forced": None,
                        "diffim": None,
                        "flux_zero_point": None,
                        "data_quality": 0,
                        "discovery_point": 1,
                    },
                },
            },
        }
        _, phot_entries = add_transient_phot_util(
            photdict, self.transient, self.admin, do_photdata=False
        )
        TransientPhotometry.objects.bulk_create(phot_entries)
        add_transient_phot_util(photdict, self.transient, self.admin, do_photdata=True)

        phot = TransientPhotometry.objects.get(transient=self.transient)
        self.assertEqual(
            set(phot.groups.values_list("name", flat=True)),
            {PUBLIC_COLLABORATION_GROUP_NAME},
        )

    def test_add_transient_via_http_marks_tns_photometry_public(self):
        proc = processTNS()
        proc.clobber = True
        phot, *_ = proc.getTNSPhotometry(_sample_tns_photometry_json())

        payload = {
            self.transient.name: {
                "name": self.transient.name,
                "ra": self.transient.ra,
                "dec": self.transient.dec,
                "status": "New",
                "obs_group": self.transient.obs_group.name,
                "transientphotometry": phot,
            },
            "TNS": True,
        }

        client = Client()
        client.force_login(self.admin)
        with mock.patch(
            "YSE_App.data_utils.auth.authenticate",
            return_value=self.admin,
        ):
            response = client.post(
                "/add_transient/",
                data=json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Basic dGVzdDp0ZXN0",
            )
        self.assertEqual(response.status_code, 200, response.content)

        names = set(
            TransientPhotometry.objects.filter(transient=self.transient)
            .values_list("groups__name", flat=True)
            .distinct()
        )
        names.discard(None)
        self.assertEqual(names, {PUBLIC_COLLABORATION_GROUP_NAME})

    def test_collaboration_groups_from_photometry_upload_reads_per_point_groups(self):
        photometry = {
            "photdata": {
                "a": {"groups": ["Public"]},
                "b": {"groups": ["Public"]},
            },
        }
        self.assertEqual(
            collaboration_groups_from_photometry_upload(photometry),
            ["Public"],
        )

    def test_add_transient_spec_util_applies_public_from_tns_upload(self):
        specdict = {
            "clobber": True,
            "spec1": {
                "instrument": self.instrument.name,
                "obs_group": self.obs_group.name,
                "obs_date": "2026-06-01T12:00:00",
                "ra": self.transient.ra,
                "dec": self.transient.dec,
                "groups": PUBLIC_COLLABORATION_GROUP_NAME,
                "specdata": {
                    5000.0: {"wavelength": 5000.0, "flux": 1.0, "flux_err": 0.1},
                },
            },
        }
        add_transient_spec_util(specdict, self.transient, self.admin)

        spec = TransientSpectrum.objects.get(transient=self.transient)
        self.assertEqual(
            set(spec.groups.values_list("name", flat=True)),
            {PUBLIC_COLLABORATION_GROUP_NAME},
        )
