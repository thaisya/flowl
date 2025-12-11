"""Settings management for Flowl application."""

import json
import os
from dataclasses import dataclass, asdict
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
    
    # Device settings
    device_index: int = None
    device_name: str = None
    
    # Model paths (computed properties)
    @property
    def model_path(self) -> str:
        """Get the ASR model path based on from_code."""
        # Use a relative path 'models' in the current working directory,
        # or fallback to an environment variable if set.
        base_path = os.getenv("FLOWL_MODELS_PATH", os.path.join(os.getcwd(), "models"))
        suffix = "vosk-en" if self.from_code == "en" else "vosk-ru"
        return os.path.join(base_path, suffix)
    
    @property
    def mt_model_path(self) -> str:
        """Get the MT model path based on from_code and to_code."""
        if self.from_code == "en" and self.to_code == "ru":
            return "Helsinki-NLP/opus-mt-en-ru"
        elif self.from_code == "ru" and self.to_code == "en":
            return "Helsinki-NLP/opus-mt-ru-en"
        else:
            # Default fallback
            return "Helsinki-NLP/opus-mt-en-ru"

    
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


