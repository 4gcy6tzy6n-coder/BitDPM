# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`
- Folds: 5
- Overall: 0.820
- Baseline: 0.830
- Delta: -0.010
- Fixes: 0
- Breaks: 1
- Precision proxy: 0.000

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 20 | 16 | 0.800 | 0.800 | +0.000 | 0 | 0 |
| 1 | 17 | 10 | 0.824 | 0.824 | +0.000 | 0 | 0 |
| 2 | 23 | 11 | 0.826 | 0.826 | +0.000 | 0 | 0 |
| 3 | 19 | 16 | 0.895 | 0.895 | +0.000 | 0 | 0 |
| 4 | 21 | 15 | 0.762 | 0.810 | -0.048 | 0 | 1 |

## Held-Out Fix Samples


## Held-Out Break Samples

- fold=4 #31 `math` commonsense_choice via `has_number`: What is 9 times 8?
