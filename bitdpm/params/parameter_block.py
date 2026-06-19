"""Independent parameter block (LoRA-like ΔW = A·B).

Each ParameterBlock represents a low-rank update ΔW_i = α · A_i B_i
applied to a specific linear layer of the backbone model.
"""

from __future__ import annotations

import json
import os
import pickle
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn as nn


@dataclass
class ParameterBlockConfig:
    """Configuration for a single parameter block."""

    block_id: str
    layer_id: int
    module_name: str  # e.g., "q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"
    rank: int = 8
    scale: float = 1.0
    block_type: str = "general"  # "general", "math", "code", "chinese", "factual", etc.
    hidden_size: int = 0
    in_features: int = 0
    out_features: int = 0


class ParameterBlock(nn.Module):
    """A low-rank parameter block ΔW = α · A @ B.

    For a linear layer y = Wx, the composed forward becomes:
        y = Wx + Σ_i g_i · ΔW_i x
        = Wx + Σ_i g_i · (α_i · A_i @ B_i) x

    This is mathematically equivalent to LoRA's approach.
    """

    def __init__(self, config: ParameterBlockConfig):
        super().__init__()
        self.config = config
        self.block_id = config.block_id
        self.block_type = config.block_type
        self.layer_id = config.layer_id
        self.module_name = config.module_name
        self.rank = config.rank
        self.scale = config.scale

        # Infer dimensions from config: prefer explicit in_features/out_features
        if config.in_features > 0 and config.out_features > 0:
            in_f = config.in_features
            out_f = config.out_features
        elif config.hidden_size > 0:
            # Rough defaults — only used when actual dims are unavailable
            if "q_proj" in config.module_name or "k_proj" in config.module_name:
                in_f = out_f = config.hidden_size
            elif "v_proj" in config.module_name:
                in_f = out_f = config.hidden_size
            elif "o_proj" in config.module_name:
                in_f = out_f = config.hidden_size
            elif "gate_proj" in config.module_name or "up_proj" in config.module_name:
                in_f = config.hidden_size
                out_f = config.hidden_size * 4  # rough default for intermediate
            elif "down_proj" in config.module_name:
                in_f = config.hidden_size * 4  # rough default for intermediate
                out_f = config.hidden_size
            else:
                in_f = config.hidden_size
                out_f = config.hidden_size
        else:
            in_f = config.in_features
            out_f = config.out_features

        # Low-rank decomposition stored for efficient forward:
        #   ΔW^T = A @ B   (shape: in_features x out_features)
        #   ΔW  = B^T @ A^T  (shape: out_features x in_features)
        # Forward: x @ A @ B = (batch, in_f) @ (in_f, rank) @ (rank, out_f) = (batch, out_f)
        self.A = nn.Parameter(torch.empty(in_f, self.rank))    # (in_features, rank)
        self.B = nn.Parameter(torch.empty(self.rank, out_f))   # (rank, out_features)

        self.reset_parameters()

    def reset_parameters(self):
        """Initialize A with normal(0, σ²), B with zeros — standard LoRA init."""
        nn.init.kaiming_uniform_(self.A, a=5**0.5)
        nn.init.zeros_(self.B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Compute ΔW @ x = α · (B^T @ A^T) @ x = α · x @ A @ B."""
        if self.A.device != x.device:
            raise RuntimeError(
                f"Block {self.block_id}: A on {self.A.device} but x on {x.device}. "
                "Move block to model device before forward via BlockDeviceManager."
            )
        if self.A.dtype != x.dtype:
            raise RuntimeError(
                f"Block {self.block_id}: A dtype {self.A.dtype} but x dtype {x.dtype}. "
                "Move/cast block before forward via BlockDeviceManager or explicit block.to(...)."
            )
        return self.scale * ((x @ self.A) @ self.B)

    def get_delta_weight(self) -> torch.Tensor:
        """Materialize ΔW = α · B^T @ A^T as a full (out_features, in_features) matrix.

        ΔW^T = A @ B, so ΔW = (A @ B)^T = B^T @ A^T.
        """
        return self.scale * (self.B.T @ self.A.T)

    def save(self, path: str):
        """Save block parameters and config."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(
            {
                "config": self.config,
                "state_dict": self.state_dict(),
            },
            path,
        )

    @classmethod
    def load(cls, path: str, device: Optional[torch.device] = None) -> "ParameterBlock":
        """Load a saved parameter block."""
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        config = checkpoint["config"]
        if not isinstance(config, ParameterBlockConfig):
            config = ParameterBlockConfig(**config)
        block = cls(config)
        block.load_state_dict(checkpoint["state_dict"])
        if device is not None:
            block = block.to(device)
        return block

    def extra_repr(self) -> str:
        return (
            f"block_id={self.block_id}, type={self.block_type}, "
            f"layer={self.layer_id}/{self.module_name}, "
            f"rank={self.rank}, scale={self.scale}, "
            f"A={list(self.A.shape)}, B={list(self.B.shape)}"
        )


class BlockBank:
    """A collection of parameter blocks with lookup and selection utilities."""

    def __init__(self):
        self.blocks: dict[str, ParameterBlock] = {}

    def add_block(self, block: ParameterBlock):
        """Register a parameter block by its block_id."""
        self.blocks[block.block_id] = block

    def get_block(self, block_id: str) -> ParameterBlock:
        return self.blocks[block_id]

    def list_blocks(self) -> list[dict]:
        """Return metadata for all registered blocks."""
        return [
            {
                "block_id": b.block_id,
                "block_type": b.block_type,
                "layer_id": b.layer_id,
                "module_name": b.module_name,
                "rank": b.rank,
                "scale": b.scale,
            }
            for b in self.blocks.values()
        ]

    def get_blocks_by_type(self, block_type: str) -> list[ParameterBlock]:
        return [b for b in self.blocks.values() if b.block_type == block_type]

    def get_blocks_by_layer(self, layer_id: int) -> list[ParameterBlock]:
        return [b for b in self.blocks.values() if b.layer_id == layer_id]

    def save_all(self, directory: str):
        """Save all blocks to a directory, one file per block."""
        os.makedirs(directory, exist_ok=True)
        for block_id, block in self.blocks.items():
            path = os.path.join(directory, f"block_{block_id}.pt")
            block.save(path)

    @classmethod
    def load_all(cls, directory: str, device: Optional[torch.device] = None) -> "BlockBank":
        """Load all .pt files from a directory as blocks."""
        bank = cls()
        for fname in sorted(os.listdir(directory)):
            if fname.endswith(".pt"):
                path = os.path.join(directory, fname)
                block = ParameterBlock.load(path, device=device)
                bank.add_block(block)
        return bank

    def __len__(self):
        return len(self.blocks)

    def __iter__(self):
        return iter(self.blocks.values())
