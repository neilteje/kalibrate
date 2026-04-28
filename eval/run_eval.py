"""End-to-end evaluation harness.

Runs every (system, task, trial) combination and persists results as JSON
files under `results/`. Designed to be resumable: existing result files
are skipped unless --overwrite is passed.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import agent as kalibrate_agent  # noqa: E402
from agent.market_state import get_outcome, load_task  # noqa: E402
from baselines import frontier_tool, market_only, random_baseline, single_prompt  # noqa: E402
from benchmark.scoring import brier, log_loss, task_success  # noqa: E402


def _run_kalibrate(task):
    result = kalibrate_agent.run_episode(task)
    result["system"] = "kalibrate"
    return result


SYSTEMS = {
    "random": (random_baseline.run, True),         # deterministic
    "single_prompt": (single_prompt.run, False),
    "frontier_tool": (frontier_tool.run, False),
    "market_only": (market_only.run, False),
    "kalibrate": (_run_kalibrate, False),
}


def score_result(result: dict, outcome: int) -> dict:
    p = float(result["p_final"])
    return {
        **result,
        "outcome": outcome,
        "brier": brier(p, outcome),
        "log_loss": log_loss(p, outcome),
        "correct": task_success(p, outcome),
    }


def output_path(results_dir: Path, system: str, task_id: str, trial: int) -> Path:
    return results_dir / f"{system}__{task_id}__trial{trial}.json"


def run_single(system_name: str, runner, task: dict, outcome: int, trial: int) -> dict:
    try:
        result = runner(task)
    except Exception as e:
        traceback.print_exc()
        return {
            "task_id": task["task_id"],
            "system": system_name,
            "trial": trial,
            "outcome": outcome,
            "error": f"{type(e).__name__}: {e}",
            "p_final": 0.5,
            "brier": 0.25,
            "log_loss": log_loss(0.5, outcome),
            "correct": 0,
        }
    result["trial"] = trial
    return score_result(result, outcome)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--systems", type=str, nargs="*", default=list(SYSTEMS.keys()))
    parser.add_argument("--tasks", type=str, nargs="*", default=None,
                        help="Optional list of task IDs (e.g. T1 T2). Default: all.")
    parser.add_argument("--results-dir", type=str, default=str(ROOT / "results"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    tasks_dir = ROOT / "tasks"
    task_files = sorted(tasks_dir.glob("T*.json"))
    if args.tasks:
        wanted = set(args.tasks)
        task_files = [p for p in task_files if p.stem in wanted]
    tasks = [load_task(p) for p in task_files]

    for system_name in args.systems:
        if system_name not in SYSTEMS:
            print(f"WARN: unknown system '{system_name}', skipping")
            continue
        runner, deterministic = SYSTEMS[system_name]
        n_trials = 1 if deterministic else args.trials

        for task in tasks:
            outcome = get_outcome(task)
            for trial in range(1, n_trials + 1):
                out = output_path(results_dir, system_name, task["task_id"], trial)
                if out.exists() and not args.overwrite:
                    print(f"[skip] {out.name}")
                    continue
                ts = datetime.now(timezone.utc).isoformat()
                print(f"[run ] {ts}  {system_name:15s}  {task['task_id']}  trial={trial}")
                result = run_single(system_name, runner, task, outcome, trial)
                with out.open("w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, default=str)
                p = result.get("p_final", 0.5)
                br = result.get("brier", 0.25)
                ok = "OK" if "error" not in result else "ERR"
                print(f"        -> p={p:.3f} y={outcome} brier={br:.3f}  ({ok})")

    print("\nDone.")


if __name__ == "__main__":
    main()
