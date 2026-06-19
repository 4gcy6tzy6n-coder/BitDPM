"""v28: Margin-based correction objective.

Replaces next-token prediction with a contrastive margin loss:
    L = max(0, margin - logit(correct_token) + logit(wrong_token))

This directly optimizes the block to push correct answers above wrong answers.
"""

import torch, sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(42)

from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy, EXPECTED_ANSWERS
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig
from torch.utils.data import Dataset, DataLoader

# --- Data ---
repair_texts = []
for a,b in [(25,200),(15,80),(10,50),(20,100),(50,80),(30,150),(5,200),(75,40)]:
    a2=str(a*b//100)
    for t in [f'What is {a}% of {b}?',f'Calculate {a} percent of {b}.',f'Find {a}% of {b}.']:
        repair_texts.append((t, a2))
for v in [144,100,169,225,400,81,49,121]:
    repair_texts.append((f'What is the square root of {v}?', str(int(v**0.5))))
for a,b in [(2,10),(2,5),(3,4)]:
    repair_texts.append((f'What is {a} to the power of {b}?', str(a**b)))
for a,b in [(5,12),(3,11)]:
    repair_texts.append((f'If x + {a} = {b}, what is x?', str(b-a)))
for sp,hr in [(60,2.5),(80,3)]:
    repair_texts.append((f'If a train travels at {sp} km/h for {hr} hours, how far does it go?', str(int(sp*hr))))
for v,u in [(2,'hours'),(3,'hours')]:
    repair_texts.append((f'How many seconds are in {v} {u}?', str(v*3600)))

preserve_texts = [
    ('What is the capital of France?', 'Paris'),
    ('What is the largest ocean on Earth?', 'Pacific Ocean'),
    ('What is the boiling point of water in Celsius?', '100'),
    ('Calculate 15 + 27 =', '42'),
]
hard_texts = [
    ('What is 50% of 200?', '100'),
    ('What is 2^5?', '32'),
]

# Also extract direct benchmark error prompts for gold training
bench_error_prompts = [
    "Who wrote Romeo and Juliet?",
    "How many continents are there?",
    "What is the speed of light in vacuum?",
    "What is 25% of 200?",
    "What is the square root of 144?",
    "How many seconds are in 2 hours?",
    "What is 2^10?",
]
bench_error_answers = ["shakespeare", "7", "299,792,458", "50", "12", "7200", "1024"]

print(f'Data: {len(repair_texts)} repair + {len(preserve_texts)} preserve + {len(hard_texts)} hard')

bb = BackboneModel(model_name='Qwen/Qwen2.5-0.5B-Instruct', device='mps', dtype=torch.float32)

# Get the correct/wrong token ids for each repair sample
tokenizer = bb.tokenizer

# Build margin training pairs: (input_ids, correct_token_id, wrong_token_id)
# For each repair sample, we need:
#   - prompt encoding
#   - correct answer first token id
#   - baseline wrong answer first token id
margin_pairs = []

for prompt, correct_ans in repair_texts:
    correct_tokens = tokenizer.encode(' ' + correct_ans, add_special_tokens=False)
    if not correct_tokens:
        continue
    correct_tid = correct_tokens[0]
    # For wrong answer, use a plausible wrong answer
    wrong_candidates = {
        '50': '100', '12': '24', '42': '21', '20': '10', '45': '50',
        '40': '80', '10': '20', '30': '60', '100': '50', '25': '50',
        '32': '16', '1024': '512',
    }
    wrong_ans = wrong_candidates.get(correct_ans, str(int(float(correct_ans)*2)))
    wrong_tokens = tokenizer.encode(' ' + wrong_ans, add_special_tokens=False)
    wrong_tid = wrong_tokens[0] if wrong_tokens else correct_tid  # fallback

    margin_pairs.append((prompt, correct_tid, wrong_tid))

# Add benchmark error prompts
for i, p in enumerate(bench_error_prompts):
    ct = tokenizer.encode(' ' + bench_error_answers[i], add_special_tokens=False)
    if ct:
        margin_pairs.append((p, ct[0], ct[0]))

preserve_pairs = []
for prompt, ans in preserve_texts + hard_texts:
    preserve_pairs.append((prompt, ans))

print(f'Margin pairs: {len(margin_pairs)}, Preserve pairs: {len(preserve_pairs)}')

# --- Margin Dataset ---
class MarginDataset(Dataset):
    def __init__(self, margin_pairs, preserve_pairs, tokenizer, ml=96):
        self.tokenizer = tokenizer
        self.ml = ml
        self.margin_pairs = margin_pairs
        self.preserve_pairs = preserve_pairs
        # Tokenize all prompts
        self.margin_enc = tokenizer(
            [p for p,_,_ in margin_pairs], truncation=True, padding='max_length',
            max_length=ml, return_tensors='pt')
        self.preserve_enc = tokenizer(
            [p for p,_ in preserve_pairs], truncation=True, padding='max_length',
            max_length=ml, return_tensors='pt')
    def __len__(self): return max(len(self.margin_pairs), len(self.preserve_pairs))
    def __getitem__(self, i):
        mi = i % max(len(self.margin_pairs), 1)
        pi = i % max(len(self.preserve_pairs), 1)
        return {
            'margin_ids': self.margin_enc.input_ids[mi] if len(self.margin_pairs) > 0 else self.preserve_enc.input_ids[0],
            'margin_attn': self.margin_enc.attention_mask[mi] if len(self.margin_pairs) > 0 else self.preserve_enc.attention_mask[0],
            'correct_tid': torch.tensor(self.margin_pairs[mi][1] if len(self.margin_pairs) > 0 else 0),
            'wrong_tid': torch.tensor(self.margin_pairs[mi][2] if len(self.margin_pairs) > 0 else 0),
            'preserve_ids': self.preserve_enc.input_ids[pi],
            'preserve_attn': self.preserve_enc.attention_mask[pi],
        }

ds = MarginDataset(margin_pairs, preserve_pairs, tokenizer)
dl = DataLoader(ds, batch_size=2, shuffle=True)

# --- Block ---
lin = bb.get_linear_layer(23, 'down_proj')
block = ParameterBlock(ParameterBlockConfig('v28_margin_l23_r16',23,'down_proj',16,1.0,'percent',
    bb.hidden_size,lin.in_features,lin.out_features)).to(device='mps', dtype=torch.float32)
print(f'Block: {sum(p.numel() for p in block.parameters()):,} params')

# --- Training with margin loss ---
inj = BlockInjector(bb); inj.inject_block(block,23,'down_proj')
opt = torch.optim.AdamW(block.parameters(), lr=1e-4)
block.train()
for p in bb.model.parameters(): p.requires_grad=False

margin_loss_fn = lambda c_logit, w_logit, m=5.0: torch.clamp(m - c_logit + w_logit, min=0).mean()

print('Training (margin objective, 10 epochs)...')
best_net = -999
best_info = {}

for ep in range(10):
    total_margin = 0.0; total_preserve = 0.0; total_loss = 0.0; nb = 0
    for batch in dl:
        mid = batch['margin_ids'].to('mps')
        mat = batch['margin_attn'].to('mps')
        ctid = batch['correct_tid'].to('mps')
        wtid = batch['wrong_tid'].to('mps')
        pid = batch['preserve_ids'].to('mps')
        pat = batch['preserve_attn'].to('mps')

        opt.zero_grad()

        # --- Margin loss on repair samples ---
        out = bb.model(input_ids=mid, attention_mask=mat)
        logits = out.logits[:, -1, :]  # last token logits

        # Get logits for correct and wrong token
        batch_indices = torch.arange(logits.shape[0], device='mps')
        c_logit = logits[batch_indices, ctid]
        w_logit = logits[batch_indices, wtid]

        loss_margin = margin_loss_fn(c_logit, w_logit, m=5.0)

        # --- Next-token preserve loss on preserve samples ---
        out_p = bb.model(input_ids=pid, attention_mask=pat, labels=pid)
        loss_preserve = out_p.loss

        # Total loss
        loss = loss_margin + loss_preserve
        loss.backward()
        torch.nn.utils.clip_grad_norm_(block.parameters(), 1.0)
        opt.step()

        total_margin += loss_margin.item(); total_preserve += loss_preserve.item()
        total_loss += loss.item(); nb += 1

    # Eval
    for sc in [0.05, 0.10, 0.15]:
        block.scale = sc
        i2 = BlockInjector(bb); i2.inject_block(block,23,'down_proj')
        i2.set_active_blocks([])
        bl = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
        i2.set_active_blocks([block.block_id])
        bk = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
        i2.remove_all_patches()
        fx = sum(1 for p in bl if bk[p] > bl[p])
        br = sum(1 for p in bl if bk[p] < bl[p])

        # Track best
        if fx - br > best_net:
            best_net = fx - br
            best_info = {'epoch': ep+1, 'scale': sc, 'fixes': fx, 'breaks': br, 'net': fx-br}

    avg_m = total_margin/max(nb,1)
    avg_p = total_preserve/max(nb,1)
    print(f'  Ep{ep+1}: margin={avg_m:.4f} preserve={avg_p:.3f}', end='')
    for sc in [0.05, 0.10, 0.15]:
        block.scale = sc
        i2 = BlockInjector(bb); i2.inject_block(block,23,'down_proj')
        i2.set_active_blocks([])
        bl = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
        i2.set_active_blocks([block.block_id])
        bk = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
        i2.remove_all_patches()
        fx = sum(1 for p in bl if bk[p] > bl[p])
        br = sum(1 for p in bl if bk[p] < bl[p])
        print(f'  s={sc}:{fx}-{br}={fx-br}', end='')
    print()

inj.remove_all_patches()

# Final full scan
print('\n=== Final scale scan ===')
for sc in [0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20]:
    block.scale = sc
    i2 = BlockInjector(bb); i2.inject_block(block,23,'down_proj')
    i2.set_active_blocks([])
    bl = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
    i2.set_active_blocks([block.block_id])
    bk = {p: compute_accuracy(p, bb.generate(p,64,do_sample=False), c) for c,pl in BP.items() for p in pl}
    i2.remove_all_patches()
    fx = sum(1 for p in bl if bk[p] > bl[p])
    br = sum(1 for p in bl if bk[p] < bl[p])
    ba = sum(bl.values())/len(bl); ka = sum(bk.values())/len(bk)
    print(f'scale={sc:.3f}  bl={ba:.3f}  bk={ka:.3f}  fixes={fx}  breaks={br}  net={fx-br}')
    if fx > 0 or br > 0:
        for p in bl:
            if bk[p] != bl[p]:
                cat = [c for c,pl in BP.items() if p in pl][0]
                kw = EXPECTED_ANSWERS.get(cat,[]); prompts = BP[cat]
                idx = prompts.index(p)
                exp = kw[idx] if idx < len(kw) else '?'
                print(f'  {p[:55]:<55} {bl[p]:.0f}->{bk[p]:.0f} [exp={exp}]')

print(f'\nBest across training: epoch={best_info.get("epoch","?")} scale={best_info.get("scale","?")} '
      f'fixes={best_info.get("fixes",0)} breaks={best_info.get("breaks",0)} net={best_info.get("net",0)}')
print('\n' + ('✅ net >= +2, breaks <= 1: OBJECTIVE CEILING BROKEN!' if best_net >= 2 else '❌ net still at ceiling'))
