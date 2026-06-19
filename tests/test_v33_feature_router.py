"""Lightweight tests for v33 feature-rule router utilities.

Run directly without pytest:

    python tests/test_v33_feature_router.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.mine_v33_safety_router import mine_rules_for_run, prompt_features
from scripts.run_v32_router_validation import (
    baseline_cache_key,
    feature_expr_active,
    load_baseline_cache,
    router_active,
    run_key,
    write_baseline_cache,
)


class FeatureRuleRouterTest(unittest.TestCase):
    def test_prompt_features_detect_math(self) -> None:
        feats = prompt_features("math", "What is 25% of 200?")
        self.assertTrue(feats["cat_math"])
        self.assertTrue(feats["has_digit"])
        self.assertTrue(feats["has_percent"])
        self.assertTrue(feats["short_answer_math"])
        self.assertFalse(feats["is_chinese_text"])

    def test_prompt_features_detect_risk(self) -> None:
        feats = prompt_features("commonsense", "What is the speed of light in vacuum?")
        self.assertTrue(feats["cat_commonsense"])
        self.assertTrue(feats["has_speed"])
        self.assertTrue(feats["has_constant_risk"])

    def test_feature_expr_supports_conjunction(self) -> None:
        self.assertTrue(feature_expr_active("cat_math AND has_percent", "math", "What is 25% of 200?"))
        self.assertFalse(feature_expr_active("cat_math AND has_sqrt", "math", "What is 25% of 200?"))

    def test_feature_expr_supports_negation(self) -> None:
        self.assertTrue(feature_expr_active("cat_math AND !is_chinese_text", "math", "What is 2^10?"))
        self.assertFalse(feature_expr_active("cat_math AND !has_power", "math", "What is 2^10?"))

    def test_feature_rule_requires_allow(self) -> None:
        self.assertFalse(router_active("feature_rule", "math", "What is 2^10?", allow_features=[], deny_features=[]))

    def test_feature_rule_allow(self) -> None:
        self.assertTrue(
            router_active(
                "feature_rule",
                "math",
                "What is 2^10?",
                allow_features=["cat_math"],
                deny_features=[],
            )
        )

    def test_feature_rule_deny_takes_priority(self) -> None:
        self.assertFalse(
            router_active(
                "feature_rule",
                "math",
                "What is 2^10?",
                allow_features=["cat_math"],
                deny_features=["has_power"],
            )
        )

    def test_miner_finds_zero_break_allow_rule(self) -> None:
        run = {
            "metadata": {
                "benchmark_set": "core",
                "router": "unrestricted",
                "scale": 0.85,
                "block": {"block_id": "test_block"},
                "block_sha256": "abc123",
            },
            "summary": {"baseline": 0.8, "routed": 0.8, "fixes": 2, "breaks": 1, "net": 1},
            "samples": [
                {"category": "math", "prompt": "What is 25% of 200?", "delta": 1.0},
                {"category": "math", "prompt": "What is 2^10?", "delta": 1.0},
                {"category": "chinese", "prompt": "请用中文写一句问候语。", "delta": -1.0},
            ],
        }
        mined = mine_rules_for_run(run, include_conjunctions=True)
        rules = {row["feature"]: row for row in mined["zero_break_allow_rules"]}
        self.assertIn("cat_math", rules)
        self.assertEqual(rules["cat_math"]["fixes"], 2)
        self.assertEqual(rules["cat_math"]["breaks"], 0)

    def test_run_key_distinguishes_router_and_scale(self) -> None:
        base = {
            "model": "m",
            "benchmark_set": "core",
            "block_path": "b.pt",
            "block_sha256": "abc",
            "router": "allow_math",
            "scale": 0.85,
            "deterministic": True,
            "temperature": 0.1,
            "max_tokens": 64,
            "max_prompts_per_category": 0,
            "allow_features": [],
            "deny_features": [],
        }
        same = dict(base)
        changed_router = dict(base, router="blacklist_only")
        changed_scale = dict(base, scale=1.0)
        self.assertEqual(run_key(base), run_key(same))
        self.assertNotEqual(run_key(base), run_key(changed_router))
        self.assertNotEqual(run_key(base), run_key(changed_scale))

    def test_baseline_cache_roundtrip(self) -> None:
        key = baseline_cache_key("model", "core", True, 0.1, 64, 0, "What is 2^10?")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "baseline.json"
            write_baseline_cache(path, {key: ("1024", 1.0)})
            loaded = load_baseline_cache(path)
        self.assertEqual(loaded[key], ("1024", 1.0))

    def test_baseline_cache_key_distinguishes_sampling(self) -> None:
        deterministic = baseline_cache_key("model", "core", True, 0.1, 64, 0, "p")
        sampling = baseline_cache_key("model", "core", False, 0.1, 64, 0, "p")
        self.assertNotEqual(deterministic, sampling)


if __name__ == "__main__":
    unittest.main()
