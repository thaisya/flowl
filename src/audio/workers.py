"""Worker threads for ASR and MT."""

import threading
import time
import json
from collections import deque

from utils.utils import filter_partial, exec_time_wrap
from utils.logger import logger
from audio.buffer import TriStateBuffer

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
                continue

            try:
                if self._rec.AcceptWaveform(data):
                    self.generate_final_result(data)
                else:
                    self.generate_partial_result(data)
            except Exception as e:
                logger.error(f"ASR ERROR: {e}", "ASR")


class MTWorker(threading.Thread):
    def __init__(self, events_q: deque, translate_fn, punct_fn, events_lock: threading.Condition, ui_callback=None, settings=None):
        super().__init__(daemon=True)
        self._events_q = events_q
        self._translate = translate_fn
        self._punct_fn = punct_fn
        self._events_lock = events_lock
        self._last_emit_time = 0.0
        self._last_shown_partial = ""
        self._ui_callback = ui_callback  # Callback for UI updates
        self.settings = settings
        self.buffer = TriStateBuffer()

    def output_final_result(self, text) -> None:
        if not text:
            return
            
        # Push any remaining text in the buffer as a final commit
        punctuated_text = self._apply_punctuation(text)
        self.buffer.update(punctuated_text)
        remaining_text = self.buffer.get_all_text()
        
        if remaining_text:
            try:
                translated_text = self._translate(remaining_text)
                if self._ui_callback:
                    self._ui_callback("final", {
                        "original": remaining_text,
                        "translated": translated_text,
                        "timestamp": time.time()
                    })
                else:
                    logger.info(f"Final translation: {remaining_text} --> {translated_text}", "MT")
            except Exception as e:
                if self._ui_callback:
                    self._ui_callback("error", {
                        "type": "translation_error",
                        "message": str(e),
                        "original": remaining_text,
                        "timestamp": time.time()
                    })
                else:
                    logger.error(f"Final translation error: {remaining_text} --> {e}", "MT")

        self._last_emit_time = 0
        self.buffer.reset()

    def _apply_punctuation(self, text: str) -> str:
        """Apply punctuation using the external HuggingFace models."""
        if not text:
            return ""
        if self._punct_fn:
            return self._punct_fn(text, self.settings.from_code)
        return text
    def output_partial_result(self, partial_text: str) -> None:
        now = time.time() * 1000.0
        if now - self._last_emit_time < self.settings.throttle_ms:
            return

        punctuated_text = self._apply_punctuation(partial_text)
        self.buffer.update(punctuated_text)
        
        # 1. Extract any newly punctuated HARD sentences
        new_commit = self.buffer.extract_committed()
        if new_commit:
            try:
                commit_trans = self._translate(new_commit)
                if self._ui_callback:
                    # Emitting "final" causes UI to lock this text into its history array
                    self._ui_callback("final", {
                        "original": new_commit,
                        "translated": commit_trans,
                        "timestamp": now
                    })
            except Exception as e:
                logger.error(f"Commit translation error: {e}", "MT")
                
        # 2. Get the remaining active buffer separated
        active_stable, active_tail = self.buffer.get_active_segments()
        active_text = self.buffer.get_all_text()
        
        if not active_text and not new_commit:
            return

        try:
            # 3. Translate the active buffer together to preserve grammar context
            translated_active = ""
            translated_tail = ""
            if active_text:
                translated_active = self._translate(active_text)
                
                # Proportional word count heuristic to find the "tail" of the translation
                if active_tail:
                    orig_words = active_text.split()
                    tail_words = active_tail.split()
                    trans_words = translated_active.split()
                    
                    if orig_words and trans_words:
                        # Calculate proportional number of tail words in the translation
                        tail_ratio = len(tail_words) / len(orig_words)
                        trans_tail_count = max(1, int(round(len(trans_words) * tail_ratio)))
                        
                        if trans_tail_count >= len(trans_words):
                            translated_tail = translated_active
                        else:
                            # Extract exact suffix using string slicing to preserve punctuation spacing if any
                            # But since we just want the substring, we can join the last N words
                            translated_tail = " ".join(trans_words[-trans_tail_count:])
            
            # Send the combined payload to the UI
            if active_text:
                payload = {
                    "original_stable": active_stable,
                    "original_tail": active_tail,
                    "original": active_text,
                    "translated": translated_active,
                    "translated_tail": translated_tail,
                    "timestamp": now
                }
                if self._ui_callback:
                    self._ui_callback("partial", payload)
                else:
                    logger.info(f"Partial translation: {active_text} --> {translated_active}{translated_tail}", "MT")
                
            self._last_emit_time = now
            
        except Exception as e:
            if self._ui_callback:
                self._ui_callback("error", {
                    "type": "partial_translation_error",
                    "message": str(e),
                    "original": active_text,
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
                    event_type, payload = self._events_q.popleft()
            except IndexError:
                continue

            if event_type == "final":
                if payload is None:
                    logger.info("MT worker exiting", "MT")
                    break
                self.output_final_result(payload)

            elif event_type == "partial":
                self.output_partial_result(payload)


            
