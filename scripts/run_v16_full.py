"""BitDPM v16 full experiment: all connection variants on v11 pool + v15 benchmark.

Usage:
    # Standard 45-prompt benchmark
    python scripts/run_v16_full.py --model Qwen/Qwen2.5-0.5B-Instruct

    # V15 router-validation benchmark
    python scripts/run_v16_full.py --model Qwen/Qwen2.5-0.5B-Instruct --v15
"""

import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['ALL_PROXY'] = ''
os.environ['all_proxy'] = ''

import torch
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank, ParameterBlock
from bitdpm.params.composer import ConnectionMode
from bitdpm.runtime.device_manager import BlockDeviceManager
from bitdpm.eval.benchmark import EVAL_PROMPTS, compute_accuracy

# ── Config ──────────────────────────────────────────────────────────────
MODEL = os.environ.get('MODEL', 'Qwen/Qwen2.5-0.5B-Instruct')
REGISTRY = 'configs/bitdpm_v11_admitted_pool.json'
BLOCK_DIRS = [
    'experiments/outputs/blocks_v08_error_l22_l24_down_rank16',
    'experiments/outputs/blocks_v09_repair_l22_l24_down_rank16',
    'experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16',
]
MAX_TOKENS = 64

CONNECTIONS = [
    ('hard_add',      ConnectionMode.HARD_ADD,    0.5,  'none'),
    ('norm_clip_0.3', ConnectionMode.NORM_CLIP,    0.3,  'none'),
    ('norm_clip_0.5', ConnectionMode.NORM_CLIP,    0.5,  'none'),
    ('norm_clip_0.7', ConnectionMode.NORM_CLIP,    0.7,  'none'),
    ('token_gate',    ConnectionMode.TOKEN_GATE,   0.5,  'numerical'),
]

# ── Helpers ─────────────────────────────────────────────────────────────

def load_v11_blocks(device):
    """Load v11 admitted pool blocks."""
    bank = {}
    for d in BLOCK_DIRS:
        if os.path.isdir(d):
            for fname in sorted(os.listdir(d)):
                if fname.endswith('.pt'):
                    try:
                        block = ParameterBlock.load(os.path.join(d, fname), device='cpu')
                        bank[block.block_id] = block
                    except Exception as e:
                        print(f'  [Warn] {fname}: {e}')
    return bank

def get_registry_configs():
    with open(REGISTRY) as f:
        cfg = json.load(f)
    return cfg.get('configs', ['baseline', 'always_all']), cfg.get('block_scales', {})

# ── Main ────────────────────────────────────────────────────────────────

def run(args):
    use_v15 = args.v15
    ts = time.strftime('%Y%m%d_%H%M%S')
    label = f'v16_v11_{"v15" if use_v15 else "std"}_{ts}'

    # 1. Device detection
    if torch.backends.mps.is_available():
        DEVICE = torch.device('mps')
    elif torch.cuda.is_available():
        DEVICE = torch.device('cuda')
    else:
        DEVICE = torch.device('cpu')
    DTYPE = torch.float16 if DEVICE.type != 'cpu' else torch.float32
    print(f'Device: {DEVICE}, dtype: {DTYPE}')

    # 2. Load backbone
    bb = BackboneModel(model_name=MODEL, device=str(DEVICE), dtype=DTYPE)

    # 3. Load blocks + preload to device
    block_dict = load_v11_blocks('cpu')
    print(f'Loaded {len(block_dict)} blocks')
    dev_mgr = BlockDeviceManager(target_device=DEVICE, dtype=DTYPE)
    dev_mgr.preload_all(block_dict)

    device_blocks = list(dev_mgr.gpu_cache.values())
    bids = list(dev_mgr.gpu_cache.keys())

    registry_configs, block_scales = get_registry_configs()
    configs = registry_configs  # ['baseline', ...individual blocks..., 'always_all']
    print(f'Configs: {configs}')
    print(f'Blocks: {len(bids)}')

    # 4. Build benchmark
    if use_v15:
        from bitdpm.eval.v15_benchmark import V15_EVAL_PROMPTS
        flat_prompts: list[tuple[str, str]] = []
        for cat, plist in V15_EVAL_PROMPTS.items():
            for p in plist:
                flat_prompts.append((cat, p))
        print(f'V15 benchmark: {len(flat_prompts)} prompts')
    else:
        flat_prompts: list[tuple[str, str]] = []
        for cat, plist in EVAL_PROMPTS.items():
            for p in plist:
                flat_prompts.append((cat, p))
        print(f'Standard benchmark: {len(flat_prompts)} prompts')

    # 5. Run each connection
    all_results = {}
    for conn_label, conn_mode, ratio, gate_fn in CONNECTIONS:
        print(f'\n{"="*60}')
        print(f'CONNECTION: {conn_label}')
        print(f'{"="*60}')

        inj = BlockInjector(bb)
        # Set blocks with per-block scales from registry
        for b in device_blocks:
            b.scale = block_scales.get(b.block_id, block_scales.get(b.block_type, 0.75))
        inj.inject_blocks(device_blocks)
        inj.set_connection(conn_mode, ratio=ratio)

        all_sc: dict[str, dict[str, float]] = {}

        for cfg in configs:
            if cfg == 'baseline':
                inj.set_active_blocks([])
            elif cfg == 'always_all':
                inj.set_active_blocks(bids)
            elif cfg in dev_mgr.gpu_cache:
                inj.set_active_blocks([cfg])
            else:
                # Try matching by block type prefix
                matches = [bid for bid in bids if bid.startswith(cfg)]
                inj.set_active_blocks(matches[:1] if matches else [])

            cat_scores: dict[str, float] = {}
            cat_counts: dict[str, int] = {}
            for cat, p in flat_prompts:
                if not use_v15:
                    cat = [c for c in EVAL_PROMPTS if c == cat][0]  # already correct
                g = bb.generate(p, max_new_tokens=MAX_TOKENS, temperature=0.1)
                s = compute_accuracy(p, g, cat)
                all_sc.setdefault(p, {})[cfg] = s
                cat_scores[cat] = cat_scores.get(cat, 0.0) + s
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            avg_by_cat = {c: cat_scores[c] / max(cat_counts[c], 1) for c in cat_scores}
            overall = sum(avg_by_cat.values()) / max(len(avg_by_cat), 1)
            if cfg in ('baseline', 'always_all') or overall != 0.0:
                print(f'  {cfg:<30} {overall:.3f}')

        inj.remove_all_patches()

        # Oracle
        ot, oc = 0.0, 0
        for p, cs in all_sc.items():
            bc = max(cs, key=cs.get)
            ot += cs[bc]
            if bc != 'baseline':
                oc += 1
        n = max(len(all_sc), 1)
        oracle_score = ot / n
        print(f'  {"ORACLE":<30} {oracle_score:.3f} ({oc}/{n})')

        # Break counts
        break_counts = {}
        for cfg in configs:
            if cfg in ('baseline', 'always_all'):
                continue
            fx = br = 0
            for p, cs in all_sc.items():
                bl = cs.get('baseline', 0.0)
                c = cs.get(cfg, bl)
                if c > bl: fx += 1
                elif c < bl: br += 1
            break_counts[cfg] = {'fixes': fx, 'breaks': br}

        # Print non-zero
        for cfg in sorted(break_counts.keys()):
            bc = break_counts[cfg]
            if bc['fixes'] > 0 or bc['breaks'] > 0:
                print(f'  {cfg:<30} fixes={bc["fixes"]} breaks={bc["breaks"]}')

        all_results[conn_label] = {
            'baseline': sum(all_sc[p].get('baseline', 0.0) for p in all_sc) / max(n, 1),
            'always_all': sum(all_sc[p].get('always_all', 0.0) for p in all_sc) / max(n, 1),
            'oracle': oracle_score,
            'coverage': oc,
            'total_samples': n,
            'break_counts': break_counts,
        }

    # 6. Summary
    print(f'\n{"="*70}')
    print('V16 FULL EXPERIMENT SUMMARY')
    print(f'{"="*70}')
    print(f'{"Connection":<20} {"Baseline":<9} {"AlwaysAll":<10} {"Oracle":<8} {"Coverage":<8}')
    print(f'{"-"*20} {"-"*9} {"-"*10} {"-"*8} {"-"*8}')
    for conn_label, _, _, _ in CONNECTIONS:
        r = all_results.get(conn_label, {})
        print(f'{conn_label:<20} {r.get("baseline",0):<9.3f} {r.get("always_all",0):<10.3f} {r.get("oracle",0):<8.3f} {r.get("coverage",0)}/{r.get("total_samples",0)}')

    # 7. Save
    out = os.path.join('experiments/reports', f'{label}.json')
    with open(out, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nSaved: {out}')
    print('Done.')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='Qwen/Qwen2.5-0.5B-Instruct')
    p.add_argument('--v15', action='store_true', help='Use v15 validation benchmark')
    args = p.parse_args()
    run(args)
