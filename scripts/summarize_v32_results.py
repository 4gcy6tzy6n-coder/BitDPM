"""Summarize BitDPM v32 router-validation JSON files.

The v32 runner can produce large per-sample JSON files. This script extracts
the ranked run table needed for quick experiment decisions and paper notes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_runs(paths: list[str]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        for row in data:
            if "metadata" not in row or "summary" not in row:
                continue
            row = dict(row)
            row["_source"] = str(path)
            runs.append(row)
    return runs


def sort_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        runs,
        key=lambda r: (
            r["summary"].get("net", 0),
            r["summary"].get("routed", 0.0),
            -r["summary"].get("breaks", 0),
            r["summary"].get("fixes", 0),
        ),
        reverse=True,
    )


def fmt_float(x: Any) -> str:
    return f"{float(x):.3f}"


def print_table(runs: list[dict[str, Any]], limit: int) -> None:
    print(make_table(runs, limit))


def make_table(runs: list[dict[str, Any]], limit: int) -> str:
    lines = [
        "| Rank | Benchmark | Block | SHA | Router | Scale | Baseline | Routed | Gain | Fixes | Breaks | Net | Active | Source |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for idx, row in enumerate(runs[:limit], start=1):
        md = row["metadata"]
        sm = row["summary"]
        block = md.get("block", {}).get("block_id", "?")
        sha = str(md.get("block_sha256", ""))[:12] or "?"
        gain = float(sm.get("routed", 0)) - float(sm.get("baseline", 0))
        lines.append(
            f"| {idx} | {md.get('benchmark_set', '?')} | `{block}` | `{sha}` | `{md.get('router', '?')}` | "
            f"{md.get('scale', '?')} | {fmt_float(sm.get('baseline', 0))} | "
            f"{fmt_float(sm.get('routed', 0))} | {gain:+.3f} | {sm.get('fixes', 0)} | "
            f"{sm.get('breaks', 0)} | {sm.get('net', 0)} | {sm.get('active', 0)} | "
            f"`{row['_source']}` |"
        )
    return "\n".join(lines)


def print_best(runs: list[dict[str, Any]]) -> None:
    if not runs:
        print("No valid runs found.")
        return
    best = runs[0]
    md = best["metadata"]
    sm = best["summary"]
    block = md.get("block", {}).get("block_id", "?")
    print("\nBest run:")
    print(f"- Source: `{best['_source']}`")
    print(f"- Benchmark: `{md.get('benchmark_set', '?')}`")
    print(f"- Block: `{block}`")
    print(f"- Block path: `{md.get('block_path', '?')}`")
    if md.get("block_sha256"):
        print(f"- Block sha256: `{md.get('block_sha256')}`")
    print(f"- Router: `{md.get('router', '?')}`")
    if md.get("allow_features") or md.get("deny_features"):
        print(f"- Allow features: `{md.get('allow_features', [])}`")
        print(f"- Deny features: `{md.get('deny_features', [])}`")
    print(f"- Scale: `{md.get('scale', '?')}`")
    print(f"- Score: {fmt_float(sm.get('baseline', 0))} -> {fmt_float(sm.get('routed', 0))}")
    print(f"- Fixes / breaks / net: {sm.get('fixes', 0)} / {sm.get('breaks', 0)} / {sm.get('net', 0)}")
    print(f"- Active / disabled: {sm.get('active', 0)} / {sm.get('disabled', 0)}")
    fixes = sm.get("fixes_list", [])
    breaks = sm.get("breaks_list", [])
    if fixes:
        print("- Fixes:")
        for item in fixes:
            print(f"  - {item}")
    if breaks:
        print("- Breaks:")
        for item in breaks:
            print(f"  - {item}")


def gate_status(row: dict[str, Any]) -> tuple[str, list[str]]:
    md = row["metadata"]
    sm = row["summary"]
    benchmark = md.get("benchmark_set", "?")
    routed = float(sm.get("routed", 0))
    baseline = float(sm.get("baseline", 0))
    fixes = int(sm.get("fixes", 0))
    breaks = int(sm.get("breaks", 0))
    net = int(sm.get("net", 0))
    router = md.get("router", "?")

    notes: list[str] = []
    if benchmark == "core":
        if breaks == 0 and fixes >= 6 and routed >= 0.95:
            notes.append("PASS: reproduces/approaches the v31 core safety-router result.")
        elif breaks == 0 and net > 0:
            notes.append("PARTIAL: zero-break core improvement, but below v31 target.")
        elif net > 0:
            notes.append("PARTIAL: positive core net, but breaks remain.")
        else:
            notes.append("FAIL: no positive core safety-router evidence.")
    else:
        if breaks == 0 and net > 0:
            notes.append("PASS: positive zero-break transfer beyond core.")
        elif net > 0 and routed > baseline:
            notes.append("PARTIAL: positive transfer, but safety is not clean.")
        elif router in {"blacklist_only", "allow_math", "math_only"} and breaks <= fixes and net >= 0:
            notes.append("PARTIAL: router is not harmful, but gain is weak.")
        else:
            notes.append("FAIL: no useful transfer evidence.")
    return notes[0].split(":", 1)[0], notes


def best_by_benchmark(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_benchmark: dict[str, list[dict[str, Any]]] = {}
    for row in runs:
        by_benchmark.setdefault(row["metadata"].get("benchmark_set", "?"), []).append(row)
    best: list[dict[str, Any]] = []
    for rows in by_benchmark.values():
        best.append(sort_runs(rows)[0])
    return sort_runs(best)


def make_report(runs: list[dict[str, Any]], limit: int) -> str:
    ranked = sort_runs(runs)
    lines: list[str] = [
        "# BitDPM v32 Result Summary",
        "",
        "## Ranked Runs",
        "",
        make_table(ranked, limit),
        "",
        "## Best By Benchmark",
        "",
        make_table(best_by_benchmark(ranked), limit=max(limit, 20)),
        "",
        "## Gate Assessment",
        "",
    ]

    for row in best_by_benchmark(ranked):
        md = row["metadata"]
        sm = row["summary"]
        status, notes = gate_status(row)
        block = md.get("block", {}).get("block_id", "?")
        lines.extend(
            [
                f"### {md.get('benchmark_set', '?')} - {status}",
                "",
                f"- Block: `{block}`",
                f"- Block path: `{md.get('block_path', '?')}`",
                f"- Block sha256: `{md.get('block_sha256', '?')}`",
                f"- Router: `{md.get('router', '?')}`",
                f"- Allow features: `{md.get('allow_features', [])}`",
                f"- Deny features: `{md.get('deny_features', [])}`",
                f"- Scale: `{md.get('scale', '?')}`",
                f"- Score: {fmt_float(sm.get('baseline', 0))} -> {fmt_float(sm.get('routed', 0))}",
                f"- Fixes / breaks / net: {sm.get('fixes', 0)} / {sm.get('breaks', 0)} / {sm.get('net', 0)}",
                f"- Active / disabled: {sm.get('active', 0)} / {sm.get('disabled', 0)}",
            ]
        )
        lines.extend(f"- {note}" for note in notes)
        if sm.get("fixes_list"):
            lines.append("- Fixes:")
            lines.extend(f"  - {item}" for item in sm["fixes_list"])
        if sm.get("breaks_list"):
            lines.append("- Breaks:")
            lines.extend(f"  - {item}" for item in sm["breaks_list"])
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- A high-level result requires transfer beyond core-45, not just reproducing v31.",
            "- Prefer zero-break positive-net routers over higher-recall routers with breaks.",
            "- If core reproduces but v08/v15 fail, the current router is overfit and the next step is validation-mined routing.",
            "- If v08/v15 show zero-break positive net, freeze the block path and write a v32 technical report.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize BitDPM v32 result JSON")
    parser.add_argument("json_files", nargs="+")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--only-zero-breaks", action="store_true")
    parser.add_argument("--min-net", type=int, default=None)
    parser.add_argument("--write-report", default=None, help="Optional Markdown report output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = load_runs(args.json_files)
    if args.only_zero_breaks:
        runs = [r for r in runs if r["summary"].get("breaks", 0) == 0]
    if args.min_net is not None:
        runs = [r for r in runs if r["summary"].get("net", 0) >= args.min_net]
    ranked = sort_runs(runs)
    print_table(ranked, args.limit)
    print_best(ranked)
    if args.write_report:
        report = make_report(ranked, args.limit)
        out = Path(args.write_report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\nWrote report: {out}")


if __name__ == "__main__":
    main()
