"""Utilities package public API: configuration constants and helpers."""

from .utils import (
    AUDIO_RATE,
    FRAMES_PER_BUFFER,
    THROTTLE_MS,
    MAX_PARTIAL_WORDS,
    MIN_PARTIAL_CHARS,
    MIN_PARTIAL_WORDS,
    FROM_CODE,
    TO_CODE,
    MODEL_PATH,
    MT_MODEL_PATH,
    MIC_MODE,
    CONSOLE_MODE,
    filter_partial,
    exec_time_wrap
)

from .device_manager import DeviceManager
from .settings import SettingsManager, get_settings, set_settings

__all__ = [
    "AUDIO_RATE",
    "FRAMES_PER_BUFFER",
    "THROTTLE_MS",
    "MAX_PARTIAL_WORDS",
    "MIN_PARTIAL_CHARS",
    "MIN_PARTIAL_WORDS",
    "FROM_CODE",
    "TO_CODE",
    "MODEL_PATH",
    "MT_MODEL_PATH",
    "MIC_MODE",
    "CONSOLE_MODE",
    "filter_partial",
    "DeviceManager",
    "exec_time_wrap",
    "Settings",
    "get_settings",
    "set_settings"
]
