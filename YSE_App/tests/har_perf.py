"""
Parse browser HAR exports into compact JSON for page-load diagnostics.

Usage:
  python3 -m YSE_App.tests.har_perf /path/to/capture.har -o docs/perf/har_snapshots/foo.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _normalize_page_timing_ms(value: Optional[float]) -> Optional[float]:
    if value is None or value < 0:
        return None
    # Safari Web Inspector sometimes records µs while HAR spec says ms.
    if value > 100_000:
        return round(value / 1000.0, 2)
    return round(value, 2)


def _category(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    path = urlparse(url).path or ""
    if "aladin" in host or "alasky" in host or "unistra.fr" in host:
        return "aladin"
    if host in ("127.0.0.1", "localhost") or path.startswith("/static/"):
        return "static" if "/static/" in url else "yse_api"
    if "skyservice.pha.jhu.edu" in host or "sdss" in host:
        return "external_sky"
    if "bokeh" in host or "cdn.bokeh.org" in host:
        return "bokeh_cdn"
    if host.endswith("stsci.edu") or "legacysurvey.org" in host:
        return "external_cutout"
    if "googleapis.com" in host:
        return "fonts"
    return "other"


def _short_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if len(path) > 80:
        path = path[:77] + "..."
    if parsed.query:
        return f"{path}?…"
    return path


def har_to_perf_json(har_path: Path, label: Optional[str] = None) -> Dict[str, Any]:
    har = json.loads(har_path.read_text(encoding="utf-8"))
    log = har["log"]
    page = log["pages"][0] if log.get("pages") else {}
    page_title = page.get("title", "")
    entries = log.get("entries") or []
    if not entries:
        raise ValueError(f"No entries in {har_path}")

    t0 = _parse_iso(entries[0]["startedDateTime"])
    rows: List[Dict[str, Any]] = []
    milestones: Dict[str, float] = {}

    for entry in entries:
        start = _parse_iso(entry["startedDateTime"])
        start_ms = round((start - t0).total_seconds() * 1000, 1)
        url = entry["request"]["url"]
        duration_ms = round(float(entry.get("time") or 0), 1)
        status = entry["response"]["status"]
        cat = _category(url)
        path = _short_url(url)
        rows.append(
            {
                "url": url,
                "path": path,
                "category": cat,
                "start_ms": start_ms,
                "duration_ms": duration_ms,
                "status": status,
            }
        )
        if "spectrumplot" in path and "first_spectrumplot" not in milestones:
            milestones["first_spectrumplot_ms"] = start_ms
        if "lightcurveplot_detail" in path and "first_lightcurve_ms" not in milestones:
            milestones["first_lightcurve_ms"] = start_ms
        if (
            cat == "yse_api"
            and "first_yse_xhr_ms" not in milestones
            and path not in ("/",)
            and "transient_detail" not in path
        ):
            milestones["first_yse_xhr_ms"] = start_ms
        if "aladin.min.js" in url and "first_aladin_js_ms" not in milestones:
            milestones["first_aladin_js_ms"] = start_ms

    rows.sort(key=lambda r: r["start_ms"])
    timings = page.get("pageTimings") or {}
    by_category: Dict[str, Dict[str, float]] = {}
    for row in rows:
        bucket = by_category.setdefault(
            row["category"],
            {"count": 0, "total_duration_ms": 0.0, "max_duration_ms": 0.0},
        )
        bucket["count"] += 1
        bucket["total_duration_ms"] += row["duration_ms"]
        bucket["max_duration_ms"] = max(bucket["max_duration_ms"], row["duration_ms"])

    slowest = sorted(rows, key=lambda r: -r["duration_ms"])[:15]
    slug_match = re.search(r"/transient_detail/([^/]+)/", page_title)
    snapshot_label = label or (slug_match.group(1) if slug_match else har_path.stem)

    return {
        "label": snapshot_label,
        "source_har": har_path.name,
        "page_url": page_title,
        "captured_at": entries[0]["startedDateTime"],
        "entry_count": len(rows),
        "page_timings_ms": {
            "on_content_load": _normalize_page_timing_ms(timings.get("onContentLoad")),
            "on_load": _normalize_page_timing_ms(timings.get("onLoad")),
        },
        "milestones_ms": milestones,
        "by_category": by_category,
        "slowest": slowest,
        "entries": rows,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert HAR to YSE perf JSON snapshot")
    parser.add_argument("har", type=Path, help="Input .har file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON path (default: docs/perf/har_snapshots/<har-stem>.json)",
    )
    parser.add_argument("--label", help="Snapshot label (e.g. transient slug)")
    args = parser.parse_args(argv)
    out = args.output
    if out is None:
        out = Path("docs/perf/har_snapshots") / f"{args.har.stem}.json"
    payload = har_to_perf_json(args.har, label=args.label)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({payload['entry_count']} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
