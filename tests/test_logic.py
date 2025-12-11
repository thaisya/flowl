import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import threading
from collections import deque
import time

# Mock sounddevice BEFORE importing application modules
sys.modules['sounddevice'] = MagicMock()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio.workers import MTWorker, ASRWorker
from utils.settings import SettingsManager

class TestMTWorker(unittest.TestCase):
    def setUp(self):
        self.events_q = deque()
        self.events_lock = threading.Lock()
        self.settings = SettingsManager()
        self.settings.throttle_ms = 0 # Disable throttle for testing

        # Mock translation function
        self.mock_translate = MagicMock(side_effect=lambda x: f"TRANSLATED[{x}]")
        self.ui_callback = MagicMock()

        self.worker = MTWorker(
            events_q=self.events_q,
            translate_fn=self.mock_translate,
            events_lock=self.events_lock,
            ui_callback=self.ui_callback,
            settings=self.settings
        )

    def test_output_final_result_slicing(self):
        """Test the slicing logic in output_final_result."""
        self.worker._last_shown_partial = "hello world this is"

        # partial words: [hello, world, this, is] (4) -> half is 2.
        # text words: [hello, world, this, is, a, test] (6)
        # text_words[-2:] -> ["a", "test"] -> "a test"

        final_text = "hello world this is a test"
        self.worker.output_final_result(final_text)

        self.mock_translate.assert_called_with("a test")

    def test_empty_string_crash(self):
        """Test handling of empty strings."""
        try:
            self.worker.output_final_result("")
            self.worker.output_partial_result("")
        except Exception as e:
            self.fail(f"Worker crashed on empty string: {e}")

    def test_short_string_logic(self):
        self.worker._last_shown_partial = "hi"
        # 1 word. half = 0.

        self.worker.output_final_result("hi there")
        # Logic is: if 0 < partial_half_word_count (0) <= len... -> False.
        # So it takes full text "hi there".
        self.mock_translate.assert_called_with("hi there")

class TestASRWorker(unittest.TestCase):
    def setUp(self):
        self.audio_q = deque()
        self.events_q = deque()
        self.audio_lock = threading.Lock()
        self.events_lock = threading.Lock()
        self.settings = SettingsManager()

        self.mock_recognizer = MagicMock()

        self.worker = ASRWorker(
            audio_q=self.audio_q,
            events_q=self.events_q,
            recognizer=self.mock_recognizer,
            audio_lock=self.audio_lock,
            events_lock=self.events_lock,
            settings=self.settings
        )

    def test_asr_worker_stops_on_none(self):
        """Test that worker exits when None is popped from queue."""
        self.audio_q.append(None)

        t = threading.Thread(target=self.worker.run)
        t.start()
        t.join(timeout=1.0)

        self.assertFalse(t.is_alive(), "ASR Worker did not exit on None sentinel")

if __name__ == '__main__':
    unittest.main()
