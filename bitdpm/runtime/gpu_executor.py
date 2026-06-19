"""GPU executor for BitDPM.

Handles the actual model forward pass with composed blocks on GPU.
Currently a stub — in v0, the backbone runs directly.
"""

from __future__ import annotations

from typing import Optional

import torch


class GpuExecutor:
    """Manages GPU execution of the backbone + active blocks.

    In v0, this is a thin wrapper. Future versions will handle:
    - Block loading/unloading to GPU
    - Mixed-precision execution
    - KV cache management
    """

    def __init__(self, device: str = "cuda"):
        self.device = device
        self.is_available = torch.cuda.is_available() if "cuda" in device else False

    def prepare_blocks(self, block_ids: list[str], block_bank) -> list:
        """Move selected blocks to GPU."""
        blocks = []
        for bid in block_ids:
            block = block_bank.get_block(bid)
            blocks.append(block.to(self.device))
        return blocks

    def cleanup(self):
        """Clear GPU memory cache."""
        if self.is_available:
            torch.cuda.empty_cache()
