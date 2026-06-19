# BitDPM v15 Router-Validation Plan

## Purpose

v14 full validation established that BitDPM has a real sparse-correction oracle (`0.903` over baseline `0.840`, coverage `19/300`) and that the current safest deployable router is the atomic allow-core utility router (`0.857` strict CV, `5` fixes, `0` breaks). The next bottleneck is not adding more blocks; it is expanding safe router triggers without introducing baseline breaks.

v15 is therefore a router-validation benchmark, not a broad capability benchmark.

## Benchmark Design

`bitdpm/eval/v15_benchmark.py` defines 120 prompts across six validation slices:

| Slice | N | Role |
|---|---:|---|
| `router_multiplication` | 20 | current safe allow-core trigger family |
| `router_core_mixed` | 20 | distance, log, and mean triggers |
| `router_risky_arithmetic` | 20 | addition and sqrt controls that caused prior breaks |
| `router_factual_constants` | 20 | candidate factual trigger expansion |
| `router_commonsense_repairs` | 20 | candidate commonsense repair expansion |
| `router_commonsense_controls` | 20 | baseline-correct commonsense safety controls |

All prompts have explicit expected answers, so the benchmark can be used for strict router safety checks.

## Command

Run the full validation suite with:

```bash
bash experiments/reports/v15_router_validation_commands.sh
```

This command runs:

- v11 admitted pool on `--benchmark-set v15`
- block safety analysis
- utility mining
- allow-core full-report router
- allow-core strict CV router
- conjunction full-report router
- conjunction strict CV router
- paper table rebuild

## Decision Gates

The current router to beat is:

- strict CV: `0.857`
- baseline: `0.840`
- gain: `+0.017`
- fixes: `5`
- breaks: `0`

v15 should be interpreted with stricter gates than oracle evaluation:

1. A router expansion is admissible only if strict CV has `0` breaks.
2. A new trigger family should improve either strict-CV gain or held-out fixes.
3. Full-report gains without held-out safety are diagnostic only.
4. Conjunction features are not admitted unless they beat atomic allow-core under zero-break strict CV.
5. Always-All remains a negative control, not a target mode.

## Expected Outcomes

Possible outcomes:

- If allow-core remains zero-break but does not improve coverage, it remains the deployable baseline.
- If factual or commonsense triggers improve full-report score but fail CV, they become data-mining targets, not admitted router rules.
- If a new trigger family achieves zero-break CV and adds fixes beyond allow-core, it becomes the next admitted router expansion.

## Current Interpretation Before Running

The best current claim remains:

BitDPM supports runtime-selective sparse correction. Conservative utility-aware routing recovers part of the oracle gain with zero observed held-out breaks on v14 full validation. v15 is designed to test whether this zero-break router can be safely expanded beyond arithmetic-like correction features.

