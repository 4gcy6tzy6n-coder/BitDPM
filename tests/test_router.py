"""Tests for keyword-based router and entropy router."""

import torch

from bitdpm.router.entropy_router import ComputeEntropy, EntropyRouter
from bitdpm.router.simple_router import SimpleRouter


# --- SimpleRouter tests (existing) ---


def test_router_returns_default():
    """Router should return default block when no keywords match."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [], priority=0)

    output = router.route("Hello world")
    assert output.active_block_ids == ["general"]


def test_router_matches_keywords():
    """Router should match math keywords."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [])
    router.register_block("math", ["calculate", "math", "solver"])

    output = router.route("Please calculate 15 + 27")
    assert "math" in output.active_block_ids, "Router should match 'calculate' keyword"


def test_router_code_keywords():
    """Router should match code keywords."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [])
    router.register_block("code", ["python", "code", "function", "json"])

    output = router.route("Write a Python function to sort a list")
    assert "code" in output.active_block_ids, "Router should match 'python' and 'function' keywords"


def test_router_chinese_keywords():
    """Router should match Chinese keywords."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [])
    router.register_block("chinese", ["中文", "汉语"])

    output = router.route("请用中文回答")
    assert "chinese" in output.active_block_ids, "Router should match Chinese keyword"


def test_router_priority():
    """Higher priority blocks should appear first in active list."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("low", ["test"], priority=1)
    router.register_block("high", ["test"], priority=10)

    output = router.route("this is a test keyword")
    assert output.active_block_ids[0] == "high", "Higher priority should come first"


def test_router_build_default():
    """Build default router with standard categories."""
    router = SimpleRouter()
    router.build_default(["general", "math", "code", "chinese"])

    registered = router.list_registered_blocks()
    assert "math" in registered
    assert "code" in registered
    assert "chinese" in registered


def test_router_available_blocks_filter():
    """Router should only use blocks in the available list."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [])
    router.register_block("math", ["calculate"])
    router.register_block("code", ["python"])

    # Only general and math are available
    output = router.route("python code", available_blocks=["general", "math"])
    assert "code" not in output.active_block_ids, "code block should not be in available list"


def test_router_no_match_fallback():
    """When no block matches and none available, fallback to default if available."""
    router = SimpleRouter(default_block_id="general")
    router.register_block("general", [])
    router.register_block("math", ["equation"])

    # No keyword matches
    output = router.route("Hello world")
    assert "general" in output.active_block_ids


# --- EntropyRouter tests ---

def test_compute_entropy_uniform():
    """Uniform logits should give entropy close to 1.0."""
    logits = torch.ones(1, 100)  # uniform
    entropy = ComputeEntropy.from_logits(logits)
    assert entropy > 0.8, f"Uniform should have high entropy, got {entropy}"


def test_compute_entropy_confident():
    """One dominant logit should give entropy close to 0."""
    logits = torch.zeros(1, 100)
    logits[0, 0] = 100.0  # one token dominates
    entropy = ComputeEntropy.from_logits(logits)
    assert entropy < 0.3, f"Confident should have low entropy, got {entropy}"


def test_compute_entropy_mid():
    """Mixed logits should give medium entropy."""
    logits = torch.zeros(1, 100)
    logits[0, :10] = 5.0  # 10 tokens somewhat likely
    entropy = ComputeEntropy.from_logits(logits)
    assert 0.2 < entropy < 0.8, f"Mid confidence should give medium entropy, got {entropy}"


def test_top1_margin_confident():
    """High margin should indicate confidence."""
    logits = torch.zeros(1, 100)
    logits[0, 0] = 50.0
    logits[0, 1] = 1.0
    margin = ComputeEntropy.top1_margin(logits)
    assert margin > 0.5, f"Confident should have large margin, got {margin}"


def test_entropy_router_high_entropy_more_blocks():
    """High entropy should activate more blocks (up to type_map capacity)."""
    type_map = {
        "general": ["g1", "g2", "g3"],
        "math": ["m1"],
    }
    router = EntropyRouter(
        block_type_map=type_map,
        entropy_low=0.3,
        entropy_high=0.6,
        min_blocks=1,
        max_blocks=3,
        mode="entropy_only",
    )

    # High entropy → more blocks
    output = router.route("test", entropy=0.9)
    assert len(output.active_block_ids) >= 2, \
        f"High entropy should give >=2 blocks, got {len(output.active_block_ids)}"
    assert output.confidence < 0.5


def test_entropy_router_low_entropy_few_blocks():
    """Low entropy should activate fewer blocks."""
    type_map = {
        "general": ["general_l23_o_proj"],
        "math": ["math_l23_o_proj"],
    }
    router = EntropyRouter(
        block_type_map=type_map,
        entropy_low=0.3,
        entropy_high=0.6,
        min_blocks=0,
        max_blocks=3,
        mode="entropy_only",
    )

    # Low entropy → few or no blocks
    output = router.route("test", entropy=0.05)
    assert len(output.active_block_ids) <= 1, \
        f"Low entropy should give few blocks, got {len(output.active_block_ids)}"
    assert output.confidence > 0.8


def test_entropy_router_hybrid_keyword_match():
    """Hybrid mode should match keywords when entropy is moderate."""
    type_map = {
        "general": ["general_l23_o_proj"],
        "math": ["math_l23_o_proj", "math_l23_down_proj"],
    }
    router = EntropyRouter(
        block_type_map=type_map,
        entropy_low=0.3,
        entropy_high=0.6,
        min_blocks=1,
        max_blocks=3,
        mode="hybrid",
    )

    # Math keyword in prompt + moderate entropy → math blocks
    output = router.route("calculate 15 + 27", entropy=0.4)
    matched = output.metadata.get("matched_type")
    assert matched == "math", f"Hybrid should match 'calculate' to math, got {matched}"


def test_entropy_router_routing_time():
    """Router should record routing time."""
    type_map = {"general": ["general_block"]}
    router = EntropyRouter(type_map)
    output = router.route("test", entropy=0.5)
    assert output.routing_time_ms >= 0

