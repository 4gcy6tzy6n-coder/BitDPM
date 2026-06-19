# BitDPM v11-v15 Roadmap

## Frozen v10 State

Current best setting:

```text
Version: BitDPM v10
Best pool: v0.8 hybrid error-type pool + admitted arithmetic_power_log
Benchmark: v08 100-sample stable sampling
Oracle: 0.890
Coverage: 6/100
Best fixed: 0.830
Always-All: 0.000
```

Core design rule:

> Block admission should be based on unique per-sample correction coverage, not task label, semantic name, or aggregate fixed-block score.

Operational registry:

```text
configs/bitdpm_v10_admitted_pool.json
```

## What Not To Do Next

Do not continue:

1. blind rank32 / rank64 scaling,
2. full repair-block group admission,
3. aggregate-score-only block filtering,
4. attempts to make Always-All good,
5. premature full-model NF4 engineering,
6. semantic-label routing based on block names.

The v10 result shows that useful blocks are sparse correction directions, not semantic experts. Always-All collapse is a mechanism signal, not a deployment target.

## v11: Unique-Utility Repair Mining

Priority: highest.

Goal:

```text
coverage: 6/100 -> 8/100 or 10/100+
oracle:   0.890 -> 0.900+
```

Method:

1. Start from the v10 admitted pool.
2. Identify samples where:
   - baseline is wrong,
   - current best pool is wrong,
   - a candidate block can fix the sample,
   - the fix is not an overlap fix.
3. Admit only blocks with unique per-sample correction coverage.
4. For every candidate block, report:
   - fixes,
   - unique fixes,
   - overlap fixes,
   - breaks,
   - net unique utility,
   - damage rate,
   - admit / reject decision.

Candidate repair directions:

- `arithmetic_geometry_distance`
- `arithmetic_fraction_percent`
- `arithmetic_log_power`
- `arithmetic_integer_ops`
- `factual_physical_constants`
- `literature_factual_recall`

Acceptance rule:

> A block that fixes only already-covered samples is rejected, even if the block name appears relevant.

## v12: Conservative Utility Router

Precondition:

v11 should first increase coverage to at least 8/100 or 10/100. Router work is not the current bottleneck while coverage remains too sparse.

Goal:

```text
deployable router >= baseline + 0.02
router precision > router recall
low trigger rate
few breaks
```

Do not revive old KeywordRouter or EntropyRouter as the main router. They do not estimate unique block utility.

First router should be a conservative utility predictor:

- prompt pattern features,
- numeric/formula/entity detectors,
- baseline output features,
- optional baseline confidence/entropy,
- validation-mined utility rules.

Example rules:

```text
if prompt has coordinate-distance pattern:
    try arithmetic_power_log
if prompt has sqrt/log/power form:
    try corresponding repair direction
if prompt has physical-constant form:
    try factual constant block only if it has unique validation utility
```

The router should predict whether to trigger a repair direction, not choose a semantic domain expert.

## v13: Safety Cards and Incompatibility Matrix

Every admitted block should have a safety card:

```text
Block name:
Structure:
Rank:
Scale:
Unique fixes:
Overlap fixes:
Breaks:
Net unique utility:
Damage rate:
Admitted: yes/no
Allowed activation mode: single-only / can-compose / forbidden-with-X
```

Example:

```text
arithmetic_power_log
unique fixes: 1
overlap fixes: 1
breaks: 11
admitted: yes
activation: single-only, never Always-All
```

Add pairwise incompatibility tests:

```text
block A alone
block B alone
block A + block B
```

Output an incompatibility matrix to guide router composition.

## v14: Benchmark Expansion

The v08 100-sample benchmark is useful but still small.

Targets:

```text
300 samples: quick validation
500 samples: stable medium setting
1000 samples: paper-scale main evaluation
```

Benchmark should be stratified:

- arithmetic,
- factual constants,
- commonsense,
- format following,
- Chinese,
- code / structured output,
- short reasoning.

Each category should contain at least 50-100 samples in the larger settings.

Key questions:

1. Does sparse utility persist at larger scale?
2. Which failure types are most correctable?
3. Does Always-All collapse across all categories?
4. Are repair blocks mainly arithmetic, or broader?

## v15: Low-Bit and Local Deployment

Do not let NF4 engineering block mechanism research now.

After v11-v14:

1. FP16 backbone + BitDPM for mechanism results.
2. INT8 backbone + BitDPM for lower-risk deployment results.
3. Partial NF4 layers + BitDPM for local low-bit validation.
4. GGUF / llama.cpp comparison for realistic local throughput.

Deployment metrics:

- token/s,
- peak RAM / VRAM,
- active block count,
- block loading overhead,
- router overhead,
- best-pool storage size.

## Immediate Next Step

Run v10 from registry when reproduction is needed:

```bash
python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v10_admitted_pool.json \
  --tag v10_registry_repro
```

Then v11 should begin from:

```text
experiments/reports/v08_utility_mining/v10_admitted_powerlog_stable_sampling_utility_mining.md
experiments/reports/v10_admission/v10_v09b_admission_admission.md
```

The next experimental objective is not more blocks. It is a larger, safer correction library built by unique correction coverage.
