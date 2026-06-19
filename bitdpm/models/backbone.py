"""Backbone model wrapper for BitDPM.

Loads a HuggingFace transformer and provides:
- Frozen backbone forward
- Layer-level access for parameter block injection
- Quantization support (INT4/INT8 via bitsandbytes)
- ModelScope as fallback download source
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Literal, Optional

import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


# Map of HuggingFace model IDs to their ModelScope equivalents
MODELSCOPE_MAP: dict[str, str] = {
    # Qwen series
    "Qwen/Qwen2.5-0.5B-Instruct": "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct": "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct": "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
    # LLaMA series
    "meta-llama/Llama-3.2-1B": "LLM-Research/Llama-3.2-1B",
    "meta-llama/Llama-3.2-3B": "LLM-Research/Llama-3.2-3B",
    # Qwen older series
    "Qwen/Qwen2-0.5B-Instruct": "Qwen/Qwen2-0.5B-Instruct",
    "Qwen/Qwen2-1.5B-Instruct": "Qwen/Qwen2-1.5B-Instruct",
}

# Default local cache directory for model files
DEFAULT_CACHE_DIR = os.environ.get(
    "BITDPM_CACHE_DIR",
    os.path.join(os.environ.get("TMPDIR", os.path.expanduser("~")), "bitdpm-cache", "models"),
)


def _resolve_model_source(
    model_name_or_path: str,
    prefer: str = "hf",
) -> tuple[str, str]:
    """Resolve model name to (effective_path, source).

    Args:
        model_name_or_path: HF model ID or local path.
        prefer: "hf" (try HuggingFace first, fallback to ModelScope)
                or "modelscope" (try ModelScope first).

    Returns:
        Tuple of (effective_model_name, source_name).
    """
    # If it's already a local path, use it directly
    if os.path.exists(os.path.join(model_name_or_path, "config.json")):
        return model_name_or_path, "local"

    sources = ["modelscope", "hf"] if prefer == "modelscope" else ["hf", "modelscope"]

    for source in sources:
        if source == "modelscope":
            ms_name = MODELSCOPE_MAP.get(model_name_or_path, model_name_or_path)
            try:
                from modelscope import snapshot_download
                # Try to see if the model exists on ModelScope
                cache_dir = os.path.join(DEFAULT_CACHE_DIR, "modelscope")
                os.makedirs(cache_dir, exist_ok=True)
                local_path = snapshot_download(ms_name, cache_dir=cache_dir)
                logger.info(f"[Backbone] Downloaded {model_name_or_path} from ModelScope -> {local_path}")
                return local_path, "modelscope"
            except Exception as e:
                logger.warning(f"[Backbone] ModelScope download failed for {ms_name}: {e}")
                continue

    # Return original name — HF will handle its own retries/errors
    return model_name_or_path, "hf"


class BackboneModel(nn.Module):
    """Wrapper around a HuggingFace causal LM as a frozen backbone.

    The backbone itself is always frozen — all learnable parameters
    are in the separate ParameterBlock modules.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float16,
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        attn_implementation: str = "sdpa",
        bnb_config: Optional[dict] = None,
        source: str = "auto",
        local_files_only: bool = False,
        quantize_method: Optional[Literal["nf4", "int8_sym"]] = None,
    ):
        super().__init__()

        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype
        self._load_in_4bit = load_in_4bit
        self._load_in_8bit = load_in_8bit
        self._attn_implementation = attn_implementation
        self._source = source
        self._local_files_only = local_files_only
        self._quantize_method = quantize_method

        # Detect Metal MPS unless CPU was explicitly requested for memory stability.
        if (
            self.device == "cpu"
            and torch.backends.mps.is_available()
            and os.environ.get("BITDPM_FORCE_CPU", "0") != "1"
        ):
            self.device = "mps"

        # Resolve model source (local path / HF / ModelScope)
        if source == "auto":
            prefer = "modelscope" if "MODELSCOPE" in os.environ else "hf"
        else:
            prefer = source
        self._resolved_model, self._model_source = _resolve_model_source(model_name, prefer=prefer)
        logger.info(f"[Backbone] Using model: {self._resolved_model} (source: {self._model_source})")

        self.config = AutoConfig.from_pretrained(
            self._resolved_model,
            trust_remote_code=True,
            local_files_only=local_files_only,
        )
        self.hidden_size = getattr(self.config, "hidden_size", self.config.hidden_size)
        self.num_hidden_layers = getattr(self.config, "num_hidden_layers", self.config.num_hidden_layers)

        print(f"[Backbone] Loading {model_name} on {self.device} ...")
        self._load_model()
        self._freeze_all()

        # Cache for layer module references (layer_id -> dict of submodules)
        self._layer_cache: dict[int, dict[str, nn.Module]] = {}

        # Apply NF4 / INT8 quantization if requested
        if self._quantize_method == "nf4":
            from bitdpm.models.bitlinear import convert_linear_to_nf4
            n_converted = convert_linear_to_nf4(self.model)
            print(f"[Backbone] Converted {n_converted} linear layers to NF4")
        elif self._quantize_method == "int8_sym":
            from bitdpm.models.bitlinear import convert_linear_to_int8_symmetric
            n_converted = convert_linear_to_int8_symmetric(self.model)
            print(f"[Backbone] Quantized {n_converted} linear layers to INT8 symmetric")

        print(f"[Backbone] Loaded {model_name}: {self.num_params():,} params, device={self.device}")

    def _load_model(self):
        """Load model with optional quantization, supporting HF and ModelScope."""
        model_name = self._resolved_model
        load_kwargs: dict[str, Any] = {
            "trust_remote_code": True,
            "torch_dtype": self.dtype,
            "attn_implementation": self._attn_implementation,
        }

        if self._local_files_only:
            load_kwargs["local_files_only"] = True

        if self._load_in_4bit or self._load_in_8bit:
            try:
                import bitsandbytes  # noqa: F401
                from transformers import BitsAndBytesConfig

                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=self._load_in_4bit,
                    load_in_8bit=self._load_in_8bit,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                load_kwargs["quantization_config"] = bnb_config
                load_kwargs["device_map"] = "auto"
            except ImportError:
                print("[Backbone] bitsandbytes not available, loading in full precision")
                self._load_in_4bit = False
                self._load_in_8bit = False

        self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)

        if not self._load_in_4bit and not self._load_in_8bit:
            self.model = self.model.to(self.device)

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True,
            local_files_only=self._local_files_only,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _freeze_all(self):
        """Freeze all backbone parameters."""
        for param in self.model.parameters():
            param.requires_grad = False

    def num_params(self) -> int:
        """Return total number of parameters."""
        return sum(p.numel() for p in self.model.parameters())

    def num_trainable_params(self) -> int:
        """Return number of trainable (unfrozen) parameters."""
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)

    def get_layer_modules(self, layer_id: int) -> dict[str, nn.Module]:
        """Get submodules of a specific transformer layer.

        Returns a dict: {"q_proj": ..., "k_proj": ..., etc.}
        """
        if layer_id in self._layer_cache:
            return self._layer_cache[layer_id]

        layers = self.model.model.layers if hasattr(self.model.model, "layers") else self.model.model.model.layers
        layer = layers[layer_id]

        modules = {}
        if hasattr(layer, "self_attn"):
            attn = layer.self_attn
            for name in ["q_proj", "k_proj", "v_proj", "o_proj"]:
                if hasattr(attn, name):
                    modules[name] = getattr(attn, name)

        if hasattr(layer, "mlp"):
            mlp = layer.mlp
            for name in ["gate_proj", "up_proj", "down_proj"]:
                if hasattr(mlp, name):
                    modules[name] = getattr(mlp, name)

        self._layer_cache[layer_id] = modules
        return modules

    def get_linear_layer(self, layer_id: int, module_name: str) -> Optional[nn.Linear]:
        """Get a specific linear layer by layer_id and module_name."""
        modules = self.get_layer_modules(layer_id)
        return modules.get(module_name, None)

    def get_layer_dimensions(self, layer_id: int, module_name: str) -> tuple[int, int]:
        """Get (out_features, in_features) for a linear layer."""
        lin = self.get_linear_layer(layer_id, module_name)
        if lin is None:
            return (0, 0)
        return (lin.out_features, lin.in_features)

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        **kwargs,
    ) -> str:
        """Generate text from a prompt."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=self.tokenizer.pad_token_id,
            **kwargs,
        )
        return self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True)

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, **kwargs):
        """Standard forward pass through the backbone."""
        return self.model(input_ids=input_ids, attention_mask=attention_mask, **kwargs)

    def get_logits(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        """Get logits from the backbone."""
        outputs = self.forward(input_ids, attention_mask=attention_mask)
        return outputs.logits

    def to(self, device: str):
        """Move backbone to device (only if not quantized)."""
        if not self._load_in_4bit and not self._load_in_8bit:
            self.model = self.model.to(device)
        self.device = device
        return self
