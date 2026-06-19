# BitDPM: Bit-level Dynamic Parameter Mixing

**BitDPM** is a framework for efficient LLM inference on local devices through dynamic parameter composition.

## Core Idea

Instead of loading a full model for every task, BitDPM maintains:
- A **low-bit main model** W_main (INT4/INT8/FP16)
- Multiple **independent parameter blocks** ΔW_i (LoRA-like low-rank updates)
- Runtime **parameter composition**: W_eff = W_main + Σ g_i · ΔW_i

This enables:
- Task-specific model adaptation without full fine-tuning
- Memory savings by loading only needed parameter blocks
- CPU + GPU cooperative scheduling for resource-constrained devices

## Installation

```bash
# Core dependencies
pip install torch transformers datasets

# Optional: Use ModelScope for model downloads (China-friendly)
pip install modelscope

# Optional: bitsandbytes for INT4/INT8 quantization
pip install bitsandbytes

# Optional: psutil for memory measurement
pip install psutil
```

## Quick Start

```bash
# 1. Baseline: Test the backbone model (use local path if already downloaded)
python scripts/run_baseline.py --model /path/to/Qwen2.5-0.5B-Instruct --latency

# 2. Or download from HuggingFace
python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --latency

# 3. Or download from ModelScope (if HuggingFace is slow/unavailable)
python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --source modelscope --latency

# 4. Interactive generation
python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --interactive

# 5. Full benchmark
python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --benchmark

# 6. BitDPM with parameter blocks
python scripts/run_bitdpm.py --model Qwen/Qwen2.5-0.5B-Instruct --num-blocks 3 --benchmark

# 7. BitDPM with router
python scripts/run_bitdpm.py --model Qwen/Qwen2.5-0.5B-Instruct --num-blocks 3 --router --interactive

# 8. Train and evaluate a single block
python scripts/run_single_block.py --model Qwen/Qwen2.5-0.5B-Instruct --train --benchmark

# 9. Run all evaluations
# Use --source modelscope if you're in China or HuggingFace is unreachable
python scripts/eval_all.py --quick --source modelscope
python scripts/eval_all.py --full
```

### Model Download Sources

BitDPM supports downloading models from **HuggingFace** (default) or **ModelScope**:

| Flag | Source | Best for |
|------|--------|----------|
| `--source hf` | HuggingFace Hub | Default — global users |
| `--source modelscope` | ModelScope (modelscope.cn) | China, fast downloads |
| `--source auto` | Try HF first, fallback to ModelScope | Mixed environments |
| `--model /local/path` | Local filesystem | Already downloaded models |

Set `MODELSCOPE=1` environment variable to prefer ModelScope automatically:
```bash
export MODELSCOPE=1
python scripts/run_baseline.py --model Qwen/Qwen2.5-0.5B-Instruct --latency
```

**Known ModelScope model IDs:**
| HuggingFace ID | ModelScope ID |
|----------------|---------------|
| `Qwen/Qwen2.5-0.5B-Instruct` | `Qwen/Qwen2.5-0.5B-Instruct` |
| `Qwen/Qwen2.5-1.5B-Instruct` | `Qwen/Qwen2.5-1.5B-Instruct` |
| `meta-llama/Llama-3.2-1B` | `LLM-Research/Llama-3.2-1B` |

## Run Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
BitDPM/
├── configs/                  # YAML configurations
│   ├── bitdpm_qwen05b.yaml
│   └── bitdpm_qwen15b.yaml
├── bitdpm/                   # Core library
│   ├── models/               # Backbone and patching
│   │   ├── backbone.py       # HuggingFace model wrapper
│   │   └── patch_lora.py     # LoRA-like parameter injection
│   ├── params/               # Parameter blocks
│   │   ├── parameter_block.py  # Low-rank ΔW = A·B blocks
│   │   ├── block_bank.py     # Block storage and lookup
│   │   └── composer.py       # W_eff = W_main + Σ g·ΔW
│   ├── router/               # Block selection
│   │   ├── simple_router.py  # Keyword-based routing
│   │   └── entropy_router.py # Confidence-aware routing (future)
│   ├── runtime/              # CPU/GPU/Storage scheduling
│   │   ├── cpu_scheduler.py  # CPU-side scheduling (future)
│   │   ├── gpu_executor.py   # GPU execution (future)
│   │   └── cache_manager.py  # Block cache (future)
│   ├── train/                # Training utilities
│   └── eval/                 # Evaluation
│       ├── benchmark.py      # Accuracy benchmarks
│       ├── latency.py        # Speed measurement
│       └── memory.py         # Memory footprint
├── scripts/                  # Run scripts
│   ├── run_baseline.py       # Baseline evaluation
│   ├── run_single_block.py   # Single block training/eval
│   ├── run_bitdpm.py         # Full BitDPM evaluation
│   └── eval_all.py           # All configurations comparison
├── experiments/              # Results storage
└── tests/                    # Unit tests
```

## Development Roadmap

See the full roadmap in the project documentation. Key milestones:

1. **Milestone 1**: Baseline model evaluation (current)
2. **Milestone 2**: Single parameter block training/injection
3. **Milestone 3**: Multiple independent blocks
4. **Milestone 4**: Keyword-based router
5. **Milestone 5**: Low-bit main model (INT4/INT8)
6. **Milestone 6**: CPU + GPU scheduling
7. **Milestone 7**: Full evaluation report

## License

MIT
