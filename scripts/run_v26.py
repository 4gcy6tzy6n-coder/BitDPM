"""v26: Same-layer dual-module block composition (o_proj + down_proj)."""
import torch, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(42)

from bitdpm.eval.benchmark import EVAL_PROMPTS as BP, compute_accuracy, EXPECTED_ANSWERS
from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig
from torch.utils.data import DataLoader, Dataset

repair_texts = []
for a,b in [(25,200),(15,80),(10,50),(20,100),(50,80),(30,150),(5,200),(75,40)]:
    ans = str(a*b//100)
    for t in [f'What is {a}% of {b}?', f'Calculate {a} percent of {b}.', f'Find {a}% of {b}.']:
        repair_texts.append(f'{t} {ans}')
for v in [144,100,169,225,400,81,49,121]:
    repair_texts.append(f'What is the square root of {v}? {str(int(v**0.5))}')
for a,b in [(2,10),(2,5),(3,4)]:
    repair_texts.append(f'What is {a} to the power of {b}? {str(a**b)}')
for sp,hr in [(60,2.5),(80,3)]:
    repair_texts.append(f'If a train travels at {sp} km/h for {hr} hours, how far does it go? {str(int(sp*hr))}')
for a,b in [(5,12),(3,11)]:
    repair_texts.append(f'If x + {a} = {b}, what is x? {str(b-a)}')

preserve_texts = [
    'What is the capital of France? Paris.',
    'What is the largest ocean on Earth? Pacific Ocean.',
    'Calculate 15 + 27 = 42.',
]
hard_texts = ['What is 50% of 200? 100.', 'What is 2^5? 32.']

all_texts = repair_texts + preserve_texts + hard_texts
random.shuffle(all_texts)
print(f'Data: {len(repair_texts)}R + {len(preserve_texts)}P + {len(hard_texts)}H = {len(all_texts)}T')

bb = BackboneModel(model_name='Qwen/Qwen2.5-0.5B-Instruct', device='mps', dtype=torch.float32)

lin_d = bb.get_linear_layer(23, 'down_proj')
lin_o = bb.get_linear_layer(23, 'o_proj')

b_d = ParameterBlock(ParameterBlockConfig('v26_down_l23_r16',23,'down_proj',16,1.0,'percent',
    bb.hidden_size,lin_d.in_features,lin_d.out_features)).to(device='mps',dtype=torch.float32)
b_o = ParameterBlock(ParameterBlockConfig('v26_o_l23_r16',23,'o_proj',16,1.0,'percent',
    bb.hidden_size,lin_o.in_features,lin_o.out_features)).to(device='mps',dtype=torch.float32)
print(f'Blocks: down={sum(p.numel() for p in b_d.parameters()):,}p  o={sum(p.numel() for p in b_o.parameters()):,}p')

class SDS(Dataset):
    def __init__(self,t,tok,ml=96):
        self.e=tok(t,truncation=True,padding='max_length',max_length=ml,return_tensors='pt')
    def __len__(self): return len(self.e.input_ids)
    def __getitem__(self,i): return {'input_ids':self.e.input_ids[i]}

ds=SDS(all_texts,bb.tokenizer); dl=DataLoader(ds,batch_size=2,shuffle=True)

def train(blk,mname,eps=10):
    inj=BlockInjector(bb); inj.inject_block(blk,23,mname)
    opt=torch.optim.AdamW(blk.parameters(),lr=1e-4); blk.train()
    for p in bb.model.parameters(): p.requires_grad=False
    print(f'Training {blk.block_id}...')
    for ep in range(eps):
        ls_sum=0;nb=0
        for batch in dl:
            ids=batch['input_ids'].to('mps'); opt.zero_grad()
            out=bb.model(input_ids=ids,labels=ids); ls=out.loss
            if ls.grad_fn is not None:
                ls.backward(); torch.nn.utils.clip_grad_norm_(blk.parameters(),1.0); opt.step()
                ls_sum+=ls.item(); nb+=1
        print(f'  Ep{ep+1}: loss={ls_sum/max(nb,1):.3f}')
    inj.remove_all_patches()

train(b_d,'down_proj'); train(b_o,'o_proj')

def eval_blk(blks,scales,label):
    print(f'\n=== {label} ===')
    inj=BlockInjector(bb)
    for b,s in zip(blks,scales): b.scale=s; inj.inject_block(b,b.layer_id,b.module_name)
    inj.set_active_blocks([])
    bl={p: compute_accuracy(p,bb.generate(p,max_new_tokens=64,do_sample=False),cat)
        for cat,pl in BP.items() for p in pl}
    ba=sum(bl.values())/len(bl); print(f'  Baseline: {ba:.3f}')
    inj.set_active_blocks([b.block_id for b in blks])
    bk={p: compute_accuracy(p,bb.generate(p,max_new_tokens=64,do_sample=False),cat)
        for cat,pl in BP.items() for p in pl}
    inj.remove_all_patches()
    fx=sum(1 for p in bl if bk[p]>bl[p]); br=sum(1 for p in bl if bk[p]<bl[p])
    ka=sum(bk.values())/len(bk); print(f'  Block: {ka:.3f}  fixes={fx}  breaks={br}  net={fx-br}')
    for p in bl:
        if bk[p]!=bl[p] and (fx>0 or br>0):
            cat=[c for c,pl in BP.items() if p in pl][0]
            kw=EXPECTED_ANSWERS.get(cat,[]); pl=BP[cat]; idx=pl.index(p)
            exp=kw[idx] if idx<len(kw) else '?'
            print(f'    {p[:50]:<50} {bl[p]:.0f}->{bk[p]:.0f} [exp={exp}]')
    return fx,br,fx-br

eval_blk([b_d],[0.10],'DOWN only(0.10)')
eval_blk([b_o],[0.10],'O only(0.10)')
eval_blk([b_o],[0.05],'O only(0.05)')
for os in [0.03,0.05,0.075,0.10]:
    eval_blk([b_d,b_o],[0.10,os],f'DOWN(0.10)+O({os})')
for s in [0.05,0.075]:
    eval_blk([b_d,b_o],[s,s],f'DOWN+O both({s})')
