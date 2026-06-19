#!/usr/bin/env python3
"""Build BitDPM block safety cards from eval and admission reports."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


def load_json(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def admission_rows(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    data = load_json(path)
    rows: dict[str, dict[str, Any]] = {}
    for row in data.get("rows", []):
        rows[row["block"]] = row
    return rows


def run(args):
    safety = load_json(args.safety_report)
    registry = load_json(args.registry) if args.registry else {}
    admissions = admission_rows(args.admission_report)
    block_scales = registry.get("block_scales", safety.get("report", {}).get("block_scales", {}))
    admitted = set(registry.get("configs", [])) - {"baseline", "always_all"}

    cards = []
    for row in safety["rows"]:
        block = row["block"]
        admission = admissions.get(block)
        if admission is not None:
            unique_fixes = admission.get("unique_fixes", row.get("unique_fixes", 0))
            overlap_fixes = admission.get("overlap_fixes", max(row.get("fixes", 0) - unique_fixes, 0))
            breaks = admission.get("breaks", row.get("breaks", 0))
            admitted_flag = block in admitted or bool(admission.get("admit"))
        else:
            unique_fixes = row.get("unique_fixes", 0)
            overlap_fixes = max(row.get("fixes", 0) - unique_fixes, 0)
            breaks = row.get("breaks", 0)
            admitted_flag = block in admitted

        if admitted_flag and breaks > 0:
            activation_mode = "single-only"
        elif admitted_flag:
            activation_mode = "can-compose-candidate"
        else:
            activation_mode = "rejected"

        cards.append({
            "block": block,
            "structure": args.structure,
            "rank": args.rank,
            "scale": block_scales.get(block),
            "fixed_score": row["fixed_score"],
            "score_delta": row["score_delta"],
            "fixes": row["fixes"],
            "unique_fixes": unique_fixes,
            "overlap_fixes": overlap_fixes,
            "breaks": breaks,
            "net_unique_utility": unique_fixes - breaks,
            "damage_rate": breaks / max(args.baseline_correct_count, 1),
            "admitted": admitted_flag,
            "activation_mode": activation_mode,
            "damaged_categories": row.get("damaged_categories", {}),
        })

    cards.sort(key=lambda c: (c["admitted"], c["unique_fixes"], c["net_unique_utility"]), reverse=True)

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, f"{args.tag}_safety_cards.json")
    md_path = os.path.join(args.output_dir, f"{args.tag}_safety_cards.md")
    with open(json_path, "w") as f:
        json.dump({"cards": cards}, f, indent=2, ensure_ascii=False)

    lines = [
        "# BitDPM v13 Block Safety Cards",
        "",
        f"- Safety report: `{args.safety_report}`",
        f"- Registry: `{args.registry or ''}`",
        "",
        "| Block | Rank | Scale | Fixed | Unique | Overlap | Breaks | Net Unique | Damage Rate | Admitted | Activation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for card in cards:
        scale = "" if card["scale"] is None else f"{card['scale']:.2f}"
        lines.append(
            f"| {card['block']} | {card['rank']} | {scale} | {card['fixed_score']:.3f} | "
            f"{card['unique_fixes']} | {card['overlap_fixes']} | {card['breaks']} | "
            f"{card['net_unique_utility']} | {card['damage_rate']:.3f} | "
            f"{'yes' if card['admitted'] else 'no'} | {card['activation_mode']} |"
        )

    lines.extend(["", "## Card Details", ""])
    for card in cards:
        lines.extend([
            f"### {card['block']}",
            f"- Structure: `{card['structure']}`",
            f"- Rank: `{card['rank']}`",
            f"- Scale: `{card['scale']}`",
            f"- Unique fixes: {card['unique_fixes']}",
            f"- Overlap fixes: {card['overlap_fixes']}",
            f"- Breaks: {card['breaks']}",
            f"- Activation mode: `{card['activation_mode']}`",
            f"- Damaged categories: `{card['damaged_categories']}`",
            "",
        ])

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Build BitDPM block safety cards")
    parser.add_argument("--safety-report", required=True)
    parser.add_argument("--admission-report", default="")
    parser.add_argument("--registry", default="")
    parser.add_argument("--output-dir", default="experiments/reports/v13_safety")
    parser.add_argument("--tag", default="v13")
    parser.add_argument("--structure", default="l22_l24_down")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--baseline-correct-count", type=int, default=83)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
