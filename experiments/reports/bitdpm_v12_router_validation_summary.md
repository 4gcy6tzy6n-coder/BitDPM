# BitDPM v12 Router Validation Summary

## Status

v12 tested whether the v10 oracle-only sparse correction result can be converted
into a deployable routing policy.

Current answer:

> Partially. A validation-mined conservative rule router can recover most v10
> oracle corrections without observed breaks, but strict held-out
> cross-validation does not yet show positive router gain.

## Evidence

### Validation-Mined Prototype

Report:
`experiments/reports/v12_router/smoke_v12_utility_router_safe_specific_utility_router.md`

Setting:

- Source: v10 100-sample stable-sampling report
- Rule mining: prompt-feature utility rules
- Safety: full-report zero-break filter
- Feature gate: specific features only (`--min-specificity 2`)

Result:

| Method | Score | Gain | Fixes | Breaks |
|---|---:|---:|---:|---:|
| Baseline | 0.830 | - | - | - |
| Utility router | 0.880 | +0.050 | 5 | 0 |
| Oracle | 0.890 | +0.060 | 6 | - |

Interpretation:

The current oracle choices are not purely inaccessible. They can be approximated
by conservative prompt-feature routing rules when those rules are admitted by
observed fix/break safety.

### Strict Cross-Validation

Report:
`experiments/reports/v12_router/smoke_v12_utility_router_strict_cv_specific_crossval.md`

Setting:

- 5-fold held-out evaluation
- Rules mined only from training folds
- Feature gate: specific features only
- No full-report safety leakage

Result:

| Method | Score | Gain | Fixes | Breaks |
|---|---:|---:|---:|---:|
| Baseline | 0.830 | - | - | - |
| Strict CV router | 0.830 | +0.000 | 0 | 0 |

Interpretation:

The router can be made safe, but held-out correction gain is not yet proven.
The v10 benchmark is too small and the useful correction events are too sparse
for robust router learning.

## Updated Claim

Do not claim:

> BitDPM has a deployable router that generalizes.

Current valid claim:

> BitDPM v12 shows that oracle sparse corrections can be converted into a
> conservative validation-mined routing prototype, but held-out router
> generalization remains unresolved.

## Next Required Check

Run v14:

```bash
bash experiments/reports/v14_benchmark_commands.sh
```

v14 will determine whether a larger 300-sample benchmark provides enough
correction events to train and validate utility-aware routing without relying
on full-report admission.
