"""Audio engine: manages sounddevice and pushes frames to a queue via callback."""

from typing import Callable, Tuple
import queue
import sounddevice as sd
import numpy as np

from utils import AUDIO_RATE, FRAMES_PER_BUFFER


class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None], device_index: int):
        self._on_audio = on_audio
        self._stream = None
        self._input_device_index = device_index

    def _callback(self, in_data: np.ndarray, frame_count: int, time_info, status) -> None:
        if status:
            print("Audio callback Status:", status)
        try:
            # in_data is int16 ndarray; forward raw PCM s16le bytes
            self._on_audio(in_data.tobytes())
        except queue.Full:
            pass

    def start(self) -> None:
        if self._input_device_index is None:
            return None
        if self._stream is None:
            self._stream = sd.InputStream(
                device=self._input_device_index,
                blocksize=FRAMES_PER_BUFFER,
                samplerate=AUDIO_RATE,
                channels=1,
                dtype='int16',
                callback=self._callback,
            )
        self._stream.start()

    def is_active(self) -> bool:
        return self._stream is not None and self._stream.active

    def stop(self) -> None:
        if self._stream is not None:
            if self._stream.active:
                self._stream.stop()
            self._stream.close()
            self._stream = None


