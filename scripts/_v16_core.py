"""Internal v16 core experiment runner."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['ALL_PROXY'] = ''
os.environ['all_proxy'] = ''

import torch
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank
from bitdpm.params.composer import ConnectionMode
from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy

MODEL_PATH = '/tmp/claude-501/bitdpm-cache/models/modelscope/Qwen/Qwen2.5-0.5B-Instruct'
BLOCK_DIR = 'experiments/outputs/blocks'

print('Loading backbone...')
bb = BackboneModel(model_name=MODEL_PATH, device='cpu', dtype=torch.float32)
print('Loading blocks...')
bank = BlockBank.load_all(BLOCK_DIR, device='cpu')
print(f'{len(bank)} blocks loaded')

block_ids = list(bank.blocks.keys())
print(f'Block IDs: {block_ids}')

configs = ['baseline'] + block_ids + ['always_all']

connections = [
    ('hard_add', ConnectionMode.HARD_ADD, 0.5),
    ('norm_clip_0.3', ConnectionMode.NORM_CLIP, 0.3),
    ('norm_clip_0.5', ConnectionMode.NORM_CLIP, 0.5),
    ('norm_clip_0.7', ConnectionMode.NORM_CLIP, 0.7),
]

results = {}

for conn_label, conn_mode, ratio in connections:
    print(f'\n=== {conn_label} ===')
    injector = BlockInjector(bb)
    injector.inject_blocks(list(bank.blocks.values()))
    for b in list(bank.blocks.values()):
        b.scale = 0.15

    all_scores = {}

    for cfg in configs:
        if cfg == 'baseline':
            injector.set_active_blocks([])
        elif cfg == 'always_all':
            injector.set_active_blocks(block_ids)
        else:
            injector.set_active_blocks([cfg] if cfg in bank.blocks else [])

        injector.set_connection(conn_mode, ratio=ratio)

        cat_scores = {}
        for cat, prompts in BP.items():
            correct = 0.0
            for p in prompts:
                g = bb.generate(p, max_new_tokens=64, temperature=0.1)
                sc = compute_accuracy(p, g, cat)
                correct += sc
                all_scores.setdefault(p, {})[cfg] = sc
            cat_scores[cat] = correct / len(prompts) if prompts else 0.0

        overall = sum(cat_scores.values()) / len(cat_scores) if cat_scores else 0.0
        print(f'  {cfg:<30} {overall:.3f}')

    injector.remove_all_patches()

    # Oracle
    oracle_total = 0.0
    oracle_coverage = 0
    for p, cs in all_scores.items():
        best_cfg = max(cs, key=cs.get)
        oracle_total += cs[best_cfg]
        if best_cfg != 'baseline':
            oracle_coverage += 1
    n = len(all_scores)
    oracle_score = oracle_total / n if n > 0 else 0.0
    print(f'  {"ORACLE":<30} {oracle_score:.3f} (cov={oracle_coverage}/{n})')

    # Break counts
    break_counts = {}
    for cfg in configs:
        if cfg in ('baseline', 'always_all'):
            continue
        fixes = breaks = neutral = 0
        for p, cs in all_scores.items():
            bl = cs.get('baseline', 0.0)
            c = cs.get(cfg, bl)
            if c > bl: fixes += 1
            elif c < bl: breaks += 1
            else: neutral += 1
        break_counts[cfg] = {'fixes': fixes, 'breaks': breaks}

    # Print blocks with any fixes or breaks
    for cfg in sorted(break_counts.keys()):
        bc = break_counts[cfg]
        if bc['fixes'] > 0 or bc['breaks'] > 0:
            print(f'  {cfg:<30} fixes={bc["fixes"]:2d} breaks={bc["breaks"]:2d}')

    results[conn_label] = {
        'configs': {cfg: None for cfg in configs},  # filled below
        'oracle': oracle_score,
        'coverage': oracle_coverage,
        'total_samples': n,
        'break_counts': break_counts,
    }
    # Store config scores
    for cfg in configs:
        # Reconstruct from all_scores
        scores_for_cfg = [all_scores[p].get(cfg, 0.0) for p in all_scores if cfg in all_scores[p]]
        results[conn_label]['configs'][cfg] = sum(scores_for_cfg) / len(scores_for_cfg) if scores_for_cfg else 0.0

# Summary
print(f'\n{"="*60}')
print('V16 CONNECTION FUNCTION COMPARISON')
print(f'{"="*60}')
print(f'{"Connection":<20} {"Baseline":<9} {"AlwaysAll":<9} {"Oracle":<8} {"Coverage":<8}')
print(f'{"-"*20} {"-"*9} {"-"*9} {"-"*8} {"-"*8}')
for cn, _, _ in connections:
    r = results.get(cn, {})
    bl = r.get('configs', {}).get('baseline', 0)
    aa = r.get('configs', {}).get('always_all', 0)
    ora = r.get('oracle', 0)
    cov = r.get('coverage', 0)
    tot = r.get('total_samples', 45)
    print(f'{cn:<20} {bl:<9.3f} {aa:<9.3f} {ora:<8.3f} {cov}/{tot:<4}')

# Break comparison
print(f'\n{"="*60}')
print('BREAK COUNT COMPARISON')
print(f'{"="*60}')

# Collect all block configs that had breaks/fixes
all_breakable = sorted(set(
    b for r in results.values() for b in r.get('break_counts', {}).keys()
))

header = f'{"Block":<30}'
for cn, _, _ in connections:
    header += f' {cn[:12]:>12}'
print(header)

for cfg in all_breakable:
    line = f'{cfg:<30}'
    for cn, _, _ in connections:
        bc = results.get(cn, {}).get('break_counts', {}).get(cfg, {})
        f = bc.get('fixes', 0)
        br = bc.get('breaks', 0)
        line += f' {f}:{br:<8}'
    print(line)

# Save
ts = time.strftime('%Y%m%d_%H%M%S')
out = os.path.join('experiments/reports', f'v16_results_{ts}.json')
with open(out, 'w') as f:
    json.dump(results, f, indent=2)
print(f'\nSaved: {out}')
print('Done.')
