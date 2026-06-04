"""Tests for TNS -> YSE telescope/instrument/band mapping."""

from django.test import SimpleTestCase

from YSE_App.common.tns_photometry_map import (
    parse_tns_composite_label,
    resolve_tns_photometry,
)


class TnsPhotometryMapTests(SimpleTestCase):
    def test_resolve_ztf_cam(self):
        r = resolve_tns_photometry("ZTF-Cam", "r")
        self.assertEqual(r.telescope, "P48")
        self.assertEqual(r.instrument, "ZTF-Cam")
        self.assertEqual(r.band, "r")

    def test_resolve_atlas_05_wide(self):
        r = resolve_tns_photometry("ATLAS-05", "wide")
        self.assertEqual(r.telescope, "ATLAS-TDO")
        self.assertEqual(r.instrument, "ATLAS-05")
        self.assertEqual(r.band, "w")

    def test_resolve_atlas_orange_cyan(self):
        self.assertEqual(resolve_tns_photometry("ATLAS-01", "orange-ATLAS").band, "o")
        self.assertEqual(resolve_tns_photometry("ATLAS-01", "cyan-ATLAS").band, "c")

    def test_resolve_wfst(self):
        r = resolve_tns_photometry("WFST-WFC", "r")
        self.assertEqual(r.telescope, "WFST")
        self.assertEqual(r.instrument, "WFC")
        self.assertEqual(r.band, "r")

    def test_resolve_blackgem(self):
        r = resolve_tns_photometry("BlackGEM-Cam3", "BG-q-BlackGem")
        self.assertEqual(r.telescope, "BG3")
        self.assertEqual(r.instrument, "BG-Cam3")
        self.assertEqual(r.band, "q")

    def test_parse_composite_p48(self):
        r = parse_tns_composite_label("P48_ZTF-Cam_r")
        self.assertIsNotNone(r)
        self.assertEqual(r.telescope, "P48")
        self.assertEqual(r.instrument, "ZTF-Cam")
        self.assertEqual(r.band, "r")

    def test_parse_composite_atlas(self):
        r = parse_tns_composite_label("ATLAS-TDO_ATLAS-05_wide")
        self.assertIsNotNone(r)
        self.assertEqual(r.instrument, "ATLAS-05")
        self.assertEqual(r.band, "w")
