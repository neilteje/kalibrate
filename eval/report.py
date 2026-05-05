"""Aggregate raw run results into summary tables and LaTeX-ready output.

Usage:
    python eval/report.py [--results-dir results]

Outputs:
    - results/summary.csv           (one row per system)
    - results/per_task.csv          (one row per (system, task))
    - results/by_difficulty.csv     (one row per (system, difficulty))
    - LaTeX table snippets printed to stdout
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.market_state import load_task  # noqa: E402


SYSTEM_ORDER = ["random", "single_prompt", "frontier_tool", "market_only", "kalibrate"]
SYSTEM_DISPLAY = {
    "random": "(B1) Random / Prior",
    "single_prompt": "(B2) Single-Prompt LLM",
    "frontier_tool": "(B3) Tool-Enabled Frontier",
    "market_only": "(B4) Market-Only Ablation",
    "kalibrate": "KALIBRATE (Full)",
}


def load_results(results_dir: Path) -> list[dict]:
    out = []
    for p in sorted(results_dir.glob("*.json")):
        if p.name in {"summary.csv", "per_task.csv", "by_difficulty.csv"}:
            continue
        try:
            with p.open("r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def load_task_meta() -> dict[str, dict]:
    tasks_dir = ROOT / "tasks"
    return {
        p.stem: load_task(p) for p in sorted(tasks_dir.glob("T*.json"))
    }


def _agg(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0
    return mean(values), pstdev(values)


def build_overall(results: list[dict]) -> dict[str, dict]:
    """Per-system: mean of per-trial averages over all tasks. Std across trials."""
    by_system: dict[str, list[dict]] = {}
    for r in results:
        by_system.setdefault(r["system"], []).append(r)

    summary = {}
    for sys_name, runs in by_system.items():
        # Group by trial across tasks: each trial has one row per task; we want
        # the per-trial mean across tasks, then mean+std of those.
        by_trial: dict[int, list[dict]] = {}
        for r in runs:
            by_trial.setdefault(int(r.get("trial", 1)), []).append(r)
        per_trial_brier = []
        per_trial_logloss = []
        per_trial_tsr = []
        for trial_id, trial_runs in by_trial.items():
            per_trial_brier.append(mean(r["brier"] for r in trial_runs))
            per_trial_logloss.append(mean(r["log_loss"] for r in trial_runs))
            per_trial_tsr.append(mean(r["correct"] for r in trial_runs))
        b_mean, b_std = _agg(per_trial_brier)
        l_mean, l_std = _agg(per_trial_logloss)
        t_mean, t_std = _agg(per_trial_tsr)
        summary[sys_name] = {
            "brier_mean": b_mean,
            "brier_std": b_std,
            "logloss_mean": l_mean,
            "logloss_std": l_std,
            "tsr_mean": t_mean,
            "tsr_std": t_std,
            "n_trials": len(by_trial),
            "n_runs": len(runs),
        }
    return summary


def build_by_difficulty(results: list[dict], task_meta: dict[str, dict]) -> dict:
    out: dict = {}
    for r in results:
        diff = task_meta.get(r["task_id"], {}).get("difficulty", "unknown")
        out.setdefault(r["system"], {}).setdefault(diff, []).append(r["brier"])
    summary: dict = {}
    for sys_name, by_diff in out.items():
        summary[sys_name] = {
            d: mean(vals) for d, vals in by_diff.items()
        }
    return summary


def build_by_domain(results: list[dict], task_meta: dict[str, dict]) -> dict:
    out: dict = {}
    for r in results:
        domain = task_meta.get(r["task_id"], {}).get("domain", "unknown")
        out.setdefault(r["system"], {}).setdefault(domain, []).append(r["brier"])
    summary: dict = {}
    for sys_name, by_domain in out.items():
        summary[sys_name] = {
            d: mean(vals) for d, vals in by_domain.items()
        }
    return summary


def build_per_task(results: list[dict]) -> dict:
    """system -> task_id -> mean brier across trials."""
    grouped: dict = {}
    for r in results:
        grouped.setdefault(r["system"], {}).setdefault(r["task_id"], []).append(r["brier"])
    return {
        sys_name: {tid: mean(vals) for tid, vals in tmap.items()}
        for sys_name, tmap in grouped.items()
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def print_overall_latex(summary: dict):
    print("\n% --- Overall results table ---")
    print(r"\begin{tabular}{lccc}")
    print(r"\toprule")
    print(r"\textbf{System} & \textbf{Brier} $\downarrow$ & \textbf{Log Loss} $\downarrow$ & \textbf{TSR} $\uparrow$ \\")
    print(r"\midrule")
    for s in SYSTEM_ORDER:
        if s not in summary:
            continue
        row = summary[s]
        if row["n_trials"] > 1:
            br = f"{row['brier_mean']:.3f} $\\pm$ {row['brier_std']:.3f}"
            ll = f"{row['logloss_mean']:.3f} $\\pm$ {row['logloss_std']:.3f}"
            ts = f"{row['tsr_mean']:.3f}"
        else:
            br = f"{row['brier_mean']:.3f}"
            ll = f"{row['logloss_mean']:.3f}"
            ts = f"{row['tsr_mean']:.3f}"
        line = f"{SYSTEM_DISPLAY[s]} & {br} & {ll} & {ts} \\\\"
        if s == "kalibrate":
            line = line.replace(SYSTEM_DISPLAY[s], r"\textbf{" + SYSTEM_DISPLAY[s] + r"}")
        print(line)
    print(r"\bottomrule")
    print(r"\end{tabular}")


def print_difficulty_latex(by_diff: dict, summary: dict):
    print("\n% --- By difficulty table ---")
    print(r"\begin{tabular}{lcccc}")
    print(r"\toprule")
    print(r"\textbf{System} & \textbf{Overall} & \textbf{Easy} & \textbf{Medium} & \textbf{Hard} \\")
    print(r"\midrule")
    for s in SYSTEM_ORDER:
        if s not in by_diff:
            continue
        d = by_diff[s]
        overall = summary[s]["brier_mean"]
        e = d.get("easy", float("nan"))
        m = d.get("medium", float("nan"))
        h = d.get("hard", float("nan"))
        print(f"{SYSTEM_DISPLAY[s]} & {overall:.3f} & {e:.3f} & {m:.3f} & {h:.3f} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")


def print_domain_latex(by_domain: dict, task_meta: dict):
    print("\n% --- By domain table ---")
    domains = sorted({m["domain"] for m in task_meta.values()})
    print(r"\begin{tabular}{l" + "c" * len(domains) + "}")
    print(r"\toprule")
    header = r"\textbf{System} " + " ".join(
        f"& \\textbf{{{d.capitalize()}}}" for d in domains
    ) + r" \\"
    print(header)
    print(r"\midrule")
    for s in SYSTEM_ORDER:
        if s not in by_domain:
            continue
        row = [f"{by_domain[s].get(d, float('nan')):.3f}" for d in domains]
        print(f"{SYSTEM_DISPLAY[s]} & " + " & ".join(row) + r" \\")
    print(r"\bottomrule")
    print(r"\end{tabular}")


def print_per_task_latex(per_task: dict, task_meta: dict):
    print("\n% --- Per-task table ---")
    print(r"\begin{tabular}{llccccc}")
    print(r"\toprule")
    print(r"\textbf{Task} & \textbf{Domain} & \textbf{Diff.} & \textbf{B1} & \textbf{B2} & \textbf{B3} & \textbf{Ours} \\")
    print(r"\midrule")
    for tid in sorted(task_meta.keys(), key=lambda x: int(x[1:])):
        meta = task_meta[tid]
        domain = meta["domain"][:14]
        diff = meta["difficulty"].capitalize()
        b1 = per_task.get("random", {}).get(tid, float("nan"))
        b2 = per_task.get("single_prompt", {}).get(tid, float("nan"))
        b3 = per_task.get("frontier_tool", {}).get(tid, float("nan"))
        ours = per_task.get("kalibrate", {}).get(tid, float("nan"))
        print(f"{tid} & {domain} & {diff} & {b1:.3f} & {b2:.3f} & {b3:.3f} & {ours:.3f} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=str, default=str(ROOT / "results"))
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results = load_results(results_dir)
    if not results:
        print(f"No results found in {results_dir}")
        sys.exit(1)
    task_meta = load_task_meta()

    summary = build_overall(results)
    by_diff = build_by_difficulty(results, task_meta)
    by_domain = build_by_domain(results, task_meta)
    per_task = build_per_task(results)

    # --- CSV writes ---
    write_csv(
        results_dir / "summary.csv",
        [
            {
                "system": s,
                "brier_mean": summary[s]["brier_mean"],
                "brier_std": summary[s]["brier_std"],
                "logloss_mean": summary[s]["logloss_mean"],
                "logloss_std": summary[s]["logloss_std"],
                "tsr_mean": summary[s]["tsr_mean"],
                "n_trials": summary[s]["n_trials"],
                "n_runs": summary[s]["n_runs"],
            }
            for s in SYSTEM_ORDER
            if s in summary
        ],
        ["system", "brier_mean", "brier_std", "logloss_mean", "logloss_std", "tsr_mean", "n_trials", "n_runs"],
    )
    write_csv(
        results_dir / "per_task.csv",
        [
            {"system": s, "task_id": t, "brier": v}
            for s, tmap in per_task.items()
            for t, v in tmap.items()
        ],
        ["system", "task_id", "brier"],
    )
    write_csv(
        results_dir / "by_difficulty.csv",
        [
            {"system": s, "difficulty": d, "brier": v}
            for s, dmap in by_diff.items()
            for d, v in dmap.items()
        ],
        ["system", "difficulty", "brier"],
    )
    write_csv(
        results_dir / "by_domain.csv",
        [
            {"system": s, "domain": d, "brier": v}
            for s, dmap in by_domain.items()
            for d, v in dmap.items()
        ],
        ["system", "domain", "brier"],
    )

    # --- Console summary ---
    print("=" * 70)
    print("OVERALL")
    print("=" * 70)
    for s in SYSTEM_ORDER:
        if s not in summary:
            continue
        r = summary[s]
        print(
            f"  {SYSTEM_DISPLAY[s]:32s}  "
            f"Brier={r['brier_mean']:.3f} (±{r['brier_std']:.3f})  "
            f"LogLoss={r['logloss_mean']:.3f}  "
            f"TSR={r['tsr_mean']:.3f}  "
            f"n_trials={r['n_trials']}"
        )

    print_overall_latex(summary)
    print_difficulty_latex(by_diff, summary)
    print_domain_latex(by_domain, task_meta)
    print_per_task_latex(per_task, task_meta)


if __name__ == "__main__":
    main()
