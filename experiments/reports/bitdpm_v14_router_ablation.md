# BitDPM v14 Router Feature Ablation

## Objective

Test whether category-feature conjunctions can expand deployable router coverage beyond the current allow-core router while preserving zero held-out breaks.

## Results

| Router Variant | Full Report | Full Fixes | Full Breaks | Strict CV | CV Fixes | CV Breaks | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| allow-core atomic | 0.867 | 8 | 0 | 0.857 | 5 | 0 | current best safe router |
| unrestricted conjunction | 0.877 | 11 | 0 | 0.843 | 5 | 4 | overfits, unsafe |
| conjunction + risky-deny | n/a | n/a | n/a | 0.853 | 5 | 1 | still unsafe |
| conjunction + allow-core | 0.867 | 8 | 0 | 0.857 | 5 | 0 | ties atomic allow-core |

## Interpretation

Category-feature conjunctions can recover more oracle fixes on the same full report, but they do not generalize safely under held-out cross-validation. The unrestricted conjunction router introduces breaks on broad conjunctions such as `category=commonsense&short_prompt`, `category=arithmetic&has_addition`, `category=arithmetic&has_sqrt`, and `category=factual_constants&asks_brief`.

After denying risky broad features, one break remains through `category=arithmetic&has_2plus_numbers`. Restricting conjunctions to the same core features as the atomic allow-core router removes breaks, but it does not improve over the atomic allow-core result.

## Current Decision

Keep the atomic allow-core router as the current deployable-router result:

- strict CV: `0.857`
- baseline: `0.840`
- gain: `+0.017`
- fixes: `5`
- breaks: `0`

Do not claim that conjunction features improve deployment readiness. Their value is diagnostic: they expose candidate correction regions for future data collection, but they are not currently safe enough for router expansion.

## Next Direction

Future router progress should come from expanding safe features with stronger evidence, not from unconstrained feature conjunctions. The next useful step is to collect additional validation prompts for each candidate feature family, especially factual constants and commonsense repairs, then require zero-break behavior on those expanded validation slices before admitting new router triggers.

