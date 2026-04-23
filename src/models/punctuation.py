import torch
from transformers import pipeline
from utils.logger import logger

class PunctuationRestorer:
    """Handles external punctuation models for Korean, English, and Russian."""
    
    def __init__(self, device="cpu"):
        self._device = 0 if device == "cuda" else -1
        self._koen_pipe = None
        self._ru_pipe = None
        
        # Mapping for koen model labels
        self.koen_map = {
            "LABEL_0": "",
            "LABEL_1": ",",
            "LABEL_2": ".",
            "LABEL_3": "?",
            "LABEL_4": "!"
        }
        
        # Mapping for RUPunct model labels
        self.ru_map = {
            "O": "",
            "COMMA": ",",
            "PERIOD": ".",
            "QUESTION": "?",
            "VOSKL": "!",
            "TIRE": "-",
            "DVOETOCHIE": ":",
            "PERIODCOMMA": ";",
            "DEFIS": "-",
            "QUESTIONVOSKL": "?!",
            "MNOGOTOCHIE": "..."
        }

    def _load_koen(self):
        """Lazy load the Korean/English punctuation model."""
        if self._koen_pipe is None:
            logger.info("Loading koen_punctuation model...", "PUNCT")
            try:
                self._koen_pipe = pipeline(
                    "token-classification", 
                    model="whooray/koen_punctuation", 
                    trust_remote_code=True, 
                    device=self._device,
                    aggregation_strategy="simple"
                )
            except Exception as e:
                logger.error(f"Failed to load koen_punctuation: {e}", "PUNCT")

    def _load_ru(self):
        """Lazy load the Russian punctuation model."""
        if self._ru_pipe is None:
            logger.info("Loading RUPunct_small model...", "PUNCT")
            try:
                self._ru_pipe = pipeline(
                    "token-classification", 
                    model="RUPunct/RUPunct_small", 
                    trust_remote_code=True, 
                    device=self._device,
                    aggregation_strategy="simple"
                )
            except Exception as e:
                logger.error(f"Failed to load RUPunct_small: {e}", "PUNCT")

    def restore(self, text: str, lang_code: str) -> str:
        """
        Apply punctuation restoration to the given text.
        lang_code can be 'en', 'ko', or 'ru'.
        """
        if not text or not text.strip():
            return text
            
        if lang_code in ["en", "ko"]:
            return self._restore_koen(text)
        elif lang_code == "ru":
            return self._restore_ru(text)
        else:
            return text

    def _restore_koen(self, text: str) -> str:
        self._load_koen()
        if not self._koen_pipe:
            return text
            
        try:
            outputs = self._koen_pipe(text)
            
            # We reconstruct the string by inserting punctuation at the 'end' index of each grouped entity
            # We iterate backwards so we don't mess up the indices as we insert characters!
            out_chars = list(text)
            
            for group in reversed(outputs):
                label = group.get("entity_group", "LABEL_0")
                punct = self.koen_map.get(label, "")
                if punct:
                    end_idx = group["end"]
                    out_chars.insert(end_idx, punct)
                    
            # Basic fallback capitalize
            result = "".join(out_chars)
            if result and result[0].islower():
                result = result[0].upper() + result[1:]
            return result
        except Exception as e:
            logger.error(f"Error in koen restore: {e}", "PUNCT")
            return text

    def _restore_ru(self, text: str) -> str:
        self._load_ru()
        if not self._ru_pipe:
            return text
            
        try:
            outputs = self._ru_pipe(text)
            
            out_chars = list(text)
            
            # For RUPunct, the label is UPPER_PUNCT or LOWER_PUNCT or UPPER_TOTAL_PUNCT
            # Iterate backwards to safely insert characters
            for group in reversed(outputs):
                label: str = group.get("entity_group", "LOWER_O")
                
                parts = label.split("_")
                case_action = parts[0] # UPPER, LOWER
                punct_type = parts[-1] # O, COMMA, PERIOD...
                
                punct = self.ru_map.get(punct_type, "")
                start_idx = group["start"]
                end_idx = group["end"]
                
                # Apply case formatting to the first letter of this word segment
                if start_idx < len(out_chars):
                    if case_action == "UPPER":
                        out_chars[start_idx] = out_chars[start_idx].upper()
                    elif case_action == "LOWER":
                        out_chars[start_idx] = out_chars[start_idx].lower()
                        
                # Apply punctuation
                if punct:
                    out_chars.insert(end_idx, punct)
                    
            # Ensure the first letter of the sentence is capitalized
            result = "".join(out_chars)
            if result and result[0].islower():
                result = result[0].upper() + result[1:]
                
            return result
        except Exception as e:
            logger.error(f"Error in ru restore: {e}", "PUNCT")
            return text
