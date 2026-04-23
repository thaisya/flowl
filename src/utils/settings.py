"""Settings management for Flowl application."""

import json
import os
from dataclasses import dataclass, asdict, field
from utils.logger import logger


@dataclass
class SettingsManager:
    """Configuration settings for Flowl application."""
    
    # Audio configuration
    rate: int = 16000
    frames_per_buffer: int = 2048
    throttle_ms: int = 50
    max_part_words: int = 16
    min_part_words: int = 1
    min_part_chars: int = 1
    
    # Language configuration
    from_code: str = "en"
    to_code: str = "ru"
    aviable_langs: tuple = ("en", "ru", "ko")
    
    # Device settings
    device_index: int = None
    device_name: str = None
    
    # UI configuration
    font_size: int = 24
    opacity: float = 0.3
    font_color: str = "WHITE"
    bg_color: str = "BLACK"
    show_original: bool = True
    text_alignment: str = "CENTER"
    
    # Keybind configuration
    lock_hotkey: str = "ctrl+alt+l"
    
    # Text display limit
    max_screen_words: int = 30
    
    # Model configuration
    asr_model_paths: dict = field(default_factory=lambda: {
        "en": r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-en",
        "ru": r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-ru",
        "ko": r"C:\Users\nikit\Desktop\Flowl_necessary_files\vosk-ko"
    })
    
    mt_model_paths: dict = field(default_factory=lambda: {
        "en-ru": "Helsinki-NLP/opus-mt-en-ru",
        "ru-en": "Helsinki-NLP/opus-mt-ru-en"
    })
    
    # Model paths (computed properties)
    @property
    def model_path(self) -> str:
        """Get the ASR model path based on from_code."""
        return self.asr_model_paths.get(self.from_code, "")
    
    @property
    def mt_model_path(self) -> str:
        """Get the MT model path based on from_code and to_code."""
        pair = f"{self.from_code}-{self.to_code}"
        return self.mt_model_paths.get(pair, "Helsinki-NLP/opus-mt-en-ru")

    
    def save_to_file(self, filepath: str = "config.json") -> None:
        """Save settings to JSON file."""
        config_data = asdict(self)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str = "config.json") -> "SettingsManager":
        """Load settings from JSON file."""
        if not os.path.exists(filepath):
            return cls()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Create settings instance
            settings = cls(**config_data)
            return settings
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Error loading config file {filepath}: {e}", "SETTINGS")
            logger.info("Using default settings.", "SETTINGS")
            return cls()
    
    def update_from_dict(self, config_dict: dict) -> None:
        """Update settings from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)


