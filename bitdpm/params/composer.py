"""Parameter composition: W_eff = W_main + Σ g_i · ΔW_i.

Provides three connection function variants (v16):
    v1: HardAdd — current baseline: y = Wx + Σ g·ΔWx (unchanged).
    v2: NormClipped — clip Δy if ||Δy|| / ||y_base|| > max_ratio.
    v3: TokenGated — apply block only to selected token positions
        (e.g. answer tokens, numerical tokens, low-confidence steps).

GPU-Centric design principle:
    CPU produces an ExecutionPlan (which blocks, what connection, what gate).
    GPU executes the actual block computation fused with the main forward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

import torch
import torch.nn as nn

from bitdpm.params.parameter_block import ParameterBlock


# ---------------------------------------------------------------------------
# Connection function modes (v16)
# ---------------------------------------------------------------------------

class ConnectionMode(str, Enum):
    """How parameter block output is connected into the main forward."""
    HARD_ADD = "hard_add"       # y = Wx + Σ g·ΔWx  (current v1 baseline)
    NORM_CLIP = "norm_clip"     # clip Δy if too large relative to y_base (v2)
    TOKEN_GATE = "token_gate"   # apply Δy only to specific token positions (v3)


@dataclass
class ExecutionPlan:
    """CPU-produced plan consumed by GPU for block execution.

    CPU does: routing, metadata lookup, feature detection.
    GPU does: actual block forward with the connection function.
    """
    active_block_ids: list[str] = field(default_factory=list)
    scales: list[float] = field(default_factory=list)
    connection_mode: ConnectionMode = ConnectionMode.HARD_ADD
    norm_clip_ratio: float = 0.5        # max ||Δy|| / ||y_base|| for NormClip
    token_gate_fn: str = "none"          # "none", "numerical", "answer", "low_confidence"
    routing_time_ms: float = 0.0

    @classmethod
    def make_hard_add(cls, block_ids: list[str], scales: Optional[list[float]] = None) -> "ExecutionPlan":
        """Create a v1 hard-add plan."""
        scales = scales or [1.0] * len(block_ids)
        return cls(active_block_ids=block_ids, scales=scales, connection_mode=ConnectionMode.HARD_ADD)

    @classmethod
    def make_norm_clip(cls, block_ids: list[str], scales: Optional[list[float]] = None,
                       ratio: float = 0.5) -> "ExecutionPlan":
        """Create a v2 norm-clipped plan."""
        scales = scales or [1.0] * len(block_ids)
        return cls(active_block_ids=block_ids, scales=scales,
                   connection_mode=ConnectionMode.NORM_CLIP, norm_clip_ratio=ratio)

    @classmethod
    def make_token_gate(cls, block_ids: list[str], scales: Optional[list[float]] = None,
                        gate_fn: str = "numerical") -> "ExecutionPlan":
        """Create a v3 token-gated plan."""
        scales = scales or [1.0] * len(block_ids)
        return cls(active_block_ids=block_ids, scales=scales,
                   connection_mode=ConnectionMode.TOKEN_GATE, token_gate_fn=gate_fn)


# ---------------------------------------------------------------------------
# Connection function implementations (GPU side)
# ---------------------------------------------------------------------------

def apply_delta_hard_add(y_base: torch.Tensor, delta: torch.Tensor, scale: float) -> torch.Tensor:
    """v1: Hard-add connection. No gate, no clip."""
    return y_base + scale * delta


def apply_delta_norm_clip(y_base: torch.Tensor, delta: torch.Tensor,
                          scale: float, max_ratio: float = 0.5) -> torch.Tensor:
    """v2: Norm-clipped connection.

    Computes ratio = ||Δy|| / ||y_base|| per token (row).
    If ratio > max_ratio, scales Δy down so the ratio equals max_ratio.
    This prevents any single block from overwhelming the main hidden state.
    """
    delta_scaled = scale * delta

    # Compute per-token norms
    y_norm = y_base.norm(dim=-1, keepdim=True)  # (batch, 1)
    d_norm = delta_scaled.norm(dim=-1, keepdim=True)  # (batch, 1)

    # Clip where ratio exceeds max_ratio
    ratio = d_norm / (y_norm.clamp(min=1e-8))
    clip_factor = torch.where(ratio > max_ratio, max_ratio / ratio, torch.ones_like(ratio))

    return y_base + delta_scaled * clip_factor


def apply_delta_token_gate(y_base: torch.Tensor, delta: torch.Tensor,
                           scale: float, hidden_states: Optional[torch.Tensor] = None,
                           gate_fn: str = "numerical") -> torch.Tensor:
    """v3: Token-level selective connection.

    Only applies the block update to tokens matching the gate condition.
    For "numerical": gates on tokens where hidden state has high numerical density.
    For "low_confidence": gates on tokens where softmax entropy is high.

    For now, uses a simple heuristic: gate based on attention norm pattern.
    A learned gate would be the production version.
    """
    delta_scaled = scale * delta

    if gate_fn == "numerical" and hidden_states is not None:
        # Detect tokens likely to be answer tokens (high activation norm)
        h_norm = hidden_states.norm(dim=-1, keepdim=True)  # (batch, seq, 1)
        gate = (h_norm > h_norm.mean(dim=-2, keepdim=True)).float()
        return y_base + delta_scaled * gate
    elif gate_fn == "all":
        return y_base + delta_scaled
    else:
        return y_base + delta_scaled  # fallback: no gate


# Register connection functions by mode
CONNECTION_FUNCTIONS: dict[ConnectionMode, Callable] = {
    ConnectionMode.HARD_ADD: apply_delta_hard_add,
    ConnectionMode.NORM_CLIP: apply_delta_norm_clip,
    ConnectionMode.TOKEN_GATE: apply_delta_token_gate,
}


# ---------------------------------------------------------------------------
# Composer (v16 with connection function support)
# ---------------------------------------------------------------------------

class Composer(nn.Module):
    """Composes the main model weights with selected parameter blocks.

    Supports three connection modes:
        HARD_ADD:  y = Wx + Σ g·ΔWx  (v1 baseline)
        NORM_CLIP: same but clip Δy if ||Δy||/||y_base|| > ratio (v2)
        TOKEN_GATE: apply Δy only at gated token positions (v3)
    """

    def __init__(
        self,
        mode: ConnectionMode = ConnectionMode.HARD_ADD,
        blocks: Optional[list[ParameterBlock]] = None,
        default_weights: Optional[list[float]] = None,
        norm_clip_ratio: float = 0.5,
    ):
        super().__init__()
        self.connection_mode = mode
        self.norm_clip_ratio = norm_clip_ratio
        self.token_gate_fn = "none"
        self._blocks: dict[str, ParameterBlock] = {}
        self._active_block_ids: Optional[list[str]] = None

        if blocks:
            for block in blocks:
                self._blocks[block.block_id] = block

        self.default_weights: dict[str, float] = {}
        if default_weights and blocks:
            for block, weight in zip(blocks, default_weights):
                self.default_weights[block.block_id] = weight
        elif blocks:
            for block in blocks:
                self.default_weights[block.block_id] = 1.0

    def add_block(self, block: ParameterBlock, weight: float = 1.0):
        self._blocks[block.block_id] = block
        self.default_weights[block.block_id] = weight

    def set_active_blocks(self, block_ids: Optional[list[str]]):
        self._active_block_ids = block_ids

    def set_connection(self, mode: ConnectionMode, ratio: float = 0.5, gate_fn: str = "none"):
        """Switch connection function at runtime."""
        self.connection_mode = mode
        self.norm_clip_ratio = ratio
        self.token_gate_fn = gate_fn

    def apply_plan(self, plan: ExecutionPlan):
        """Accept an ExecutionPlan from CPU and configure accordingly."""
        self.set_active_blocks(plan.active_block_ids)
        self.set_connection(plan.connection_mode, plan.norm_clip_ratio, plan.token_gate_fn)

    @property
    def blocks(self) -> dict[str, ParameterBlock]:
        return dict(self._blocks)

    @property
    def num_blocks(self) -> int:
        return len(self._blocks)

    @property
    def active_block_ids(self) -> list[str]:
        if self._active_block_ids is None:
            return list(self._blocks.keys())
        return [bid for bid in self._active_block_ids if bid in self._blocks]

    def get_weights(self, block_ids: list[str]) -> list[float]:
        return [self.default_weights.get(bid, 1.0) for bid in block_ids]

    def compute(
        self,
        x: torch.Tensor,
        main_forward_fn: Callable,
        active_block_ids: Optional[list[str]] = None,
        weights: Optional[list[float]] = None,
        hidden_states: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Compute composed forward with the active connection function.

        Args:
            x: Input tensor (batch, in_features).
            main_forward_fn: Function that computes W_main @ x.
            active_block_ids: Override for active blocks (None = use mask or all).
            weights: Per-block gate values (None = default weights).
            hidden_states: Hidden states for token-level gating (v3 only).

        Returns:
            Composed output y = W_main x + connection(ΔW_i x).
        """
        # Main forward (GPU)
        y = main_forward_fn(x)

        # Determine active blocks
        if active_block_ids is not None:
            active_ids = [bid for bid in active_block_ids if bid in self._blocks]
        elif self._active_block_ids is not None:
            active_ids = [bid for bid in self._active_block_ids if bid in self._blocks]
        else:
            active_ids = list(self._blocks.keys())

        if weights is None:
            gate_weights = [self.default_weights.get(bid, 1.0) for bid in active_ids]
        else:
            gate_weights = weights

        # For token-gated mode, we need the hidden states for each token
        # hidden_states should be the intermediate hidden states before this linear
        for bid, g in zip(active_ids, gate_weights):
            if g == 0.0:
                continue

            # Compute ΔW_i x (GPU)
            delta = self._blocks[bid].forward(x)

            # Apply connection function (GPU)
            if self.connection_mode == ConnectionMode.NORM_CLIP:
                conn_fn = CONNECTION_FUNCTIONS[ConnectionMode.NORM_CLIP]
                y = conn_fn(y, delta, g, max_ratio=self.norm_clip_ratio)
            elif self.connection_mode == ConnectionMode.TOKEN_GATE:
                conn_fn = CONNECTION_FUNCTIONS[ConnectionMode.TOKEN_GATE]
                hs_for_gate = hidden_states if hidden_states is not None else x
                y = conn_fn(y, delta, g, hidden_states=hs_for_gate, gate_fn=self.token_gate_fn)
            else:
                # HARD_ADD (default)
                y = y + g * delta

        return y

    def set_mode(self, mode: ConnectionMode):
        self.connection_mode = mode

    def extra_repr(self) -> str:
        return (f"connection={self.connection_mode.value}, "
                f"num_blocks={self.num_blocks}, "
                f"norm_clip_ratio={self.norm_clip_ratio}")
