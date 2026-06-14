"""
CI regression: primary page load times must not exceed perf_baselines.json ceilings.
"""

import json
import unittest
from pathlib import Path

from django.test import TestCase, override_settings

from YSE_App.perf.benchmark import run_primary_pages

BASELINES_PATH = Path(__file__).with_name("perf_baselines.json")


def _load_baselines() -> dict:
    with BASELINES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PageLoadRegressionTests(TestCase):
    """Compare live benchmark to committed baselines (+ tolerance)."""

    def test_primary_pages_within_regression_ceiling(self):
        baselines = _load_baselines()
        tolerance = baselines.get("tolerance_fraction", 0.15)
        measured = {p.page_key: p for p in run_primary_pages()}
        failures = []

        for page_key, spec in baselines.get("pages", {}).items():
            page = measured.get(page_key)
            if page is None:
                failures.append(f"missing measurement for {page_key}")
                continue
            max_ms = spec.get("max_ms")
            if max_ms is None:
                baseline_ms = spec["baseline_ms"]
                max_ms = baseline_ms * (1.0 + tolerance)
            if page.ttfb_ms > max_ms:
                failures.append(
                    f"{page_key}: {page.ttfb_ms:.1f} ms > ceiling {max_ms:.1f} ms"
                )

        if failures:
            self.fail("Page load regression:\n" + "\n".join(failures))
