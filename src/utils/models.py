"""ASR (Vosk) and MT (Transformers) model initialization and helpers."""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from vosk import Model, KaldiRecognizer
from .utils import AUDIO_RATE, MODEL_PATH, MT_MODEL_PATH

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, AUDIO_RATE)

# TODO convert to ONNX later
tokenizer = AutoTokenizer.from_pretrained(MT_MODEL_PATH)
mt_model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL_PATH)

def translate(text: str) -> str:
    """Translate the given text using the loaded MT model."""
    inputs = tokenizer(text, return_tensors="pt")
    outputs = mt_model.generate(**inputs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)