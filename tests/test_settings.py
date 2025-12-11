import unittest
from unittest.mock import MagicMock
import os
import sys
import shutil
import tempfile

# Mock sounddevice BEFORE importing application modules
sys.modules['sounddevice'] = MagicMock()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.settings import SettingsManager

class TestSettings(unittest.TestCase):
    def setUp(self):
        # Create a temp file for settings
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_settings(self):
        settings = SettingsManager()
        self.assertEqual(settings.from_code, "en")
        self.assertEqual(settings.to_code, "ru")
        self.assertEqual(settings.rate, 16000)

    def test_save_and_load(self):
        settings = SettingsManager(rate=44100, from_code="ru")
        settings.save_to_file(self.config_path)

        loaded_settings = SettingsManager.load_from_file(self.config_path)
        self.assertEqual(loaded_settings.rate, 44100)
        self.assertEqual(loaded_settings.from_code, "ru")
