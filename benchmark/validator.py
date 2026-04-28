"""Validate that all task JSON files conform to the POPCAST schema."""
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "task_id": str,
    "domain": str,
    "difficulty": str,
    "title": str,
    "decision_timestamp": str,
    "resolution_timestamp": str,
    "resolution_criteria": str,
    "outcome": int,
    "price_history": list,
    "volatility_proxy": (int, float),
    "liquidity_proxy": (int, float),
    "context_hint": str,
}

VALID_DIFFICULTY = {"easy", "medium", "hard"}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"{path.name}: failed to parse JSON: {e}"]

    for field, ftype in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"{path.name}: missing field '{field}'")
            continue
        if not isinstance(data[field], ftype):
            errors.append(
                f"{path.name}: field '{field}' has type {type(data[field]).__name__}, expected {ftype}"
            )

    if data.get("outcome") not in (0, 1):
        errors.append(f"{path.name}: outcome must be 0 or 1")
    if data.get("difficulty") not in VALID_DIFFICULTY:
        errors.append(f"{path.name}: difficulty must be one of {VALID_DIFFICULTY}")
    return errors


def main():
    tasks_dir = Path(__file__).resolve().parents[1] / "tasks"
    files = sorted(tasks_dir.glob("T*.json"))
    if not files:
        print(f"No task files found in {tasks_dir}")
        sys.exit(1)
    all_errors: list[str] = []
    for fp in files:
        all_errors.extend(validate_file(fp))
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        sys.exit(1)
    print(f"All {len(files)} task files validated successfully.")


if __name__ == "__main__":
    main()
