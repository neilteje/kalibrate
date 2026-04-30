"""Generate publication-quality plots for the POPCAST benchmark evaluation.

Requires the sibling `pretty-plots` repo (``../pretty-plots/utils.py``) for
matplotlib defaults, palette indices (COLOR), and line/marker styles.

Usage:
    python eval/plots.py [--results-dir results] [--output-dir results/figures]

Generates:
    1. overall_brier.png         - System comparison bar chart (Brier score)
    2. overall_logloss.png       - System comparison bar chart (Log Loss)
    3. overall_tsr.png           - System comparison bar chart (TSR)
    4. per_task_heatmap.png      - Heatmap of Brier scores per (system, task)
    5. by_difficulty.png         - Grouped bar chart by difficulty level
    6. calibration.png           - Calibration plot (predicted vs actual)
    7. runtime_comparison.png    - Runtime bar chart per system
    8. radar.png                 - Radar/spider chart of multi-metric profile
    9. per_task_grouped.png      - Grouped bar chart per task
   10. confidence_vs_brier.png   - Scatter: confidence vs Brier score
   11. price_history_tasks.png   - Task price histories (context)
   12. dashboard.png             - Combined 2x3 dashboard figure
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from statistics import mean

import matplotlib

ROOT = Path(__file__).resolve().parents[1]
PRETTY_PLOTS_DIR = ROOT.parent / "pretty-plots"
sys.path.insert(0, str(ROOT))


def _load_pretty_plots_utils():
    """Load sibling `pretty-plots/utils.py` (publication rcParams, palettes, helpers)."""
    path = PRETTY_PLOTS_DIR / "utils.py"
    if not path.is_file():
        raise FileNotFoundError(
            f"pretty-plots not found at {path}. Clone or place pretty-plots next to this repo."
        )
    spec = importlib.util.spec_from_file_location("pretty_plots_utils", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_pp = _load_pretty_plots_utils()
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from agent.market_state import load_task  # noqa: E402

# pretty-plots: seaborn "deep" palette via C0–C9, line/marker styles
COLOR = _pp.COLOR
LINESTYLE = _pp.LINESTYLE
MARKER = _pp.MARKER

SYSTEM_ORDER = ["random", "single_prompt", "frontier_tool", "market_only", "kalibrate"]
SYSTEM_LABELS = {
    "random": "Random\n(B1)",
    "single_prompt": "Single-Prompt\n(B2)",
    "frontier_tool": "Frontier+Tools\n(B3)",
    "market_only": "Market-Only\n(B4)",
    "kalibrate": "KALIBRATE\n(Ours)",
}
# Muted, distinguishable mapping: neutral baseline → baselines → accent (ours)
SYSTEM_COLORS = {
    "random": COLOR[7],
    "single_prompt": COLOR[0],
    "frontier_tool": COLOR[2],
    "market_only": COLOR[1],
    "kalibrate": COLOR[4],
}
DIFFICULTY_ORDER = ["easy", "medium", "hard"]

sns.set_style(
    "whitegrid",
    {"axes.edgecolor": ".15", "grid.color": ".92", "axes.grid": True},
)
sns.set_context("notebook", font_scale=1.05)
plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 180,
    "savefig.bbox": "tight",
    "axes.titleweight": "bold",
    "axes.labelweight": "medium",
    "grid.alpha": 0.45,
})

# Heatmap: perceptually uniform (lower Brier = darker = better in viridis)
_HEATMAP_CMAP = sns.color_palette("viridis", as_cmap=True)


def load_results(results_dir: Path) -> list[dict]:
    out = []
    for p in sorted(results_dir.glob("*.json")):
        try:
            with p.open("r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def load_task_meta() -> dict[str, dict]:
    tasks_dir = ROOT / "tasks"
    return {p.stem: load_task(p) for p in sorted(tasks_dir.glob("T*.json"))}


def _sys_label(s: str) -> str:
    return SYSTEM_LABELS.get(s, s)


def _sys_color(s: str) -> str:
    return SYSTEM_COLORS.get(s, "#6b7280")


# ── Aggregation helpers ──────────────────────────────────────────────────

def aggregate_overall(results: list[dict]) -> dict:
    by_sys: dict[str, list[dict]] = {}
    for r in results:
        by_sys.setdefault(r["system"], []).append(r)
    summary = {}
    for s, runs in by_sys.items():
        by_trial: dict[int, list[dict]] = {}
        for r in runs:
            by_trial.setdefault(int(r.get("trial", 1)), []).append(r)
        tb, tl, tt = [], [], []
        for _, trial_runs in by_trial.items():
            tb.append(mean(r["brier"] for r in trial_runs))
            tl.append(mean(r["log_loss"] for r in trial_runs))
            tt.append(mean(r["correct"] for r in trial_runs))
        from statistics import pstdev
        _std = lambda v: pstdev(v) if len(v) > 1 else 0.0
        summary[s] = {
            "brier_mean": mean(tb), "brier_std": _std(tb),
            "logloss_mean": mean(tl), "logloss_std": _std(tl),
            "tsr_mean": mean(tt), "tsr_std": _std(tt),
            "n_runs": len(runs),
        }
    return summary


def aggregate_per_task(results: list[dict]) -> dict:
    grouped: dict[str, dict[str, list[float]]] = {}
    for r in results:
        grouped.setdefault(r["system"], {}).setdefault(r["task_id"], []).append(r["brier"])
    return {s: {t: mean(v) for t, v in tmap.items()} for s, tmap in grouped.items()}


def aggregate_by_difficulty(results: list[dict], task_meta: dict) -> dict:
    out: dict[str, dict[str, list[float]]] = {}
    for r in results:
        diff = task_meta.get(r["task_id"], {}).get("difficulty", "unknown")
        out.setdefault(r["system"], {}).setdefault(diff, []).append(r["brier"])
    return {s: {d: mean(v) for d, v in dm.items()} for s, dm in out.items()}


def aggregate_runtimes(results: list[dict]) -> dict:
    by_sys: dict[str, list[float]] = {}
    for r in results:
        rt = r.get("runtime_s", 0.0)
        by_sys.setdefault(r["system"], []).append(rt)
    return {s: {"mean": mean(v), "max": max(v), "min": min(v)} for s, v in by_sys.items()}


# ── Plot functions ────────────────────────────────────────────────────────

def plot_overall_bar(summary: dict, metric: str, ylabel: str, title: str, out: Path):
    systems = [s for s in SYSTEM_ORDER if s in summary]
    means = [summary[s][f"{metric}_mean"] for s in systems]
    stds = [summary[s].get(f"{metric}_std", 0) for s in systems]
    colors = [_sys_color(s) for s in systems]
    labels = [_sys_label(s) for s in systems]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(systems))
    err_kw = dict(ecolor="0.25", lw=1.1, capsize=5, capthick=1.1)
    bars = ax.bar(
        x,
        means,
        yerr=stds,
        color=colors,
        edgecolor="0.12",
        linewidth=1,
        zorder=3,
        width=0.62,
        error_kw=err_kw,
        clip_on=False,
    )
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(stds) * 0.15 + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_ylim(0, max(means) * 1.35 + 0.02)
    ax.grid(axis="y", alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_per_task_heatmap(per_task: dict, task_meta: dict, out: Path):
    tasks = sorted(task_meta.keys(), key=lambda t: int(t[1:]))
    systems = [s for s in SYSTEM_ORDER if s in per_task]
    matrix = []
    for s in systems:
        row = [per_task[s].get(t, float("nan")) for t in tasks]
        matrix.append(row)
    arr = np.array(matrix)
    labels_y = [_sys_label(s).replace("\n", " ") for s in systems]
    labels_x = [f"{t}\n{task_meta[t]['domain'][:8]}" for t in tasks]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    im = ax.imshow(arr, cmap=_HEATMAP_CMAP, aspect="auto", vmin=0, vmax=0.35)
    for i in range(len(systems)):
        for j in range(len(tasks)):
            val = arr[i, j]
            # viridis: dark (low Brier) → light text; bright (high Brier) → dark text
            txt_color = "white" if val < 0.16 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=9, color=txt_color)
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels(labels_x, fontsize=9)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels(labels_y, fontsize=10)
    ax.set_title("Brier Score per Task (lower = better)", fontsize=13, pad=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Brier Score")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_by_difficulty(by_diff: dict, out: Path):
    systems = [s for s in SYSTEM_ORDER if s in by_diff]
    n = len(systems)
    x = np.arange(len(DIFFICULTY_ORDER))
    width = 0.75 / n

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, s in enumerate(systems):
        vals = [by_diff[s].get(d, 0) for d in DIFFICULTY_ORDER]
        offset = (i - n / 2 + 0.5) * width
        bars = ax.bar(
            x + offset,
            vals,
            width,
            label=_sys_label(s).replace("\n", " "),
            color=_sys_color(s),
            edgecolor="0.12",
            linewidth=0.9,
            zorder=3,
            clip_on=False,
        )
        for bar, v in zip(bars, vals):
            if v > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                        f"{v:.3f}", ha="center", va="bottom", fontsize=7.5, rotation=45)
    ax.set_xticks(x)
    ax.set_xticklabels([d.capitalize() for d in DIFFICULTY_ORDER], fontsize=12)
    ax.set_ylabel("Mean Brier Score", fontsize=12)
    ax.set_title("Performance by Task Difficulty", fontsize=14, pad=12)
    ax.legend(fontsize=8, ncol=3, loc="upper left", framealpha=0.95)
    ax.grid(axis="y", alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_calibration(results: list[dict], out: Path):
    n_bins = 5
    systems = [s for s in SYSTEM_ORDER if s != "random"]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], color="0.35", linestyle="--", alpha=0.75, label="Perfect calibration")
    for idx, s in enumerate(systems):
        runs = [r for r in results if r["system"] == s]
        if not runs:
            continue
        preds = [r["p_final"] for r in runs]
        outcomes = [r["outcome"] for r in runs]
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_means_p, bin_means_y = [], []
        for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
            mask = [(lo <= p < hi) or (hi == 1.0 and p == 1.0) for p in preds]
            bp = [p for p, m in zip(preds, mask) if m]
            by = [o for o, m in zip(outcomes, mask) if m]
            if bp:
                bin_means_p.append(mean(bp))
                bin_means_y.append(mean(by))
        ax.plot(
            bin_means_p,
            bin_means_y,
            color=_sys_color(s),
            linestyle=LINESTYLE[idx % len(LINESTYLE)],
            marker=MARKER[idx % len(MARKER)],
            label=_sys_label(s).replace("\n", " "),
            markersize=8,
            linewidth=2,
            clip_on=False,
        )
    ax.set_xlabel("Mean Predicted Probability", fontsize=12)
    ax.set_ylabel("Observed Frequency (YES)", fontsize=12)
    ax.set_title("Calibration Plot", fontsize=14, pad=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper left", framealpha=0.95)
    ax.grid(alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_runtime(runtimes: dict, out: Path):
    systems = [s for s in SYSTEM_ORDER if s in runtimes]
    means = [runtimes[s]["mean"] for s in systems]
    colors = [_sys_color(s) for s in systems]
    labels = [_sys_label(s) for s in systems]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(systems))
    bars = ax.bar(
        x,
        means,
        color=colors,
        edgecolor="0.12",
        linewidth=1,
        zorder=3,
        width=0.62,
        clip_on=False,
    )
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1f}s", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Mean Runtime (seconds)", fontsize=12)
    ax.set_title("Average Runtime per Forecast", fontsize=14, pad=12)
    ax.grid(axis="y", alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_radar(summary: dict, out: Path):
    systems = [s for s in SYSTEM_ORDER if s in summary]
    metrics = ["Brier (inv)", "LogLoss (inv)", "TSR"]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    for idx, s in enumerate(systems):
        vals = [
            1 - summary[s]["brier_mean"],
            1 - min(1.0, summary[s]["logloss_mean"]),
            summary[s]["tsr_mean"],
        ]
        vals += vals[:1]
        ax.plot(
            angles,
            vals,
            linestyle=LINESTYLE[idx % len(LINESTYLE)],
            marker=MARKER[idx % len(MARKER)],
            label=_sys_label(s).replace("\n", " "),
            color=_sys_color(s),
            linewidth=2,
            markersize=7,
            clip_on=False,
        )
        ax.fill(angles, vals, alpha=0.09, color=_sys_color(s))
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_title("Multi-Metric System Profile", fontsize=14, pad=20)
    ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1.3, 1.1), framealpha=0.95)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_per_task_grouped(per_task: dict, task_meta: dict, out: Path):
    tasks = sorted(task_meta.keys(), key=lambda t: int(t[1:]))
    systems = [s for s in SYSTEM_ORDER if s in per_task]
    n = len(systems)
    x = np.arange(len(tasks))
    width = 0.75 / n

    fig, ax = plt.subplots(figsize=(14, 5.5))
    for i, s in enumerate(systems):
        vals = [per_task[s].get(t, 0) for t in tasks]
        offset = (i - n / 2 + 0.5) * width
        ax.bar(
            x + offset,
            vals,
            width,
            label=_sys_label(s).replace("\n", " "),
            color=_sys_color(s),
            edgecolor="0.12",
            linewidth=0.7,
            zorder=3,
            clip_on=False,
        )
    ax.set_xticks(x)
    labels = [f"{t}\n({task_meta[t]['difficulty'][:3]})" for t in tasks]
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Mean Brier Score", fontsize=12)
    ax.set_title("Per-Task Brier Score Comparison", fontsize=14, pad=12)
    ax.legend(fontsize=8, ncol=5, loc="upper center", framealpha=0.95)
    ax.grid(axis="y", alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_confidence_vs_brier(results: list[dict], out: Path):
    fig, ax = plt.subplots(figsize=(7, 5))
    for idx, s in enumerate(SYSTEM_ORDER):
        runs = [r for r in results if r["system"] == s and "confidence" in r]
        if not runs:
            continue
        confs = [r["confidence"] for r in runs]
        briers = [r["brier"] for r in runs]
        ax.scatter(
            confs,
            briers,
            alpha=0.58,
            s=42,
            color=_sys_color(s),
            marker=MARKER[idx % len(MARKER)],
            label=_sys_label(s).replace("\n", " "),
            edgecolors="0.15",
            linewidth=0.55,
            clip_on=False,
        )
    ax.set_xlabel("Self-Reported Confidence", fontsize=12)
    ax.set_ylabel("Brier Score", fontsize=12)
    ax.set_title("Confidence vs Actual Brier Score", fontsize=14, pad=10)
    ax.legend(fontsize=8, framealpha=0.95)
    ax.grid(alpha=0.35)
    sns.despine()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_price_histories(task_meta: dict, out: Path):
    tasks = sorted(task_meta.keys(), key=lambda t: int(t[1:]))
    fig, axes = plt.subplots(2, 5, figsize=(18, 6), sharey=True)
    axes_flat = axes.flatten()
    for i, tid in enumerate(tasks):
        ax = axes_flat[i]
        meta = task_meta[tid]
        ph = meta.get("price_history", [])
        outcome = meta.get("outcome", 0)
        ax.plot(
            range(len(ph)),
            ph,
            linestyle=LINESTYLE[0],
            marker=MARKER[0],
            color=COLOR[0],
            linewidth=2,
            markersize=5,
            clip_on=False,
        )
        ax.axhline(
            y=outcome,
            color=COLOR[3] if outcome == 0 else COLOR[2],
            linestyle="--",
            alpha=0.72,
            linewidth=1.5,
        )
        ax.set_title(f"{tid} ({meta['difficulty'][:3]})", fontsize=10, fontweight="bold")
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel("Time step", fontsize=8)
        if i % 5 == 0:
            ax.set_ylabel("Implied P(YES)", fontsize=9)
        ax.grid(alpha=0.35)
        ax.text(
            0.97,
            0.03,
            f"y={outcome}",
            transform=ax.transAxes,
            ha="right",
            fontsize=8,
            color=COLOR[2] if outcome else COLOR[3],
            fontweight="bold",
        )
    fig.suptitle("POPCAST Task Price Histories (dashed = outcome)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def plot_dashboard(summary: dict, per_task: dict, by_diff: dict, task_meta: dict,
                   runtimes: dict, results: list[dict], out: Path):
    fig = plt.figure(figsize=(20, 13))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)

    # 1) Overall Brier bar
    ax1 = fig.add_subplot(gs[0, 0])
    systems = [s for s in SYSTEM_ORDER if s in summary]
    means = [summary[s]["brier_mean"] for s in systems]
    stds = [summary[s]["brier_std"] for s in systems]
    colors = [_sys_color(s) for s in systems]
    x = np.arange(len(systems))
    err_kw = dict(ecolor="0.25", lw=1.0, capsize=4, capthick=1.0)
    ax1.bar(
        x,
        means,
        yerr=stds,
        color=colors,
        edgecolor="0.12",
        linewidth=1,
        width=0.6,
        error_kw=err_kw,
        clip_on=False,
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels([_sys_label(s) for s in systems], fontsize=7)
    ax1.set_ylabel("Brier Score")
    ax1.set_title("Overall Brier Score", fontweight="bold")
    ax1.grid(axis="y", alpha=0.35)

    # 2) TSR bar
    ax2 = fig.add_subplot(gs[0, 1])
    tsrs = [summary[s]["tsr_mean"] for s in systems]
    ax2.bar(
        x,
        tsrs,
        color=colors,
        edgecolor="0.12",
        linewidth=1,
        width=0.6,
        clip_on=False,
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels([_sys_label(s) for s in systems], fontsize=7)
    ax2.set_ylabel("TSR")
    ax2.set_title("Task Success Rate", fontweight="bold")
    ax2.set_ylim(0, 1.1)
    ax2.grid(axis="y", alpha=0.35)

    # 3) By difficulty
    ax3 = fig.add_subplot(gs[0, 2])
    n = len(systems)
    xd = np.arange(len(DIFFICULTY_ORDER))
    width = 0.7 / n
    for i, s in enumerate(systems):
        vals = [by_diff.get(s, {}).get(d, 0) for d in DIFFICULTY_ORDER]
        offset = (i - n / 2 + 0.5) * width
        ax3.bar(
            xd + offset,
            vals,
            width,
            color=_sys_color(s),
            edgecolor="0.12",
            linewidth=0.55,
            clip_on=False,
        )
    ax3.set_xticks(xd)
    ax3.set_xticklabels([d.capitalize() for d in DIFFICULTY_ORDER])
    ax3.set_ylabel("Mean Brier")
    ax3.set_title("By Difficulty", fontweight="bold")
    ax3.grid(axis="y", alpha=0.35)

    # 4) Per-task heatmap
    ax4 = fig.add_subplot(gs[1, 0:2])
    tasks = sorted(task_meta.keys(), key=lambda t: int(t[1:]))
    sys_in = [s for s in SYSTEM_ORDER if s in per_task]
    matrix = np.array([[per_task[s].get(t, float("nan")) for t in tasks] for s in sys_in])
    im = ax4.imshow(matrix, cmap=_HEATMAP_CMAP, aspect="auto", vmin=0, vmax=0.35)
    for i in range(len(sys_in)):
        for j in range(len(tasks)):
            v = matrix[i, j]
            txt_color = "white" if v < 0.16 else "black"
            ax4.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=8, color=txt_color)
    ax4.set_xticks(range(len(tasks)))
    ax4.set_xticklabels(tasks, fontsize=9)
    ax4.set_yticks(range(len(sys_in)))
    ax4.set_yticklabels([_sys_label(s).replace("\n", " ") for s in sys_in], fontsize=8)
    ax4.set_title("Per-Task Brier Heatmap", fontweight="bold")
    fig.colorbar(im, ax=ax4, shrink=0.7)

    # 5) Calibration
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.plot([0, 1], [0, 1], color="0.35", linestyle="--", alpha=0.75)
    cal_systems = [s for s in SYSTEM_ORDER if s != "random"]
    for idx, s in enumerate(cal_systems):
        runs = [r for r in results if r["system"] == s]
        if not runs:
            continue
        preds = [r["p_final"] for r in runs]
        outcomes = [r["outcome"] for r in runs]
        bin_edges = np.linspace(0, 1, 6)
        bmp, bmy = [], []
        for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
            mask = [(lo <= p < hi) or (hi == 1.0 and p == 1.0) for p in preds]
            bp = [p for p, m in zip(preds, mask) if m]
            by = [o for o, m in zip(outcomes, mask) if m]
            if bp:
                bmp.append(mean(bp))
                bmy.append(mean(by))
        ax5.plot(
            bmp,
            bmy,
            color=_sys_color(s),
            linestyle=LINESTYLE[idx % len(LINESTYLE)],
            marker=MARKER[idx % len(MARKER)],
            linewidth=2,
            markersize=5,
            label=_sys_label(s).replace("\n", " "),
            clip_on=False,
        )
    ax5.set_xlabel("Predicted P")
    ax5.set_ylabel("Observed freq")
    ax5.set_title("Calibration", fontweight="bold")
    ax5.set_xlim(-0.02, 1.02)
    ax5.set_ylim(-0.02, 1.02)
    ax5.set_aspect("equal")
    ax5.legend(fontsize=6, framealpha=0.95)
    ax5.grid(alpha=0.35)

    fig.suptitle("POPCAST Benchmark — KALIBRATE Evaluation Dashboard",
                 fontsize=16, fontweight="bold", y=0.98)
    fig.savefig(out)
    plt.close(fig)
    print(f"  saved {out.name}")


def main():
    parser = argparse.ArgumentParser(description="Generate POPCAST benchmark plots.")
    parser.add_argument("--results-dir", type=str, default=str(ROOT / "results"))
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(results_dir)
    if not results:
        print(f"No results found in {results_dir}")
        sys.exit(1)

    task_meta = load_task_meta()
    summary = aggregate_overall(results)
    per_task = aggregate_per_task(results)
    by_diff = aggregate_by_difficulty(results, task_meta)
    runtimes = aggregate_runtimes(results)

    print(f"Loaded {len(results)} result files across {len(summary)} systems.")
    print(f"Generating plots in {output_dir}/\n")

    plot_overall_bar(summary, "brier", "Mean Brier Score", "Overall Brier Score (lower = better)",
                     output_dir / "overall_brier.png")
    plot_overall_bar(summary, "logloss", "Mean Log Loss", "Overall Log Loss (lower = better)",
                     output_dir / "overall_logloss.png")
    plot_overall_bar(summary, "tsr", "Task Success Rate", "Task Success Rate (higher = better)",
                     output_dir / "overall_tsr.png")
    plot_per_task_heatmap(per_task, task_meta, output_dir / "per_task_heatmap.png")
    plot_by_difficulty(by_diff, output_dir / "by_difficulty.png")
    plot_calibration(results, output_dir / "calibration.png")
    plot_runtime(runtimes, output_dir / "runtime_comparison.png")
    plot_radar(summary, output_dir / "radar.png")
    plot_per_task_grouped(per_task, task_meta, output_dir / "per_task_grouped.png")
    plot_confidence_vs_brier(results, output_dir / "confidence_vs_brier.png")
    plot_price_histories(task_meta, output_dir / "price_history_tasks.png")
    plot_dashboard(summary, per_task, by_diff, task_meta, runtimes, results,
                   output_dir / "dashboard.png")

    print(f"\nAll {12} plots saved to {output_dir}/")


if __name__ == "__main__":
    main()
