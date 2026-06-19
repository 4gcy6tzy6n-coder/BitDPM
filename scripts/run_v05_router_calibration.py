#!/usr/bin/env python3
"""BitDPM v0.5: router calibration and block utility learning.

This script measures block utility directly instead of assuming that keyword or
entropy heuristics select the useful block. It evaluates each prompt under:

- baseline: no blocks
- one fixed block type: general, math, code, chinese
- always_all: all blocks

Then it derives:

- Oracle per-sample router: best config per prompt after observing scores
- Validation-calibrated router: best config per category from a calibration split
- Block utility matrix: average score by category and config

Usage:
    python scripts/run_v05_router_calibration.py \
      --model /path/to/Qwen2.5-0.5B-Instruct \
      --load-blocks experiments/outputs/blocks

Quick smoke run:
    python scripts/run_v05_router_calibration.py --quick --max-prompts-per-category 2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS, compute_accuracy_with_refs
from bitdpm.eval.v08_benchmark import V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
from bitdpm.eval.v14_benchmark import V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
from bitdpm.eval.v1k_benchmark import V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
from bitdpm.eval.v1k_clean_benchmark import V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank


CONFIGS = ["baseline", "general", "math", "code", "chinese", "always_all"]
LEGACY_BLOCK_TYPES = ["general", "math", "code", "chinese"]


@dataclass
class ConfigAggregate:
    overall: float
    category_scores: dict[str, float]
    active_blocks: float


@dataclass
class V05Results:
    model: str
    device: str
    benchmark_set: str
    total_prompts: int
    block_scale: float
    block_scales: dict[str, float]
    max_tokens: int
    config_results: dict[str, ConfigAggregate]
    oracle: ConfigAggregate
    validation_calibrated: ConfigAggregate
    category_policy: dict[str, str]
    utility_matrix: dict[str, dict[str, float]]
    selection_frequency: dict[str, int]
    per_sample: list[dict[str, Any]] = field(default_factory=list)


def build_block_type_map(bank: BlockBank) -> dict[str, list[str]]:
    type_map: dict[str, list[str]] = {}
    for meta in bank.list_blocks():
        type_map.setdefault(meta["block_type"], []).append(meta["block_id"])
    return type_map


def load_block_dirs(directories: list[str], device: torch.device, dtype: torch.dtype | None = None) -> BlockBank:
    """Load one or more block directories into a single bank.

    Duplicate block IDs are renamed with a directory-derived prefix while
    preserving block_type, so config-level activation still works by type.
    """
    merged = BlockBank()
    for directory in directories:
        source_bank = BlockBank.load_all(directory, device=device)
        prefix = os.path.basename(os.path.normpath(directory))
        for block in source_bank.blocks.values():
            if block.block_id in merged.blocks:
                old_id = block.block_id
                block.block_id = f"{prefix}__{old_id}"
                block.config.block_id = block.block_id
            # Convert dtype to match backbone (e.g. float32 -> float16 for MPS)
            if dtype is not None:
                block = block.to(dtype=dtype)
            merged.add_block(block)
    return merged


def resolve_configs(type_map: dict[str, list[str]], requested: list[str] | None = None) -> list[str]:
    """Resolve evaluation configs from requested names or loaded block types."""
    if requested:
        configs = []
        for config in requested:
            if config in configs:
                continue
            if config in ("baseline", "always_all") or config in type_map:
                configs.append(config)
            elif "+" in config:
                missing = [part for part in config.split("+") if part not in type_map]
                if missing:
                    print(
                        f"  [Warn] Requested combo '{config}' has missing block types "
                        f"{missing}; keeping it partially inactive"
                    )
                configs.append(config)
            else:
                print(f"  [Warn] Requested config '{config}' has no loaded blocks; keeping it inactive")
                configs.append(config)
        if "baseline" not in configs:
            configs.insert(0, "baseline")
        return configs

    loaded_types = set(type_map)
    if loaded_types.issubset(set(LEGACY_BLOCK_TYPES)):
        return [cfg for cfg in CONFIGS if cfg in ("baseline", "always_all") or cfg in type_map]

    ordered_types = [t for t in LEGACY_BLOCK_TYPES if t in type_map]
    ordered_types.extend(sorted(t for t in type_map if t not in LEGACY_BLOCK_TYPES))
    return ["baseline"] + ordered_types + ["always_all"]


def get_benchmark_refs(benchmark_set: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    if benchmark_set == "core":
        return EVAL_PROMPTS, EXPECTED_ANSWERS
    if benchmark_set == "v08":
        return V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
    if benchmark_set == "v14":
        return V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
    if benchmark_set == "v15":
        return V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
    if benchmark_set == "v1k":
        return V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
    if benchmark_set == "v1k_clean":
        return V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS
    raise ValueError(f"Unknown benchmark set: {benchmark_set}")


def select_prompts(
    prompts_by_category: dict[str, list[str]],
    max_prompts_per_category: int = 0,
) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    for category, prompts in prompts_by_category.items():
        use_prompts = prompts[:max_prompts_per_category] if max_prompts_per_category else prompts
        selected.extend((category, prompt) for prompt in use_prompts)
    return selected


def split_calibration_indices(samples: list[dict[str, Any]], calib_ratio: float) -> tuple[set[int], set[int]]:
    by_category: dict[str, list[int]] = {}
    for idx, sample in enumerate(samples):
        by_category.setdefault(sample["category"], []).append(idx)

    calib: set[int] = set()
    eval_idx: set[int] = set()
    for indices in by_category.values():
        if len(indices) == 1:
            calib.update(indices)
            eval_idx.update(indices)
            continue
        n_calib = max(1, min(len(indices) - 1, int(round(len(indices) * calib_ratio))))
        calib.update(indices[:n_calib])
        eval_idx.update(indices[n_calib:])
    return calib, eval_idx


def aggregate_scores(samples: list[dict[str, Any]], config_by_sample: list[str]) -> ConfigAggregate:
    category_totals: dict[str, float] = {}
    category_counts: dict[str, int] = {}
    active_total = 0.0
    total = 0.0

    for sample, config in zip(samples, config_by_sample):
        score = sample["scores"][config]
        category = sample["category"]
        total += score
        active_total += sample["active_counts"][config]
        category_totals[category] = category_totals.get(category, 0.0) + score
        category_counts[category] = category_counts.get(category, 0) + 1

    category_scores = {
        cat: category_totals[cat] / max(category_counts[cat], 1)
        for cat in category_totals
    }
    return ConfigAggregate(
        overall=total / max(len(samples), 1),
        category_scores=category_scores,
        active_blocks=active_total / max(len(samples), 1),
    )


def best_config_for_sample(sample: dict[str, Any], configs: list[str]) -> str:
    # Stable tie-break: prefer fewer active blocks, then baseline, then config order.
    return max(
        configs,
        key=lambda cfg: (
            sample["scores"][cfg],
            -sample["active_counts"][cfg],
            -configs.index(cfg),
        ),
    )


def choose_category_policy(
    samples: list[dict[str, Any]],
    calib_indices: set[int],
    configs: list[str],
) -> dict[str, str]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for idx in calib_indices:
        sample = samples[idx]
        by_category.setdefault(sample["category"], []).append(sample)

    policy: dict[str, str] = {}
    for category, category_samples in by_category.items():
        averages = {}
        for config in configs:
            averages[config] = sum(s["scores"][config] for s in category_samples) / len(category_samples)
        policy[category] = max(
            configs,
            key=lambda cfg: (
                averages[cfg],
                -sum(s["active_counts"][cfg] for s in category_samples) / len(category_samples),
                -configs.index(cfg),
            ),
        )
    return policy


def stable_seed(base_seed: int, sample_index: int, config: str) -> int:
    """Build a reproducible seed for one sample/config generation."""
    digest = hashlib.sha256(f"{sample_index}:{config}".encode("utf-8")).hexdigest()
    offset = int(digest[:8], 16)
    return (base_seed + sample_index * 1009 + offset) % (2**31)


def set_generation_seed(seed: int):
    """Seed torch RNGs used by generation across available devices."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.backends.mps.is_available():
        try:
            torch.mps.manual_seed(seed)
        except AttributeError:
            pass


def checkpoint_path(output_dir: str, tag: str) -> str:
    return os.path.join(output_dir, f"{tag}_checkpoint.json")


def save_checkpoint(
    path: str,
    args: argparse.Namespace,
    configs: list[str],
    prompts: list[tuple[str, str]],
    samples: list[dict[str, Any]],
):
    payload = {
        "tag": args.tag,
        "benchmark_set": args.benchmark_set,
        "configs": configs,
        "prompts": [{"category": category, "prompt": prompt} for category, prompt in prompts],
        "samples": samples,
    }
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def load_checkpoint(
    path: str,
    configs: list[str],
    prompts: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    with open(path) as f:
        payload = json.load(f)

    saved_configs = payload.get("configs", [])
    if saved_configs != configs:
        raise ValueError(
            f"Checkpoint configs do not match current configs.\n"
            f"checkpoint={saved_configs}\ncurrent={configs}"
        )

    saved_prompts = payload.get("prompts", [])
    current_prompts = [{"category": category, "prompt": prompt} for category, prompt in prompts]
    if saved_prompts != current_prompts:
        raise ValueError("Checkpoint prompts do not match current benchmark/prompt selection.")

    return payload.get("samples", [])


def parse_block_scales(values: list[str] | None) -> dict[str, float]:
    """Parse block-type-specific scales from KEY=VALUE arguments."""
    scales: dict[str, float] = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"Invalid --block-scales item '{item}'. Expected name=value")
        name, value = item.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"Invalid --block-scales item '{item}'. Empty name")
        scales[name] = float(value)
    return scales


def run(args):
    requested_device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    os.makedirs(args.output, exist_ok=True)

    print(f"{'='*70}")
    print("BitDPM v0.5 Router Calibration")
    print(f"{'='*70}")
    print(f"  Model: {args.model}")
    print(f"  Requested device: {requested_device}")
    print(f"  Benchmark: {args.benchmark_set}")
    block_scales = parse_block_scales(args.block_scales)
    if block_scales:
        print(f"  Block-specific scales: {block_scales}")

    backbone = BackboneModel(
        model_name=args.model,
        device=requested_device,
        dtype=torch.float16 if not args.float32 else torch.float32,
        source=args.source,
    )
    device = backbone.device
    backbone_dtype = backbone.dtype
    print(f"  Effective device: {device}, backbone dtype: {backbone_dtype}")

    bank = load_block_dirs(args.load_blocks, device=torch.device(device), dtype=backbone_dtype)
    type_map = build_block_type_map(bank)
    all_ids = [m["block_id"] for m in bank.list_blocks()]
    configs = resolve_configs(type_map, args.configs)
    print(f"  Blocks: {len(bank)}")
    print(f"  Block types: {sorted(type_map)}")
    print(f"  Configs: {configs}")

    injector = BlockInjector(backbone)
    all_blocks = list(bank.blocks.values())
    injector.inject_blocks(all_blocks)

    prompts_by_category, expected_answers = get_benchmark_refs(args.benchmark_set)
    prompts = select_prompts(prompts_by_category, args.max_prompts_per_category)
    ckpt_path = checkpoint_path(args.output, args.tag)
    samples: list[dict[str, Any]] = []
    if args.resume and os.path.exists(ckpt_path):
        samples = load_checkpoint(ckpt_path, configs, prompts)
        print(f"  [Resume] Loaded {len(samples)} completed samples from {ckpt_path}")

    def activate(config: str) -> int:
        if config == "baseline":
            injector.set_active_blocks([])
            return 0
        if config == "always_all":
            default_per_block = args.block_scale / max(len(all_blocks), 1)
            for block in all_blocks:
                type_scale = block_scales.get(block.block_type)
                if type_scale is None:
                    block.scale = default_per_block
                else:
                    block.scale = type_scale / max(len(type_map.get(block.block_type, [])), 1)
            injector.set_active_blocks(None)
            return len(all_blocks)

        config_types = config.split("+") if "+" in config else [config]
        ids: list[str] = []
        for block_type in config_types:
            block_ids = type_map.get(block_type, [])
            config_scale = block_scales.get(block_type, block_scales.get(config, args.block_scale))
            per_block = config_scale / max(len(block_ids), 1)
            for bid in block_ids:
                bank.get_block(bid).scale = per_block
            ids.extend(block_ids)
        injector.set_active_blocks(ids)
        return len(ids)

    for idx, (category, prompt) in enumerate(prompts, start=1):
        if idx <= len(samples):
            saved = samples[idx - 1]
            if saved.get("category") == category and saved.get("prompt") == prompt:
                print(f"\n[{idx}/{len(prompts)}] {category}: {prompt[:72]}")
                print("  [Resume] skip completed sample")
                continue
            raise ValueError(f"Checkpoint sample mismatch at index {idx}")

        print(f"\n[{idx}/{len(prompts)}] {category}: {prompt[:72]}")
        sample = {
            "category": category,
            "prompt": prompt,
            "scores": {},
            "active_counts": {},
            "outputs": {} if args.save_outputs else None,
        }

        for config in configs:
            active_count = activate(config)
            if args.stable_sampling_seeds and not args.deterministic:
                set_generation_seed(stable_seed(args.seed, idx, config))
            start = time.time()
            output = backbone.generate(
                prompt,
                max_new_tokens=args.max_tokens,
                temperature=args.temperature,
                do_sample=not args.deterministic,
            )
            elapsed = time.time() - start
            score = compute_accuracy_with_refs(prompt, output, category, prompts_by_category, expected_answers)
            sample["scores"][config] = score
            sample["active_counts"][config] = active_count
            if args.save_outputs:
                sample["outputs"][config] = output
            print(f"  {config:<10} score={score:.1f} active={active_count} time={elapsed:.2f}s")

        samples.append(sample)
        if args.resume:
            save_checkpoint(ckpt_path, args, configs, prompts, samples)
            print(f"  [Checkpoint] saved {len(samples)}/{len(prompts)} samples")

    injector.remove_all_patches()

    config_results = {
        cfg: aggregate_scores(samples, [cfg] * len(samples))
        for cfg in configs
    }

    oracle_choices = [best_config_for_sample(sample, configs) for sample in samples]
    oracle = aggregate_scores(samples, oracle_choices)
    selection_frequency = {cfg: oracle_choices.count(cfg) for cfg in configs}

    calib_indices, eval_indices = split_calibration_indices(samples, args.calib_ratio)
    category_policy = choose_category_policy(samples, calib_indices, configs)
    calibrated_eval_samples = [samples[i] for i in sorted(eval_indices)]
    calibrated_choices = [
        category_policy.get(sample["category"], "baseline")
        for sample in calibrated_eval_samples
    ]
    validation_calibrated = aggregate_scores(calibrated_eval_samples, calibrated_choices)

    utility_matrix = {
        category: {
            cfg: config_results[cfg].category_scores.get(category, 0.0)
            for cfg in configs
        }
        for category in prompts_by_category
        if any(sample["category"] == category for sample in samples)
    }

    result = V05Results(
        model=args.model,
        device=device,
        benchmark_set=args.benchmark_set,
        total_prompts=len(samples),
        block_scale=args.block_scale,
        block_scales=block_scales,
        max_tokens=args.max_tokens,
        config_results=config_results,
        oracle=oracle,
        validation_calibrated=validation_calibrated,
        category_policy=category_policy,
        utility_matrix=utility_matrix,
        selection_frequency=selection_frequency,
        per_sample=samples,
    )

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(args.output, f"{args.tag}_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for cfg in configs:
        agg = config_results[cfg]
        print(f"{cfg:<12} overall={agg.overall:.3f} active={agg.active_blocks:.2f}")
    print(f"oracle      overall={oracle.overall:.3f} active={oracle.active_blocks:.2f} freq={selection_frequency}")
    print(
        "calibrated  "
        f"overall={validation_calibrated.overall:.3f} "
        f"active={validation_calibrated.active_blocks:.2f} "
        f"policy={category_policy}"
    )
    print(f"\nSaved: {out_path}")
    if args.resume and os.path.exists(ckpt_path):
        print(f"Checkpoint retained: {ckpt_path}")


def main():
    parser = argparse.ArgumentParser(description="BitDPM v0.5 router calibration")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--load-blocks", type=str, nargs="+", default=["experiments/outputs/blocks"])
    parser.add_argument("--device", type=str, default="")
    parser.add_argument("--source", type=str, default="auto")
    parser.add_argument("--benchmark-set", type=str, default="core", choices=["core", "v08", "v14", "v15", "v1k", "v1k_clean"],
                        help="Benchmark set: core=45 historical, v08=100 expanded, v14=300 stratified, v15=120 router validation, v1k/v1k_clean=1000 mixed")
    parser.add_argument("--output", type=str, default="experiments/reports")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--block-scale", type=float, default=0.15)
    parser.add_argument("--block-scales", nargs="+", default=None,
                        help="Optional per-block-type total scales, e.g. commonsense_choice=0.75 format_following=0.45")
    parser.add_argument("--calib-ratio", type=float, default=0.5)
    parser.add_argument("--max-prompts-per-category", type=int, default=0)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--seed", type=int, default=0,
                        help="Torch RNG seed for sampling-based matched-protocol checks")
    parser.add_argument("--stable-sampling-seeds", action="store_true",
                        help="Use a fixed seed per sample/config so sampling results are comparable across config lists")
    parser.add_argument("--save-outputs", action="store_true")
    parser.add_argument("--resume", action="store_true",
                        help="Write/read a per-tag checkpoint so long evaluations can resume after interruption.")
    parser.add_argument("--float32", action="store_true")
    parser.add_argument("--configs", nargs="+", default=None,
                        help="Optional explicit configs to evaluate. baseline and always_all are special names.")
    parser.add_argument("--tag", type=str, default="v05_router_calibration",
                        help="Report filename prefix")
    args = parser.parse_args()

    if args.quick and args.max_prompts_per_category == 0:
        args.max_prompts_per_category = 2

    torch.manual_seed(args.seed)

    run(args)


if __name__ == "__main__":
    main()
