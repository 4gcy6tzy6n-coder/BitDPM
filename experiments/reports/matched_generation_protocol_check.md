# BitDPM Matched Generation Protocol Check

**Date**: 2026-06-07

## Source Files

- v0.4 sampling: `experiments/reports/v04_router_20260606_224457.json`

- v0.4 deterministic: `experiments/reports/v04_router_20260607_000506.json`

- v0.5 deterministic: `experiments/reports/v05_router_calibration_20260606_235110.json`

- v0.5 sampling: `experiments/reports/v05_router_calibration_20260607_000439.json`

## Matched Table

| Setting | Baseline | General | Math | Code | Chinese | Always-All | Oracle | Conclusion |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v0.4 sampling | 0.800 | 0.756 | 0.800 | 0.756 | 0.811 | 0.778 | - | fixed block gain appears under sampling |
| v0.4 deterministic | 0.778 | 0.778 | 0.778 | 0.778 | 0.767 | 0.778 | - | no deterministic block utility |
| v0.5 deterministic | 0.778 | 0.778 | 0.778 | 0.778 | 0.767 | 0.778 | 0.778 | oracle selects baseline for all samples |
| v0.5 sampling | 0.800 | 0.822 | 0.800 | 0.800 | 0.800 | 0.778 | 0.844 | sparse sampling-sensitive utility |

## v0.5 Sampling Details

- Oracle overall: 0.844

- Oracle active blocks: 0.089

- Selection frequency: {'baseline': 43, 'general': 1, 'math': 1, 'code': 0, 'chinese': 0, 'always_all': 0}

- Validation-calibrated overall: 0.739

- Validation-calibrated policy: {'commonsense': 'baseline', 'math': 'baseline', 'code': 'baseline', 'chinese': 'baseline', 'reasoning': 'baseline'}


## Utility Matrix Under Sampling

| Category | Best Config | Baseline | General | Math | Code | Chinese | Always-All |
|---|---|---:|---:|---:|---:|---:|---:|
| commonsense | general | 0.800 | 0.900 | 0.700 | 0.800 | 0.800 | 0.700 |
| math | math | 0.300 | 0.300 | 0.400 | 0.300 | 0.300 | 0.300 |
| code | baseline | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| chinese | baseline | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| reasoning | baseline | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Conclusion

The matched-protocol check confirms that deterministic generation has no stable block utility: v0.4 deterministic and v0.5 deterministic both collapse to baseline, and chinese blocks are slightly worse. Sampling generation does expose small block effects: v0.5 sampling reaches oracle=0.844 and general=0.822, but oracle selects non-baseline only 2 out of 45 samples. Therefore, the current blocks provide sparse, sampling-sensitive utility rather than stable deterministic capability gains.

中文：matched 复核确认 deterministic 下没有稳定参数块收益；sampling 下存在小幅且稀疏的参数块效用，但 oracle 只在 45 个样本中的 2 个选择非 baseline。因此当前参数块更像影响采样分布，而不是形成稳定 greedy 能力提升。

## Frozen Current Claim

BitDPM validates controllable parameter-block activation and reveals that naive all-block composition introduces interference. However, the current parameter blocks do not provide stable deterministic improvements. Under sampling-based generation, parameter blocks produce sparse distributional benefits: the oracle improves from 0.800 to 0.844, but selects non-baseline blocks for only 2 out of 45 samples. This suggests that the present BitDPM blocks primarily modulate generation distributions rather than encode robust greedy-decodable task capabilities.

中文：

BitDPM 证明了参数块可控激活，并揭示了全量参数块组合会产生干扰。然而，当前参数块没有带来稳定的 deterministic 提升。在 sampling generation 下，参数块产生了稀疏的分布调节收益：oracle 从 0.800 提升到 0.844，但仅在 2/45 个样本中选择非 baseline。这说明当前 BitDPM 参数块主要是在调节生成分布，而不是形成可被 greedy decoding 稳定利用的任务能力。


## Next Direction

- Shift from router work to block utility amplification. Current oracle space is too small for router improvements to matter: only 2/45 samples select non-baseline blocks.

- Track which exact prompts oracle selects non-baseline for, then inspect saved outputs.

- If stable gains are required, retrain stronger blocks before adding new router/system features.

- Stop deprioritized work for now: NF4 full-model recovery, more EntropyRouter variants, and active block budget scans.
