"""Models bundle: ASR (Vosk) and MT (Transformers)."""

import torch
# from noisereduce.torchgate import TorchGate as TG
from typing import Callable
from collections import OrderedDict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import exec_time_wrap
from utils.logger import logger
from models.punctuation import PunctuationRestorer


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

        self.punct_restorer = PunctuationRestorer(device=self._device)

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
            logger.info(f"Loading MT model(s): {mt_model_path}", "MODELS")
            
            self._is_pivot = "," in mt_model_path
            if self._is_pivot:
                self._tokenizers = []
                self._mt_models = []
                for path in mt_model_path.split(","):
                    path = path.strip()
                    logger.info(f"Loading pivot part: {path}", "MODELS")
                    tok = AutoTokenizer.from_pretrained(path)
                    mod = AutoModelForSeq2SeqLM.from_pretrained(
                        path, dtype=torch.float16 if self._device == "cuda" else torch.float32
                    ).to(self._device)
                    mod.eval()
                    self._tokenizers.append(tok)
                    self._mt_models.append(mod)
            else:
                self._tokenizer = AutoTokenizer.from_pretrained(mt_model_path)
                self._mt_model = AutoModelForSeq2SeqLM.from_pretrained(
                    mt_model_path,
                    dtype=torch.float16 if self._device == "cuda" else torch.float32
                ).to(self._device)
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
            if getattr(self, '_is_pivot', False):
                current_text = text
                for i in range(len(self._mt_models)):
                    tok = self._tokenizers[i]
                    mod = self._mt_models[i]
                    inputs = tok(current_text, return_tensors="pt").to(self._device)
                    with torch.no_grad():
                        outputs = mod.generate(
                            **inputs, 
                            max_length=128, 
                            num_beams=1, 
                            do_sample=False, 
                            early_stopping=True, 
                            pad_token_id=tok.eos_token_id, 
                            use_cache=True
                        )
                    current_text = tok.decode(outputs[0], skip_special_tokens=True)
                result = current_text
            else:
                # Map Flowl short codes to NLLB target language codes
                nllb_lang_map = {
                    "ru": "rus_Cyrl",
                    "en": "eng_Latn",
                    "ko": "kor_Hang"
                }
                
                # Check if we are using NLLB
                if "nllb" in self.settings.mt_model_path.lower():
                    src_lang = nllb_lang_map.get(self.settings.from_code, "eng_Latn")
                    self._tokenizer.src_lang = src_lang
                    target_lang = nllb_lang_map.get(self.settings.to_code, "eng_Latn")
                
                # Move inputs to the same device as the model
                inputs = self._tokenizer(text, return_tensors="pt").to(self._device)
                
                # Use faster generation parameters
                with torch.no_grad():  # Disable gradient computation for faster inference
                    
                    if "nllb" in self.settings.mt_model_path.lower():
                        forced_bos_token_id = self._tokenizer.convert_tokens_to_ids(target_lang)
                        outputs = self._mt_model.generate(
                            **inputs,
                            forced_bos_token_id=forced_bos_token_id,
                            max_length=128,        # Reduced from 512
                            num_beams=1,           # Keep greedy
                            do_sample=False,       # Keep deterministic
                            early_stopping=True,   # Stop early when possible
                            pad_token_id=self._tokenizer.eos_token_id,
                            use_cache=True,        # Enable KV cache
                        )
                    else:
                        # Fallback for Helsinki/MarianMT
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



