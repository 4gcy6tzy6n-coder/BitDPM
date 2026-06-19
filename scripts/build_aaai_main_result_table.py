#!/usr/bin/env python3
"""Build the AAAI main-result table from completed validation artifacts.

The table is intentionally conservative: missing experiment outputs remain
`PENDING` instead of being inferred from command files or older historical
reports.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BENCHMARKS = ["v14", "v15", "v1k_clean"]


@dataclass
class MainResultRow:
    benchmark: str
    status: str
    n: str
    baseline: str
    best_fixed: str
    best_fixed_config: str
    oracle: str
    oracle_gain: str
    oracle_coverage: str
    always_all: str
    router: str
    router_delta: str
    router_fixes: str
    router_breaks: str
    prompt_only: str
    prompt_net: str
    lora: str
    lora_net: str
    current_pool_path: str
    router_path: str
    prompt_path: str
    lora_path: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_json(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    matches = sorted(directory.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def rel(path: Path | None, root: Path) -> str:
    if path is None:
        return "-"
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "PENDING"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def coverage_from_selection(selection: dict[str, Any]) -> int | None:
    if not selection:
        return None
    return sum(int(count) for name, count in selection.items() if name != "baseline")


def best_fixed(data: dict[str, Any]) -> tuple[str, float | None]:
    config_results = data.get("config_results", {})
    baseline = config_results.get("baseline", {}).get("overall")
    best_name = "baseline"
    best_score = baseline
    for name, result in config_results.items():
        if name in {"baseline", "always_all"}:
            continue
        score = result.get("overall")
        if score is not None and (best_score is None or score > best_score):
            best_name = name
            best_score = score
    return best_name, best_score


def summarize_benchmark(root: Path, benchmark: str) -> MainResultRow:
    reports = root / "experiments/reports"
    current_path = latest_json(reports, f"aaai_{benchmark}_current_pool_*.json")
    router_path = latest_json(
        reports / "v12_router",
        f"aaai_{benchmark}_current_pool_allow_core_nolog_cv*_crossval.json",
    )
    prompt_path = latest_json(reports / "prompt_only", f"prompt_only_*_{benchmark}_*.json")
    lora_path = latest_json(reports / "lora_baseline", f"lora_*_{benchmark}_*.json")

    n: int | None = None
    baseline: float | None = None
    best_fixed_name = "PENDING"
    best_fixed_score: float | None = None
    oracle: float | None = None
    oracle_gain: float | None = None
    oracle_coverage: str = "PENDING"
    always_all: float | None = None
    if current_path is not None:
        current = load_json(current_path)
        n = current.get("total_prompts")
        config_results = current.get("config_results", {})
        baseline = config_results.get("baseline", {}).get("overall")
        oracle = current.get("oracle", {}).get("overall")
        oracle_gain = (oracle - baseline) if oracle is not None and baseline is not None else None
        best_fixed_name, best_fixed_score = best_fixed(current)
        coverage = coverage_from_selection(current.get("selection_frequency", {}))
        oracle_coverage = f"{coverage}/{n}" if coverage is not None and n else "PENDING"
        always_all = config_results.get("always_all", {}).get("overall")

    router = router_delta = router_fixes = router_breaks = None
    if router_path is not None:
        summary = load_json(router_path).get("summary", {})
        router = summary.get("overall")
        router_delta = summary.get("delta")
        router_fixes = summary.get("fixes")
        router_breaks = summary.get("breaks")

    prompt_only = prompt_net = None
    if prompt_path is not None:
        summary = load_json(prompt_path).get("summary", {})
        prompt_only = summary.get("prompted")
        prompt_net = summary.get("net")

    lora = lora_net = None
    if lora_path is not None:
        summary = load_json(lora_path).get("summary", {})
        lora = summary.get("lora")
        lora_net = summary.get("net")

    required_paths = [current_path, router_path, prompt_path, lora_path]
    if all(path is not None for path in required_paths):
        status = "COMPLETE"
    elif any(path is not None for path in required_paths):
        status = "PARTIAL"
    else:
        status = "PENDING"

    return MainResultRow(
        benchmark=benchmark,
        status=status,
        n=fmt(n, 0),
        baseline=fmt(baseline),
        best_fixed=fmt(best_fixed_score),
        best_fixed_config=best_fixed_name,
        oracle=fmt(oracle),
        oracle_gain=fmt(oracle_gain),
        oracle_coverage=oracle_coverage,
        always_all=fmt(always_all),
        router=fmt(router),
        router_delta=fmt(router_delta),
        router_fixes=fmt(router_fixes),
        router_breaks=fmt(router_breaks),
        prompt_only=fmt(prompt_only),
        prompt_net=fmt(prompt_net),
        lora=fmt(lora),
        lora_net=fmt(lora_net),
        current_pool_path=rel(current_path, root),
        router_path=rel(router_path, root),
        prompt_path=rel(prompt_path, root),
        lora_path=rel(lora_path, root),
    )


def make_markdown(rows: list[MainResultRow]) -> str:
    lines = [
        "# BitDPM AAAI Main Result Table",
        "",
        "This table is generated from completed AAAI validation artifacts. Missing",
        "rows remain `PENDING`; command scripts are not counted as evidence.",
        "",
        "## Main Validation Matrix",
        "",
        "| Benchmark | Status | N | Baseline | Best Fixed | Best Config | Oracle | Oracle Gain | Coverage | Always-All | Strict-CV Router | Router Delta | Fixes | Breaks | Prompt-Only | Prompt Net | LoRA | LoRA Net |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.benchmark} | **{row.status}** | {row.n} | {row.baseline} | "
            f"{row.best_fixed} | {row.best_fixed_config} | {row.oracle} | "
            f"{row.oracle_gain} | {row.oracle_coverage} | {row.always_all} | "
            f"{row.router} | {row.router_delta} | {row.router_fixes} | "
            f"{row.router_breaks} | {row.prompt_only} | {row.prompt_net} | "
            f"{row.lora} | {row.lora_net} |"
        )

    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
            "| Benchmark | Current Pool | Strict-CV Router | Prompt-Only | LoRA |",
            "|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.benchmark} | `{row.current_pool_path}` | `{row.router_path}` | "
            f"`{row.prompt_path}` | `{row.lora_path}` |"
        )

    lines.extend(
        [
            "",
            "## Claim Rule",
            "",
            "- Use this table for paper main-result claims only after the relevant rows are `COMPLETE`.",
            "- v1k_clean must have a completed current-pool oracle row before making paper-scale validation claims.",
            "- Prompt-only and LoRA rows are external baselines; missing rows keep the AAAI gate open.",
            "- Historical v31 results are intentionally excluded from this table until provenance is recovered.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build BitDPM AAAI main-result table.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/paper_tables/bitdpm_aaai_main_results.md"))
    parser.add_argument("--json-out", type=Path, default=Path("experiments/reports/paper_tables/bitdpm_aaai_main_results.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    rows = [summarize_benchmark(root, benchmark) for benchmark in BENCHMARKS]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(make_markdown(rows), encoding="utf-8")
    args.json_out.write_text(json.dumps([asdict(row) for row in rows], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
