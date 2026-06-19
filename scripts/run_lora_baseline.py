#!/usr/bin/env python3
"""Train/evaluate a standard always-on LoRA adapter baseline.

This is an external baseline for BitDPM. It uses PEFT LoRA when available and
reports the same benchmark metrics as the prompt-only and BitDPM evaluations.
The script is intentionally conservative: it is not used by the report-only
paper package unless the user runs it and produces JSON outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitdpm.eval.benchmark import EVAL_PROMPTS, EXPECTED_ANSWERS, compute_accuracy_with_refs
from bitdpm.eval.v08_benchmark import V08_EVAL_PROMPTS, V08_EXPECTED_ANSWERS
from bitdpm.eval.v14_benchmark import V14_EVAL_PROMPTS, V14_EXPECTED_ANSWERS
from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS, V15_EXPECTED_ANSWERS
from bitdpm.eval.v1k_benchmark import V1K_EVAL_PROMPTS, V1K_EXPECTED_ANSWERS
from bitdpm.eval.v1k_clean_benchmark import V1K_CLEAN_EVAL_PROMPTS, V1K_CLEAN_EXPECTED_ANSWERS
from bitdpm.models.backbone import _resolve_model_source
from scripts.run_prompt_only_baseline import select_prompts
from scripts.train_v24_real_data import PERCENT_PROBLEMS, GENERAL_INSTRUCTIONS, GENERAL_ANSWERS, generate_v24_data


@dataclass
class LoraSummary:
    model: str
    benchmark_set: str
    train_samples: int
    rank: int
    alpha: int
    epochs: int
    lr: float
    total_prompts: int
    baseline: float
    lora: float
    delta: float
    fixes: int
    breaks: int
    net: int
    max_tokens: int
    deterministic: bool


@dataclass
class LoraReport:
    summary: LoraSummary
    category_scores: dict[str, dict[str, float]]
    rows: list[dict[str, Any]] = field(default_factory=list)
    train_loss: list[float] = field(default_factory=list)


class TextDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_length: int):
        self.rows = []
        for text in texts:
            encoded = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"][0]
            labels = input_ids.clone()
            labels[encoded["attention_mask"][0] == 0] = -100
            self.rows.append(
                {
                    "input_ids": input_ids,
                    "attention_mask": encoded["attention_mask"][0],
                    "labels": labels,
                }
            )

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return self.rows[idx]


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


def build_train_texts(limit: int) -> list[str]:
    repair, preserve, hard = generate_v24_data(
        PERCENT_PROBLEMS,
        GENERAL_INSTRUCTIONS,
        GENERAL_ANSWERS,
        num_repair=max(10, limit // 2),
        num_preserve=max(5, limit // 3),
        num_hard=max(5, limit // 6),
    )
    texts = repair + preserve + hard
    return texts[:limit]


def load_base_model(model_name: str, device: str, dtype: torch.dtype, source: str):
    resolved, _ = _resolve_model_source(model_name, prefer="modelscope" if source == "modelscope" else "hf")
    tokenizer = AutoTokenizer.from_pretrained(resolved, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        resolved,
        trust_remote_code=True,
        torch_dtype=dtype,
        attn_implementation="sdpa",
    ).to(device)
    return model, tokenizer


@torch.no_grad()
def generate(model, tokenizer, prompt: str, device: str, args: argparse.Namespace) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=args.max_tokens,
        temperature=args.temperature,
        do_sample=not args.deterministic,
        pad_token_id=tokenizer.pad_token_id,
    )
    return tokenizer.decode(outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True)


def aggregate_category(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}
    for row in rows:
        category = row["category"]
        totals.setdefault(category, {"baseline": 0.0, "lora": 0.0})
        counts[category] = counts.get(category, 0) + 1
        totals[category]["baseline"] += float(row["baseline_score"])
        totals[category]["lora"] += float(row["lora_score"])
    return {
        category: {
            "baseline": values["baseline"] / counts[category],
            "lora": values["lora"] / counts[category],
            "delta": (values["lora"] - values["baseline"]) / counts[category],
        }
        for category, values in totals.items()
    }


def train_lora(model, tokenizer, train_texts: list[str], device: str, args: argparse.Namespace) -> list[float]:
    try:
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:
        raise RuntimeError(
            "PEFT is required for the LoRA baseline. Install with `pip install peft` "
            "or add the project extra once dependencies are refreshed."
        ) from exc

    target_modules = [item.strip() for item in args.target_modules.split(",") if item.strip()]
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        target_modules=target_modules,
        bias="none",
    )
    model = get_peft_model(model, config)
    model.train()
    dataset = TextDataset(train_texts, tokenizer, args.max_length)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    losses: list[float] = []
    for epoch in range(args.epochs):
        total = 0.0
        count = 0
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            total += float(loss.detach().cpu())
            count += 1
        avg = total / max(count, 1)
        losses.append(avg)
        print(f"[LoRA] epoch={epoch + 1}/{args.epochs} loss={avg:.4f}")
    model.eval()
    return losses


def run(args: argparse.Namespace) -> None:
    prompts_by_category, expected_answers = get_benchmark_refs(args.benchmark_set)
    prompts = select_prompts(prompts_by_category, args.max_prompts_per_category)
    train_texts = build_train_texts(args.train_samples)
    if args.dry_run:
        print(f"benchmark={args.benchmark_set} eval_prompts={len(prompts)} train_texts={len(train_texts)}")
        print(f"target_modules={args.target_modules}")
        print("first_train_text=", train_texts[0] if train_texts else "")
        return

    device = args.device or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else "cpu"
    )
    dtype = torch.float32 if args.float32 else torch.float16
    base_model, tokenizer = load_base_model(args.model, device, dtype, args.source)
    lora_model, _ = load_base_model(args.model, device, dtype, args.source)
    losses = train_lora(lora_model, tokenizer, train_texts, device, args)

    rows: list[dict[str, Any]] = []
    baseline_total = 0.0
    lora_total = 0.0
    fixes = 0
    breaks = 0
    for idx, (category, prompt) in enumerate(prompts, start=1):
        print(f"[{idx}/{len(prompts)}] {category}: {prompt[:72]}")
        base_output = generate(base_model, tokenizer, prompt, device, args)
        lora_output = generate(lora_model, tokenizer, prompt, device, args)
        base_score = compute_accuracy_with_refs(prompt, base_output, category, prompts_by_category, expected_answers)
        lora_score = compute_accuracy_with_refs(prompt, lora_output, category, prompts_by_category, expected_answers)
        if lora_score >= args.correct_threshold and base_score < args.correct_threshold:
            fixes += 1
        elif base_score >= args.correct_threshold and lora_score < args.correct_threshold:
            breaks += 1
        baseline_total += base_score
        lora_total += lora_score
        row = {
            "index": idx - 1,
            "category": category,
            "prompt": prompt,
            "baseline_score": base_score,
            "lora_score": lora_score,
        }
        if args.save_outputs:
            row["baseline_output"] = base_output
            row["lora_output"] = lora_output
        rows.append(row)
        print(f"  baseline={base_score:.1f} lora={lora_score:.1f}")

    n = max(len(rows), 1)
    summary = LoraSummary(
        model=args.model,
        benchmark_set=args.benchmark_set,
        train_samples=len(train_texts),
        rank=args.rank,
        alpha=args.alpha,
        epochs=args.epochs,
        lr=args.lr,
        total_prompts=len(rows),
        baseline=baseline_total / n,
        lora=lora_total / n,
        delta=(lora_total - baseline_total) / n,
        fixes=fixes,
        breaks=breaks,
        net=fixes - breaks,
        max_tokens=args.max_tokens,
        deterministic=args.deterministic,
    )
    report = LoraReport(summary=summary, category_scores=aggregate_category(rows), rows=rows, train_loss=losses)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"{args.tag}_{ts}.json"
    md_path = out_dir / f"{args.tag}_{ts}.md"
    json_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(make_markdown(report), encoding="utf-8")
    print(
        f"lora={summary.lora:.3f} baseline={summary.baseline:.3f} "
        f"delta={summary.delta:+.3f} fixes={fixes} breaks={breaks} net={fixes - breaks}"
    )
    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")


def make_markdown(report: LoraReport) -> str:
    s = report.summary
    lines = [
        "# BitDPM Standard LoRA Baseline",
        "",
        f"- Model: `{s.model}`",
        f"- Benchmark: `{s.benchmark_set}`",
        f"- Train samples: {s.train_samples}",
        f"- Rank / alpha: {s.rank}/{s.alpha}",
        f"- Epochs: {s.epochs}",
        f"- Baseline: {s.baseline:.3f}",
        f"- LoRA: {s.lora:.3f}",
        f"- Delta: {s.delta:+.3f}",
        f"- Fixes / breaks / net: {s.fixes}/{s.breaks}/{s.net}",
        "",
        "## Category Scores",
        "",
        "| Category | Baseline | LoRA | Delta |",
        "|---|---:|---:|---:|",
    ]
    for category, scores in sorted(report.category_scores.items()):
        lines.append(f"| {category} | {scores['baseline']:.3f} | {scores['lora']:.3f} | {scores['delta']:+.3f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/evaluate a standard LoRA baseline.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--device", default="")
    parser.add_argument("--source", default="auto", choices=["auto", "hf", "modelscope"])
    parser.add_argument("--benchmark-set", default="v14", choices=["core", "v08", "v14", "v15", "v1k", "v1k_clean"])
    parser.add_argument("--output", default="experiments/reports/lora_baseline")
    parser.add_argument("--tag", default="lora_baseline")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=int, default=32)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")
    parser.add_argument("--train-samples", type=int, default=120)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=96)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--float32", action="store_true")
    parser.add_argument("--correct-threshold", type=float, default=1.0)
    parser.add_argument("--max-prompts-per-category", type=int, default=0)
    parser.add_argument("--save-outputs", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
