"""Decide next BitDPM experiment actions from v32/v33 result JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_runs(paths: list[str]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        for row in data:
            if isinstance(row, dict) and "metadata" in row and "summary" in row:
                row = dict(row)
                row["_source"] = str(path)
                runs.append(row)
    return runs


def score_run(row: dict[str, Any]) -> tuple[int, float, int, int]:
    sm = row["summary"]
    return (
        int(sm.get("net", 0)),
        float(sm.get("routed", 0.0)),
        -int(sm.get("breaks", 0)),
        int(sm.get("fixes", 0)),
    )


def best(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not runs:
        return None
    return sorted(runs, key=score_run, reverse=True)[0]


def is_core_repro(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    sm = row["summary"]
    return (
        row["metadata"].get("benchmark_set") == "core"
        and float(sm.get("routed", 0.0)) >= 0.95
        and int(sm.get("fixes", 0)) >= 6
        and int(sm.get("breaks", 0)) == 0
    )


def is_strong_transfer(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    sm = row["summary"]
    return (
        row["metadata"].get("benchmark_set") in {"v08", "v14", "v15"}
        and int(sm.get("net", 0)) > 0
        and int(sm.get("breaks", 0)) == 0
    )


def is_partial_transfer(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    sm = row["summary"]
    return row["metadata"].get("benchmark_set") in {"v08", "v14", "v15"} and int(sm.get("net", 0)) > 0


def run_line(row: dict[str, Any] | None) -> str:
    if not row:
        return "none"
    md = row["metadata"]
    sm = row["summary"]
    block = md.get("block", {}).get("block_id", "?")
    return (
        f"{md.get('benchmark_set')} block={block} router={md.get('router')} scale={md.get('scale')} "
        f"score={float(sm.get('baseline', 0)):.3f}->{float(sm.get('routed', 0)):.3f} "
        f"fixes={sm.get('fixes')} breaks={sm.get('breaks')} net={sm.get('net')} "
        f"path={md.get('block_path')}"
    )


def make_decision(runs: list[dict[str, Any]]) -> str:
    core = best([r for r in runs if r["metadata"].get("benchmark_set") == "core"])
    transfers = [r for r in runs if r["metadata"].get("benchmark_set") in {"v08", "v14", "v15"}]
    transfer = best(transfers)

    lines = ["# BitDPM v32/v33 Next-Step Decision", ""]
    lines.extend(["## Best Runs", "", f"- Core: {run_line(core)}", f"- Transfer: {run_line(transfer)}", ""])

    core_ok = is_core_repro(core)
    strong_transfer = is_strong_transfer(transfer)
    partial_transfer = is_partial_transfer(transfer)

    if core_ok and strong_transfer:
        lines.extend(
            [
                "## Decision: FREEZE_AND_SCALE",
                "",
                "Core reproduces v31 and at least one larger benchmark has positive zero-break transfer.",
                "",
                "Next actions:",
                "1. Freeze the block path and sha256 as the current best artifact.",
                "2. Run v14 300-sample validation with the same feature/router setting.",
                "3. Generate a v32/v33 technical report with core + transfer evidence.",
            ]
        )
    elif core_ok and partial_transfer:
        lines.extend(
            [
                "## Decision: MINE_SAFETY_RULES",
                "",
                "Core reproduces v31 and larger benchmark transfer is positive, but breaks remain.",
                "",
                "Next actions:",
                "1. Run `scripts/mine_v33_safety_router.py` on the result JSON.",
                "2. Fresh-validate zero-break mined feature rules on v08 and v15.",
                "3. Prefer lower-recall zero-break rules over higher-recall unsafe rules.",
            ]
        )
    elif core_ok:
        lines.extend(
            [
                "## Decision: ROUTER_OVERFIT",
                "",
                "Core reproduces v31, but transfer is missing or non-positive.",
                "",
                "Next actions:",
                "1. Treat the current hand router as core-overfit.",
                "2. Use v32 per-sample outputs to mine validation-safe feature rules.",
                "3. Do not claim broad improvement until v08/v15 transfer is positive.",
            ]
        )
    elif core:
        lines.extend(
            [
                "## Decision: RECOVER_V31_ARTIFACT",
                "",
                "A core result exists, but it does not reproduce the v31 target.",
                "",
                "Next actions:",
                "1. Continue candidate block scan or expanded candidate scan.",
                "2. If no saved block matches v31, rerun the v28-v31 training path and save the block.",
                "3. Do not move to transfer validation until core reproduction is recovered.",
            ]
        )
    else:
        lines.extend(
            [
                "## Decision: RUN_CORE_SCAN",
                "",
                "No core result JSON was found.",
                "",
                "Next actions:",
                "1. Run the v32 core candidate scan with `--output-path` and `--resume`.",
                "2. Summarize zero-break positive-net candidates.",
                "3. Only then proceed to v08/v15 validation.",
            ]
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide next BitDPM experiment step from v32/v33 JSON")
    parser.add_argument("json_files", nargs="+")
    parser.add_argument("--md-out", default="experiments/reports/bitdpm_next_decision.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = load_runs(args.json_files)
    report = make_decision(runs)
    out = Path(args.md_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
