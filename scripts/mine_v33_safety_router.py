"""Mine safety-router rules from BitDPM v32 per-sample results.

The v31/v32 router is intentionally conservative and hand-written. This script
turns v32 result JSON into candidate allow/deny rules by scoring prompt features
against observed fixes and breaks.

Goal: prefer high-precision activation rules. A useful rule should capture
fixes while avoiding baseline-correct samples that the block breaks.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Feature:
    name: str
    value: bool


def load_runs(paths: list[str]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        for row in data:
            if "metadata" in row and "samples" in row:
                row = dict(row)
                row["_source"] = str(path)
                runs.append(row)
    return runs


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def prompt_features(category: str, prompt: str) -> dict[str, bool]:
    p = prompt.lower()
    return {
        "cat_commonsense": category == "commonsense",
        "cat_math": category == "math",
        "cat_code": category == "code",
        "cat_chinese": category == "chinese",
        "cat_reasoning": category == "reasoning",
        "has_digit": bool(re.search(r"\d", prompt)),
        "has_percent": "%" in prompt or "percent" in p,
        "has_power": "^" in prompt or "power" in p,
        "has_sqrt": "square root" in p or "sqrt" in p,
        "has_log": "log" in p,
        "has_coordinate": bool(re.search(r"\(\s*-?\d+\s*,\s*-?\d+\s*\)", prompt)),
        "has_distance": "distance" in p,
        "has_equation": bool(re.search(r"\bx\b", p)) or "=" in prompt or "solve" in p,
        "has_time": "hour" in p or "minute" in p or "second" in p,
        "has_speed": "speed" in p or "km/h" in p,
        "has_constant_risk": any(term in p for term in ["speed of light", "avogadro", "gravity", "boiling point"]),
        "has_biology_risk": any(term in p for term in ["plants absorb", "gas do plants", "atmosphere"]),
        "is_chinese_text": has_cjk(prompt),
        "asks_write": "write" in p or "写" in prompt,
        "asks_explain": "explain" in p or "解释" in prompt,
        "short_answer_math": category == "math" and len(prompt.split()) <= 12,
        "short_answer_commonsense": category == "commonsense" and len(prompt.split()) <= 12,
    }


def sample_label(sample: dict[str, Any]) -> str:
    delta = float(sample.get("delta", 0.0))
    if delta > 0:
        return "fix"
    if delta < 0:
        return "break"
    return "same"


def run_id(run: dict[str, Any]) -> str:
    md = run["metadata"]
    block = md.get("block", {}).get("block_id", "?")
    sha = str(md.get("block_sha256", ""))[:12] or "nohash"
    return f"{md.get('benchmark_set')}::{block}::{sha}::{md.get('router')}::scale={md.get('scale')}"


def score_feature(samples: list[dict[str, Any]], feature_name: str) -> dict[str, Any]:
    selected = []
    not_selected = []
    for sample in samples:
        feats = prompt_features(sample.get("category", ""), sample.get("prompt", ""))
        (selected if feats.get(feature_name, False) else not_selected).append(sample)

    fixes = sum(1 for s in selected if sample_label(s) == "fix")
    breaks = sum(1 for s in selected if sample_label(s) == "break")
    same = sum(1 for s in selected if sample_label(s) == "same")
    missed_fixes = sum(1 for s in not_selected if sample_label(s) == "fix")
    avoided_breaks = sum(1 for s in not_selected if sample_label(s) == "break")
    net = fixes - breaks
    precision = fixes / max(fixes + breaks, 1)
    recall = fixes / max(fixes + missed_fixes, 1)
    return {
        "feature": feature_name,
        "selected": len(selected),
        "fixes": fixes,
        "breaks": breaks,
        "same": same,
        "net": net,
        "precision": precision,
        "recall": recall,
        "missed_fixes": missed_fixes,
        "avoided_breaks": avoided_breaks,
    }


def score_conjunction(samples: list[dict[str, Any]], names: tuple[str, str]) -> dict[str, Any]:
    selected = []
    not_selected = []
    for sample in samples:
        feats = prompt_features(sample.get("category", ""), sample.get("prompt", ""))
        ok = feats.get(names[0], False) and feats.get(names[1], False)
        (selected if ok else not_selected).append(sample)
    fixes = sum(1 for s in selected if sample_label(s) == "fix")
    breaks = sum(1 for s in selected if sample_label(s) == "break")
    same = sum(1 for s in selected if sample_label(s) == "same")
    missed_fixes = sum(1 for s in not_selected if sample_label(s) == "fix")
    net = fixes - breaks
    precision = fixes / max(fixes + breaks, 1)
    recall = fixes / max(fixes + missed_fixes, 1)
    return {
        "feature": f"{names[0]} AND {names[1]}",
        "selected": len(selected),
        "fixes": fixes,
        "breaks": breaks,
        "same": same,
        "net": net,
        "precision": precision,
        "recall": recall,
        "missed_fixes": missed_fixes,
    }


def all_feature_names(samples: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for sample in samples:
        names.update(prompt_features(sample.get("category", ""), sample.get("prompt", "")).keys())
    return sorted(names)


def mine_rules_for_run(run: dict[str, Any], include_conjunctions: bool) -> dict[str, Any]:
    samples = run.get("samples", [])
    feature_names = all_feature_names(samples)
    rows = [score_feature(samples, name) for name in feature_names]
    if include_conjunctions:
        for i, left in enumerate(feature_names):
            for right in feature_names[i + 1 :]:
                rows.append(score_conjunction(samples, (left, right)))

    rows.sort(key=lambda r: (r["net"], r["precision"], r["fixes"], -r["breaks"]), reverse=True)
    zero_break = [r for r in rows if r["fixes"] > 0 and r["breaks"] == 0]
    deny = [r for r in rows if r["breaks"] > 0 and r["fixes"] == 0]
    deny.sort(key=lambda r: (r["breaks"], r["selected"]), reverse=True)

    labels = {label: sum(1 for s in samples if sample_label(s) == label) for label in ("fix", "break", "same")}
    return {
        "run_id": run_id(run),
        "metadata": run.get("metadata", {}),
        "summary": run.get("summary", {}),
        "labels": labels,
        "top_allow_rules": rows[:20],
        "zero_break_allow_rules": zero_break[:20],
        "deny_rules": deny[:20],
    }


def make_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# BitDPM v33 Safety Router Mining",
        "",
        "This report mines prompt-feature rules from v32 per-sample fixes/breaks.",
        "Rules are candidates only; validate them in a fresh held-out run before using them as paper evidence.",
        "",
    ]
    for result in results:
        md = result["metadata"]
        sm = result["summary"]
        lines.extend(
            [
                f"## {result['run_id']}",
                "",
                f"- Score: {sm.get('baseline', 0):.3f} -> {sm.get('routed', 0):.3f}",
                f"- Fixes / breaks / net: {sm.get('fixes', 0)} / {sm.get('breaks', 0)} / {sm.get('net', 0)}",
                f"- Block path: `{md.get('block_path', '?')}`",
                f"- Block sha256: `{md.get('block_sha256', '?')}`",
                "",
                "### Zero-Break Allow Candidates",
                "",
                "| Rule | Selected | Fixes | Breaks | Net | Precision | Recall |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in result["zero_break_allow_rules"][:10]:
            lines.append(
                f"| `{row['feature']}` | {row['selected']} | {row['fixes']} | {row['breaks']} | "
                f"{row['net']} | {row['precision']:.3f} | {row['recall']:.3f} |"
            )
        lines.extend(["", "### Deny Candidates", "", "| Rule | Selected | Fixes | Breaks | Avoided Breaks |", "|---|---:|---:|---:|---:|"])
        for row in result["deny_rules"][:10]:
            lines.append(
                f"| `{row['feature']}` | {row['selected']} | {row['fixes']} | {row['breaks']} | "
                f"{row.get('avoided_breaks', 0)} |"
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine v33 safety-router rules from v32 JSON")
    parser.add_argument("json_files", nargs="+")
    parser.add_argument("--include-conjunctions", action="store_true")
    parser.add_argument("--json-out", default="experiments/reports/v33_safety_router_mining.json")
    parser.add_argument("--md-out", default="experiments/reports/v33_safety_router_mining.md")
    parser.add_argument("--only-positive-net", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = load_runs(args.json_files)
    if args.only_positive_net:
        runs = [r for r in runs if r.get("summary", {}).get("net", 0) > 0]
    results = [mine_rules_for_run(run, args.include_conjunctions) for run in runs]
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(make_markdown(results), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
