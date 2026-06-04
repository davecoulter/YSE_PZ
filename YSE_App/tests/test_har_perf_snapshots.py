"""Validate checked-in HAR perf JSON snapshots."""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = REPO_ROOT / "docs" / "perf" / "har_snapshots"


class HarPerfSnapshotTests(unittest.TestCase):
    def test_transient_detail_2026fba_baseline_snapshot(self):
        path = SNAPSHOT_DIR / "transient_detail_2026fba_2026-06-04.json"
        self.assertTrue(path.is_file(), f"Missing snapshot: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("milestones_ms", data)
        self.assertGreater(data["entry_count"], 10)
        self.assertIn("2026fba", data["page_url"])
        milestones = data["milestones_ms"]
        self.assertIn("first_yse_xhr_ms", milestones)
        self.assertIn("first_spectrumplot_ms", milestones)
        by_cat = data["by_category"]
        self.assertIn("yse_api", by_cat)
        self.assertIn("aladin", by_cat)

    def test_transient_detail_2026fba_after_perf_snapshot(self):
        path = SNAPSHOT_DIR / "transient_detail_2026fba_2026-06-04_after_perf.json"
        self.assertTrue(path.is_file(), f"Missing snapshot: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        milestones = data["milestones_ms"]
        self.assertIn("first_spectrumplot_ms", milestones)
        self.assertLess(
            milestones["first_spectrumplot_ms"],
            2500,
            "Expected faster spectrum XHR after perf work",
        )
