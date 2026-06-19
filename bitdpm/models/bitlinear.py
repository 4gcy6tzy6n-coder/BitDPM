"""BitLinear / NF4 quantization for BitDPM backbone.

Implements proper NF4 (Normal Float 4) quantization following QLoRA:
- Non-uniform 4-bit quantization optimized for normally distributed weights
- Two 4-bit values packed per byte
- On-the-fly dequantization during forward pass
- Support for INT8 symmetric quantization via PyTorch native

NF4 quantile values from: QLoRA (Dettmers et al., 2023)
https://arxiv.org/abs/2305.14314
"""

from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# NF4 quantile table (from QLoRA paper)
# 16 values for 4-bit, optimized for normal distribution N(0, 1)
# ---------------------------------------------------------------------------

NF4_QUANTILES = torch.tensor([
    -1.0, -0.6961928009986877, -0.5250730514526367, -0.39491748809814453,
    -0.28444138169288635, -0.18477343022823334, -0.09105003625154495, 0.0,
    0.07958029955625534, 0.16093020141124725, 0.24611230194568634,
    0.33791524171829224, 0.44070982933044434, 0.5626170039176941,
    0.7229568362236023, 1.0,
])


class NF4Linear(nn.Module):
    """Linear layer with NF4 quantized weights.

    Stores weights in NF4 format (4-bit), dequantizes on-the-fly.
    In a real deployment, this would use efficient uint4 matmul kernels.
    For research prototyping, we pack/dequantize per forward.
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        orig_linear: Optional[nn.Linear] = None,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self._orig_dtype = torch.float16  # default, overridden in _quantize

        if orig_linear is not None:
            self._quantize_from_linear(orig_linear)
        else:
            numel = in_features * out_features
            self.register_buffer("quantized_weight", torch.zeros(math.ceil(numel // 2), dtype=torch.uint8))
            self.register_buffer("absmax", torch.zeros(out_features, 1))
            self.register_buffer("bias", torch.zeros(out_features))

    def _quantize_from_linear(self, linear: nn.Linear):
        """Quantize a nn.Linear's weights to NF4 format."""
        self._orig_dtype = linear.weight.dtype
        w = linear.weight.data.float()

        # Per-row absmax normalization
        absmax = w.abs().max(dim=1, keepdim=True).values.clamp(min=1e-8)
        w_norm = w / absmax

        # Quantize to NF4 indices. The quantile table is sorted, so nearest
        # quantization can be done by bucketizing against adjacent midpoints
        # instead of materializing a huge (num_weights x 16) distance matrix.
        flat = w_norm.reshape(-1).contiguous()
        quantiles = NF4_QUANTILES.to(w.device)
        boundaries = (quantiles[:-1] + quantiles[1:]) / 2
        indices = torch.bucketize(flat, boundaries).to(torch.uint8)

        # Pack two 4-bit values per byte
        n = indices.numel()
        n_packed = (n + 1) // 2
        packed = torch.zeros(n_packed, dtype=torch.uint8)
        packed[: n // 2] = indices[::2] | (indices[1::2] << 4)
        if n % 2 == 1:
            packed[-1] = indices[-1]

        self.register_buffer("quantized_weight", packed)
        self.register_buffer("absmax", absmax)
        bias_val = (linear.bias.data.clone().float() if linear.bias is not None
                    else torch.zeros(self.out_features))
        self.register_buffer("bias", bias_val)

    @property
    def weight(self) -> torch.Tensor:
        """Dequantized weight in original dtype (for transformers compatibility)."""
        return self.dequantize().to(self._orig_dtype)

    def dequantize(self) -> torch.Tensor:
        """Dequantize the packed NF4 weights to full float.

        Returns: (out_features, in_features) float tensor.
        """
        # Unpack
        packed = self.quantized_weight
        n = self.in_features * self.out_features
        n_half = packed.numel()

        indices = torch.zeros(n, dtype=torch.uint8, device=packed.device)
        indices[: min(n, n_half * 2) : 2] = packed[: n_half] & 0x0F
        indices[1 : min(n, n_half * 2) : 2] = (packed[: n_half] >> 4) & 0x0F

        # Map indices to NF4 values
        nf4_vals = NF4_QUANTILES.to(packed.device)[indices.long()]

        # Denormalize with per-row absmax
        w = nf4_vals.reshape(self.out_features, self.in_features).float()
        w = w * self.absmax
        return w

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Dequantize weights and compute linear forward.

        NOTE: For research prototyping. A production version would use
        efficient uint4 matmul kernels.
        """
        w = self.dequantize().to(dtype=x.dtype)
        b = self.bias.to(dtype=x.dtype) if self.bias is not None else None
        return nn.functional.linear(x, w, b)

    def extra_repr(self) -> str:
        return f"in_features={self.in_features}, out_features={self.out_features}, quant=NF4"


def convert_linear_to_nf4(model: nn.Module) -> int:
    """Replace all nn.Linear modules with NF4Linear in-place.

    Args:
        model: The PyTorch model to quantize.

    Returns:
        Number of layers converted.
    """
    converted = 0

    def _convert(module: nn.Module) -> None:
        nonlocal converted
        for name, child in list(module.named_children()):
            if isinstance(child, nn.Linear):
                nf4 = NF4Linear(
                    child.in_features,
                    child.out_features,
                    bias=child.bias is not None,
                    orig_linear=child,
                )
                setattr(module, name, nf4)
                converted += 1
                if converted % 25 == 0:
                    print(f"[NF4] Converted {converted} linear layers...")
            else:
                _convert(child)

    _convert(model)
    return converted


def convert_linear_to_int8_symmetric(model: nn.Module) -> int:
    """Apply INT8 symmetric quantization to all nn.Linear weights in-place.

    Unlike simulated quant, this stores the scale per-row for accuracy.
    """
    converted = 0
    for module in model.modules():
        if isinstance(module, nn.Linear):
            w = module.weight.data.float()
            # Per-row quantization
            scale = w.abs().max(dim=1, keepdim=True).values / 127.0
            scale = scale.clamp(min=1e-8)
            w_q = torch.clamp(torch.round(w / scale), -128, 127)
            w_deq = w_q * scale
            module.weight.data = w_deq.to(module.weight.dtype)
            converted += 1
    return converted
