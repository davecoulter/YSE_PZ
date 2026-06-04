#!/usr/bin/env python3
"""Plot HAR snapshot JSON: timeline by category and slowest requests."""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: plot_har_snapshot.py <snapshot.json>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib required: pip install matplotlib", file=sys.stderr)
        return 1

    entries = data.get("entries") or []
    if not entries:
        print("No entries in snapshot", file=sys.stderr)
        return 1

    fig, (ax_timeline, ax_slow) = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)
    colors = {
        "yse_api": "#2563eb",
        "static": "#64748b",
        "aladin": "#dc2626",
        "external_sky": "#f59e0b",
        "external_cutout": "#16a34a",
        "bokeh_cdn": "#7c3aed",
        "fonts": "#a3a3a3",
        "other": "#9ca3af",
    }
    for row in entries:
        cat = row.get("category", "other")
        ax_timeline.barh(
            row["path"][:60],
            row["duration_ms"],
            left=row["start_ms"],
            height=0.6,
            color=colors.get(cat, "#9ca3af"),
            alpha=0.85,
        )
    ax_timeline.set_xlabel("ms from navigation start")
    ax_timeline.set_title(f"Request timeline — {data.get('label', path.stem)}")
    milestones = data.get("milestones_ms") or {}
    for name, ms in milestones.items():
        ax_timeline.axvline(ms, color="#111827", linestyle="--", linewidth=0.8, alpha=0.5)
        ax_timeline.text(ms, ax_timeline.get_ylim()[1] * 0.02, name.replace("_ms", ""), rotation=90, fontsize=7)

    slow = (data.get("slowest") or [])[:12]
    labels = [f"{r['path'][:50]} ({r['duration_ms']:.0f}ms)" for r in reversed(slow)]
    vals = [r["duration_ms"] for r in reversed(slow)]
    ax_slow.barh(labels, vals, color="#2563eb")
    ax_slow.set_xlabel("duration (ms)")
    ax_slow.set_title("Slowest requests")

    out = path.with_suffix(".png")
    fig.savefig(out, dpi=120)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
