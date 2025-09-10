"""Models bundle: ASR (Vosk) and MT (Transformers)."""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer

from utils.utils import AUDIO_RATE, MODEL_PATH, MT_MODEL_PATH


class ModelBundle:
    def __init__(self):
        self._asr_model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self._asr_model, AUDIO_RATE)
        self._tokenizer = AutoTokenizer.from_pretrained(MT_MODEL_PATH)
        self._mt_model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL_PATH)

    def translate(self, text: str) -> str:
        inputs = self._tokenizer(text, return_tensors="pt")
        outputs = self._mt_model.generate(**inputs)
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True)


