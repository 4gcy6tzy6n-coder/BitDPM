"""Quick v16 connection function comparison with GPU-resident blocks."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['ALL_PROXY'] = ''
os.environ['all_proxy'] = ''

import torch
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import BlockBank
from bitdpm.params.composer import ConnectionMode
from bitdpm.runtime.device_manager import BlockDeviceManager
from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy

MODEL = '/tmp/claude-501/bitdpm-cache/models/modelscope/Qwen/Qwen2.5-0.5B-Instruct'
BLOCKS = 'experiments/outputs/blocks'

# Detect best available device
if torch.backends.mps.is_available():
    DEVICE = torch.device('mps')
elif torch.cuda.is_available():
    DEVICE = torch.device('cuda')
else:
    DEVICE = torch.device('cpu')
DTYPE = torch.float16 if DEVICE.type != 'cpu' else torch.float32

print(f'Device: {DEVICE}, dtype: {DTYPE}')

# 1. Load backbone (on target device)
bb = BackboneModel(model_name=MODEL, device=str(DEVICE), dtype=DTYPE)
print(f'Backbone loaded on {DEVICE}')

# 2. Load blocks (initially on CPU, then preload to target device)
bank_cpu = BlockBank.load_all(BLOCKS, device='cpu')

dev_mgr = BlockDeviceManager(target_device=DEVICE, dtype=DTYPE)
# Get a plain dict of blocks for the device manager
block_dict = dict(bank_cpu.blocks)
dev_mgr.preload_all(block_dict)
print(f'{len(dev_mgr)} blocks preloaded to {DEVICE}')

# 3. Build device-resident block list from device manager
device_blocks = list(dev_mgr.gpu_cache.values())
bids = list(dev_mgr.gpu_cache.keys())
configs = ['baseline'] + bids + ['always_all']

for label, mode, ratio in [
    ('hard_add', ConnectionMode.HARD_ADD, 0.5),
    ('norm_clip_0.3', ConnectionMode.NORM_CLIP, 0.3),
    ('norm_clip_0.5', ConnectionMode.NORM_CLIP, 0.5),
]:
    print(f'\n=== {label} (blocks on {DEVICE}) ===')
    inj = BlockInjector(bb)

    # Inject blocks that are ALREADY on the target device
    for b in device_blocks:
        b.scale = 0.15
    inj.inject_blocks(device_blocks)
    inj.set_connection(mode, ratio=ratio)

    all_sc = {}
    for cfg in configs:
        if cfg == 'baseline':
            inj.set_active_blocks([])
        elif cfg == 'always_all':
            inj.set_active_blocks(bids)
        else:
            inj.set_active_blocks([cfg])

        cat_scores = {}
        for cat, prompts in BP.items():
            hits = 0.0
            for p in prompts:
                g = bb.generate(p, max_new_tokens=64, temperature=0.1)
                s = compute_accuracy(p, g, cat)
                hits += s
                all_sc.setdefault(p, {})[cfg] = s
            cat_scores[cat] = hits / len(prompts) if prompts else 0.0
        ov = sum(cat_scores.values()) / len(cat_scores) if cat_scores else 0.0
        if cfg in ('baseline', 'always_all'):
            print(f'  {cfg:<30} {ov:.3f}')

    inj.remove_all_patches()

    # Oracle
    ot, oc = 0.0, 0
    for p, cs in all_sc.items():
        bc = max(cs, key=cs.get)
        ot += cs[bc]
        if bc != 'baseline':
            oc += 1
    n = max(len(all_sc), 1)
    print(f'  {"ORACLE":<30} {ot/n:.3f} ({oc}/{n})')

    # Breaks
    for cfg in bids:
        fx = br = 0
        for p, cs in all_sc.items():
            bl = cs.get('baseline', 0.0)
            c = cs.get(cfg, bl)
            if c > bl: fx += 1
            elif c < bl: br += 1
        if fx > 0 or br > 0:
            print(f'  {cfg:<30} fixes={fx} breaks={br}')

print('\nDone!')
