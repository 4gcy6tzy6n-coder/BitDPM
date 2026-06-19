"""LoRA-like patching for injecting ParameterBlocks into backbone layers.

Provides utilities to:
- Identify target linear layers (o_proj, down_proj by default)
- Wrap a layer's forward with composed (W_main + Σ g·ΔW) computation
- Enable/disable blocks at runtime
"""

from __future__ import annotations

from typing import Callable, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from bitdpm.models.bitlinear import NF4Linear
from bitdpm.params.composer import Composer, ConnectionMode
from bitdpm.params.parameter_block import ParameterBlock


class PatchedLinear(nn.Module):
    """Wraps an nn.Linear to run composed forward: Wx + connection(ΔW x).

    Supports v16 connection function variants. The connection is determined
    by the Composer's connection_mode at runtime.

    Keeps the original linear as a submodule. When no blocks are active,
    falls through to the original linear for zero overhead.
    """

    def __init__(self, original_linear: nn.Linear, composer: Composer):
        super().__init__()
        self.original = original_linear
        self.composer = composer
        self.enabled = True

    def forward(self, x: torch.Tensor, hidden_states: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Composed forward with active parameter blocks.

        Args:
            x: Input tensor (batch, in_features).
            hidden_states: Optional intermediate hidden states for token-level
                           gating (v3 TokenGated mode).

        Returns:
            Composed output Wx + connection(ΔW x).
        """
        if not self.enabled or self.composer.num_blocks == 0:
            return self.original(x)

        def main_forward(x_t: torch.Tensor) -> torch.Tensor:
            return self.original(x_t)

        return self.composer.compute(x, main_forward, hidden_states=hidden_states)

    def extra_repr(self) -> str:
        return f"original={self.original}, connection={self.composer.connection_mode.value}"


def _get_target_modules(config: dict) -> list[str]:
    """Get list of target module names based on config.

    Default: ['o_proj', 'down_proj'] as recommended for first version.
    """
    return config.get("target_modules", ["o_proj", "down_proj"])


def patch_layer_with_blocks(
    layer: nn.Module,
    layer_id: int,
    target_modules: list[str],
    blocks_at_layer: dict[str, list[ParameterBlock]],
    connection_mode: ConnectionMode = ConnectionMode.HARD_ADD,
    norm_clip_ratio: float = 0.5,
) -> dict[str, PatchedLinear]:
    """Patch specific submodules of a transformer layer with PatchedLinear.

    Args:
        layer: The transformer layer (e.g., model.model.layers[i]).
        layer_id: The index of this layer.
        target_modules: Which module names to patch (e.g., ['o_proj', 'down_proj']).
        blocks_at_layer: Dict mapping module_name -> list of ParameterBlocks for that layer.

    Returns:
        Dict mapping module_name -> PatchedLinear for all patched modules.
    """
    patches: dict[str, PatchedLinear] = {}

    for module_name in target_modules:
        if module_name not in blocks_at_layer:
            continue
        if not hasattr(layer, "self_attn") and not hasattr(layer, "mlp"):
            continue

        # Find the target submodule
        target: Optional[nn.Module] = None
        if module_name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            if hasattr(layer, "self_attn") and hasattr(layer.self_attn, module_name):
                target = getattr(layer.self_attn, module_name)
        elif module_name in ("gate_proj", "up_proj", "down_proj"):
            if hasattr(layer, "mlp") and hasattr(layer.mlp, module_name):
                target = getattr(layer.mlp, module_name)

        if target is None or not (isinstance(target, nn.Linear) or isinstance(target, NF4Linear)):
            continue

        # Create composer with blocks for this module (v16 connection mode)
        blocks = blocks_at_layer[module_name]
        default_weights = [1.0] * len(blocks)
        composer = Composer(
            mode=connection_mode,
            blocks=blocks,
            default_weights=default_weights,
            norm_clip_ratio=norm_clip_ratio,
        )

        # Replace with PatchedLinear
        patched = PatchedLinear(target, composer)

        # Replace in-place
        if module_name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            setattr(layer.self_attn, module_name, patched)
        else:
            setattr(layer.mlp, module_name, patched)

        patches[module_name] = patched

    return patches


def unpatch_layer(
    layer: nn.Module,
    target_modules: list[str],
    patches: dict[str, PatchedLinear],
):
    """Restore original linear layers by removing PatchedLinear wrappers."""
    for module_name in target_modules:
        if module_name not in patches:
            continue
        patched = patches[module_name]
        if module_name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            setattr(layer.self_attn, module_name, patched.original)
        elif module_name in ("gate_proj", "up_proj", "down_proj"):
            setattr(layer.mlp, module_name, patched.original)


class BlockInjector:
    """Manages injection and removal of parameter blocks across model layers."""

    def __init__(self, backbone):
        self.backbone = backbone
        self.patches: dict[tuple[int, str], PatchedLinear] = {}  # (layer_id, module_name) -> PatchedLinear
        self.target_modules: list[str] = ["o_proj", "down_proj"]
        self._connection_mode: ConnectionMode = ConnectionMode.HARD_ADD
        self._norm_clip_ratio: float = 0.5

    def set_target_modules(self, modules: list[str]):
        self.target_modules = modules

    def set_connection(self, mode: ConnectionMode, ratio: float = 0.5):
        """Set the connection function for all future patches and existing ones."""
        self._connection_mode = mode
        self._norm_clip_ratio = ratio
        for patched in self.patches.values():
            patched.composer.set_connection(mode, ratio=ratio)

    def apply_plan(self, plan):
        """Accept an ExecutionPlan (CPU output) and configure all patches accordingly."""
        self.set_connection(plan.connection_mode, plan.norm_clip_ratio)
        self.set_active_blocks(plan.active_block_ids)

    def inject_block(
        self,
        block: ParameterBlock,
        layer_id: Optional[int] = None,
        module_name: Optional[str] = None,
    ):
        lid = layer_id if layer_id is not None else block.layer_id
        mname = module_name if module_name is not None else block.module_name

        key = (lid, mname)
        if key in self.patches:
            self.patches[key].composer.add_block(block)
            return

        try:
            layer = self.backbone.model.model.layers[lid]
        except AttributeError:
            layer = self.backbone.model.model.model.layers[lid]

        target_modules = [mname]
        blocks_at_layer = {mname: [block]}

        patches = patch_layer_with_blocks(
            layer, lid, target_modules, blocks_at_layer,
            connection_mode=self._connection_mode,
            norm_clip_ratio=self._norm_clip_ratio,
        )
        if mname in patches:
            self.patches[key] = patches[mname]

    def inject_blocks(self, blocks: list[ParameterBlock]):
        groups: dict[tuple[int, str], list[ParameterBlock]] = {}
        for block in blocks:
            key = (block.layer_id, block.module_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(block)

        for (lid, mname), block_group in groups.items():
            try:
                layer = self.backbone.model.model.layers[lid]
            except AttributeError:
                layer = self.backbone.model.model.model.layers[lid]

            target = [mname]
            blocks_at_layer = {mname: block_group}

            patches = patch_layer_with_blocks(
                layer, lid, target, blocks_at_layer,
                connection_mode=self._connection_mode,
                norm_clip_ratio=self._norm_clip_ratio,
            )
            patch_key = (lid, mname)
            if mname in patches:
                self.patches[patch_key] = patches[mname]

    def remove_all_patches(self):
        by_layer: dict[int, list[tuple[int, str]]] = {}
        for lid, mname in self.patches:
            by_layer.setdefault(lid, []).append((lid, mname))

        for lid, keys in by_layer.items():
            try:
                layer = self.backbone.model.model.layers[lid]
            except AttributeError:
                layer = self.backbone.model.model.model.layers[lid]

            target_modules = [mname for _, mname in keys]
            patches = {mname: self.patches[(lid, mname)] for _, mname in keys}
            unpatch_layer(layer, target_modules, patches)

        self.patches.clear()

    def set_active_blocks(self, block_ids: Optional[list[str]] = None):
        for patched in self.patches.values():
            patched.composer.set_active_blocks(block_ids)

    @property
    def num_patches(self) -> int:
        return len(self.patches)
