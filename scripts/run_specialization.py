#!/usr/bin/env python3
"""Block specialization matrix: test each block type per category.

Usage:
    python scripts/run_specialization.py --model /path/to/model
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from bitdpm.eval.benchmark import (
    EVAL_PROMPTS, run_benchmark, format_benchmark_table, save_benchmark_results,
)
from bitdpm.eval.memory import measure_model_memory
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank

MODEL_PATH = os.environ.get("MODEL_PATH", "/Users/yyl/Desktop/workshop/Evidence-to-Answer Trace/internal_cot_index/models/Qwen--Qwen2.5-0.5B-Instruct")
BLOCK_DIR = "experiments/outputs/blocks"
R = 10  # random seed

def get_type_map(bank):
    m = {}
    for meta in bank.list_blocks():
        m.setdefault(meta["block_type"], []).append(meta["block_id"])
    return m

def main():
    device = "cpu"
    print(f"Loading backbone...")
    backbone = BackboneModel(model_name=MODEL_PATH, device=device, dtype=torch.float16)
    print(f"Loading blocks...")
    bank = BlockBank.load_all(BLOCK_DIR, device=torch.device(device))
    type_map = get_type_map(bank)

    block_types = ["general", "math", "code", "chinese"]
    results = []

    # Baseline
    mem = measure_model_memory(backbone.model, device)
    r = run_benchmark(lambda p: backbone.generate(p, max_new_tokens=64, temperature=0.1), verbose=False)
    r.model_name = "Baseline"; r.quant = "FP16"
    r.num_params = f"{backbone.num_params()/1e9:.1f}B"; r.device = device; r.peak_memory_mb = mem.total_model_mb
    results.append(r)
    print(f"Baseline: {r.overall_score:.3f}")

    # Per block type
    for bt in block_types:
        bids = type_map.get(bt, [])
        if not bids: continue
        injector = BlockInjector(backbone)
        blocks = [bank.get_block(bid) for bid in bids if bid in bank.blocks]
        for b in blocks: b.scale = 0.15 / max(len(blocks), 1)
        injector.inject_blocks(blocks)
        r = run_benchmark(lambda p: backbone.generate(p, max_new_tokens=64, temperature=0.1), verbose=False)
        r.model_name = f"Only {bt}"; r.quant = "FP16+blocks"
        r.num_params = f"{backbone.num_params()/1e9:.1f}B"; r.device = device; r.peak_memory_mb = mem.total_model_mb
        results.append(r)
        injector.remove_all_patches()
        print(f"Only {bt}: {r.overall_score:.3f}", end="")
        for cat, sc in r.category_scores.items():
            print(f"  {cat[:4]}={sc:.1f}", end="")
        print()

    # Summary
    print(f"\n{format_benchmark_table(results)}")
    ts = time.strftime("%Y%m%d_%H%M%S")
    save_benchmark_results(results, f"experiments/reports/v04_spec_{ts}.json")
    print(f"Saved to experiments/reports/v04_spec_{ts}.json")

if __name__ == "__main__":
    main()
