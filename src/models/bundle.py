"""Models bundle: ASR (Vosk) and MT (Transformers)."""

import torch
# from noisereduce.torchgate import TorchGate as TG
from typing import Callable
from collections import OrderedDict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import AUDIO_RATE, MODEL_PATH, MT_MODEL_PATH, exec_time_wrap


class ModelBundle:
    def __init__(self):
        # Simple cache to avoid re-translating identical text
        self._translation_cache = OrderedDict()
        self._max_cache_size = 100
        # Try to load on GPU for much faster inference
        try:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Using device: {self._device}")
        except Exception as e:
            print(f"Failed to load torch: {e}")
            self._device = "cpu"

        try:
            print(f"Loading ASR model from: {MODEL_PATH}")
            self._asr_model = Model(MODEL_PATH)
            self.recognizer = KaldiRecognizer(self._asr_model, AUDIO_RATE)
            print("✓ ASR model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load ASR model from {MODEL_PATH}: {e}")
        
        try:
            print(f"Loading MT model: {MT_MODEL_PATH}")
            self._tokenizer = AutoTokenizer.from_pretrained(MT_MODEL_PATH)
            # Optimize tokenizer for faster generation
            self._tokenizer.pad_token = self._tokenizer.eos_token
            self._tokenizer.padding_side = "left"  # For faster generation
            
            self._mt_model = AutoModelForSeq2SeqLM.from_pretrained(
                MT_MODEL_PATH,
                dtype=torch.float16 if self._device == "cuda" else torch.float32
            ).to(self._device)
            
            # Enable evaluation mode for faster inference
            self._mt_model.eval()
            print(f"✓ MT model loaded successfully on {self._device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load MT model {MT_MODEL_PATH}: {e}")

        self._tg = None
        self._cache_hits = 0
        self._cache_requests = 0
        self._translation_count = 0
        self._total_translation_time = 0.0

    @exec_time_wrap
    def translate(self, text: str) -> str:
        self._cache_requests += 1
        # Check cache first
        if text in self._translation_cache:
            self._cache_hits += 1
            return self._translation_cache[text]
        
        # Track translation count and time
        self._translation_count += 1
        
        try:
            # Move inputs to the same device as the model
            inputs = self._tokenizer(text, return_tensors="pt").to(self._device)
            
            # Use faster generation parameters
            with torch.no_grad():  # Disable gradient computation for faster inference
                outputs = self._mt_model.generate(
                    **inputs,
                    max_length=256,        # Reduced from 512
                    num_beams=1,           # Keep greedy
                    do_sample=False,       # Keep deterministic
                    early_stopping=True,   # Stop early when possible
                    pad_token_id=self._tokenizer.eos_token_id,
                    use_cache=True,        # Enable KV cache
                )
            
            result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Cache the result
            if len(self._translation_cache) >= self._max_cache_size:
                # Remove oldest 25% of cache entries
                self._evict_cache()
            
            self._translation_cache[text] = result
            
            return result
        except Exception as e:
            print(f"[TRANSLATION ERROR] Failed to translate '{text}': {e}")
            return text  # Return original text if translation fails

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self._translation_cache.clear()
        print(f"[CACHE] Cleared translation cache")

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._translation_cache),
            "max_size": self._max_cache_size,
            "hit_rate": self._cache_hits / max(self._cache_requests, 1)
        }

    def _cleanup_cache(self) -> None:
        """Periodically clean up cache to prevent memory bloat."""
        if len(self._translation_cache) > self._max_cache_size * 0.8:
            # Remove oldest 50% when cache is 80% full
            for _ in range(len(self._translation_cache) // 2):
                self._translation_cache.popitem(last=False)

    def _evict_cache(self) -> None:
        """Efficiently evict oldest entries."""
        if len(self._translation_cache) >= self._max_cache_size:
            # Use iterator to avoid creating full list
            keys_to_remove = []
            for i, key in enumerate(self._translation_cache.keys()):
                if i >= self._max_cache_size // 4:
                    break
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._translation_cache[key]

    def get_noise_reducer(self) -> Callable:
        """Get the noise reduction model for use in audio processing."""
        return self._tg

    def get_device(self) -> str:
        """Get the device (cpu/cuda) for tensor operations."""
        return self._device

    def get_performance_stats(self) -> dict:
        """Get detailed performance statistics."""
        return {
            "cache": self.get_cache_stats(),
            "translation_count": self._translation_count,
            "avg_translation_time": self._total_translation_time / max(self._translation_count, 1),
            "memory_usage": len(self._translation_cache) * 100,  # Rough estimate
        }



