# BitDPM 技术文档：崩溃与兼容性复盘

> 项目从 v0.1 到 v31，经历了多类系统级崩溃和机制级失效。  
> 本文档记录每类崩溃的根本原因、诊断方法、修复方案，以及防止复发的工程规范。

> **2026-06-16 v31-R 审计更新**：`v31_router_20260610_144251.json`
> 记录了 `allow_math@0.85 -> fixes=6, breaks=0, net=+6`，但该文件没有保存
> `model`、`block_path`、`block_sha256` 等 provenance。后续复验发现当前保存的
> 145 个 block artifact 均为 Qwen2.5-0.5B 维度，未发现 1.5B-compatible block；
> 使用现有 0.5B block pool 复跑 `allow_math@0.85` 也未复现 v31 强结果。因此，
> `fixes=6, breaks=0` 只能作为历史记录保留，不能作为已确认 1.5B 主结果或当前
> 可复现主结果，直到精确 block artifact 被找回或重新训练并复验。

---

## 目录

1. [维度不匹配：模型切换时 Block 形状崩溃](#1-维度不匹配模型切换时-block-形状崩溃)
2. [设备不匹配：CPU↔MPS 搬运导致的运行时崩溃](#2-设备不匹配-cupmps-搬运导致的运行时崩溃)
3. [精度不匹配：FP16 NaN 崩溃](#3-精度不匹配-fp16-nan-崩溃)
4. [训练不收敛：Rank32 梯度消失](#4-训练不收敛-rank32-梯度消失)
5. [Gating 无声失效：Block 看起来生效但实际是 No-op](#5-gating-无声失效-block-看起来生效但实际是-no-op)
6. [后端兼容性：MPS 不可用时的静默回退](#6-后端兼容性mps-不可用时的静默回退)
7. [附录：工程规范清单](#7-附录工程规范清单)

---

## 1. 维度不匹配：模型切换时 Block 形状崩溃

### 错误信息

```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (7x8960 and 4864x16)
```

### 崩溃现场

在将 BitDPM 从 Qwen2.5-0.5B（hidden=896, intermediate=4864）迁移到 Qwen2.5-1.5B（hidden=1536, intermediate=8960）时，加载旧的 `.pt` block 文件后执行 forward 报错。

### 根本原因

`ParameterBlockConfig` 中的 `in_features` / `out_features` 是在创建时从 `lin.in_features` / `lin.out_features` 推导的。当 block 文件在 0.5B 上训练好，保存后直接在 1.5B 上加载时，block 的 A 矩阵形状（4864×16）与 1.5B 模型的 hidden state 形状（batch×8960）不兼容。

```
0.5B down_proj: 4864 → 896
1.5B down_proj: 8960 → 1536

ΔW = A @ B
A: (in_features, rank) = (4864, 16)  ← 0.5B 形状
B: (rank, out_features) = (16, 896)  

但 1.5B 输入 x 的形状是 (batch, 8960)
x @ A 时: (batch, 8960) @ (4864, 16) → ❌ 维度不匹配
```

### 触发条件

- 在不同 backbone 间共享 block 文件（0.5B ↔ 1.5B）
- 在同一 backbone 的不同 layer 间复制 block 文件（layer 23 → layer 0）
- 在不检查维度的加载路径中 `ParameterBlock.load()` 无维度验证

### 诊断方法

```python
# 加载后检查维度
block = ParameterBlock.load(path, device=device)
expected_in = model.get_linear_layer(layer, module).in_features
assert block.A.shape[0] == expected_in, \
    f"Block in_features {block.A.shape[0]} != layer {expected_in}"
```

### 修复方案

```python
class ParameterBlockConfig:
    def validate_for_layer(self, lin: nn.Linear) -> bool:
        return (self.in_features == lin.in_features and 
                self.out_features == lin.out_features)
```

**加载时校验：**

```python
@classmethod
def load(cls, path: str, device=None, validate_for: nn.Linear = None):
    block = cls(config)
    if validate_for is not None:
        assert config.in_features == validate_for.in_features
        assert config.out_features == validate_for.out_features
```

### 防止复发

1. **Block 文件与模型绑定**：文件名包含 model_name、layer_id、module_name（如 `v29_l26_r16.pt`）
2. **加载时维度验证**：加载后比对 `block.A.shape[0] == lin.in_features`
3. **`BlockBank.list_blocks()` 输出 metadata**：每次加载块时打印形状供审计

---

## 2. 设备不匹配：CPU↔MPS 搬运导致的运行时崩溃

### 错误信息

```
RuntimeError: expected mat1 and mat2 to have the same dtype, but got: c10::Half != float
RuntimeError: Tensor for argument #2 'mat2' is on CPU, but expected it to be on GPU
```

### 崩溃现场

模型 backbone 在 MPS（Apple GPU）上以 float16 运行，Block 的 A/B 矩阵在 CPU 上以 float32 初始化。首次 forward 时 `block.forward(x)` 报错，因为 `x` 在 MPS 上而 `self.A` 在 CPU 上。

### 根本原因

`ParameterBlock` 没有保证 A/B 矩阵与输入 x 在同一设备。BlockDeviceManager 不存在时，每个 block forward 都需要手动 `A.to(x.device)`，但早期代码中没有实现。

```python
# ❌ 错误的实现：不检查设备
def forward(self, x):
    return self.scale * ((x @ self.A) @ self.B)
    # x 在 mps, self.A 在 cpu → RuntimeError
```

### 触发条件

- 模型用 `to('mps')` / `to('cuda')` 加载而 block 默认在 CPU
- `ParameterBlock.load()` 未指定 device 参数
- 训练脚本中创建 backbone 后未移动 block

### 诊断方法

```python
# 快速诊断
for name, block in [('down', block_down), ('o', block_o)]:
    print(f"{name}_block A device: {block.A.device}")  # → cpu ❌
    print(f"model device: {next(bb.model.parameters()).device}")  # → mps ✅
```

### 修复方案

**方案 A：加载时指定设备**

```python
block = ParameterBlock.load(path, device=torch.device('mps'))
# 或
block = block.to(device='mps', dtype=torch.float16)
```

**方案 B：引入 BlockDeviceManager（推荐）**

```python
dev_mgr = BlockDeviceManager(target_device='mps', dtype=torch.float16)
dev_mgr.preload_all(block_bank.blocks)
# forward 中不再有 .to(x.device)，A/B 已在 mps 上
```

**方案 C：forward 中添加断言和自动搬移（不推荐作为长期方案）**

```python
class ParameterBlock:
    def forward(self, x):
        if self.A.device != x.device:
            raise RuntimeError(f"Block {self.block_id}: A on {self.A.device} but x on {x.device}")
        if self.A.dtype != x.dtype:
            self.A.data = self.A.data.to(dtype=x.dtype)
            self.B.data = self.B.data.to(dtype=x.dtype)
```

### 防止复发

1. **git hook / 代码检查**：禁止 `forward` 中出现 `.to(x.device)` 或 `.to(x.dtype)`
2. **训练前打印设备信息**：加载后验证 backbone.device == block.A.device
3. **单元测试**：

```python
def test_block_device_match(device='mps'):
    block = make_test_block()
    x = torch.randn(4, 64, device=device)
    block = block.to(device)
    y = block(x)
    assert y.device == device
```

---

## 3. 精度不匹配：FP16 NaN 崩溃

### 错误信息

```
RuntimeError: probability tensor contains inf, nan or element < 0
loss = nan  # 训练日志中
```

### 崩溃现场

在 MPS 上用 float16 训练时，loss 在第一个 epoch 就变成 NaN。  
在 MPS 上用 float32 训练正常。

### 根本原因

MPS 的 float16 梯度不稳定，尤其在以下场景：
1. **B 矩阵零初始化**：B = 0 → 首次前向时 `x @ A @ B = 0`，梯度通过零张量回传时产生 NaN
2. **LoRA 的 `scale * (x @ A) @ B` 在 FP16 下**：A 的初始值较大（kaiming uniform），乘以 FP16 的 x 后上溢
3. **MPS 的 FP16 matmul 精度低于 CUDA**

### 触发条件

- `ParameterBlock()` 使用默认 float32 初始化但模型在 float16
- MPS 后端训练
- B 矩阵为零初始化（LoRA 标准做法）

### 诊断方法

```python
# 打印 A/B 的 norm 和是否 NaN
print(f'A.norm={block.A.norm().item()}, B.norm={block.B.norm().item()}')
print(f'A has nan: {torch.isnan(block.A).any()}')
# 在 loss.backward() 后
print(f'A.grad nan: {torch.isnan(block.A.grad).any() if block.A.grad is not None else "no grad"}')
```

### 修复方案

```python
# ✅ 方案：用 float32 训练，转 float16 推理
# 训练
model = BackboneModel(model_name, device='mps', dtype=torch.float32)
block = ParameterBlock(config).to(device='mps', dtype=torch.float32)

# 推理时转 float16
block_f16 = block.to(dtype=torch.float16)
```

### 防止复发

1. **训练用 float32，推理用 float16**
2. **梯度裁剪**：`clip_grad_norm_(block.parameters(), max_norm=1.0)`
3. **NaN 检查**：训练循环中添加 `if torch.isnan(loss): break`

---

## 4. 训练不收敛：Rank32 梯度消失

### 错误信息

```
Ep1: loss=7.769  (比 Ep1 的 6.411 还高)
Ep2-12: loss 波动，不自下降
Rank32: 所有 scale 下 fixes=0, breaks=0, net=0
```

### 崩溃现场

Rank-32 block（184K 参数）在 0.5B backbone 上训练时，loss 不下降，block 不产生任何可观测效果。

### 根本原因

Rank-32 的参数数量（184K）相对于 frozen backbone（494M）的梯度信号来说太大。gradient signal-to-noise ratio 太低，导致参数更新方向随机，无法形成有效修复方向。

```text
Rank-16:  92K params / 494M frozen = 0.00019  (信号/噪声比刚好可用)
Rank-32: 184K params / 494M frozen = 0.00037  (信号被稀释)
Rank-64: 368K params / 494M frozen = 0.00075  (完全噪声支配)
```

### 触发条件

- 在小型 frozen backbone（0.5B）上尝试 > rank-16 的 block
- 单层单模块注入
- 训练数据量不足以支撑大容量 block

### 诊断方法

```python
# 检查 A/B 在训练前后的变化
a_before = block.A.clone().detach()
# ... 训练 ...
a_after = block.A.clone().detach()
delta_norm = (a_after - a_before).norm().item()
print(f'A matrix delta norm: {delta_norm}')  # 如果 < 0.01，说明梯度太弱
```

### 修复方案

```text
在 0.5B backbone 上使用 rank-16 作为当前较稳的上限。若要切换到
1.5B backbone，必须重新训练 1.5B-compatible block，并保存完整 provenance
（model、layer、module、rank、A/B shape、block sha256、训练数据、评估配置）。
历史 v31 记录中出现的 `net=+6` 尚未通过当前 block artifact 复验，不能作为
1.5B 训练稳定有效的证据。
```

### 防止复发

1. **配置 rank 上限为 backbone 规模的函数**：`max_rank = min(16, backbone_params / 5e6)`
2. **训练前输出参数比**：`print(f'Block/Backbone ratio: {block_params}/{backbone_params}')`
3. **首次尝试新 rank 时，先做 3 个 epoch 的收敛测试**

---

## 5. Gating 无声失效：Block 看起来生效但实际是 No-op

### 错误信息

**无 RuntimeError**，但：

```python
screen_output: "routed block active"
实际行为: set_active_blocks() 后 block 仍然输出 baseline 结果
```

### 崩溃现场

v0.1–v0.3 的所有路由实验。Block 被注入，路由器签名输出选择，但 `BlockInjector.set_active_blocks()` 的方法体是 `pass`——所有 "routed" 配置实际等于 "always-all"。

```python
# ❌ v0.1-v0.3 的实现
class BlockInjector:
    def set_active_blocks(self, block_ids):
        for patched in self.patches.values():
            patched.composer.mode = "dynamic_topk"
            pass  # ← 没有实际设置 active block mask！
```

该 bug 持续了 3 个版本，所有 v0.1–v0.3 的路由实验结果作废。

### 根本原因

早期工程师在编写 `set_active_blocks` 时添加了 `pass` 作为占位符，但从未填充实际逻辑。测试路径没有覆盖"block 禁用时 baseline 是否恢复"。

### 触发条件

- 任何使用 `BlockInjector.set_active_blocks()` 的代码路径
- 任何依赖 `PatchedLinear.enabled = False` 以外的方式来禁用 block 的测试

### 诊断方法

```python
# ✅ 最简单的诊断方式：比较 block 启用和禁用时的输出
def test_gating_works(backbone, injector, block):
    injector.set_active_blocks([])  # 禁用所有块
    out_disabled = generate("What is 2+2?")
    
    injector.set_active_blocks([block.block_id])  # 启用
    out_enabled = generate("What is 2+2?")
    
    if out_disabled == out_enabled:
        print("⚠️ GATING NOT WORKING — block has zero effect!")
```

### 修复方案

```python
# ✅ v0.4 修正后的实现
class Composer:
    def set_active_blocks(self, block_ids):
        self._active_block_ids = block_ids  # ← 现在实际生效

    def compute(self, x, main_forward_fn):
        # 使用 self._active_block_ids 过滤 active blocks
        if self._active_block_ids is not None:
            active_ids = [bid for bid in self._active_block_ids if bid in self._blocks]
        else:
            active_ids = list(self._blocks.keys())
        # ... 只对 active_ids 中的块执行 forward
```

### 防止复发

1. **每次注入 block 后执行 gating test**：确认 baseline → block → baseline 恢复
2. **单元测试中验证**：`test_block_injection()` 检查 block 启用时输出变化，禁用时恢复到 baseline
3. **Gating 作为 CI 检查**：任何 router 实验前必须通过 gating test

---

## 6. 后端兼容性：MPS 不可用时的静默回退

### 错误信息

```
RuntimeError: The MPS backend is supported on MacOS 14.0+. Current OS version can be queried using `sw_vers`.
```

### 崩溃现场

项目中多次出现 MPS 检测 `torch.backends.mps.is_available()` 返回 `True`，但实际运行时报 MPS 版本不兼容错误。

### 根本原因

`torch.backends.mps.is_built()` 返回 `True`（PyTorch 编译了 MPS 支持），  
`torch.backends.mps.is_available()` 在某些 macOS 版本（如 macOS 26.2）上也可能返回 `True`，  
但实际 MPS 的实现与操作系统版本有兼容窗口，超过窗口的版本会静默失败。

### 触发条件

- macOS 版本高于 MPS 实现的兼容窗口（macOS 14.0-26.1 兼容，26.2+ 不兼容）
- 使用 `BackboneModel` 的自动设备检测：`device = "mps" if torch.backends.mps.is_available() else "cpu"`

### 诊断方法

```python
# 更保守的检测
def safe_mps_available():
    if not torch.backends.mps.is_built():
        return False
    if not torch.backends.mps.is_available():
        return False
    # 实际测试一次小张量运算
    try:
        x = torch.randn(4, 16, device='mps')
        y = x + 1
        return True
    except RuntimeError:
        return False
```

### 修复方案

```python
# ✅ 训练脚本中使用 try/except 包裹设备选择
for device in ['mps', 'cuda', 'cpu']:
    try:
        bb = BackboneModel(model_name, device=device, dtype=torch.float32)
        break
    except RuntimeError:
        continue
```

### 防止复发

1. **设备检测使用实际运算测试**，不只依赖 `is_available()`
2. **在 `BackboneModel.__init__` 中添加 fallback**：检测到 MPS 不可用时打印 WARNING 并回退到 CPU
3. **`run_*` 脚本的 `--device` 参数默认值中使用 try/except**

---

## 7. 附录：工程规范清单

### 7.0 当前结果归属状态

| 项目 | 状态 |
|------|------|
| v31 历史记录 | `allow_math@0.85` 记录为 `0.822 -> 0.956`, fixes=6, breaks=0 |
| provenance | 缺失 exact `block_path` / `block_sha256` / model metadata |
| block inventory | 145 个已保存 blocks 中 0 个 1.5B-compatible |
| 1.5B 复验 | 因 `(7x8960 and 4864x16)` 维度不匹配失败 |
| 0.5B 复验 | 31 个候选全部 `net <= 0`，最好 `1/3/-2` |
| 当前可用主张 | v31 强结果冻结；先做 block-backbone provenance recovery |

交接组不要直接把 `fixes=6, breaks=0` 写成当前 1.5B 主结果。正确表述是：

```text
v31 记录显示 safety router 可能达到 net=+6，但该结果缺少可复现 provenance。
当前保存 block 与 1.5B 不兼容，且 0.5B 候选池未复现 v31。因此 v31 必须先完成
block-backbone compatibility revalidation，才能进入更大 benchmark migration。
```

### 7.1 Block 加载规范

```python
# ✅ 每次加载 block 时验证维度
def load_block_safe(path, layer_id, module_name, backbone):
    block = ParameterBlock.load(path)
    lin = backbone.get_linear_layer(layer_id, module_name)
    assert block.A.shape[0] == lin.in_features, \
        f"Block in_features {block.A.shape[0]} != {lin.in_features}"
    assert block.B.shape[1] == lin.out_features, \
        f"Block out_features {block.B.shape[1]} != {lin.out_features}"
    block = block.to(device=next(backbone.model.parameters()).device,
                     dtype=next(backbone.model.parameters()).dtype)
    return block
```

### 7.2 Gating 测试规范（每次注入后执行）

```python
def verify_gating(backbone, injector, block_ids, test_prompts):
    """验证 block 启用/禁用能改变输出，禁用时恢复到 baseline。"""
    baseline_outputs = {}
    # Step 1: 获取 baseline
    injector.set_active_blocks([])
    for p in test_prompts:
        baseline_outputs[p] = backbone.generate(p, max_new_tokens=32, do_sample=False)
    # Step 2: 启用 block
    injector.set_active_blocks(block_ids)
    has_effect = False
    for p in test_prompts:
        out = backbone.generate(p, max_new_tokens=32, do_sample=False)
        if out != baseline_outputs[p]:
            has_effect = True
    # Step 3: 禁用 block，确认恢复
    injector.set_active_blocks([])
    for p in test_prompts:
        out = backbone.generate(p, max_new_tokens=32, do_sample=False)
        assert out == baseline_outputs[p], f"Gating failed: baseline not restored for {p}"
    assert has_effect, "Block has zero effect — injection may be broken"
```

### 7.3 精度管理规范

| 场景 | backbone dtype | block dtype | 说明 |
|------|---------------|-------------|------|
| 训练 | float32 | float32 | MPS 上 float16 不稳定 |
| 推理 | float16 | float16 | 加速，需前向前转换 |
| CPU 推理 | float32 | float32 | 无加速需求 |

### 7.4 维度验证清单

| 检查点 | 验证内容 |
|--------|----------|
| Block 加载 | `A.shape[0] == layer.in_features` |
| Block 加载 | `B.shape[1] == layer.out_features` |
| Block 加载 | `block.A.device == model_device` |
| Block 加载 | `block.A.dtype == model_dtype` |
| 训练开始前 | `A.norm() > 0, B.norm() == 0` |
| 训练开始前 | `block.parameters()` 的 requires_grad 正确 |
| forward 前 | input 与 block A 的 device/dtype 一致 |

### 7.5 交接代码入口

| 用途 | 路径 | 当前状态 |
|------|------|----------|
| 标准 router/block 评估框架 | `scripts/run_v32_router_validation.py` | 561 行；已加入 `validate_block_compatible()` 维度闸门 |
| v31 provenance 一键审计 | `scripts/audit_v31_provenance.py` | 汇总 v31 历史 JSON、block manifest、0.5B recovery，输出是否 recovered |
| block inventory / 维度审计 | `scripts/build_block_manifest.py` | 输出 `block_manifest.json/md`，可识别 0.5B/1.5B 维度族 |
| v31-R 兼容性审计报告 | `experiments/reports/bitdpm_v31r_compatibility_audit.md` | 当前权威归属结论 |
| 0.5B 复验摘要 | `experiments/reports/bitdpm_v31r_0p5b_recovery_summary.md` | 31 个候选均未复现 v31 强结果 |

最小验证命令：

```bash
python -m py_compile \
  bitdpm/params/parameter_block.py \
  scripts/run_v32_router_validation.py \
  scripts/build_block_manifest.py

python scripts/run_v32_router_validation.py \
  --block-path experiments/outputs/blocks_v17/v17_down_proj_l23_r16.pt \
  --benchmark-set core \
  --routers allow_math \
  --scales 0.85 \
  --dry-run

python scripts/audit_v31_provenance.py \
  --out experiments/reports/bitdpm_v31_provenance_audit.md
```

---

> 本文档最后更新：2026-06-17  
> 对应 BitDPM v31-R 审计状态，包含 v0.1 到 v31 的崩溃修复记录与当前结果归属修正。
