"""Models bundle: ASR (Vosk) and MT (Transformers)."""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import AUDIO_RATE, MODEL_PATH, MT_MODEL_PATH


class ModelBundle:
    def __init__(self):
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
            self._mt_model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL_PATH)
            print("✓ MT model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load MT model {MT_MODEL_PATH}: {e}")

    def translate(self, text: str) -> str:
        try:
            inputs = self._tokenizer(text, return_tensors="pt")
            outputs = self._mt_model.generate(**inputs)
            return self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"[TRANSLATION ERROR] Failed to translate '{text}': {e}")
            return text  # Return original text if translation fails


