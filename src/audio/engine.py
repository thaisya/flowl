"""Audio engine: manages PyAudio and pushes frames to a queue via callback."""

from typing import Callable, Tuple
import queue
import pyaudio

from src.utils import AUDIO_RATE, FRAMES_PER_BUFFER


class AudioEngine:
    def __init__(self, on_audio: Callable[[bytes], None]):
        self._on_audio = on_audio
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            stream_callback=self._callback,
        )

    def _callback(self, in_data: bytes, frame_count: int, time_info, status) -> Tuple[None, int]:
        try:
            self._on_audio(in_data)
        except queue.Full:
            pass
        return (None, pyaudio.paContinue)

    def start(self) -> None:
        self._stream.start_stream()

    def is_active(self) -> bool:
        return self._stream.is_active()

    def stop(self) -> None:
        if self._stream.is_active():
            self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()


