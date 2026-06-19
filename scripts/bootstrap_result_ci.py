"""Bootstrap confidence intervals for BitDPM result JSON files.

Supports:
- block-pool reports with `per_sample[*].scores`
- router reports with `eval_rows[*].score` and `baseline_score`
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from statistics import mean
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def bootstrap_mean(values: list[float], samples: int, seed: int) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(values)
    estimates = []
    for _ in range(samples):
        draw = [values[rng.randrange(n)] for _ in range(n)]
        estimates.append(mean(draw))
    return mean(values), percentile(estimates, 0.025), percentile(estimates, 0.975)


def block_pool_metrics(data: dict[str, Any]) -> dict[str, list[float]]:
    rows = data.get("per_sample", [])
    metrics: dict[str, list[float]] = {}
    if not rows:
        return metrics
    score_keys = sorted(rows[0].get("scores", {}).keys())
    for key in score_keys:
        metrics[key] = [float(row.get("scores", {}).get(key, 0.0)) for row in rows]
    metrics["oracle"] = [
        max(float(value) for value in row.get("scores", {}).values())
        for row in rows
        if row.get("scores")
    ]
    return metrics


def router_metrics(data: dict[str, Any]) -> dict[str, list[float]]:
    rows = data.get("eval_rows", [])
    if not rows:
        return {}
    return {
        "baseline": [float(row.get("baseline_score", 0.0)) for row in rows],
        "router": [float(row.get("score", 0.0)) for row in rows],
        "delta": [float(row.get("score", 0.0)) - float(row.get("baseline_score", 0.0)) for row in rows],
    }


def extract_metrics(data: dict[str, Any]) -> dict[str, list[float]]:
    if "per_sample" in data:
        return block_pool_metrics(data)
    if "eval_rows" in data:
        return router_metrics(data)
    raise ValueError("Unsupported report JSON: expected `per_sample` or `eval_rows`.")


def make_report(path: Path, metrics: dict[str, list[float]], samples: int, seed: int) -> str:
    lines = [
        "# BitDPM Bootstrap Confidence Intervals",
        "",
        f"- Source: `{path}`",
        f"- Bootstrap samples: {samples}",
        f"- Seed: {seed}",
        "",
        "| Metric | N | Mean | 95% CI Low | 95% CI High |",
        "|---|---:|---:|---:|---:|",
    ]
    preferred = ["baseline", "router", "oracle", "always_all", "delta"]
    keys = [key for key in preferred if key in metrics] + [
        key for key in sorted(metrics) if key not in preferred
    ]
    for key in keys:
        values = metrics[key]
        avg, lo, hi = bootstrap_mean(values, samples=samples, seed=seed)
        lines.append(f"| `{key}` | {len(values)} | {avg:.3f} | {lo:.3f} | {hi:.3f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap CIs for BitDPM report JSON files.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    data = load_json(args.report)
    metrics = extract_metrics(data)
    report = make_report(args.report, metrics, samples=args.samples, seed=args.seed)
    if args.out is None:
        print(report)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(report)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
