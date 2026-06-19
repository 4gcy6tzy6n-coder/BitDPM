"""Memory usage measurement utilities.

Provides peak memory tracking for both CPU RAM and GPU VRAM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import torch


@dataclass
class MemoryMetrics:
    """Memory usage measurements."""
    model_params_mb: float = 0.0
    model_buffers_mb: float = 0.0
    total_model_mb: float = 0.0
    peak_reserved_mb: float = 0.0
    peak_allocated_mb: float = 0.0
    ram_usage_mb: float = 0.0
    device_name: str = ""
    metadata: dict = field(default_factory=dict)


def get_device_info(device: str = "") -> dict:
    """Get device capability information."""
    if not device:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    info = {"device": device}

    if device == "cuda" and torch.cuda.is_available():
        info["name"] = torch.cuda.get_device_name(0)
        info["capability"] = torch.cuda.get_device_capability(0)
        info["total_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    elif device == "mps":
        info["name"] = "Apple Silicon (MPS)"
        info["total_memory_gb"] = 0  # Shared memory, hard to report accurately
    else:
        try:
            import psutil
            info["name"] = "CPU"
            info["total_memory_gb"] = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            info["name"] = "CPU"
            info["total_memory_gb"] = 0.0

    return info


def measure_model_memory(model, device: str = "") -> MemoryMetrics:
    """Measure a model's memory footprint.

    Args:
        model: PyTorch model.
        device: Device to measure on.

    Returns:
        MemoryMetrics with model size and peak usage.
    """
    metrics = MemoryMetrics()

    # Model parameter size
    param_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    buffer_bytes = sum(b.numel() * b.element_size() for b in model.buffers())
    metrics.model_params_mb = param_bytes / (1024**2)
    metrics.model_buffers_mb = buffer_bytes / (1024**2)
    metrics.total_model_mb = (param_bytes + buffer_bytes) / (1024**2)

    # Peak memory tracking
    if device == "cuda" and torch.cuda.is_available():
        metrics.peak_reserved_mb = torch.cuda.max_memory_reserved() / (1024**2)
        metrics.peak_allocated_mb = torch.cuda.max_memory_allocated() / (1024**2)
        metrics.device_name = torch.cuda.get_device_name(0)
    elif device == "mps":
        # MPS doesn't have detailed tracking, estimate from model size
        metrics.peak_allocated_mb = metrics.total_model_mb * 1.2  # rough overhead
        metrics.device_name = "Apple Silicon (MPS)"
    else:
        try:
            import psutil
            metrics.ram_usage_mb = psutil.Process().memory_info().rss / (1024**2)
        except ImportError:
            metrics.ram_usage_mb = metrics.total_model_mb * 1.1  # rough estimate
        metrics.device_name = "CPU"

    return metrics


def format_memory_table(results: list[tuple[str, str, str, MemoryMetrics]]) -> str:
    """Format memory results as a markdown table.

    Each entry: (model_name, quant, device, metrics)
    """
    header = "| Model | Quant | Device | Params(MB) | Total(MB) | Peak(MB) | RAM(MB) |"
    sep = "|" + "---|" * 7
    rows = [header, sep]
    for name, quant, device, m in results:
        rows.append(
            f"| {name} | {quant} | {device} | {m.model_params_mb:.0f} | "
            f"{m.total_model_mb:.0f} | {m.peak_allocated_mb:.0f} | {m.ram_usage_mb:.0f} |"
        )
    return "\n".join(rows)
