"""Worker threads for ASR and MT."""

import threading
import time
import json
from collections import deque

from utils.utils import filter_partial, exec_time_wrap
from utils.logger import logger


class ASRWorker(threading.Thread):
    def __init__(self, audio_q: deque, events_q: deque, recognizer, audio_lock: threading.Condition, events_lock: threading.Condition, settings):
        super().__init__(daemon=True)
        self._audio_q = audio_q
        self._events_q = events_q
        self._rec = recognizer
        self._prev_partial = ""
        self._last_partial_time = 0.0
        self._audio_lock = audio_lock
        self.settings = settings
        self._events_lock = events_lock

    def generate_final_result(self, data: bytes) -> None:
            res = json.loads(self._rec.Result())
            final_text = res.get("text", "").strip()

            if final_text:
                with self._events_lock:
                    self._events_q.append(("final", final_text))
                    self._events_lock.notify()
            self._prev_partial = ""

    def generate_partial_result(self, data: bytes) -> None:
        now = time.time() * 1000
        if now - self._last_partial_time < self.settings.throttle_ms:
            return

        self._last_partial_time = now

        pres = json.loads(self._rec.PartialResult())
        partial_text = pres.get("partial", "").strip()

        if not partial_text or partial_text == self._prev_partial or (len(partial_text) < self.settings.min_part_chars and len(partial_text.split()) < self.settings.min_part_words):
            return

        with self._events_lock:
            self._events_q.append(("partial", partial_text))
            self._events_lock.notify()
        self._prev_partial = partial_text


    def run(self) -> None:
        while True:
            try:
                with self._audio_lock:
                    while not self._audio_q:
                        self._audio_lock.wait()
                    data = self._audio_q.popleft()

                if data is None:
                    logger.info("ASR worker exiting", "ASR")
                    break
            except IndexError:
                # This shouldn't happen with correct Condition logic, but good for safety
                continue

            try:
                if self._rec.AcceptWaveform(data):
                    self.generate_final_result(data)
                else:
                    self.generate_partial_result(data)
            except Exception as e:
                logger.error(f"ASR ERROR: {e}", "ASR")


class MTWorker(threading.Thread):
    def __init__(self, events_q: deque, translate_fn, events_lock: threading.Condition, ui_callback=None, settings=None):
        super().__init__(daemon=True)
        self._events_q = events_q
        self._translate = translate_fn
        self._events_lock = events_lock
        self._last_emit_time = 0.0
        self._last_shown_partial = ""
        self._ui_callback = ui_callback  # Callback for UI updates
        self.settings = settings

    def output_final_result(self, text) -> None:
        if not text:
            return
        final_text_sliced = ""
        partial_text_sliced = ""
        
        try:
            partial_half_word_count = len(self._last_shown_partial.split()) // 2
            
            text_words = text.split()
            partial_words = self._last_shown_partial.split() 
            if 0 < partial_half_word_count <= len(text_words):
                final_text_sliced = " ".join(text_words[-partial_half_word_count:])
                partial_text_sliced = " ".join(partial_words[-partial_half_word_count:])
            else:
                final_text_sliced = text
                partial_text_sliced = self._last_shown_partial
        except (IndexError, ValueError):
            pass

        if final_text_sliced != partial_text_sliced and len(final_text_sliced) >= self.settings.min_part_chars:
            try:
                translated_text = self._translate(final_text_sliced)
                if self._ui_callback:
                    self._ui_callback("final", {
                        "original": final_text_sliced,
                        "translated": translated_text,
                        "timestamp": time.time()
                    })
                else:
                    logger.info(f"Final translation: {final_text_sliced} --> {translated_text}", "MT")
            except Exception as e:
                if self._ui_callback:
                    self._ui_callback("error", {
                        "type": "translation_error",
                        "message": str(e),
                        "original": final_text_sliced,
                        "timestamp": time.time()
                    })
                else:
                    logger.error(f"Final translation error: {final_text_sliced} --> {e}", "MT")

        self._last_emit_time = 0
        self._last_shown_partial = ""


    def output_partial_result(self, text: str) -> None:
        now = time.time() * 1000.0
        if now - self._last_emit_time < self.settings.throttle_ms:
            return

        if text == self._last_shown_partial:
            return

        if len(text) < self.settings.min_part_chars and len(text.split()) < self.settings.min_part_words:
            return

        text = filter_partial(text, self.settings.max_part_words)
        try:
            translated_partial = self._translate(text)
            # Send structured event to UI instead of printing
            if self._ui_callback:
                self._ui_callback("partial", {
                    "original": text,
                    "translated": translated_partial,
                    "timestamp": now
                })
            else:
                logger.info(f"Partial translation: {text} --> {translated_partial}", "MT")
            self._last_emit_time = now
            self._last_shown_partial = text
        except Exception as e:
            if self._ui_callback:
                self._ui_callback("error", {
                    "type": "partial_translation_error",
                    "message": str(e),
                    "original": text,
                    "timestamp": now
                })
            else:
                logger.error(f"Partial translation error: {e}", "MT")
        

    def run(self) -> None:
        while True:
            try:
                with self._events_lock:
                    while not self._events_q:
                        self._events_lock.wait()
                    text_type, text = self._events_q.popleft()
            except IndexError:
                continue

            if text_type == "final":
                if text is None:
                    logger.info("MT worker exiting", "MT")
                    break
                self.output_final_result(text)

            elif text_type == "partial":
                self.output_partial_result(text)


            
