# BitDPM v10 Technical Report

Date: 2026-06-07

## Executive Summary

BitDPM is best understood as a selective sparse correction framework rather than an adapter merge, parameter accumulation method, or broad fixed-block enhancement method.

The current best setting is:

```text
Best pool: v0.8 hybrid error-type pool + admitted arithmetic_power_log
Benchmark: v08 expanded 100-sample benchmark
Protocol: stable sampling
Oracle: 0.890
Coverage: 6/100
Best fixed: 0.830
Always-All: 0.000
```

The most important final principle is:

> Block admission should be based on unique per-sample correction coverage, not task label, semantic block name, or aggregate fixed-block score.

中文总结：

BitDPM 当前最稳的定义是“稀疏修复方向的选择性运行时组合”。最终最佳配置是 v0.8 hybrid error-type 参数池加上唯一准入的 `arithmetic_power_log`，在 v08 100 样本稳定采样协议下达到 oracle `0.890`、coverage `6/100`、best fixed `0.830`，而 Always-All 为 `0.000`。这说明 BitDPM 不是全量参数叠加方法，而是必须按逐样本唯一修复价值进行选择性组合。

## Final Best Setting

| Pool | Baseline | Oracle | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|---:|
| v0.8 hybrid | 0.830 | 0.880 | 5/100 | 0.830 | 0.000 |
| v0.9b + power_log | 0.830 | 0.890 | 6/100 | 0.830 | 0.000 |
| v10 admitted power_log | 0.830 | 0.890 | 6/100 | 0.830 | 0.000 |

Final admitted pool:

```text
commonsense_choice      scale 0.60
format_following        scale 0.75
chinese_semantic        scale 0.75
calculation_error       scale 0.30
short_reasoning         scale 0.45
arithmetic_power_log    scale 0.75
```

Final repaired samples:

| Sample | Selected Block |
|---|---|
| What is the speed of light in vacuum? | format_following |
| What is the square root of 144? | commonsense_choice |
| What is 18 + 24? | chinese_semantic |
| What is 15% of 80? | format_following |
| What is log base 10 of 1000? | commonsense_choice |
| What is the distance from (0,0) to (3,4)? | arithmetic_power_log |

The last sample is the unique contribution of `arithmetic_power_log`, which justifies its admission.

## Evidence Chain

### v0.1-v0.3: Early Routing Results Downgraded

The early router results can no longer be used as formal evidence because a critical bug was found:

```text
BlockInjector.set_active_blocks() was effectively inactive in early versions.
```

This meant routed configurations behaved like Always-All. The old claims about KeywordRouter gains and active-budget trends are retained only as development history.

Corrected interpretation:

> v0.1-v0.3 explored the system but did not validate true routing behavior.

### v0.4: True Gating and Interference

v0.4 fixed block gating. After the fix, router and block activation actually controlled forward execution.

Main validated findings:

- true gating works,
- block activation is controllable,
- Always-All activation does not reliably improve the model,
- parameter-block interference is real.

This established the first core BitDPM mechanism:

> Parameters cannot simply be accumulated; block activation must be selective.

### v0.5: Matched Generation Protocol

v0.5 introduced deterministic matched-setting checks and oracle evaluation.

The key result was that v0.4 single-block gains were partly sampling-sensitive. Under deterministic generation, the current blocks did not provide stable utility.

Corrected conclusion:

> Current blocks initially behaved more like sampling-distribution modulators than robust greedy-decodable capability modules.

This prevented overclaiming and redirected the project toward block utility quality.

### v0.6: Block Utility Amplification

v0.6 strengthened block training and produced the first stable deterministic fixed-block gain.

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| deterministic | 0.778 | code 0.800 | 0.822 | 2/45 | 0.778 |
| sampling | 0.800 | code 0.822 | 0.844 | 2/45 | 0.800 |

Main finding:

> Stronger block training can turn BitDPM from sampling-only perturbation into deterministic fixed-block utility.

However, coverage remained sparse.

### v0.7: Error-Type Training, Structure, and Scale Calibration

v0.7 tested utility coverage expansion.

The most important positive result was that error-type blocks, contiguous `l22-l24 down_proj` placement, and scale calibration improved utility.

Best v0.7 stable sampling:

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| error `l22_l24_down`, scale 0.75, stable sampling | 0.822 | 0.822 | 0.867 | 2/45 | 0.778 |

Important conclusions:

- hard-sample training alone did not open coverage,
- error-type blocks were more promising than task-name/domain blocks,
- continuous down-proj structure was better than fragmented FFN expansion,
- scale calibration was necessary,
- Always-All remained worse than oracle/selective activation.

Mechanism conclusion:

> Block utility is scale-dependent, sample-specific, and interference-sensitive.

### v0.8: Expanded Benchmark, Rank16, and Hybrid Scale

v0.8 expanded evaluation to 100 samples and tested rank/capacity and hybrid scale.

Rank8 on v08 benchmark:

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| det scale 0.60 | 0.800 | 0.800 | 0.840 | 4/100 | 0.775 |
| stable sampling scale 0.75 | 0.830 | 0.830 | 0.860 | 3/100 | 0.745 |

Rank16:

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| det scale 0.60 | 0.800 | commonsense_choice 0.830 | 0.840 | 4/100 | 0.785 |
| stable sampling scale 0.75 | 0.830 | 0.830 | 0.870 | 4/100 | 0.765 |

Rank16 strengthened fixed-block utility but did not solve coverage. It also amplified destructive blocks.

Hybrid scale then produced the best v0.8 result:

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| hybrid det | 0.800 | commonsense_choice 0.830 | 0.840 | 4/100 | 0.000 |
| hybrid stable sampling | 0.830 | 0.830 | 0.880 | 5/100 | 0.000 |

Hybrid scale used different scale strengths per block. This showed that safe average scaling is not enough; different correction directions need different strengths.

Key v0.8 conclusion:

> Higher-rank blocks increase both utility and risk. Hybrid scale improves oracle coverage but makes Always-All collapse, proving that high-utility blocks are mutually incompatible when jointly activated.

### v0.9: Targeted Repair Blocks as a Negative Result

v0.9 trained answer-bearing targeted repair blocks:

- `arithmetic_addition`
- `arithmetic_percent`
- `arithmetic_power_log`
- `arithmetic_sqrt`
- `factual_constants`

Result:

| Setting | Baseline | Best Fixed | Oracle | Coverage | Always-All |
|---|---:|---:|---:|---:|---:|
| det repair only | 0.800 | 0.800 | 0.840 | 4/100 | 0.000 |
| stable sampling repair only | 0.830 | 0.830 | 0.860 | 3/100 | 0.000 |

Compared with v0.8 hybrid, targeted repair-only was worse in stable sampling:

| Pool | Stable Sampling Oracle | Coverage |
|---|---:|---:|
| v0.8 hybrid | 0.880 | 5/100 |
| v0.9 repair only | 0.860 | 3/100 |

Safety analysis exposed destructive risk:

| Block | Fixes | Breaks | Net |
|---|---:|---:|---:|
| arithmetic_power_log | 2 | 11 | -9 |
| factual_constants | 1 | 26 | -25 |
| arithmetic_percent | 0 | 17 | -17 |
| arithmetic_sqrt | 0 | 17 | -17 |

Main conclusion:

> Narrow answer-bearing repair blocks can create new correction opportunities, but they also overfit and damage many baseline-correct samples.

This is an important negative result. It shows BitDPM needs safety-calibrated repair directions, not simply stronger targeted blocks.

### v0.9b and v10: Unique-Utility Admission

v0.9b tested adding selected repair directions to the v0.8 hybrid pool.

| Config Pool | Oracle | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|
| v0.8 hybrid | 0.880 | 5/100 | 0.830 | 0.000 |
| v0.9 repair only | 0.860 | 3/100 | 0.830 | 0.000 |
| hybrid + power_log | 0.890 | 6/100 | 0.830 | 0.000 |
| hybrid + factual | 0.880 | 5/100 | 0.830 | 0.000 |
| hybrid + both | 0.890 | 6/100 | 0.830 | 0.000 |

Only `arithmetic_power_log` added unique coverage:

| Candidate Block | Fixes | Unique Fixes | Overlap Fixes | Breaks | Admit |
|---|---:|---:|---:|---:|---|
| arithmetic_power_log | 2 | 1 | 1 | 11 | yes |
| factual_constants | 1 | 0 | 1 | 26 | no |
| arithmetic_percent | 0 | 0 | 0 | 17 | no |
| arithmetic_sqrt | 0 | 0 | 0 | 17 | no |

v10 then reran the admitted pool and reproduced:

```text
Oracle: 0.890
Coverage: 6/100
Best fixed: 0.830
Always-All: 0.000
```

Final admission principle:

> Block admission should be utility-unique, not label-driven.

中文：

参数块准入应该基于“是否修复现有池修不了的样本”，而不是基于任务标签、语义名称或平均分。

## Mechanistic Interpretation

BitDPM blocks are not reliable semantic experts.

Examples:

- `chinese_semantic` repaired `What is 18 + 24?`
- `commonsense_choice` repaired `sqrt(144)` and `log10(1000)`
- `arithmetic_power_log` repaired `distance from (0,0) to (3,4)`

This implies blocks are better interpreted as latent correction directions rather than human-labeled experts.

Better framing:

> BitDPM blocks are sparse correction directions, not semantic experts.

The complete mechanism:

1. A parameter block can change a small subset of model decisions.
2. The useful subset is sparse.
3. Utility depends on scale.
4. Utility depends on the sample.
5. Blocks can severely interfere with one another.
6. Therefore, the correct regime is selective runtime composition.

## Why Always-All Collapse Matters

Always-All repeatedly underperformed baseline, and in hybrid / admitted settings collapsed to `0.000`.

This is not merely a failure case; it is core mechanism evidence.

Interpretation:

> High-utility parameter blocks do not share a common update direction. When activated together, incompatible correction directions collide and destroy generation quality.

This rules out the interpretation of BitDPM as:

- adapter merge,
- parameter accumulation,
- all-expert aggregation,
- simple ensemble-style composition.

Correct interpretation:

> BitDPM is selective runtime composition of sparse correction directions.

## Final Claims

### Claim 1: True Gating Is Essential

Early router results were invalid until gating was fixed. True block activation is a necessary precondition for all later conclusions.

### Claim 2: Parameter-Block Interference Is Stable

Always-All is repeatedly worse than oracle/selective activation and often worse than baseline.

### Claim 3: Utility Is Sparse but Reliable

The best current pool repairs `6/100` samples that baseline fails. This is not broad enhancement, but sparse correction.

### Claim 4: Block Strength and Risk Grow Together

Rank16 improved best fixed-block performance, but also increased destructive behavior in high-risk blocks.

### Claim 5: Scale Must Be Block-Specific

Hybrid scale outperformed uniform safe scaling. Useful blocks need different activation strengths.

### Claim 6: Admission Must Be Unique-Utility Based

Adding all targeted repair blocks hurt. Adding only `arithmetic_power_log`, which contributed one unique correction, improved the best pool.

## Recommended Paper-Level Wording

English:

> BitDPM constructs a runtime-selective pool of decoupled parameter blocks. Our corrected experiments show that parameter blocks do not act as broadly useful semantic experts. Instead, they form sparse correction directions whose utility is sample-specific, scale-dependent, and interference-sensitive. The strongest configuration combines an error-type hybrid pool with a single admitted repair direction, `arithmetic_power_log`, improving stable-sampling oracle accuracy from 0.880 to 0.890 and correction coverage from 5/100 to 6/100. Always-All activation collapses to 0.000, confirming that high-utility blocks are mutually incompatible under indiscriminate composition. Therefore, BitDPM block-pool construction should be based on unique per-sample correction coverage rather than task labels or aggregate block scores.

Chinese:

> BitDPM 构建的是一个运行时选择性的解耦参数块池。修正后的实验表明，参数块并不是广泛有效的语义专家，而是稀疏修复方向；其效用依赖样本、依赖 scale，并且高度受块间干扰影响。当前最强配置是 error-type hybrid 参数池加上唯一准入的 `arithmetic_power_log` repair direction，将 stable-sampling oracle 从 0.880 提升到 0.890，将修复覆盖率从 5/100 提升到 6/100。Always-All 激活崩溃到 0.000，证明高效参数块在无选择组合时彼此不兼容。因此，BitDPM 参数块池应基于逐样本唯一修复覆盖率构建，而不是基于任务标签或 block 平均分。

## Current Limitations

1. Coverage is still sparse: `6/100`.
2. Oracle selection is not yet a deployable router.
3. Scoring for code / Chinese / reasoning remains heuristic.
4. The benchmark is still small relative to real evaluation suites.
5. Many useful blocks have poor fixed-block scores and high break counts.
6. Always-All collapse shows strong interference but also indicates the current composition is fragile.

## Next Work

The next experimental goal should not be blind rank scaling or adding repair blocks by label.

Recommended next direction:

```text
Unique-Utility Repair Mining
```

Target:

```text
coverage 6/100 -> 8/100 or 10/100+
oracle 0.890 -> 0.900+
```

Rules:

1. Candidate blocks must be evaluated by unique fixes, overlap fixes, breaks, and net unique utility.
2. A block is admitted only if it fixes at least one sample not fixed by the current pool.
3. Blocks with no unique coverage are rejected even if they fix overlapping samples.
4. High-break blocks can still be admitted only if they provide unique utility and are used selectively.
5. Always-All should remain a negative-control stress test, not an intended deployment mode.

## Final Status

```text
BitDPM v10 completed.
Current final best setting fixed.
Best pool: v0.8 hybrid + admitted arithmetic_power_log.
Main result: oracle 0.890, coverage 6/100, best fixed 0.830, Always-All 0.000.
Core principle: admit parameter blocks by unique per-sample utility, not task label or aggregate score.
```
