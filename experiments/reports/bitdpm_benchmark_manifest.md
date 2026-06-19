# BitDPM Benchmark Manifest

This manifest audits the static benchmark prompt sets used by current
BitDPM experiments. It is generated without model inference.

## Benchmark Summary

| Benchmark | N | Categories | Duplicate Prompts | Normalized SHA256 |
|---|---:|---:|---:|---|
| core | 45 | 5 | 0 | `423ccfadaf0edd5963c15338223d4f856523471cba74af14bc6a9fdda34d2a64` |
| v08 | 100 | 5 | 0 | `f2a72795582a736e5772f84b57647121d99a2879eeba84da2331474cccc69b46` |
| v14 | 300 | 6 | 0 | `b66741e156fc2aa0913e3be95cd22b0c52f99cafcd43ffe0a12176214b204a62` |
| v15 | 120 | 6 | 0 | `c9e0cca4a25d7ade15ee926cda67cd3452ab7704f869d56a25fe2c3e33774b15` |
| v1k | 1000 | 6 | 0 | `25bba1e5241a65082da5bd17efd1547cec2c01ba6a7c9d2f7c70e31ad86b5b99` |
| v1k_clean | 1000 | 6 | 0 | `841d96404b8775f3f35da419443d9ad5f71beabf5d1613cb8abd39382289015e` |

## Category Detail

| Benchmark | Category | Prompts | Expected Answers | Answer Coverage | Duplicates | Avg Chars | Max Chars |
|---|---|---:|---:|---:|---:|---:|---:|
| core | commonsense | 10 | 10 | 1.000 | 0 | 36.200 | 47 |
| core | math | 10 | 10 | 1.000 | 0 | 29.200 | 64 |
| core | code | 10 | 0 | 0.000 | 0 | 48.500 | 68 |
| core | chinese | 10 | 0 | 0.000 | 0 | 10.800 | 15 |
| core | reasoning | 5 | 0 | 0.000 | 0 | 121.000 | 168 |
| v08 | commonsense | 20 | 20 | 1.000 | 0 | 37.600 | 48 |
| v08 | math | 20 | 20 | 1.000 | 0 | 27.900 | 64 |
| v08 | code | 20 | 0 | 0.000 | 0 | 43.900 | 68 |
| v08 | chinese | 20 | 0 | 0.000 | 0 | 10.950 | 15 |
| v08 | reasoning | 20 | 0 | 0.000 | 0 | 84.700 | 168 |
| v14 | arithmetic | 50 | 50 | 1.000 | 0 | 22.780 | 42 |
| v14 | factual_constants | 50 | 50 | 1.000 | 0 | 66.100 | 102 |
| v14 | commonsense | 50 | 50 | 1.000 | 0 | 37.400 | 62 |
| v14 | code | 50 | 0 | 0.000 | 0 | 77.200 | 99 |
| v14 | chinese | 50 | 0 | 0.000 | 0 | 21.300 | 25 |
| v14 | reasoning | 50 | 0 | 0.000 | 0 | 103.500 | 128 |
| v15 | router_multiplication | 20 | 20 | 1.000 | 0 | 19.300 | 20 |
| v15 | router_core_mixed | 20 | 20 | 1.000 | 0 | 37.500 | 43 |
| v15 | router_risky_arithmetic | 20 | 20 | 1.000 | 0 | 23.800 | 31 |
| v15 | router_factual_constants | 20 | 20 | 1.000 | 0 | 67.700 | 95 |
| v15 | router_commonsense_repairs | 20 | 20 | 1.000 | 0 | 60.650 | 76 |
| v15 | router_commonsense_controls | 20 | 20 | 1.000 | 0 | 39.500 | 57 |
| v1k | arithmetic | 250 | 250 | 1.000 | 0 | 23.928 | 43 |
| v1k | factual_constants | 150 | 150 | 1.000 | 0 | 66.267 | 105 |
| v1k | commonsense | 200 | 200 | 1.000 | 0 | 54.400 | 86 |
| v1k | code | 150 | 0 | 0.000 | 0 | 77.600 | 100 |
| v1k | chinese | 150 | 0 | 0.000 | 0 | 21.700 | 26 |
| v1k | reasoning | 100 | 0 | 0.000 | 0 | 103.600 | 129 |
| v1k_clean | arithmetic | 250 | 250 | 1.000 | 0 | 56.852 | 85 |
| v1k_clean | factual_constants | 150 | 150 | 1.000 | 0 | 86.800 | 116 |
| v1k_clean | commonsense | 200 | 200 | 1.000 | 0 | 77.300 | 105 |
| v1k_clean | code | 150 | 0 | 0.000 | 0 | 111.600 | 123 |
| v1k_clean | chinese | 150 | 0 | 0.000 | 0 | 47.000 | 51 |
| v1k_clean | reasoning | 100 | 0 | 0.000 | 0 | 144.200 | 175 |

## Exact Normalized Prompt Overlap

| Benchmark | core | v08 | v14 | v15 | v1k | v1k_clean |
|---|---:|---:|---:|---:|---:|---:|
| core | 45 | 45 | 10 | 4 | 8 | 0 |
| v08 | 45 | 100 | 26 | 11 | 19 | 0 |
| v14 | 10 | 26 | 300 | 64 | 264 | 0 |
| v15 | 4 | 11 | 64 | 120 | 77 | 0 |
| v1k | 8 | 19 | 264 | 77 | 1000 | 0 |
| v1k_clean | 0 | 0 | 0 | 0 | 0 | 1000 |

## Paper Use

- Cite the normalized SHA256 fingerprint for any benchmark used as a fixed validation set.
- Treat a 1k benchmark as held-out only if exact normalized prompt overlap with earlier validation sets is zero.
- Qualitative categories with `0.000` answer coverage use the shared heuristic scorer; report that limitation.
- Exact prompt overlap is reported here; semantic/template similarity should be discussed separately if needed.
