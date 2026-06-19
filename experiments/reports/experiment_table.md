| Model | Quant | Params | Device | Token/s | Latency(ms) | Memory(MB) | commonsense | math | code | chinese | reasoning | Overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | FP16 | 0.5B | cpu | 14.1 | 2633.8 | 1885 | 0.800 | 0.300 | 1.000 | 1.000 | 1.000 | 0.800 |
| single | FP16+blocks | 0.5B | cpu | 13.8 | 2571.7 | 1885 | 0.700 | 0.300 | 1.000 | 1.000 | 1.000 | 0.778 |
| multi_all | FP16+blocks | 0.5B | cpu | 12.0 | 2928.8 | 1885 | 0.700 | 0.300 | 1.000 | 1.000 | 1.000 | 0.778 |
| routed | FP16+routed | 0.5B | cpu | 11.0 | 3306.4 | 1885 | 0.900 | 0.300 | 1.000 | 1.000 | 1.000 | 0.822 |