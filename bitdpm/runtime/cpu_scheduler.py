"""CPU-side block scheduler for BitDPM.

Determines which blocks to load, activate, or prefetch based on:
- Router output (which blocks are needed)
- Device state (current GPU memory, CPU memory)
- Storage state (which blocks are on SSD vs in RAM)

Currently a stub for the initial prototype.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionPlan:
    """Plan specifying which blocks go where."""
    gpu_blocks: list[str] = field(default_factory=list)
    cpu_blocks: list[str] = field(default_factory=list)
    prefetch_blocks: list[str] = field(default_factory=list)
    skipped_blocks: list[str] = field(default_factory=list)


class CpuScheduler:
    """CPU-side scheduler for block management.

    In v0, this is a pass-through: all blocks are on GPU.
    Future versions will manage SSD → RAM → GPU transfer.
    """

    def __init__(self, max_gpu_blocks: int = 4, max_ram_blocks: int = 20):
        self.max_gpu_blocks = max_gpu_blocks
        self.max_ram_blocks = max_ram_blocks

    def plan(
        self,
        router_output,
        device_state: Optional[dict] = None,
        available_blocks: Optional[list[str]] = None,
    ) -> ExecutionPlan:
        """Create an execution plan from router output."""
        active = router_output.active_block_ids if router_output else []
        return ExecutionPlan(
            gpu_blocks=active[: self.max_gpu_blocks],
            cpu_blocks=[],
            prefetch_blocks=[],
            skipped_blocks=[b for b in (available_blocks or []) if b not in active],
        )
