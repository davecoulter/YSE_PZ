"""
Matplotlib charts for page-load benchmarks (waterfall + iteration trends).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from YSE_App.perf.benchmark import PageBenchmark

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
) -> List[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = _ensure_perf_dir()
    written: List[Path] = []

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
