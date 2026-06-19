"""Simple keyword-based router for block selection (Router v0).

Maps input prompts to active parameter blocks based on keyword matching.
Supports confidence/entropy-based routing (Router v1 interface) for future use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RouterOutput:
    """Output from the router specifying active blocks and their weights."""
    active_block_ids: list[str]
    weights: list[float] = field(default_factory=list)
    confidence: float = 1.0
    routing_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class SimpleRouter:
    """Router v0: keyword-based task-to-block mapping.

    Each block type is associated with a set of keywords. When a prompt
    matches a keyword set, the corresponding block(s) are activated.
    """

    def __init__(self, default_block_id: str = "general"):
        self.default_block_id = default_block_id
        # Map: block_id -> list of keywords (lowercase)
        self.keyword_map: dict[str, list[str]] = {}
        # Map: block_id -> priority (higher = preferred when multiple match)
        self.priorities: dict[str, int] = {}

    def register_block(
        self, block_id: str, keywords: list[str], priority: int = 0
    ):
        """Register a block with its trigger keywords."""
        self.keyword_map[block_id] = [kw.lower() for kw in keywords]
        self.priorities[block_id] = priority

    def route(self, prompt: str, available_blocks: Optional[list[str]] = None) -> RouterOutput:
        """Determine which blocks to activate based on prompt content.

        Args:
            prompt: The input text to route.
            available_blocks: List of block_ids that are currently available.
                              If None, all registered blocks are considered.

        Returns:
            RouterOutput with active block IDs and uniform weights.
        """
        import time as _time
        _start = _time.time()
        prompt_lower = prompt.lower()
        available = set(available_blocks or list(self.keyword_map.keys()))
        matched: list[tuple[str, int]] = []

        for block_id, keywords in self.keyword_map.items():
            if block_id not in available:
                continue
            for kw in keywords:
                if kw in prompt_lower:
                    matched.append((block_id, self.priorities.get(block_id, 0)))
                    break  # one keyword match is enough per block

        if not matched:
            # Fall back to default block if available
            if self.default_block_id in available:
                matched = [(self.default_block_id, 0)]

        # Sort by priority (descending) for consistent ordering
        matched.sort(key=lambda x: -x[1])

        active_ids = [bid for bid, _ in matched]
        weights = [1.0 / len(active_ids)] * len(active_ids) if active_ids else []
        confidence = min(1.0, len(active_ids) / max(len(self.keyword_map), 1))

        _elapsed = (_time.time() - _start) * 1000
        return RouterOutput(
            active_block_ids=active_ids,
            weights=weights,
            confidence=confidence,
            routing_time_ms=_elapsed,
            metadata={"matched_keywords": True},
        )

    def list_registered_blocks(self) -> dict[str, list[str]]:
        """Return all registered block IDs and their keywords."""
        return dict(self.keyword_map)

    def build_default(self, available_block_types: list[str]) -> "SimpleRouter":
        """Build a default router with common task keywords.

        Block types expected: 'general', 'math', 'code', 'chinese', 'factual'
        """
        block_keywords = {
            "general": [],
            "math": [
                "计算", "数学", "证明", "equation", "formula", "calculate",
                "solve", "derivative", "integral", "algebra", "geometry",
            ],
            "code": [
                "代码", "编程", "python", "json", "function", "algorithm",
                "bug", "debug", "compile", "api", "implementation",
            ],
            "chinese": [
                "中文", "汉语", "普通话", "中国", "中文问答",
            ],
            "factual": [
                "fact", "knowledge", "history", "science", "definition",
                "what is", "explain", "describe",
            ],
        }

        # Map block_id -> block_type (in a real setup, you'd pass full metadata)
        for block_type in available_block_types:
            keywords = block_keywords.get(block_type, [])
            priority = 1 if block_type == "general" else 2
            self.register_block(block_type, keywords, priority=priority)

        return self


class EntropyRouter:
    """Router v1: entropy/confidence-aware routing.

    Not yet implemented — placeholder for future use.
    Uses model output entropy to decide whether to activate additional blocks.
    """

    def __init__(
        self,
        base_router: SimpleRouter,
        entropy_threshold: float = 0.5,
        max_blocks: int = 3,
    ):
        self.base_router = base_router
        self.entropy_threshold = entropy_threshold
        self.max_blocks = max_blocks

    def route(
        self,
        prompt: str,
        entropy: Optional[float] = None,
        available_blocks: Optional[list[str]] = None,
    ) -> RouterOutput:
        """Route based on both keywords and model confidence.

        If entropy is high (low confidence), activates more blocks.
        If entropy is low (high confidence), uses fewer or just default.
        """
        base_output = self.base_router.route(prompt, available_blocks)

        if entropy is None:
            return base_output

        if entropy >= self.entropy_threshold:
            # Low confidence — activate all available blocks
            all_avail = available_blocks or list(
                self.base_router.keyword_map.keys()
            )
            return RouterOutput(
                active_block_ids=all_avail[: self.max_blocks],
                weights=[1.0 / min(len(all_avail), self.max_blocks)] * min(len(all_avail), self.max_blocks),
                confidence=max(0.0, 1.0 - entropy),
                metadata={"entropy_triggered": True, "entropy": entropy},
            )

        return base_output
