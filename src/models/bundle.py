"""Models bundle: ASR (Vosk) and MT (Transformers)."""

import torch
# from noisereduce.torchgate import TorchGate as TG
from typing import Callable
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import AUDIO_RATE, MODEL_PATH, MT_MODEL_PATH, exec_time_wrap


class ModelBundle:
    def __init__(self):
        # Simple cache to avoid re-translating identical text
        self._translation_cache = {}
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
                    max_length=512,  # Limit output length
                    num_beams=1,     # Use greedy decoding (faster than beam search)
                    do_sample=False, # Disable sampling for faster generation
                )
            
            result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Cache the result
            if len(self._translation_cache) >= self._max_cache_size:
                # Remove the oldest entry (simple FIFO)
                oldest_key = next(iter(self._translation_cache))
                del self._translation_cache[oldest_key]
            self._translation_cache[text] = result
            
            return result
        except Exception as e:
            print(f"[TRANSLATION ERROR] Failed to translate '{text}': {e}")
            return text  # Return original text if translation fails

    def get_noise_reducer(self) -> Callable:
        """Get the noise reduction model for use in audio processing."""
        return self._tg

    def get_device(self) -> str:
        """Get the device (cpu/cuda) for tensor operations."""
        return self._device


