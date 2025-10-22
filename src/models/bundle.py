"""Models bundle: ASR (Vosk) and MT (Transformers)."""

import torch
# from noisereduce.torchgate import TorchGate as TG
from typing import Callable
from collections import OrderedDict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import exec_time_wrap
from utils.logger import logger


class ModelBundle:
    def __init__(self, settings):
        self.settings = settings
        # Simple cache to avoid re-translating identical text
        self._translation_cache = OrderedDict()
        self._max_cache_size = 100    
        self._tg = None
        # Try to load on GPU for much faster inference
        try:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self._device}", "MODELS")
        except Exception as e:
            logger.warning(f"Failed to load torch: {e}, using CPU", "MODELS")
            self._device = "cpu"

        try:
            model_path = self.settings.model_path
            logger.info(f"Loading ASR model from: {model_path}", "MODELS")
            self._asr_model = Model(model_path)
            self.recognizer = KaldiRecognizer(self._asr_model, self.settings.rate)
            logger.info("ASR model loaded successfully", "MODELS")
        except Exception as e:
            raise RuntimeError(f"Failed to load ASR model from {self.settings.model_path}: {e}")
        
        try:
            mt_model_path = self.settings.mt_model_path
            logger.info(f"Loading MT model: {mt_model_path}", "MODELS")
            self._tokenizer = AutoTokenizer.from_pretrained(mt_model_path)
            
            self._mt_model = AutoModelForSeq2SeqLM.from_pretrained(
                mt_model_path,
                dtype=torch.float16 if self._device == "cuda" else torch.float32
            ).to(self._device)
            
            # Enable evaluation mode for faster inference
            self._mt_model.eval()
            logger.info(f"MT model loaded successfully on {self._device}", "MODELS")
        except Exception as e:
            raise RuntimeError(f"Failed to load MT model {self.settings.mt_model_path}: {e}")


    @exec_time_wrap
    def translate(self, text: str) -> str:
        # Check cache first
        if text in self._translation_cache:
            return self._translation_cache[text]
        
        try:
            # Move inputs to the same device as the model
            inputs = self._tokenizer(text, return_tensors="pt").to(self._device)
            
            # Use faster generation parameters
            with torch.no_grad():  # Disable gradient computation for faster inference
                outputs = self._mt_model.generate(
                    **inputs,
                    max_length=128,        # Reduced from 512
                    num_beams=1,           # Keep greedy
                    do_sample=False,       # Keep deterministic
                    early_stopping=True,   # Stop early when possible
                    pad_token_id=self._tokenizer.eos_token_id,
                    use_cache=True,        # Enable KV cache
                )
            
            result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Cache the result
            if len(self._translation_cache) >= self._max_cache_size:
                self._cleanup_cache()
            
            self._translation_cache[text] = result
            
            return result
        except Exception as e:
            logger.error(f"Failed to translate '{text}': {e}", "MODELS")
            return text  # Return original text if translation fails

    def _cleanup_cache(self) -> None:
        """Efficiently evict oldest entries."""
        for _ in range(self._max_cache_size // 4):
            if self._translation_cache:
                self._translation_cache.popitem(last=False)

    def get_noise_reducer(self) -> Callable:
        """Get the noise reduction model for use in audio processing."""
        return self._tg

    def get_device(self) -> str:
        """Get the device (cpu/cuda) for tensor operations."""
        return self._device

    def clear_cache(self) -> None:
        """Clear the translation cache. DEBUG TOOL"""
        self._translation_cache.clear()
        logger.info("Cleared translation cache", "MODELS")



