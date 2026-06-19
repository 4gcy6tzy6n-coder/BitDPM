"""Build a reproducibility manifest for saved BitDPM parameter blocks.

The v30/v31 reports did not record the exact block artifact used. This script
creates a stable inventory of all saved `.pt` blocks with metadata and sha256
hashes so future experiment reports can cite immutable block artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def config_to_dict(config: Any) -> dict[str, Any]:
    if config is None:
        return {}
    if hasattr(config, "__dict__"):
        return dict(config.__dict__)
    if isinstance(config, dict):
        return dict(config)
    return {"repr": repr(config)}


def tensor_numel(state_dict: dict[str, Any]) -> int:
    total = 0
    for value in state_dict.values():
        if hasattr(value, "numel"):
            total += int(value.numel())
    return total


def tensor_shape(state_dict: dict[str, Any], name: str) -> list[int] | None:
    value = state_dict.get(name)
    if hasattr(value, "shape"):
        return [int(dim) for dim in value.shape]
    return None


def infer_backbone_family(module_name: str | None, a_shape: list[int] | None, b_shape: list[int] | None) -> str:
    if not a_shape or not b_shape or len(a_shape) != 2 or len(b_shape) != 2:
        return "unknown"
    in_dim = a_shape[0]
    out_dim = b_shape[1]
    module = module_name or ""
    if module == "down_proj":
        if (in_dim, out_dim) == (4864, 896):
            return "Qwen2.5-0.5B down_proj"
        if (in_dim, out_dim) == (8960, 1536):
            return "Qwen2.5-1.5B down_proj"
    if module in {"o_proj", "q_proj", "k_proj", "v_proj"}:
        if (in_dim, out_dim) == (896, 896):
            return "Qwen2.5-0.5B attention"
        if (in_dim, out_dim) == (1536, 1536):
            return "Qwen2.5-1.5B attention"
    if module in {"gate_proj", "up_proj"}:
        if (in_dim, out_dim) == (896, 4864):
            return "Qwen2.5-0.5B up/gate"
        if (in_dim, out_dim) == (1536, 8960):
            return "Qwen2.5-1.5B up/gate"
    return f"unknown ({in_dim}->{out_dim})"


def inspect_block(path: Path, root: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": str(path),
        "rel_path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
        "file_size": path.stat().st_size,
        "sha256": sha256_file(path),
        "load_ok": False,
    }
    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        if isinstance(checkpoint, dict):
            config = config_to_dict(checkpoint.get("config"))
            state_dict = checkpoint.get("state_dict", {})
        else:
            config = {}
            state_dict = {}
        a_shape = tensor_shape(state_dict, "A") if isinstance(state_dict, dict) else None
        b_shape = tensor_shape(state_dict, "B") if isinstance(state_dict, dict) else None
        row.update(
            {
                "load_ok": True,
                "block_id": config.get("block_id"),
                "block_type": config.get("block_type"),
                "layer_id": config.get("layer_id"),
                "module_name": config.get("module_name"),
                "rank": config.get("rank"),
                "scale": config.get("scale"),
                "hidden_size": config.get("hidden_size"),
                "in_features": config.get("in_features"),
                "out_features": config.get("out_features"),
                "A_shape": a_shape,
                "B_shape": b_shape,
                "in_dim": a_shape[0] if a_shape else None,
                "out_dim": b_shape[1] if b_shape else None,
                "matched_backbone": infer_backbone_family(config.get("module_name"), a_shape, b_shape),
                "num_params": tensor_numel(state_dict) if isinstance(state_dict, dict) else 0,
            }
        )
    except Exception as exc:
        row["error"] = str(exc)
    return row


def make_markdown(rows: list[dict[str, Any]], limit: int = 0) -> str:
    ok = [r for r in rows if r.get("load_ok")]
    bad = [r for r in rows if not r.get("load_ok")]
    by_pool: dict[str, int] = {}
    for row in ok:
        parts = Path(row["rel_path"]).parts
        if len(parts) > 2 and parts[0] == "experiments" and parts[1] == "outputs":
            pool = parts[2]
        else:
            pool = parts[0]
        by_pool[pool] = by_pool.get(pool, 0) + 1

    lines = [
        "# BitDPM Block Manifest",
        "",
        f"- Total files: {len(rows)}",
        f"- Loadable blocks: {len(ok)}",
        f"- Failed files: {len(bad)}",
        "",
        "## Blocks By Pool",
        "",
        "| Pool | Blocks |",
        "|---|---:|",
    ]
    for pool, count in sorted(by_pool.items()):
        lines.append(f"| `{pool}` | {count} |")

    lines.extend(
        [
            "",
            "## Block Inventory",
            "",
            "| Path | Block ID | Type | Layer | Module | Rank | Params | SHA256 |",
            "|---|---|---|---:|---|---:|---:|---|",
        ]
    )
    show = ok[:limit] if limit else ok
    for row in show:
        sha = str(row.get("sha256", ""))[:12]
        lines.append(
            f"| `{row.get('rel_path')}` | `{row.get('block_id')}` | `{row.get('block_type')}` | "
            f"{row.get('layer_id')} | `{row.get('module_name')}` | {row.get('rank')} | "
            f"{row.get('num_params')} | `{sha}` |"
        )

    lines.extend(
        [
            "",
            "## Compatibility Summary",
            "",
            "| Backbone Family | Blocks |",
            "|---|---:|",
        ]
    )
    by_family: dict[str, int] = {}
    for row in ok:
        family = str(row.get("matched_backbone", "unknown"))
        by_family[family] = by_family.get(family, 0) + 1
    for family, count in sorted(by_family.items()):
        lines.append(f"| `{family}` | {count} |")

    if bad:
        lines.extend(["", "## Load Failures", "", "| Path | Error |", "|---|---|"])
        for row in bad:
            lines.append(f"| `{row.get('rel_path')}` | {row.get('error', 'unknown')} |")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build BitDPM block manifest")
    parser.add_argument("--root", default=".")
    parser.add_argument("--glob", action="append", default=["experiments/outputs/**/*.pt"])
    parser.add_argument("--json-out", default="experiments/reports/block_manifest.json")
    parser.add_argument("--md-out", default="experiments/reports/block_manifest.md")
    parser.add_argument("--md-limit", type=int, default=0, help="Limit markdown inventory rows; 0 means all")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    paths: list[Path] = []
    for pattern in args.glob:
        paths.extend(root.glob(pattern))
    paths = sorted({p.resolve() for p in paths if p.is_file()})

    rows = [inspect_block(path, root) for path in paths]
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(make_markdown(rows, args.md_limit), encoding="utf-8")

    print(f"Wrote JSON manifest: {json_out} ({len(rows)} files)")
    print(f"Wrote Markdown manifest: {md_out}")


if __name__ == "__main__":
    main()
