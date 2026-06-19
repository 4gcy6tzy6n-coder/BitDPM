"""Audit whether the recorded BitDPM v31 result is reproducible from artifacts.

This is a lightweight handoff tool. It does not run model inference; it checks
the saved metadata and replay summaries that should prove whether the v31
`fixes=6, breaks=0` result can be attributed to a concrete block/backbone pair.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def best_v31_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    router_preference = {
        "allow_math": 3,
        "blacklist_only": 2,
        "unrestricted": 1,
    }
    return max(
        rows,
        key=lambda row: (
            int(row.get("net", -10**9)),
            -int(row.get("breaks", 10**9)),
            float(row.get("block", row.get("routed", 0.0))),
            router_preference.get(str(row.get("router")), 0),
        ),
    )


def summarize_recovery(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "runs": 0,
            "positive_net": 0,
            "zero_break": 0,
            "best": None,
        }
    ranked = sorted(
        rows,
        key=lambda row: (
            row.get("summary", {}).get("net", -10**9),
            row.get("summary", {}).get("routed", 0.0),
            -row.get("summary", {}).get("breaks", 10**9),
        ),
        reverse=True,
    )
    return {
        "runs": len(rows),
        "positive_net": sum(1 for row in rows if row.get("summary", {}).get("net", 0) > 0),
        "zero_break": sum(1 for row in rows if row.get("summary", {}).get("breaks", 10**9) == 0),
        "best": ranked[0],
    }


def make_report(
    v31_path: Path,
    manifest_path: Path,
    recovery_path: Path,
) -> str:
    v31_rows = load_json(v31_path)
    manifest_rows = load_json(manifest_path)
    recovery_rows = load_json(recovery_path)

    if not isinstance(v31_rows, list):
        raise ValueError(f"Expected list in {v31_path}")
    if not isinstance(manifest_rows, list):
        raise ValueError(f"Expected list in {manifest_path}")
    if not isinstance(recovery_rows, list):
        raise ValueError(f"Expected list in {recovery_path}")

    best = best_v31_row(v31_rows)
    by_family = Counter(str(row.get("matched_backbone", "unknown")) for row in manifest_rows)
    compatible_15b = sum(
        count for family, count in by_family.items()
        if "Qwen2.5-1.5B" in family
    )
    compatible_05b = sum(
        count for family, count in by_family.items()
        if "Qwen2.5-0.5B" in family
    )
    recovery = summarize_recovery(recovery_rows)
    rec_best = recovery["best"]

    provenance_fields = ["model", "block_path", "block_sha256", "benchmark_set", "deterministic", "max_tokens"]
    missing_provenance = []
    if best:
        missing_provenance = [field for field in provenance_fields if field not in best]

    lines = [
        "# BitDPM v31 Provenance Audit",
        "",
        "## Inputs",
        "",
        f"- v31 result: `{v31_path}`",
        f"- block manifest: `{manifest_path}`",
        f"- 0.5B recovery replay: `{recovery_path}`",
        "",
        "## v31 Historical Record",
        "",
    ]
    if best is None:
        lines.append("No v31 rows found.")
    else:
        lines.extend(
            [
                "| Router | Scale | Baseline | Routed | Fixes | Breaks | Net | Active | Disabled |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
                (
                    f"| {best.get('router')} | {best.get('scale')} | "
                    f"{float(best.get('baseline', 0.0)):.3f} | {float(best.get('block', 0.0)):.3f} | "
                    f"{best.get('fixes')} | {best.get('breaks')} | {best.get('net')} | "
                    f"{best.get('active')} | {best.get('disabled')} |"
                ),
                "",
                f"Missing provenance fields: `{', '.join(missing_provenance) if missing_provenance else 'none'}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Block Inventory Compatibility",
            "",
            "| Family | Count |",
            "|---|---:|",
        ]
    )
    for family, count in sorted(by_family.items()):
        lines.append(f"| {family} | {count} |")

    lines.extend(
        [
            "",
            "## 0.5B Recovery Replay",
            "",
            f"- Completed runs: {recovery['runs']}",
            f"- Positive-net candidates: {recovery['positive_net']}",
            f"- Zero-break candidates: {recovery['zero_break']}",
        ]
    )
    if rec_best:
        md = rec_best.get("metadata", {})
        sm = rec_best.get("summary", {})
        lines.extend(
            [
                f"- Best block: `{md.get('block_path')}`",
                (
                    f"- Best score: {float(sm.get('baseline', 0.0)):.3f} -> "
                    f"{float(sm.get('routed', 0.0)):.3f}; fixes/breaks/net = "
                    f"{sm.get('fixes')}/{sm.get('breaks')}/{sm.get('net')}"
                ),
            ]
        )

    v31_recovered = (
        best is not None
        and not missing_provenance
        and compatible_15b > 0
        and recovery["positive_net"] > 0
    )
    status = "RECOVERED" if v31_recovered else "UNRECOVERED"
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"Status: **{status}**",
            "",
        ]
    )
    if status == "UNRECOVERED":
        lines.extend(
            [
                "The v31 `fixes=6, breaks=0` result remains a historical record, not a current",
                "main result. The saved result lacks exact block/backbone provenance, the block",
                f"inventory contains {compatible_15b} Qwen2.5-1.5B-compatible artifacts, and the",
                "saved 0.5B candidate replay did not reproduce the v31 pattern.",
            ]
        )
    else:
        lines.append("The current artifacts are sufficient to attribute and replay v31.")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit BitDPM v31 provenance from saved artifacts.")
    parser.add_argument("--v31", type=Path, default=Path("experiments/reports/v31_router_20260610_144251.json"))
    parser.add_argument("--manifest", type=Path, default=Path("experiments/reports/block_manifest.json"))
    parser.add_argument("--recovery", type=Path, default=Path("experiments/reports/v31r_recover_0p5b_core_allow_math085.json"))
    parser.add_argument("--out", type=Path, default=Path("experiments/reports/bitdpm_v31_provenance_audit.md"))
    args = parser.parse_args()

    report = make_report(args.v31, args.manifest, args.recovery)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
