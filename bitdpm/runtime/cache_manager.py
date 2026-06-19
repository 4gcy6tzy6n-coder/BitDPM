"""Storage cache manager for BitDPM.

Manages the lifecycle of parameter blocks across storage tiers:
- SSD / disk (cold storage)
- RAM (warm cache)
- GPU memory (hot execution)

Currently a stub for the initial prototype.
"""

from __future__ import annotations

import os
from typing import Optional

from bitdpm.params.parameter_block import BlockBank, ParameterBlock


class CacheManager:
    """Manages block storage across tiers.

    v0: simple load-from-disk.
    Future: LRU cache across SSD → RAM → GPU.
    """

    def __init__(self, cache_dir: str = ""):
        self.cache_dir = cache_dir
        self._ram_cache: dict[str, ParameterBlock] = {}

    def load_block(self, block_id: str, device: str = "cpu") -> Optional[ParameterBlock]:
        """Load a block from cache or disk."""
        if block_id in self._ram_cache:
            return self._ram_cache[block_id].to(device)

        if self.cache_dir:
            path = os.path.join(self.cache_dir, f"block_{block_id}.pt")
            if os.path.exists(path):
                block = ParameterBlock.load(path, device=torch.device(device))
                self._ram_cache[block_id] = block.cpu()
                return block

        return None

    def prefetch_blocks(self, block_ids: list[str]):
        """Load blocks into RAM cache ahead of use."""
        for bid in block_ids:
            if bid not in self._ram_cache:
                self.load_block(bid)

    def clear_ram(self):
        """Clear the RAM cache."""
        self._ram_cache.clear()
