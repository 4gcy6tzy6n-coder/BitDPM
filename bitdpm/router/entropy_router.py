"""Entropy-based router for BitDPM (Router v1).

Uses the backbone model's output entropy/confidence to decide:
- Which blocks to activate
- How many blocks to activate
- Whether to use blocks at all

Core logic:
    entropy < low_threshold  → very confident → 0-1 blocks
    entropy > high_threshold → uncertain → top-k blocks
    in between → default routing
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import torch
import torch.nn.functional as F


@dataclass
class RouterOutput:
    """Output from the router specifying active blocks and their weights."""
    active_block_ids: list[str]
    weights: list[float] = field(default_factory=list)
    confidence: float = 1.0
    routing_time_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class ComputeEntropy:
    """Utility to compute output entropy from model logits."""

    @staticmethod
    def from_logits(logits: torch.Tensor) -> float:
        """Compute normalized entropy from logits.

        Args:
            logits: (batch, vocab) tensor.

        Returns:
            Normalized entropy in [0, 1].
            0 = fully confident (one token dominates).
            1 = uniform distribution (no confidence).
        """
        probs = F.softmax(logits.float(), dim=-1)
        entropy = -torch.sum(probs * torch.log(probs.clamp(min=1e-10)), dim=-1)
        max_entropy = torch.log(torch.tensor(logits.shape[-1], dtype=torch.float32))
        normalized = (entropy / max_entropy).mean().item()
        if not (0.0 <= normalized <= 1.0) or normalized != normalized:  # handle NaN
            return 0.5  # default medium entropy
        return normalized

    @staticmethod
    def from_model_and_prompt(
        model,
        tokenizer,
        prompt: str,
        device: str = "cpu",
    ) -> float:
        """Compute entropy from a single forward pass on the prompt.

        Encodes the prompt, runs one forward step through the model,
        extracts the last token's logits, and computes entropy.
        """
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(input_ids=inputs.input_ids)
            logits = outputs.logits[:, -1, :].float()  # last token logits, ensure float32
        return ComputeEntropy.from_logits(logits)

    @staticmethod
    def top1_margin(logits: torch.Tensor) -> float:
        """Compute margin between top-1 and top-2 probability.

        Higher margin = more confident.
        """
        probs = F.softmax(logits.float(), dim=-1)
        top_probs, _ = probs.topk(2, dim=-1)
        margin = (top_probs[..., 0] - top_probs[..., 1]).mean().item()
        return margin


class EntropyRouter:
    """Router v1: entropy/confidence-based block selection.

    Combines keyword-based task detection with model confidence measurement.
    When the model is uncertain about its output, more parameter blocks
    are activated to provide additional capacity.

    Modes:
        - entropy_only: Use only entropy for routing.
        - keyword_only: Fall back to keyword-based routing.
        - hybrid: Use keywords first, then adjust with entropy.
    """

    def __init__(
        self,
        block_type_map: dict[str, list[str]],  # block_type -> [block_ids]
        default_block_type: str = "general",
        entropy_low: float = 0.3,
        entropy_high: float = 0.6,
        min_blocks: int = 0,
        max_blocks: int = 4,
        mode: str = "hybrid",
    ):
        """
        Args:
            block_type_map: Mapping from block_type to list of block_ids.
            default_block_type: Type used when no specific match.
            entropy_low: Below this, very confident → use min_blocks.
            entropy_high: Above this, uncertain → use max_blocks.
            min_blocks: Minimum number of blocks to activate.
            max_blocks: Maximum number of blocks to activate.
            mode: "hybrid", "entropy_only", or "keyword_only".
        """
        self.block_type_map = block_type_map
        self.default_block_type = default_block_type
        self.entropy_low = entropy_low
        self.entropy_high = entropy_high
        self.min_blocks = min_blocks
        self.max_blocks = max_blocks
        self.mode = mode

        # Keyword mapping for hybrid mode
        self.keywords: dict[str, list[str]] = {
            "math": [
                "计算", "数学", "equation", "formula", "calculate",
                "solve", "derivative", "integral", "algebra",
            ],
            "code": [
                "代码", "编程", "python", "json", "function", "algorithm",
                "bug", "compile", "api", "implementation",
            ],
            "chinese": [
                "中文", "汉语", "普通话", "中国",
            ],
        }

    def _keyword_match(self, prompt: str) -> str | None:
        """Match prompt to a block type via keywords."""
        prompt_lower = prompt.lower()
        matched_types = []
        for btype, kws in self.keywords.items():
            for kw in kws:
                if kw in prompt_lower:
                    matched_types.append(btype)
                    break
        return matched_types[0] if matched_types else None

    def _compute_block_count(self, entropy: float) -> int:
        """Map entropy value to number of blocks to activate.

        Linear interpolation between min_blocks and max_blocks.
        """
        if entropy <= self.entropy_low:
            return self.min_blocks
        if entropy >= self.entropy_high:
            return self.max_blocks
        ratio = (entropy - self.entropy_low) / (self.entropy_high - self.entropy_low)
        return int(self.min_blocks + ratio * (self.max_blocks - self.min_blocks))

    def route(
        self,
        prompt: str,
        entropy: Optional[float] = None,
        available_blocks: Optional[list[str]] = None,
    ) -> RouterOutput:
        """Route based on prompt content and/or model entropy.

        Args:
            prompt: Input text.
            entropy: Model output entropy (0-1). If None, uses keyword-only.
            available_blocks: List of block_ids that are available.

        Returns:
            RouterOutput with selected blocks and confidence.
        """
        start_time = time.time()

        # Build flat available set — if None, all blocks are available
        all_block_ids = [
            bid for bids in self.block_type_map.values() for bid in bids
        ]
        if available_blocks is not None:
            avail = set(available_blocks)
        else:
            avail = set(all_block_ids)

        # Step 1: Determine target block type from keywords (if hybrid)
        matched_type = None
        if self.mode in ("hybrid", "keyword_only"):
            matched_type = self._keyword_match(prompt)

        # Step 2: Adjust with entropy
        num_blocks = None
        confidence = 1.0
        if entropy is not None and self.mode in ("hybrid", "entropy_only"):
            num_blocks = self._compute_block_count(entropy)
            confidence = max(0.0, 1.0 - entropy)
        else:
            # Default: activate 1-2 blocks
            num_blocks = 2

        # Step 3: Select blocks
        selected: list[str] = []

        if matched_type and matched_type in self.block_type_map:
            # Prefer blocks of matched type
            candidates = self.block_type_map[matched_type]
            filtered = [b for b in candidates if b in avail]
            selected.extend(filtered[:num_blocks])

        # If more blocks needed, add from default type
        remaining = num_blocks - len(selected)
        if remaining > 0:
            default_candidates = self.block_type_map.get(self.default_block_type, [])
            filtered = [b for b in default_candidates if b in avail and b not in selected]
            selected.extend(filtered[:remaining])

        # If still empty, fall back to any available
        if not selected:
            selected = list(avail)[:1]

        # Uniform weights
        weights = [1.0 / len(selected)] * len(selected) if selected else []

        routing_time = (time.time() - start_time) * 1000  # ms

        return RouterOutput(
            active_block_ids=selected,
            weights=weights,
            confidence=confidence,
            routing_time_ms=routing_time,
            metadata={
                "matched_type": matched_type,
                "entropy": entropy,
                "num_blocks_computed": num_blocks,
                "mode": self.mode,
            },
        )

    def route_with_model(
        self,
        prompt: str,
        model,
        tokenizer,
        available_blocks: Optional[list[str]] = None,
        device: str = "cpu",
    ) -> RouterOutput:
        """Route using actual model forward pass for entropy computation.

        Does one forward step on the prompt, computes entropy,
        then routes based on confidence.
        """
        entropy = ComputeEntropy.from_model_and_prompt(
            model, tokenizer, prompt, device=device
        )
        return self.route(
            prompt, entropy=entropy, available_blocks=available_blocks
        )
