"""Audio engine: manages sounddevice and pushes frames to a queue via callback."""

from typing import Callable
import sounddevice as sd
import numpy as np
from utils.settings import get_audio_rate, get_frames_per_buffer
from utils.logger import logger

class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None], device_index: int, noise_reducer=None):
        self._on_audio = on_audio
        self._stream = None
        self._input_device_index = device_index
        self._noise_reducer = noise_reducer

    def _callback(self, in_data: np.ndarray, frame_count: int, time_info, status) -> None:
        if status:
            logger.debug(f"Audio callback Status: {status}", "AUDIO")
            return

        if in_data is None or len(in_data) == 0:
            return

        self._on_audio(in_data.tobytes())


    def start(self) -> None:
        if self._input_device_index is None:
            logger.warning("No device index provided, cannot start audio engine", "AUDIO")
            return
            
        try:
            if self._stream is None:
                self._stream = sd.InputStream(
                    device=self._input_device_index,
                    blocksize=get_frames_per_buffer(),
                    samplerate=get_audio_rate(),
                    channels=1,
                    dtype='int16',
                    callback=self._callback,
                )
            self._stream.start()
            logger.info(f"Audio engine started on device {self._input_device_index}", "AUDIO")
        except Exception as e:
            logger.error(f"Failed to start audio engine: {e}", "AUDIO")
            self._stream = None

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    def stop(self) -> None:
        if self._stream is not None:
            try:
                if self._stream.active:
                    self._stream.stop()
                self._stream.close()
                logger.info("Audio engine stopped", "AUDIO")
            except Exception as e:
                logger.error(f"Error stopping audio engine: {e}", "AUDIO")
            finally:
                self._stream = None


