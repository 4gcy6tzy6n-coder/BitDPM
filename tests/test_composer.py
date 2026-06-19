"""Tests for parameter block and composer."""

import torch

from bitdpm.params.composer import Composer, CompositionMode
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig


def make_test_block(block_id: str, in_features: int = 64, out_features: int = 64, rank: int = 4) -> ParameterBlock:
    config = ParameterBlockConfig(
        block_id=block_id,
        layer_id=0,
        module_name="o_proj",
        rank=rank,
        scale=1.0,
        block_type="test",
        hidden_size=64,
        in_features=in_features,
        out_features=out_features,
    )
    return ParameterBlock(config)


def test_parameter_block_shape():
    """Test that ParameterBlock produces correct output shape."""
    block = make_test_block("test_block", in_features=64, out_features=128)
    x = torch.randn(2, 64)
    out = block(x)
    assert out.shape == (2, 128), f"Expected (2, 128), got {out.shape}"


def test_parameter_block_dtype_mismatch_fails_fast():
    """Forward should not hide dtype movement in the hot path."""
    block = make_test_block("dtype_guard").to(dtype=torch.float32)
    x = torch.randn(2, 64, dtype=torch.float16)
    try:
        block(x)
    except RuntimeError as exc:
        assert "dtype" in str(exc)
    else:
        raise AssertionError("Expected dtype mismatch to raise")


def test_parameter_block_zero_init():
    """Test B is zero-initialized, so ΔW starts as zero."""
    block = make_test_block("zero_test")
    z = torch.zeros(block.A.shape[1])
    delta = block.A @ z  # small test
    # With B=0, forward should return 0
    x = torch.randn(1, block.A.shape[1])
    out = block(x)
    assert torch.allclose(out, torch.zeros_like(out), atol=1e-6), "Block output should be zero after init"


def test_composer_single_block():
    """Test composer with a single block."""
    block = make_test_block("block1")
    composer = Composer(mode=CompositionMode.SINGLE_BLOCK, blocks=[block])

    x = torch.randn(2, 64)

    # Mock main forward
    def main_fn(x_t):
        return x_t * 2

    out = composer.compute(x, main_fn)
    # Main: 2x, block: 0 (zero init), so out = 2x
    assert torch.allclose(out, x * 2, atol=1e-5), "Composer should output main forward with zero block"


def test_composer_static_sum():
    """Test composer with multiple blocks."""
    blocks = [make_test_block(f"block{i}") for i in range(3)]
    composer = Composer(mode=CompositionMode.STATIC_SUM, blocks=blocks)

    x = torch.randn(2, 64)

    def main_fn(x_t):
        return x_t

    out = composer.compute(x, main_fn)
    # Main: x, all blocks zero, so out = x
    assert torch.allclose(out, x, atol=1e-5), "Static sum with zero blocks should match main"


def test_composer_with_subset_blocks():
    """Test composer with only a subset of blocks active."""
    blocks = [make_test_block(f"block{i}") for i in range(5)]
    composer = Composer(blocks=blocks)

    x = torch.randn(2, 64)

    def main_fn(x_t):
        return x_t

    # Only activate 2 blocks
    active = ["block0", "block3"]
    out = composer.compute(x, main_fn, active_block_ids=active)
    assert torch.allclose(out, x, atol=1e-5), "Zero-block subset should match main"


def test_composer_weighted():
    """Test composer with non-uniform weights."""
    blocks = [make_test_block("wblock")]
    composer = Composer(blocks=blocks)

    x = torch.randn(2, 64)

    def main_fn(x_t):
        return x_t

    # Weight 0 should skip the block entirely
    out = composer.compute(x, main_fn, weights=[0.0])
    assert torch.allclose(out, x, atol=1e-5), "Zero weight should skip block"


def test_parameter_block_save_load():
    """Test saving and loading a parameter block."""
    import tempfile

    block = make_test_block("save_test")
    x = torch.randn(1, 64)
    original_out = block(x)

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
        block.save(path)

        loaded = ParameterBlock.load(path)
        loaded_out = loaded(x)

        assert torch.allclose(original_out, loaded_out, atol=1e-6), \
            "Loaded block should produce same output"
