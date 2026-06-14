"""
Matplotlib charts for page-load benchmarks (waterfall + iteration trends).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from YSE_App.perf.benchmark import PageBenchmark
from YSE_App.perf.resource_timing import (
    WATERFALL_PHASES,
    PageLoadTimeline,
    ResourceTiming,
    timeline_total_ms,
)

PERF_STATIC_DIR = Path(__file__).resolve().parents[1] / "static" / "YSE_App" / "perf"
METRICS_HISTORY_PATH = PERF_STATIC_DIR / "metrics_history.json"

PRIMARY_PAGE_KEYS = ("main_dashboard", "personal_dashboard", "transient_detail")


def _ensure_perf_dir() -> Path:
    PERF_STATIC_DIR.mkdir(parents=True, exist_ok=True)
    return PERF_STATIC_DIR


def load_history() -> Dict[str, Any]:
    if not METRICS_HISTORY_PATH.exists():
        return {"runs": []}
    with METRICS_HISTORY_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_history(data: Dict[str, Any]) -> None:
    _ensure_perf_dir()
    with METRICS_HISTORY_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def append_run(
    *,
    label: str,
    commit: str,
    branch: str,
    pages: List[PageBenchmark],
    sections_by_page: Optional[Dict[str, Dict[str, float]]] = None,
    waterfalls: Optional[Dict[str, List[ResourceTiming]]] = None,
    timelines: Optional[Dict[str, PageLoadTimeline]] = None,
) -> Dict[str, Any]:
    history = load_history()
    runs: List[Dict[str, Any]] = history.setdefault("runs", [])
    iteration_index = len(runs)
    page_payload = {}
    for p in pages:
        page_payload[p.page_key] = {
            "url": p.url,
            "ttfb_ms": round(p.ttfb_ms, 1),
            "total_ms": round(p.total_ms, 1),
            "sql_count": p.sql_count,
        }
        if sections_by_page and p.page_key in sections_by_page:
            page_payload[p.page_key]["sections"] = sections_by_page[p.page_key]
        if waterfalls and p.page_key in waterfalls:
            page_payload[p.page_key]["resources"] = [
                r.to_dict() for r in waterfalls[p.page_key]
            ]
        if timelines and p.page_key in timelines:
            tl = timelines[p.page_key]
            page_payload[p.page_key]["page_load_total_ms"] = round(
                tl.page_load_total_ms, 1
            )
            page_payload[p.page_key]["schedule_note"] = tl.schedule_note

    run = {
        "iteration": label,
        "iteration_index": iteration_index,
        "commit": commit,
        "branch": branch,
        "pages": page_payload,
    }
    runs.append(run)
    save_history(history)
    return run


def write_waterfall_plots(
    pages: List[PageBenchmark],
    sections_by_page: Optional[Dict[str, Dict[str, float]]] = None,
    waterfalls: Optional[Dict[str, List[ResourceTiming]]] = None,
    timelines: Optional[Dict[str, PageLoadTimeline]] = None,
) -> List[Path]:
    out_dir = _ensure_perf_dir()
    written: List[Path] = []
    page_keys = [p.page_key for p in pages]
    if waterfalls:
        for page_key in page_keys:
            resources = waterfalls.get(page_key, [])
            if resources:
                tl = timelines.get(page_key) if timelines else None
                path = _write_network_waterfall_chart(
                    out_dir,
                    page_key,
                    resources,
                    schedule_note=tl.schedule_note if tl else "",
                    page_load_total_ms=(
                        tl.page_load_total_ms if tl else timeline_total_ms(resources)
                    ),
                )
                written.append(path)
    else:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        for p in pages:
            segments: Dict[str, float] = {}
            if sections_by_page and p.page_key in sections_by_page:
                segments = dict(sections_by_page[p.page_key])
            else:
                segments = {"total": p.total_ms}
            labels = list(segments.keys())
            values = [segments[k] for k in labels]
            fig, ax = plt.subplots(figsize=(8, max(2, 0.4 * len(labels))))
            y_pos = range(len(labels))
            ax.barh(list(y_pos), values, align="center")
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(labels)
            ax.set_xlabel("Time (ms)")
            ax.set_title(f"{p.page_key} load breakdown")
            ax.invert_yaxis()
            fig.tight_layout()
            path = out_dir / f"waterfall_{p.page_key}.png"
            fig.savefig(path, dpi=120)
            plt.close(fig)
            written.append(path)
    return written


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.2f} MB"
    if size_bytes >= 1000:
        return f"{size_bytes / 1000:.1f} KB"
    return f"{size_bytes} B"


def _write_network_waterfall_chart(
    out_dir: Path,
    page_key: str,
    resources: List[ResourceTiming],
    *,
    schedule_note: str = "",
    page_load_total_ms: float = 0.0,
) -> Path:
    """Timeline waterfall: each bar at start_ms..end_ms on a shared page axis."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    n = len(resources)
    fig_h = max(4.0, 0.45 * n + 2.5)
    fig, ax = plt.subplots(figsize=(15, fig_h))

    page_end = page_load_total_ms or timeline_total_ms(resources)
    doc_end = 0.0
    for res in resources:
        if res.resource_type == "document":
            doc_end = max(doc_end, res.end_ms)

    y_labels = []
    for i, res in enumerate(resources):
        y = n - 1 - i
        y_labels.append(f"{res.name}  ({res.resource_type})")
        phase_left = res.start_ms
        for phase_name, color in WATERFALL_PHASES:
            width = res.phase_ms().get(phase_name, 0.0)
            if width <= 0:
                continue
            ax.barh(
                y,
                width,
                left=phase_left,
                height=0.7,
                color=color,
                edgecolor="none",
            )
            phase_left += width

    if doc_end > 0:
        ax.axvline(doc_end, color="#666", linestyle="--", linewidth=1, alpha=0.8)
        ax.text(
            doc_end,
            n - 0.15,
            " document end",
            fontsize=8,
            color="#666",
            va="bottom",
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels(list(reversed(y_labels)), fontsize=9)
    ax.set_xlabel("Time since navigation start (ms)")
    ax.set_xlim(0, max(page_end * 1.08, 1.0))

    for i, res in enumerate(resources):
        y = n - 1 - i
        ax.text(
            page_end * 1.01,
            y,
            (
                f"{_format_size(res.size_bytes)}  |  "
                f"{res.start_ms:.0f}–{res.end_ms:.0f} ms  "
                f"(dur {res.total_ms:.0f})"
            ),
            va="center",
            fontsize=8,
            color="#333",
        )

    legend_handles = [
        Patch(facecolor=color, label=label) for label, color in WATERFALL_PHASES
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=6,
        fontsize=8,
        frameon=False,
    )
    subtitle = schedule_note or "timeline from measured durations + load schedule"
    ax.set_title(
        f"{page_key} — network waterfall  |  page load {page_end:.0f} ms\n"
        f"{subtitle}\n"
        "(waiting = server; download estimated; parallel rows share start offset)",
        fontsize=10,
    )
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = out_dir / f"waterfall_{page_key}.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def write_trend_plots() -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = load_history()
    runs = history.get("runs", [])
    out_dir = _ensure_perf_dir()
    written: List[Path] = []
    if not runs:
        return written

    indices = [r.get("iteration_index", i) for i, r in enumerate(runs)]
    labels = [r.get("iteration", str(i)) for i, r in enumerate(runs)]

    for page_key in PRIMARY_PAGE_KEYS:
        ys = []
        xs = []
        for i, run in enumerate(runs):
            page = run.get("pages", {}).get(page_key)
            if page:
                xs.append(indices[i])
                ys.append(page["ttfb_ms"])
        if not ys:
            continue
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(xs, ys, marker="o")
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("TTFB (ms)")
        ax.set_xlabel("Iteration")
        ax.set_title(f"{page_key} load time vs iteration")
        fig.tight_layout()
        path = out_dir / f"trend_{page_key}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        written.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    for page_key in PRIMARY_PAGE_KEYS:
        xs, ys = [], []
        for i, run in enumerate(runs):
            page = run.get("pages", {}).get(page_key)
            if page:
                xs.append(indices[i])
                ys.append(page["ttfb_ms"])
        if ys:
            ax.plot(xs, ys, marker="o", label=page_key)
    ax.set_xticks(indices)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("TTFB (ms)")
    ax.set_title("Primary pages load time vs iteration")
    ax.legend()
    fig.tight_layout()
    path = out_dir / "trend_all_pages.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    written.append(path)
    return written
