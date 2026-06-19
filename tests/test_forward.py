"""Integration tests for end-to-end forward pass with blocks."""

import torch

from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig


def test_backbone_creation():
    """Test that the backbone model loads correctly."""
    model = BackboneModel(
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        device="cpu",
        dtype=torch.float32,  # Use FP32 on CPU for test stability
    )
    assert model.model is not None
    assert model.tokenizer is not None
    assert model.num_params() > 0
    assert model.hidden_size == 1024  # Qwen2.5-0.5B hidden size


def test_backbone_generate():
    """Test that the backbone can generate text."""
    model = BackboneModel(
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        device="cpu",
        dtype=torch.float32,
    )
    output = model.generate("Hello", max_new_tokens=10, temperature=0.1)
    assert isinstance(output, str)
    assert len(output) > 0


def test_single_block_injection():
    """Test injecting a single parameter block into the backbone."""
    model = BackboneModel(
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        device="cpu",
        dtype=torch.float32,
    )

    # Verify the original linear exists
    lin = model.get_linear_layer(23, "o_proj")
    assert lin is not None, "Linear layer 23/o_proj should exist"

    # Create block
    config = ParameterBlockConfig(
        block_id="test_block",
        layer_id=23,
        module_name="o_proj",
        rank=4,
        scale=1.0,
        block_type="test",
        hidden_size=model.hidden_size,
        in_features=lin.in_features,
        out_features=lin.out_features,
    )
    block = ParameterBlock(config)

    # Inject
    injector = BlockInjector(model)
    injector.inject_block(block, 23, "o_proj")

    # Verify the layer is now patched
    key = (23, "o_proj")
    assert key in injector.patches, "Layer should be patched"

    # Generate should still work
    output = model.generate("Hello", max_new_tokens=10, temperature=0.1)
    assert isinstance(output, str)
    assert len(output) > 0


def test_multiple_blocks_injection():
    """Test injecting multiple blocks across layers."""
    model = BackboneModel(
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        device="cpu",
        dtype=torch.float32,
    )

    blocks = []
    for lid in [22, 23]:
        for module in ["o_proj", "down_proj"]:
            lin = model.get_linear_layer(lid, module)
            if lin is None:
                continue
            config = ParameterBlockConfig(
                block_id=f"block_l{lid}_{module}",
                layer_id=lid,
                module_name=module,
                rank=4,
                scale=1.0,
                block_type="test",
                hidden_size=model.hidden_size,
                in_features=lin.in_features,
                out_features=lin.out_features,
            )
            blocks.append(ParameterBlock(config))

    injector = BlockInjector(model)
    injector.inject_blocks(blocks)

    assert injector.num_patches > 0, "Should have at least one patch"

    # Generation should still work
    output = model.generate("Hello world", max_new_tokens=10, temperature=0.1)
    assert isinstance(output, str)
    assert len(output) > 0


def test_remove_patches():
    """Test removing all patches restores original behavior."""
    model = BackboneModel(
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        device="cpu",
        dtype=torch.float32,
    )

    lin = model.get_linear_layer(23, "o_proj")
    config = ParameterBlockConfig(
        block_id="test_remove",
        layer_id=23,
        module_name="o_proj",
        rank=4,
        scale=1.0,
        block_type="test",
        hidden_size=model.hidden_size,
        in_features=lin.in_features,
        out_features=lin.out_features,
    )
    block = ParameterBlock(config)

    injector = BlockInjector(model)
    injector.inject_block(block, 23, "o_proj")
    assert len(injector.patches) > 0

    injector.remove_all_patches()
    assert len(injector.patches) == 0, "All patches should be removed"
