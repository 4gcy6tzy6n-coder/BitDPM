#!/usr/bin/env python3
"""Build paper-facing BitDPM result tables from existing reports.

This script does not run models. It consolidates completed JSON reports into
compact Markdown/JSON tables that are safe to cite in reports or paper drafts.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


DEFAULT_REPORTS = [
    ("v08 rank8 det", "experiments/reports/v08_rank8_scale060_v08_det_20260607_171409.json"),
    ("v08 rank8 stable", "experiments/reports/v08_rank8_scale075_v08_stable_sampling_20260607_172636.json"),
    ("v08 rank16 det", "experiments/reports/v08_rank16_scale060_v08_det_20260607_175023.json"),
    ("v08 rank16 stable", "experiments/reports/v08_rank16_scale075_v08_stable_sampling_20260607_180805.json"),
    ("v08 hybrid det", "experiments/reports/v08_rank16_hybridscale_v08_det_20260607_191238.json"),
    ("v08 hybrid stable", "experiments/reports/v08_rank16_hybridscale_v08_stable_sampling_20260607_192543.json"),
    ("v09 repair stable", "experiments/reports/v09_repair_rank16_scale075_v08_stable_sampling_20260607_200504.json"),
    ("v09b + power_log", "experiments/reports/v09b_hybrid_plus_powerlog_stable_sampling_20260607_203029.json"),
    ("v09b + factual", "experiments/reports/v09b_hybrid_plus_factual_stable_sampling_20260607_204440.json"),
    ("v09b + both", "experiments/reports/v09b_hybrid_plus_both_stable_sampling_20260607_210321.json"),
    ("v10 admitted", "experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json"),
    ("v11 merged candidates", "experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json"),
    ("v14 pilot v10 admitted", "experiments/reports/v14_pilot_v10_admitted_20260608_064051.json"),
    ("v14 pilot v11 admitted", "experiments/reports/v14_pilot_v11_admitted_20260608_070120.json"),
    ("v14 full v11 admitted", "experiments/reports/v14_full_v11_admitted_20260608_093845.json"),
    ("v15 router validation v11 admitted", "experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json"),
    ("v14 300-sample", "experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json"),
]

ROUTER_REPORTS = [
    ("v12 rule router", "experiments/reports/v12_router/smoke_v12_rule_router_rule_router.json", "rule_router"),
    ("v12 utility full-report", "experiments/reports/v12_router/smoke_v12_utility_router_safe_specific_utility_router.json", "utility_router"),
    ("v12 utility strict CV", "experiments/reports/v12_router/smoke_v12_utility_router_strict_cv_specific_crossval.json", "crossval"),
    ("v11 pool utility full-report", "experiments/reports/v12_router/v11_merged_utility_router_safe_specific_utility_router.json", "utility_router"),
    ("v11 pool utility strict CV", "experiments/reports/v12_router/v11_merged_utility_router_strict_cv_specific_crossval.json", "crossval"),
    ("v14 pilot v10 utility full-report", "experiments/reports/v12_router/v14_pilot_v10_utility_router_safe_utility_router.json", "utility_router"),
    ("v14 pilot v10 utility strict CV", "experiments/reports/v12_router/v14_pilot_v10_utility_router_strict_cv_crossval.json", "crossval"),
    ("v14 pilot v11 utility full-report", "experiments/reports/v12_router/v14_pilot_v11_utility_router_safe_utility_router.json", "utility_router"),
    ("v14 pilot v11 utility strict CV", "experiments/reports/v12_router/v14_pilot_v11_utility_router_strict_cv_crossval.json", "crossval"),
    ("v14 full v11 utility full-report", "experiments/reports/v12_router/v14_full_v11_utility_router_safe_utility_router.json", "utility_router"),
    ("v14 full v11 utility strict CV", "experiments/reports/v12_router/v14_full_v11_utility_router_strict_cv_crossval.json", "crossval"),
    ("v14 full v11 allow-core utility full-report", "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_safe_utility_router.json", "utility_router"),
    ("v14 full v11 allow-core utility strict CV", "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_cv_crossval.json", "crossval"),
    ("v14 full v11 allow-core-no-log utility full-report", "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_safe_utility_router.json", "utility_router"),
    ("v14 full v11 allow-core-no-log utility strict CV", "experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_cv_crossval.json", "crossval"),
    ("v15 allow-core utility full-report", "experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_safe_utility_router.json", "utility_router"),
    ("v15 allow-core utility strict CV", "experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_cv_crossval.json", "crossval"),
    ("v15 allow-core-no-log utility full-report", "experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_nolog_safe_utility_router.json", "utility_router"),
    ("v15 allow-core-no-log utility strict CV", "experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_nolog_cv_crossval.json", "crossval"),
    ("v15 conjunction utility full-report", "experiments/reports/v12_router/v15_router_validation_v11_admitted_conj_safe_utility_router.json", "utility_router"),
    ("v15 conjunction utility strict CV", "experiments/reports/v12_router/v15_router_validation_v11_admitted_conj_cv_crossval.json", "crossval"),
]


def load_json(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def coverage_from_selection(selection: dict[str, int]) -> int:
    return sum(count for cfg, count in selection.items() if cfg != "baseline")


def best_fixed(data: dict[str, Any]) -> tuple[str, float]:
    baseline = data["config_results"].get("baseline", {}).get("overall", 0.0)
    best_name = "baseline"
    best_score = baseline
    for cfg, agg in data["config_results"].items():
        if cfg in ("baseline", "always_all"):
            continue
        score = agg["overall"]
        if score > best_score:
            best_name = cfg
            best_score = score
    return best_name, best_score


def report_row(label: str, path: str, data: dict[str, Any]) -> dict[str, Any]:
    baseline = data["config_results"]["baseline"]["overall"]
    oracle = data["oracle"]["overall"]
    selection = data.get("selection_frequency", {})
    best_name, best_score = best_fixed(data)
    always_all = data["config_results"].get("always_all", {}).get("overall")
    return {
        "label": label,
        "path": path,
        "benchmark": data.get("benchmark_set", ""),
        "n": data.get("total_prompts"),
        "baseline": baseline,
        "oracle": oracle,
        "oracle_gain": oracle - baseline,
        "coverage": coverage_from_selection(selection),
        "best_fixed": best_score,
        "best_fixed_config": best_name,
        "always_all": always_all,
        "selection_frequency": selection,
    }


def router_row(label: str, path: str, kind: str, data: dict[str, Any]) -> dict[str, Any]:
    if kind == "crossval":
        summary = data["summary"]
        return {
            "label": label,
            "path": path,
            "kind": kind,
            "router": summary["overall"],
            "baseline": summary["baseline"],
            "gain": summary["delta"],
            "fixes": summary["fixes"],
            "breaks": summary["breaks"],
            "notes": "held-out cross-validation",
        }
    if kind == "utility_router":
        result = data["eval"]
        return {
            "label": label,
            "path": path,
            "kind": kind,
            "router": result["overall"],
            "baseline": result["baseline"],
            "gain": result["delta"],
            "fixes": result["fixes"],
            "breaks": result["breaks"],
            "notes": "full-report safety-filter prototype",
        }
    return {
        "label": label,
        "path": path,
        "kind": kind,
        "router": data["overall"],
        "baseline": data["baseline"],
        "gain": data["delta"],
        "fixes": data["fixes"],
        "breaks": data["breaks"],
        "notes": "hand-authored conservative rules",
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_markdown(rows: list[dict[str, Any]], router_rows: list[dict[str, Any]], output: str):
    lines = [
        "# BitDPM Paper Result Tables",
        "",
        "## Block Pool Results",
        "",
        "| Setting | Benchmark | N | Baseline | Best Fixed | Best Config | Oracle | Gain | Coverage | Always-All |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['benchmark']} | {row['n']} | {fmt(row['baseline'])} | "
            f"{fmt(row['best_fixed'])} | {row['best_fixed_config']} | {fmt(row['oracle'])} | "
            f"{fmt(row['oracle_gain'])} | {row['coverage']}/{row['n']} | {fmt(row['always_all'])} |"
        )

    lines.extend([
        "",
        "## Router Results",
        "",
        "| Setting | Router | Baseline | Gain | Fixes | Breaks | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in router_rows:
        lines.append(
            f"| {row['label']} | {fmt(row['router'])} | {fmt(row['baseline'])} | "
            f"{fmt(row['gain'])} | {row['fixes']} | {row['breaks']} | {row['notes']} |"
        )

    lines.extend([
        "",
        "## Current Safe Claims",
        "",
        "- v11 current best oracle pool: `v10 admitted + v11_stats_number_theory`.",
        "- Current best oracle result on v08 100-sample stable sampling: `0.900` with coverage `7/100`.",
        "- v14 pilot supports the same direction: v11 admitted improves oracle from `0.950` to `0.983` and coverage from `5/60` to `7/60` over v10.",
        "- v14 full 300-sample validation gives oracle `0.903` with coverage `19/300` over baseline `0.840`.",
        "- v14 full-report utility router reaches `0.873` with `10` fixes and `0` breaks; strict CV reaches `0.850` over baseline `0.840` with `5` fixes and `2` breaks.",
        "- A conservative allow-core router removes held-out breaks: strict CV `0.857` over baseline `0.840`, with `5` fixes and `0` breaks.",
        "- v15 router validation gives oracle `0.742` over baseline `0.442`, but shows `has_log` is unsafe under strict CV.",
        "- Current safest deployable router is allow-core-no-log: `has_multiplication`, `has_distance`, `has_coordinate`, and `has_mean`.",
        "- Allow-core-no-log keeps v14 strict CV at `0.857` with `0` breaks and improves v15 strict CV to `0.500` over baseline `0.442` with `7` fixes and `0` breaks.",
        "- v10 remains the safer fixed/deployable baseline because v11_stats_number_theory is damage-prone under fixed activation.",
        "- Always-All remains a negative control and collapses for the high-scale admitted pool.",
        "- Full-report utility routers recover several oracle fixes; unrestricted strict CV has break cases, while allow-core-no-log strict CV is zero-break but still modest.",
        "- Deployable router generalization is promising but not yet strong enough for an unqualified claim.",
        "",
    ])

    with open(output, "w") as f:
        f.write("\n".join(lines))


def run(args):
    rows = []
    for label, path in DEFAULT_REPORTS:
        data = load_json(path)
        if data is None:
            continue
        rows.append(report_row(label, path, data))

    routers = []
    for label, path, kind in ROUTER_REPORTS:
        data = load_json(path)
        if data is None:
            continue
        routers.append(router_row(label, path, kind, data))

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}.md")
    with open(json_path, "w") as f:
        json.dump({"block_pool_results": rows, "router_results": routers}, f, indent=2, ensure_ascii=False)
    write_markdown(rows, routers, md_path)
    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Build BitDPM paper result tables")
    parser.add_argument("--output-dir", default="experiments/reports/paper_tables")
    parser.add_argument("--tag", default="bitdpm_current_results")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
