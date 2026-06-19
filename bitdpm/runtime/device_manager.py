"""BlockDeviceManager: GPU-resident block cache for BitDPM.

Ensures active parameter blocks live on the same device as the backbone,
eliminating CPU→GPU transfers from the forward hot path.

Device assignment principle:
    CPU: router, metadata, block admission, execution plan, cache decision.
    GPU/MPS: backbone forward, active block forward, delta computation.
    SSD/RAM: cold block storage, inactive block cache.
"""

from __future__ import annotations

from typing import Optional

import torch

from bitdpm.params.parameter_block import ParameterBlock


class BlockDeviceManager:
    """Manages block placement across devices.

    Pre-loads blocks to the target compute device so forward passes
    do not trigger device transfers. Supports two modes:

    Mode 1: All-block GPU preload (simple, use during experiments)
        All admitted blocks are moved to GPU at init time.

    Mode 2: Active-only GPU cache (scalable for large block pools)
        Blocks are moved to GPU only when activated by router.
    """

    def __init__(
        self,
        target_device: torch.device,
        dtype: Optional[torch.dtype] = None,
        mode: str = "all_preload",
    ):
        self.target_device = target_device
        self.dtype = dtype
        self.mode = mode
        # GPU cache: block_id -> ParameterBlock on target device
        self.gpu_cache: dict[str, ParameterBlock] = {}

    def preload_all(self, block_bank: dict[str, ParameterBlock]):
        """Mode 1: Move ALL blocks to target device at init."""
        for block_id, block in block_bank.items():
            self._ensure_on_device(block, block_id)
        print(f"[BlockDeviceManager] Preloaded {len(block_bank)} blocks to {self.target_device}")

    def activate(self, block_ids: list[str],
                 block_bank: dict[str, ParameterBlock]) -> list[ParameterBlock]:
        """Mode 2: Ensure requested blocks are on target device, return them.

        Only moves blocks that aren"t already cached. Use this when
        the router activates a specific set of blocks.
        """
        active: list[ParameterBlock] = []
        for block_id in block_ids:
            if block_id not in block_bank:
                continue
            block = self._ensure_on_device(block_bank[block_id], block_id)
            active.append(block)
        return active

    def _ensure_on_device(self, block: ParameterBlock, block_id: str) -> ParameterBlock:
        """Move a block to the target device if not already there."""
        if block_id not in self.gpu_cache:
            block = block.to(device=self.target_device, dtype=self.dtype)
            self.gpu_cache[block_id] = block
        return self.gpu_cache[block_id]

    def get_active_blocks(self, block_ids: list[str]) -> dict[str, ParameterBlock]:
        """Get cached blocks by ID (must have been activated first)."""
        return {
            bid: self.gpu_cache[bid]
            for bid in block_ids if bid in self.gpu_cache
        }

    def clear(self):
        """Clear the GPU cache, freeing device memory."""
        self.gpu_cache.clear()
        if self.target_device.type != "cpu":
            torch.cuda.empty_cache() if self.target_device.type == "cuda" else None

    def __len__(self) -> int:
        return len(self.gpu_cache)

    def __contains__(self, block_id: str) -> bool:
        return block_id in self.gpu_cache
