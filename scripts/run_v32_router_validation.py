"""BitDPM v32: reproducible safety-router validation for repair blocks.

This script evaluates the v31-style setting with explicit metadata:

    frozen backbone + one or more parameter blocks + per-sample safety router

It is intentionally separate from older experiment runners so v31/v32 results
can be reproduced without relying on ad-hoc notebooks or transient in-memory
blocks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from glob import glob
from pathlib import Path
from typing import Any

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS, compute_accuracy_with_refs
from bitdpm.eval.v08_benchmark import V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
from bitdpm.eval.v14_benchmark import V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock
from scripts.mine_v33_safety_router import prompt_features


BENCHMARKS = {
    "core": (EVAL_PROMPTS, EXPECTED_ANSWERS),
    "v08": (V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS),
    "v14": (V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS),
    "v15": (V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS),
}


ROUTERS = ("unrestricted", "blacklist_only", "allow_math", "math_only", "baseline_only", "feature_rule")


@dataclass
class SampleResult:
    index: int
    category: str
    prompt: str
    expected: str
    router: str
    active: bool
    baseline_score: float
    routed_score: float
    delta: float
    baseline_output: str | None = None
    routed_output: str | None = None


def get_benchmark(name: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    try:
        return BENCHMARKS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown benchmark set: {name}. Choices: {sorted(BENCHMARKS)}") from exc


def iter_samples(
    prompts_by_category: dict[str, list[str]],
    expected_answers: dict[str, list[str]],
    max_prompts_per_category: int,
) -> list[tuple[str, str, str]]:
    samples: list[tuple[str, str, str]] = []
    for category, prompts in prompts_by_category.items():
        selected = prompts[:max_prompts_per_category] if max_prompts_per_category else prompts
        refs = expected_answers.get(category, [])
        for idx, prompt in enumerate(selected):
            expected = refs[idx] if idx < len(refs) else ""
            samples.append((category, prompt, expected))
    return samples


def feature_expr_active(expr: str, category: str, prompt: str) -> bool:
    feats = prompt_features(category, prompt)
    parts = [part.strip() for part in expr.split("AND")]
    if not parts:
        return False
    for part in parts:
        negate = part.startswith("!")
        name = part[1:] if negate else part
        value = bool(feats.get(name, False))
        if negate:
            value = not value
        if not value:
            return False
    return True


def router_active(
    router: str,
    category: str,
    prompt: str,
    allow_features: list[str] | None = None,
    deny_features: list[str] | None = None,
) -> bool:
    """Return whether the repair block should be active for this sample.

    These rules encode the v31 safety-router hypotheses:
    - unrestricted: activate on every sample.
    - blacklist_only: disable known high-risk surfaces from v30/v31.
    - allow_math: activate only on the core categories that produced v31 fixes.
    - math_only: stricter ablation for arithmetic-only repair.
    - baseline_only: never activate, useful as a sanity control.
    """
    prompt_l = prompt.lower()
    allow_features = allow_features or []
    deny_features = deny_features or []

    if router == "feature_rule":
        if any(feature_expr_active(expr, category, prompt) for expr in deny_features):
            return False
        if not allow_features:
            return False
        return any(feature_expr_active(expr, category, prompt) for expr in allow_features)

    if router == "unrestricted":
        return True
    if router == "baseline_only":
        return False
    if router == "math_only":
        return category == "math"
    if router == "allow_math":
        return category in {"commonsense", "math"}
    if router == "blacklist_only":
        if category == "chinese":
            return False
        if "speed of light" in prompt_l:
            return False
        if "plants absorb" in prompt_l:
            return False
        return True
    raise ValueError(f"Unknown router: {router}")


def score(
    prompt: str,
    output: str,
    category: str,
    prompts_by_category: dict[str, list[str]],
    expected_answers: dict[str, list[str]],
) -> float:
    return compute_accuracy_with_refs(prompt, output, category, prompts_by_category, expected_answers)


def summarize(samples: list[SampleResult]) -> dict[str, Any]:
    baseline = sum(s.baseline_score for s in samples) / max(len(samples), 1)
    routed = sum(s.routed_score for s in samples) / max(len(samples), 1)
    fixes = [s for s in samples if s.delta > 0]
    breaks = [s for s in samples if s.delta < 0]
    active = sum(1 for s in samples if s.active)
    category: dict[str, dict[str, float]] = {}
    for s in samples:
        row = category.setdefault(s.category, {"n": 0, "baseline": 0.0, "routed": 0.0})
        row["n"] += 1
        row["baseline"] += s.baseline_score
        row["routed"] += s.routed_score
    for row in category.values():
        n = max(row["n"], 1)
        row["baseline"] /= n
        row["routed"] /= n
    return {
        "baseline": baseline,
        "routed": routed,
        "fixes": len(fixes),
        "breaks": len(breaks),
        "net": len(fixes) - len(breaks),
        "active": active,
        "disabled": len(samples) - active,
        "category": category,
        "fixes_list": [f"{s.prompt[:80]} {s.baseline_score:g}->{s.routed_score:g}" for s in fixes],
        "breaks_list": [f"{s.prompt[:80]} {s.baseline_score:g}->{s.routed_score:g}" for s in breaks],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BitDPM v32 safety-router validation")
    parser.add_argument("--block-path", action="append", default=[], help="Path to a saved ParameterBlock .pt file. Can be repeated.")
    parser.add_argument("--block-glob", action="append", default=[], help="Glob for candidate ParameterBlock .pt files. Can be repeated.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--benchmark-set", choices=sorted(BENCHMARKS), default="core")
    parser.add_argument("--routers", nargs="+", choices=ROUTERS, default=["unrestricted", "blacklist_only", "allow_math"])
    parser.add_argument("--allow-feature", action="append", default=[], help="Feature expression for feature_rule router. Supports 'A AND B' and '!A'.")
    parser.add_argument("--deny-feature", action="append", default=[], help="Deny feature expression for feature_rule router. Supports 'A AND B' and '!A'.")
    parser.add_argument("--scales", nargs="+", type=float, default=[0.85])
    parser.add_argument("--device", default=None, help="cpu, mps, cuda, or auto via BackboneModel")
    parser.add_argument("--dtype", choices=["float16", "float32"], default="float16")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--max-prompts-per-category", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--sampling", action="store_true", help="Use sampling instead of deterministic greedy decoding")
    parser.add_argument("--save-outputs", action="store_true")
    parser.add_argument("--output-dir", default="experiments/reports")
    parser.add_argument("--output-path", default=None, help="Fixed JSON output path. Useful with --resume.")
    parser.add_argument("--baseline-cache-path", default=None, help="Optional fixed baseline cache JSON path.")
    parser.add_argument("--tag", default="v32_router_validation")
    parser.add_argument("--dry-run", action="store_true", help="List resolved blocks and router active counts without loading the model")
    parser.add_argument("--resume", action="store_true", help="Load --output-path if present and skip completed block/router/scale runs.")
    return parser.parse_args()


def resolve_block_paths(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = [Path(p) for p in args.block_path]
    for pattern in args.block_glob:
        paths.extend(Path(p) for p in glob(pattern, recursive=True))

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if not path.exists():
            raise FileNotFoundError(f"Block file not found: {path}")
        unique.append(path)

    if not unique:
        raise ValueError("Provide at least one --block-path or --block-glob")
    return unique


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def run_key(metadata: dict[str, Any]) -> str:
    parts = [
        metadata.get("model"),
        metadata.get("benchmark_set"),
        metadata.get("block_path"),
        metadata.get("block_sha256"),
        metadata.get("router"),
        str(metadata.get("scale")),
        str(metadata.get("deterministic")),
        str(metadata.get("temperature")),
        str(metadata.get("max_tokens")),
        str(metadata.get("max_prompts_per_category")),
        "|".join(metadata.get("allow_features", []) or []),
        "|".join(metadata.get("deny_features", []) or []),
    ]
    return "::".join("" if p is None else str(p) for p in parts)


def load_existing_runs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [data]
    return [row for row in data if isinstance(row, dict)]


def write_runs(path: Path, runs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def baseline_cache_key(
    model: str,
    benchmark_set: str,
    deterministic: bool,
    temperature: float,
    max_tokens: int,
    max_prompts_per_category: int,
    prompt: str,
) -> str:
    return "::".join(
        [
            model,
            benchmark_set,
            str(deterministic),
            str(temperature),
            str(max_tokens),
            str(max_prompts_per_category),
            prompt,
        ]
    )


def load_baseline_cache(path: Path) -> dict[str, tuple[str, float]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, tuple[str, float]] = {}
    for key, value in data.items():
        if isinstance(value, dict) and "output" in value and "score" in value:
            out[key] = (str(value["output"]), float(value["score"]))
    return out


def write_baseline_cache(path: Path, cache: dict[str, tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {key: {"output": output, "score": score} for key, (output, score) in cache.items()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def validate_block_compatible(block: ParameterBlock, backbone: BackboneModel, block_path: Path) -> None:
    """Fail fast if a saved block does not match the target backbone layer.

    LoRA-style BitDPM blocks are tied to a specific Linear shape. A block trained
    on Qwen2.5-0.5B down_proj has A/B shapes (4864, r)/(r, 896), while the
    corresponding Qwen2.5-1.5B down_proj expects (8960, r)/(r, 1536).
    Catching this before injection avoids opaque forward-time matmul crashes.
    """
    lin = backbone.get_linear_layer(block.layer_id, block.module_name)
    if lin is None:
        raise ValueError(
            f"Block {block_path} targets layer={block.layer_id} module={block.module_name}, "
            f"but that module does not exist in model={backbone.model_name}."
        )

    expected_a = (int(lin.in_features), int(block.rank))
    expected_b = (int(block.rank), int(lin.out_features))
    actual_a = tuple(int(dim) for dim in block.A.shape)
    actual_b = tuple(int(dim) for dim in block.B.shape)
    if actual_a != expected_a or actual_b != expected_b:
        raise ValueError(
            "Incompatible BitDPM block/backbone dimensions:\n"
            f"  block_path: {block_path}\n"
            f"  model: {backbone.model_name}\n"
            f"  target: layer={block.layer_id} module={block.module_name}\n"
            f"  expected A/B: {expected_a} / {expected_b}\n"
            f"  actual   A/B: {actual_a} / {actual_b}\n"
            "This usually means a block trained on one backbone size is being "
            "loaded into another. Retrain the block for this backbone or select "
            "a compatible artifact."
        )


def main() -> None:
    args = parse_args()
    dtype = torch.float32 if args.dtype == "float32" else torch.float16
    prompts_by_category, expected_answers = get_benchmark(args.benchmark_set)
    sample_refs = iter_samples(prompts_by_category, expected_answers, args.max_prompts_per_category)
    block_paths = resolve_block_paths(args)

    if args.dry_run:
        print(f"[v32] dry run benchmark={args.benchmark_set} samples={len(sample_refs)}")
        print(f"[v32] resolved blocks={len(block_paths)}")
        for path in block_paths:
            try:
                block = ParameterBlock.load(str(path), device=None)
                print(
                    f"  {path} | id={block.block_id} type={block.block_type} "
                    f"layer={block.layer_id} module={block.module_name} rank={block.rank} "
                    f"A={list(block.A.shape)} B={list(block.B.shape)}"
                )
            except Exception as exc:
                print(f"  {path} | ERROR {exc}")
        for router in args.routers:
            active = sum(
                router_active(router, category, prompt, args.allow_feature, args.deny_feature)
                for category, prompt, _ in sample_refs
            )
            print(f"[v32] router={router} active={active} disabled={len(sample_refs) - active}")
        return

    started = time.strftime("%Y%m%d_%H%M%S")
    if args.output_path:
        out_path = Path(args.output_path)
    else:
        out_path = Path(args.output_dir) / f"{args.tag}_{started}.json"
    baseline_cache_path = Path(args.baseline_cache_path) if args.baseline_cache_path else out_path.with_suffix(".baseline.json")

    print(f"[v32] Loading backbone: {args.model}")
    backbone = BackboneModel(model_name=args.model, device=args.device, dtype=dtype)

    print(f"[v32] Loading baseline cache from {baseline_cache_path}")
    baseline_cache = load_baseline_cache(baseline_cache_path) if args.resume else {}
    print(f"[v32] Baseline cache entries loaded: {len(baseline_cache)}")
    print(f"[v32] Computing baseline cache for {len(sample_refs)} samples")
    deterministic = not args.sampling
    for idx, (category, prompt, _) in enumerate(sample_refs, start=1):
        bkey = baseline_cache_key(
            args.model,
            args.benchmark_set,
            deterministic,
            args.temperature,
            args.max_tokens,
            args.max_prompts_per_category,
            prompt,
        )
        if bkey in baseline_cache:
            baseline_output, baseline_score = baseline_cache[bkey]
            print(f"  [baseline {idx:03d}/{len(sample_refs):03d}] {category:<16} score={baseline_score:g} cached")
            continue
        baseline_output = backbone.generate(
            prompt,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            do_sample=args.sampling,
        )
        baseline_score = score(prompt, baseline_output, category, prompts_by_category, expected_answers)
        baseline_cache[bkey] = (baseline_output, baseline_score)
        write_baseline_cache(baseline_cache_path, baseline_cache)
        print(f"  [baseline {idx:03d}/{len(sample_refs):03d}] {category:<16} score={baseline_score:g}")

    all_runs: list[dict[str, Any]] = load_existing_runs(out_path) if args.resume else []
    completed_keys = {
        run_key(row.get("metadata", {}))
        for row in all_runs
        if "metadata" in row and "summary" in row and "samples" in row
    }
    if args.resume:
        print(f"[v32] resume enabled: loaded {len(all_runs)} existing runs from {out_path}")

    for block_index, block_path in enumerate(block_paths, start=1):
        print(f"\n[v32] Loading block {block_index}/{len(block_paths)}: {block_path}")
        block_sha256 = sha256_file(block_path)
        block = ParameterBlock.load(str(block_path), device=torch.device(backbone.device)).to(
            device=torch.device(backbone.device),
            dtype=dtype,
        )
        validate_block_compatible(block, backbone, block_path)
        injector = BlockInjector(backbone)
        injector.inject_block(block)
        try:
            for scale in args.scales:
                block.scale = scale
                for router in args.routers:
                    metadata = {
                        "tag": args.tag,
                        "created": started,
                        "model": args.model,
                        "benchmark_set": args.benchmark_set,
                        "block_path": str(block_path),
                        "block_sha256": block_sha256,
                        "block": {
                            "block_id": block.block_id,
                            "block_type": block.block_type,
                            "layer_id": block.layer_id,
                            "module_name": block.module_name,
                            "rank": block.rank,
                        },
                        "scale": scale,
                        "router": router,
                        "allow_features": args.allow_feature,
                        "deny_features": args.deny_feature,
                        "deterministic": not args.sampling,
                        "temperature": args.temperature,
                        "max_tokens": args.max_tokens,
                        "max_prompts_per_category": args.max_prompts_per_category,
                    }
                    key = run_key(metadata)
                    if args.resume and key in completed_keys:
                        print(f"\n[v32] skip completed block={block.block_id} router={router} scale={scale}")
                        continue

                    print(f"\n[v32] block={block.block_id} router={router} scale={scale} benchmark={args.benchmark_set}")
                    rows: list[SampleResult] = []
                    for idx, (category, prompt, expected) in enumerate(sample_refs, start=1):
                        bkey = baseline_cache_key(
                            args.model,
                            args.benchmark_set,
                            not args.sampling,
                            args.temperature,
                            args.max_tokens,
                            args.max_prompts_per_category,
                            prompt,
                        )
                        baseline_output, baseline_score = baseline_cache[bkey]

                        active = router_active(router, category, prompt, args.allow_feature, args.deny_feature)
                        injector.set_active_blocks([block.block_id] if active else [])
                        routed_output = backbone.generate(
                            prompt,
                            max_new_tokens=args.max_tokens,
                            temperature=args.temperature,
                            do_sample=args.sampling,
                        )
                        routed_score = score(prompt, routed_output, category, prompts_by_category, expected_answers)
                        delta = routed_score - baseline_score

                        rows.append(
                            SampleResult(
                                index=idx,
                                category=category,
                                prompt=prompt,
                                expected=expected,
                                router=router,
                                active=active,
                                baseline_score=baseline_score,
                                routed_score=routed_score,
                                delta=delta,
                                baseline_output=baseline_output if args.save_outputs else None,
                                routed_output=routed_output if args.save_outputs else None,
                            )
                        )
                        mark = "fix" if delta > 0 else "break" if delta < 0 else "same"
                        print(
                            f"  [{idx:03d}/{len(sample_refs):03d}] {category:<16} "
                            f"active={int(active)} {baseline_score:g}->{routed_score:g} {mark}"
                        )

                    summary = summarize(rows)
                    print(
                        f"[v32] result block={block.block_id} router={router} scale={scale}: "
                        f"baseline={summary['baseline']:.3f} routed={summary['routed']:.3f} "
                        f"fixes={summary['fixes']} breaks={summary['breaks']} net={summary['net']} "
                        f"active={summary['active']} disabled={summary['disabled']}"
                    )

                    all_runs.append(
                        {
                            "metadata": metadata,
                            "summary": summary,
                            "samples": [asdict(row) for row in rows],
                        }
                    )
                    completed_keys.add(key)
                    write_runs(out_path, all_runs)
                    print(f"[v32] checkpoint wrote {len(all_runs)} runs -> {out_path}")
        finally:
            injector.remove_all_patches()

    # Sort copy for easy reading while preserving full run order in the file.
    ranked = sorted(
        all_runs,
        key=lambda r: (r["summary"]["net"], r["summary"]["routed"], -r["summary"]["breaks"]),
        reverse=True,
    )
    print("\n[v32] Top results")
    for row in ranked[:10]:
        md = row["metadata"]
        sm = row["summary"]
        print(
            f"  net={sm['net']:>3} routed={sm['routed']:.3f} fixes={sm['fixes']:>2} breaks={sm['breaks']:>2} "
            f"router={md['router']} scale={md['scale']} block={md['block']['block_id']} path={md['block_path']}"
        )

    write_runs(out_path, all_runs)
    print(f"\n[v32] wrote {out_path}")


if __name__ == "__main__":
    main()
