#!/usr/bin/env python3
"""Summarize current AAAI experiment execution status from generated artifacts.

This report is intentionally artifact-only. It does not run inference and it
does not treat command scripts as completed experiments.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BENCHMARKS = ["v14", "v15", "v1k_clean"]


@dataclass
class StatusRow:
    group: str
    benchmark: str
    status: str
    path: str
    n: str
    baseline: str
    method_score: str
    delta: str
    fixes: str
    breaks: str
    net: str
    notes: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_json(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    matches = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def rel(path: Path | None, root: Path) -> str:
    if path is None:
        return "-"
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def oracle_fix_count(data: dict[str, Any], threshold: float = 1.0) -> tuple[int, int, int]:
    """Return oracle fixes, breaks, and net relative to baseline rows.

    Oracle selection should never break a baseline-correct row if it may choose
    baseline, but this computes it explicitly from per-sample scores.
    """

    fixes = 0
    breaks = 0
    for row in data.get("per_sample", []):
        scores = row.get("scores", {})
        baseline = float(scores.get("baseline", 0.0))
        non_baseline_scores = [
            float(score)
            for name, score in scores.items()
            if name not in {"baseline", "always_all", "oracle"}
        ]
        oracle = max([baseline, *non_baseline_scores]) if non_baseline_scores else baseline
        if oracle >= threshold and baseline < threshold:
            fixes += 1
        elif baseline >= threshold and oracle < threshold:
            breaks += 1
    return fixes, breaks, fixes - breaks


def summarize_current_pool(root: Path, benchmark: str) -> StatusRow:
    path = latest_json(root / "experiments/reports", f"aaai_{benchmark}_current_pool_*.json")
    if path is None:
        return StatusRow(
            "current-pool oracle",
            benchmark,
            "MISSING",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "Run experiments/reports/aaai_main_experiment_commands.sh.",
        )
    data = load_json(path)
    config_results = data.get("config_results", {})
    baseline = config_results.get("baseline", {}).get("overall")
    oracle = data.get("oracle", {}).get("overall")
    fixes, breaks, net = oracle_fix_count(data)
    notes = "oracle>baseline" if baseline is not None and oracle is not None and oracle > baseline else "needs review"
    return StatusRow(
        "current-pool oracle",
        benchmark,
        "DONE",
        rel(path, root),
        fmt(data.get("total_prompts")),
        fmt(baseline),
        fmt(oracle),
        fmt((oracle - baseline) if baseline is not None and oracle is not None else None),
        fmt(fixes),
        fmt(breaks),
        fmt(net),
        notes,
    )


def summarize_router(root: Path, benchmark: str) -> StatusRow:
    router_dir = root / "experiments/reports/v12_router"
    path = latest_json(router_dir, f"aaai_{benchmark}_current_pool_allow_core_nolog_cv*_crossval.json")
    if path is None:
        return StatusRow(
            "strict-CV router",
            benchmark,
            "MISSING",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "Generated after each current-pool report by aaai_main_experiment_commands.sh.",
        )
    summary = load_json(path).get("summary", {})
    breaks = int(summary.get("breaks", 0))
    fixes = int(summary.get("fixes", 0))
    delta = float(summary.get("delta", 0.0))
    status = "PASS" if delta > 0 and fixes > 0 and breaks == 0 else "REVIEW"
    return StatusRow(
        "strict-CV router",
        benchmark,
        status,
        rel(path, root),
        fmt(summary.get("total_eval_count")),
        fmt(summary.get("baseline")),
        fmt(summary.get("overall")),
        fmt(delta),
        fmt(fixes),
        fmt(breaks),
        fmt(fixes - breaks),
        "positive zero-break router" if status == "PASS" else "router needs inspection",
    )


def summarize_prompt_only(root: Path, benchmark: str) -> StatusRow:
    path = latest_json(root / "experiments/reports/prompt_only", f"prompt_only_*_{benchmark}_*.json")
    if path is None:
        return StatusRow(
            "prompt-only baseline",
            benchmark,
            "MISSING",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "Run experiments/reports/external_baseline_commands.sh.",
        )
    summary = load_json(path).get("summary", {})
    return StatusRow(
        "prompt-only baseline",
        benchmark,
        "DONE",
        rel(path, root),
        fmt(summary.get("total_prompts")),
        fmt(summary.get("baseline")),
        fmt(summary.get("prompted")),
        fmt(summary.get("delta")),
        fmt(summary.get("fixes")),
        fmt(summary.get("breaks")),
        fmt(summary.get("net")),
        f"policy={summary.get('prompt_policy', '-')}",
    )


def summarize_lora(root: Path, benchmark: str) -> StatusRow:
    path = latest_json(root / "experiments/reports/lora_baseline", f"lora_*_{benchmark}_*.json")
    if path is None:
        return StatusRow(
            "standard LoRA baseline",
            benchmark,
            "MISSING",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "Install .[peft], then run experiments/reports/lora_baseline_commands.sh.",
        )
    summary = load_json(path).get("summary", {})
    return StatusRow(
        "standard LoRA baseline",
        benchmark,
        "DONE",
        rel(path, root),
        fmt(summary.get("total_prompts")),
        fmt(summary.get("baseline")),
        fmt(summary.get("lora")),
        fmt(summary.get("delta")),
        fmt(summary.get("fixes")),
        fmt(summary.get("breaks")),
        fmt(summary.get("net")),
        f"rank={summary.get('rank', '-')}, train={summary.get('train_samples', '-')}",
    )


def build_rows(root: Path) -> list[StatusRow]:
    rows: list[StatusRow] = []
    for benchmark in BENCHMARKS:
        rows.append(summarize_current_pool(root, benchmark))
        rows.append(summarize_router(root, benchmark))
        rows.append(summarize_prompt_only(root, benchmark))
        rows.append(summarize_lora(root, benchmark))
    return rows


def overall_status(rows: list[StatusRow]) -> str:
    missing = [row for row in rows if row.status == "MISSING"]
    review = [row for row in rows if row.status == "REVIEW"]
    if missing:
        return "INCOMPLETE"
    if review:
        return "NEEDS REVIEW"
    return "READY FOR GATE CHECK"


def make_markdown(rows: list[StatusRow]) -> str:
    status = overall_status(rows)
    lines = [
        "# BitDPM AAAI Experiment Status",
        "",
        f"Overall execution status: **{status}**",
        "",
        "This report summarizes current experiment outputs only. Command scripts are",
        "listed as next actions when matching result JSON files are missing.",
        "",
        "| Group | Benchmark | Status | N | Baseline | Method/Oracle | Delta | Fixes | Breaks | Net | Latest Artifact | Notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.group} | {row.benchmark} | **{row.status}** | {row.n} | "
            f"{row.baseline} | {row.method_score} | {row.delta} | {row.fixes} | "
            f"{row.breaks} | {row.net} | `{row.path}` | {row.notes} |"
        )
    lines.extend(
        [
            "",
            "## Immediate Commands",
            "",
            "Run these only if the corresponding rows are still `MISSING`:",
            "",
            "```bash",
            "bash experiments/reports/aaai_main_experiment_commands.sh",
            "bash experiments/reports/external_baseline_commands.sh",
            "pip install -e '.[peft]'",
            "bash experiments/reports/lora_baseline_commands.sh",
            "python scripts/build_paper_package.py",
            "```",
            "",
            "## Interpretation",
            "",
            "- `DONE` means the expected artifact exists and was summarized.",
            "- `PASS` means the strict-CV router artifact exists and has positive delta, fixes>0, and zero breaks.",
            "- `MISSING` means no matching result JSON exists yet.",
            "- `REVIEW` means an artifact exists but does not satisfy the conservative status rule.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize BitDPM AAAI experiment status.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_aaai_experiment_status.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/bitdpm_aaai_experiment_status.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    rows = build_rows(root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(make_markdown(rows), encoding="utf-8")
    args.json_out.write_text(json.dumps([asdict(row) for row in rows], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    print(f"Overall execution status: {overall_status(rows)}")


if __name__ == "__main__":
    main()
